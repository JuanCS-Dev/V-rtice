"""
Wargame Orchestrator - Orchestrates complete wargaming workflow.

Complete Workflow:
1. Generate GitHub Actions workflow YAML
2. Create/update workflow file in repository
3. Trigger workflow run via GitHub API
4. Wait for workflow completion (poll status)
5. Collect evidence from workflow run
6. Calculate verdict and confidence
7. Send report to Eureka/Oráculo via RabbitMQ
8. Take action (auto-merge or trigger HITL)

Integrates all wargaming components into cohesive pipeline.
"""

import asyncio
import logging
from pathlib import Path
from typing import List, Optional

import aiohttp
from pydantic import BaseModel

from .workflow_generator import (
    WorkflowGenerator,
    ExploitContext,
)
from .exploit_templates import ExploitTemplateLibrary
from .evidence_collector import (
    EvidenceCollector,
    WargameEvidence,
)
from .verdict_calculator import (
    VerdictCalculator,
    VerdictScore,
)
from messaging.client import RabbitMQClient, get_rabbitmq_client
from messaging.publisher import WargameReportPublisher
from models.wargame import WargameReportMessage

logger = logging.getLogger(__name__)


class WargameConfig(BaseModel):
    """Configuration for wargaming orchestrator."""

    # GitHub
    github_token: str
    repository_owner: str
    repository_name: str
    default_branch: str = "main"

    # Wargaming
    enable_auto_merge: bool = True
    enable_hitl: bool = True
    workflow_timeout: int = 600  # 10 minutes
    poll_interval: int = 10  # seconds

    # Confidence thresholds
    confidence_threshold: float = 0.7
    hitl_threshold: float = 0.6


class WargameReport(BaseModel):
    """Wargaming result report."""

    apv_code: str
    cve_id: str
    pr_number: int
    pr_url: str
    workflow_run_id: int
    workflow_run_url: str
    verdict: str
    confidence: float
    should_trigger_hitl: bool
    auto_merge_approved: bool
    evidence: WargameEvidence
    verdict_score: VerdictScore


class WargameOrchestrator:
    """
    Orchestrates complete wargaming workflow.

    Features:
    - End-to-end wargaming pipeline
    - GitHub Actions integration
    - Automatic verdict calculation
    - Auto-merge for high-confidence successes
    - HITL escalation for edge cases
    - Result reporting via RabbitMQ
    """

    def __init__(
        self,
        config: WargameConfig,
        rabbitmq_client: Optional[RabbitMQClient] = None,
        auto_publish: bool = True,
    ):
        """
        Initialize wargame orchestrator.

        Args:
            config: WargameConfig
            rabbitmq_client: RabbitMQ client (optional, will get global instance if not provided)
            auto_publish: Automatically publish wargaming results to Eureka via RabbitMQ
        """
        self.config = config
        self.auto_publish = auto_publish

        # Initialize components
        self.workflow_generator = WorkflowGenerator(
            repository_owner=config.repository_owner,
            repository_name=config.repository_name,
        )

        self.exploit_library = ExploitTemplateLibrary()

        self.evidence_collector = EvidenceCollector(
            github_token=config.github_token,
            repository_owner=config.repository_owner,
            repository_name=config.repository_name,
        )

        self.verdict_calculator = VerdictCalculator(
            confidence_threshold=config.confidence_threshold,
            hitl_threshold=config.hitl_threshold,
        )

        # Initialize wargame report publisher
        self.wargame_publisher: Optional[WargameReportPublisher] = None
        if auto_publish:
            try:
                if rabbitmq_client is None:
                    rabbitmq_client = get_rabbitmq_client()
                self.wargame_publisher = WargameReportPublisher(rabbitmq_client)
                logger.info("✅ Wargame report publisher initialized")
            except Exception as e:
                logger.warning(f"⚠️ Wargame publisher initialization failed: {e}")
                logger.warning("Wargame results will not be automatically published to RabbitMQ")
                self.wargame_publisher = None

        logger.info(f"WargameOrchestrator initialized (auto_publish={auto_publish})")

    async def run_wargame(
        self,
        apv_code: str,
        cve_id: str,
        pr_number: int,
        pr_url: str,
        pr_branch: str,
        base_branch: Optional[str] = None,
        cwe_ids: Optional[List[str]] = None,
        affected_files: Optional[List[str]] = None,
        language: str = "python",
    ) -> WargameReport:
        """
        Run complete wargaming workflow for APV.

        Args:
            apv_code: APV code (e.g., APV-20251013-001)
            cve_id: CVE identifier
            pr_number: GitHub PR number
            pr_url: GitHub PR URL
            pr_branch: PR branch name (with patch)
            base_branch: Base branch (without patch), defaults to config default
            cwe_ids: List of CWE IDs
            affected_files: Files affected by vulnerability
            language: Programming language (python, javascript, bash)

        Returns:
            WargameReport with complete results

        Raises:
            RuntimeError: If wargaming fails
        """
        logger.info(f"🎮 Starting wargame for {apv_code} ({cve_id})")

        base_branch = base_branch or self.config.default_branch
        cwe_ids = cwe_ids or []
        affected_files = affected_files or []

        try:
            # Step 1: Get exploit template
            exploit_context = self._get_exploit_context(cwe_ids, language)

            # Step 2: Generate workflow YAML
            workflow_yaml = self.workflow_generator.generate_workflow(
                apv_code=apv_code,
                cve_id=cve_id,
                pr_branch=pr_branch,
                base_branch=base_branch,
                exploit_context=exploit_context,
                affected_files=affected_files,
            )

            logger.info(f"✅ Generated workflow ({len(workflow_yaml)} bytes)")

            # Step 3: Create/update workflow file in repository
            workflow_path = f".github/workflows/wargame-{apv_code.lower()}.yml"
            await self._create_workflow_file(
                workflow_path, workflow_yaml, pr_branch
            )

            logger.info(f"✅ Created workflow file: {workflow_path}")

            # Step 4: Trigger workflow run
            workflow_run_id = await self._trigger_workflow(
                workflow_path, apv_code, pr_branch
            )

            logger.info(f"✅ Triggered workflow run: {workflow_run_id}")

            # Step 5: Wait for workflow completion
            conclusion = await self.evidence_collector.wait_for_completion(
                workflow_run_id,
                timeout_seconds=self.config.workflow_timeout,
                poll_interval=self.config.poll_interval,
            )

            logger.info(f"✅ Workflow completed: {conclusion}")

            # Step 6: Collect evidence
            evidence = await self.evidence_collector.collect_evidence(
                workflow_run_id, apv_code, cve_id
            )

            logger.info(f"✅ Evidence collected: verdict={evidence.verdict}")

            # Step 7: Calculate verdict
            verdict_score = self.verdict_calculator.calculate_verdict(evidence)

            logger.info(
                f"✅ Verdict calculated: {verdict_score.verdict} "
                f"(confidence={verdict_score.confidence:.2%})"
            )

            # Step 8: Determine actions
            auto_merge_approved = False
            if self.config.enable_auto_merge:
                auto_merge_approved = self.verdict_calculator.should_auto_merge(
                    verdict_score
                )

            # Step 9: Build report
            workflow_run_url = (
                f"https://github.com/{self.config.repository_owner}/"
                f"{self.config.repository_name}/actions/runs/{workflow_run_id}"
            )

            report = WargameReport(
                apv_code=apv_code,
                cve_id=cve_id,
                pr_number=pr_number,
                pr_url=pr_url,
                workflow_run_id=workflow_run_id,
                workflow_run_url=workflow_run_url,
                verdict=verdict_score.verdict,
                confidence=verdict_score.confidence,
                should_trigger_hitl=verdict_score.should_trigger_hitl,
                auto_merge_approved=auto_merge_approved,
                evidence=evidence,
                verdict_score=verdict_score,
            )

            logger.info(
                f"🏁 Wargame complete: verdict={verdict_score.verdict}, "
                f"hitl={verdict_score.should_trigger_hitl}, "
                f"auto_merge={auto_merge_approved}"
            )

            # Publish wargaming result to Eureka via RabbitMQ
            if self.wargame_publisher:
                try:
                    # Create wargame report message
                    from datetime import datetime
                    import uuid

                    report_message = WargameReportMessage(
                        message_id=str(uuid.uuid4()),
                        remedy_id=apv_code,  # Using APV code as remedy ID
                        run_code=f"WAR-{apv_code}",
                        timestamp=datetime.utcnow(),
                        verdict=verdict_score.verdict,
                        confidence_score=verdict_score.confidence,
                        exploit_before_status="vulnerable" if evidence.exploit_before_patch_succeeded else "safe",
                        exploit_after_status="fixed" if not evidence.exploit_after_patch_succeeded else "vulnerable",
                        evidence_url=workflow_run_url,
                        evidence=evidence.model_dump() if hasattr(evidence, 'model_dump') else {},
                        should_trigger_hitl=verdict_score.should_trigger_hitl,
                        auto_merge_approved=auto_merge_approved,
                    )

                    # Publish
                    await self.wargame_publisher.publish_report(report_message)

                    logger.info(f"✅ Wargame result published to RabbitMQ: {apv_code}")

                except Exception as e:
                    logger.error(f"❌ Failed to publish wargame result to RabbitMQ: {e}")
                    # Don't fail wargaming if publishing fails

            return report

        except Exception as e:
            logger.error(f"❌ Wargame failed: {e}", exc_info=True)
            raise RuntimeError(f"Wargame failed for {apv_code}: {e}")

    def _get_exploit_context(
        self, cwe_ids: List[str], language: str
    ) -> ExploitContext:
        """Get exploit template for CWEs."""
        # Use first CWE if multiple provided
        if cwe_ids:
            primary_cwe = cwe_ids[0]
            logger.info(f"Using exploit template for {primary_cwe}")
            return self.exploit_library.get_template(primary_cwe, language)
        else:
            logger.warning("No CWE provided, using generic template")
            return self.exploit_library.get_template("CWE-000", language)

    async def _create_workflow_file(
        self, workflow_path: str, workflow_yaml: str, branch: str
    ) -> None:
        """Create or update workflow file in repository via GitHub API."""
        url = (
            f"https://api.github.com/repos/{self.config.repository_owner}/"
            f"{self.config.repository_name}/contents/{workflow_path}"
        )

        headers = {
            "Authorization": f"Bearer {self.config.github_token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

        # Check if file exists
        async with aiohttp.ClientSession() as session:
            # Try to get existing file
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    # File exists, get SHA for update
                    existing = await response.json()
                    sha = existing["sha"]
                    logger.debug(f"Workflow file exists, updating (SHA: {sha[:7]})")
                elif response.status == 404:
                    # File doesn't exist, create new
                    sha = None
                    logger.debug("Workflow file doesn't exist, creating")
                else:
                    error = await response.text()
                    raise RuntimeError(f"Failed to check workflow file: {error}")

            # Create/update file
            import base64

            content_b64 = base64.b64encode(workflow_yaml.encode()).decode()

            payload = {
                "message": f"Add wargame workflow: {workflow_path}",
                "content": content_b64,
                "branch": branch,
            }

            if sha:
                payload["sha"] = sha

            async with session.put(url, headers=headers, json=payload) as response:
                if response.status not in [200, 201]:
                    error = await response.text()
                    raise RuntimeError(f"Failed to create workflow file: {error}")

                logger.debug("Workflow file created/updated successfully")

    async def _trigger_workflow(
        self, workflow_path: str, apv_code: str, pr_branch: str
    ) -> int:
        """Trigger workflow run via GitHub API."""
        # Extract workflow filename
        workflow_file = Path(workflow_path).name

        url = (
            f"https://api.github.com/repos/{self.config.repository_owner}/"
            f"{self.config.repository_name}/actions/workflows/{workflow_file}/dispatches"
        )

        headers = {
            "Authorization": f"Bearer {self.config.github_token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

        payload = {
            "ref": pr_branch,
            "inputs": {
                "apv_code": apv_code,
                "pr_branch": pr_branch,
            },
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as response:
                if response.status != 204:
                    error = await response.text()
                    raise RuntimeError(f"Failed to trigger workflow: {error}")

        # Wait a bit for workflow to start
        await asyncio.sleep(5)

        # Get latest workflow run ID
        runs_url = (
            f"https://api.github.com/repos/{self.config.repository_owner}/"
            f"{self.config.repository_name}/actions/workflows/{workflow_file}/runs"
        )

        async with aiohttp.ClientSession() as session:
            async with session.get(runs_url, headers=headers) as response:
                if response.status != 200:
                    error = await response.text()
                    raise RuntimeError(f"Failed to get workflow runs: {error}")

                data = await response.json()
                runs = data.get("workflow_runs", [])

                if not runs:
                    raise RuntimeError("No workflow runs found after trigger")

                # Return most recent run ID
                latest_run = runs[0]
                return latest_run["id"]
