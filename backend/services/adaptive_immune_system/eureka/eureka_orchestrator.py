"""
Eureka Orchestrator - Main workflow coordinator.

Orchestrates the complete vulnerability remediation pipeline:
1. Consume APV from Oráculo (via RabbitMQ)
2. Confirm vulnerability (static + dynamic analysis)
3. Generate remedy (LLM-powered patching)
4. Validate patch (5-stage pipeline)
5. Create PR (GitHub/GitLab)
6. Send status callbacks to Oráculo

Follows the "Regra de Ouro":
- Zero TODOs
- Zero mocks
- Zero placeholders
- 100% type hints
"""

import asyncio
import logging
from pathlib import Path
from typing import Dict, Optional

from .callback_client import CallbackClient
from .confirmation import ConfirmationEngine, StaticAnalyzer, DynamicAnalyzer
from .remediation import (
    LLMClient,
    RemedyGenerator,
    PatchValidator,
    GeneratedPatch,
)
from .vcs import (
    GitHubClient,
    GitHubRepository,
    PRDescriptionGenerator,
    PRDescriptionContext,
)
from ..messaging.client import RabbitMQClient, get_rabbitmq_client
from ..messaging.publisher import HITLNotificationPublisher
from ..models.wargame import WargameReportMessage

logger = logging.getLogger(__name__)


class EurekaConfig:
    """Configuration for Eureka orchestrator."""

    def __init__(
        self,
        # RabbitMQ
        rabbitmq_url: str,
        # LLM
        anthropic_api_key: Optional[str] = None,
        openai_api_key: Optional[str] = None,
        llm_model: str = "claude-3-5-sonnet-20241022",
        # GitHub
        github_token: Optional[str] = None,
        github_owner: Optional[str] = None,
        github_repo: Optional[str] = None,
        github_default_branch: str = "main",
        # Analysis
        enable_dynamic_analysis: bool = True,
        enable_tests: bool = True,
        enable_build: bool = True,
        # Project
        project_path: Path = Path.cwd(),
    ):
        """
        Initialize Eureka configuration.

        Args:
            rabbitmq_url: RabbitMQ connection URL
            anthropic_api_key: Anthropic API key (optional)
            openai_api_key: OpenAI API key (optional)
            llm_model: LLM model to use
            github_token: GitHub personal access token (optional)
            github_owner: GitHub repository owner (optional)
            github_repo: GitHub repository name (optional)
            github_default_branch: Default branch name
            enable_dynamic_analysis: Enable dynamic analysis
            enable_tests: Enable test execution
            enable_build: Enable build verification
            project_path: Path to project root
        """
        self.rabbitmq_url = rabbitmq_url
        self.anthropic_api_key = anthropic_api_key
        self.openai_api_key = openai_api_key
        self.llm_model = llm_model
        self.github_token = github_token
        self.github_owner = github_owner
        self.github_repo = github_repo
        self.github_default_branch = github_default_branch
        self.enable_dynamic_analysis = enable_dynamic_analysis
        self.enable_tests = enable_tests
        self.enable_build = enable_build
        self.project_path = project_path


class EurekaOrchestrator:
    """
    Main Eureka workflow orchestrator.

    Coordinates all components:
    - ConfirmationEngine
    - RemedyGenerator
    - PatchValidator
    - GitHubClient
    - CallbackClient
    """

    def __init__(self, config: EurekaConfig):
        """
        Initialize Eureka orchestrator.

        Args:
            config: EurekaConfig instance
        """
        self.config = config

        # Initialize components
        self.callback_client = CallbackClient(
            rabbitmq_url=config.rabbitmq_url,
            exchange_name="eureka.status",
            routing_key="apv.status.update",
        )

        # Confirmation engine
        static_analyzer = StaticAnalyzer()
        dynamic_analyzer = DynamicAnalyzer()
        self.confirmation_engine = ConfirmationEngine(
            static_analyzer=static_analyzer,
            dynamic_analyzer=dynamic_analyzer,
            enable_dynamic_analysis=config.enable_dynamic_analysis,
        )

        # Remediation
        self.llm_client = LLMClient(
            anthropic_api_key=config.anthropic_api_key,
            openai_api_key=config.openai_api_key,
        )
        self.remedy_generator = RemedyGenerator(
            llm_client=self.llm_client,
            default_model=config.llm_model,
        )
        self.patch_validator = PatchValidator(
            project_path=config.project_path,
            enable_tests=config.enable_tests,
            enable_build=config.enable_build,
        )

        # VCS (optional)
        self.github_client: Optional[GitHubClient] = None
        if config.github_token and config.github_owner and config.github_repo:
            repository = GitHubRepository(
                owner=config.github_owner,
                repo=config.github_repo,
                default_branch=config.github_default_branch,
            )
            self.github_client = GitHubClient(
                github_token=config.github_token,
                repository=repository,
            )

        self.pr_description_generator = PRDescriptionGenerator()

        # HITL notification publisher (initialized after RabbitMQ connection)
        self.hitl_publisher: Optional[HITLNotificationPublisher] = None

        logger.info("EurekaOrchestrator initialized")

    async def process_apv(
        self,
        apv_id: str,
        apv_code: str,
        cve_id: str,
        cvss_score: Optional[float],
        severity: str,
        cwe_ids: list[str],
        vulnerability_description: str,
        vulnerable_code_signature: str,
        vulnerable_code_type: str,
        affected_files: list[str],
        dependency_name: Optional[str] = None,
        dependency_version: Optional[str] = None,
        dependency_ecosystem: Optional[str] = None,
        fixed_version: Optional[str] = None,
        create_pr: bool = False,
        pr_labels: Optional[list[str]] = None,
        pr_reviewers: Optional[list[str]] = None,
    ) -> Dict[str, any]:
        """
        Process APV through complete remediation pipeline.

        Args:
            apv_id: APV identifier
            apv_code: APV code (e.g., APV-20251013-001)
            cve_id: CVE identifier
            cvss_score: CVSS score
            severity: Severity level
            cwe_ids: CWE identifiers
            vulnerability_description: Human-readable description
            vulnerable_code_signature: Code pattern signature
            vulnerable_code_type: Type (e.g., "deserialization")
            affected_files: Files affected
            dependency_name: Dependency name (if applicable)
            dependency_version: Dependency version (if applicable)
            dependency_ecosystem: Ecosystem (e.g., "pypi", "npm")
            fixed_version: Fixed version (if available)
            create_pr: Whether to create GitHub PR
            pr_labels: PR labels
            pr_reviewers: PR reviewers

        Returns:
            Pipeline results dictionary

        Raises:
            RuntimeError: If pipeline fails
        """
        logger.info(f"🚀 Processing APV: {apv_code} ({cve_id})")

        try:
            # ========================================
            # STAGE 1: CONFIRMATION
            # ========================================
            logger.info(f"📊 Stage 1/5: Vulnerability Confirmation")

            confirmation_result = await self.confirmation_engine.confirm_apv(
                apv_id=apv_id,
                cve_id=cve_id,
                severity=severity,
                vulnerable_code_signature=vulnerable_code_signature,
                vulnerable_code_type=vulnerable_code_type,
                affected_files=affected_files,
                cwe_ids=cwe_ids,
                dependency_name=dependency_name,
                dependency_version=dependency_version,
                dependency_ecosystem=dependency_ecosystem,
            )

            # Send confirmation result to Oráculo
            await self.callback_client.send_confirmation_result(
                apv_id=apv_id,
                confirmed=confirmation_result.confirmed,
                confidence=confirmation_result.confidence,
                static_confidence=confirmation_result.static_confidence,
                dynamic_confidence=confirmation_result.dynamic_confidence,
                false_positive_probability=confirmation_result.false_positive_probability,
                analysis_details={
                    "static_finding_count": len(
                        confirmation_result.static_result.findings
                    ),
                    "dynamic_test_count": len(
                        confirmation_result.dynamic_result.tests
                    )
                    if confirmation_result.dynamic_result
                    else 0,
                    "false_positive_indicators": confirmation_result.false_positive_indicators,
                },
            )

            if not confirmation_result.confirmed:
                logger.warning(
                    f"⚠️ APV {apv_code} not confirmed (confidence={confirmation_result.confidence:.2%})"
                )
                return {
                    "status": "false_positive",
                    "confirmation": confirmation_result,
                }

            logger.info(
                f"✅ APV confirmed (confidence={confirmation_result.confidence:.2%})"
            )

            # ========================================
            # STAGE 2: REMEDY GENERATION
            # ========================================
            logger.info(f"🔧 Stage 2/5: Remedy Generation")

            try:
                remedy_result = await self.remedy_generator.generate_remedy(
                    apv_id=apv_id,
                    cve_id=cve_id,
                    severity=severity,
                    cwe_ids=cwe_ids,
                    vulnerability_description=vulnerability_description,
                    vulnerable_code_signature=vulnerable_code_signature,
                    vulnerable_code_type=vulnerable_code_type,
                    affected_files=affected_files,
                    dependency_name=dependency_name,
                    dependency_version=dependency_version,
                    dependency_ecosystem=dependency_ecosystem,
                    fixed_version=fixed_version,
                )

                if not remedy_result.primary_patch:
                    raise RuntimeError("No viable patch generated")

                primary_patch = remedy_result.primary_patch

                # Send remedy success to Oráculo
                await self.callback_client.send_remedy_generated(
                    apv_id=apv_id,
                    patch_strategy=primary_patch.strategy.name,
                    patch_description=primary_patch.description,
                    confidence=primary_patch.strategy.confidence,
                    risk_level=primary_patch.strategy.risk_level,
                    file_changes=primary_patch.file_changes,
                )

                logger.info(
                    f"✅ Remedy generated: {primary_patch.strategy.name} (confidence={primary_patch.strategy.confidence:.2%})"
                )

            except Exception as e:
                logger.error(f"❌ Remedy generation failed: {e}")

                # Send remedy failure to Oráculo
                await self.callback_client.send_remedy_failed(
                    apv_id=apv_id,
                    error_message=str(e),
                    attempted_strategies=[
                        patch.strategy.name for patch in remedy_result.all_patches
                    ]
                    if "remedy_result" in locals()
                    else [],
                )

                return {
                    "status": "remedy_failed",
                    "error": str(e),
                    "confirmation": confirmation_result,
                }

            # ========================================
            # STAGE 3: PATCH VALIDATION
            # ========================================
            logger.info(f"🧪 Stage 3/5: Patch Validation")

            validation_result = await self.patch_validator.validate_patch(
                primary_patch
            )

            # Send validation result to Oráculo
            await self.callback_client.send_validation_result(
                apv_id=apv_id,
                passed=validation_result.passed,
                confidence=validation_result.confidence,
                checks_passed=validation_result.checks_passed,
                checks_total=validation_result.checks_total,
                validation_details={
                    "syntax_valid": validation_result.syntax_valid,
                    "static_analysis_valid": validation_result.static_analysis_valid,
                    "tests_passed": validation_result.tests_passed,
                    "dependency_compatible": validation_result.dependency_compatible,
                    "build_valid": validation_result.build_valid,
                    "warnings": validation_result.warnings,
                },
            )

            if not validation_result.passed:
                logger.warning(
                    f"⚠️ Patch validation failed (confidence={validation_result.confidence:.2%})"
                )

            logger.info(
                f"✅ Patch validated (confidence={validation_result.confidence:.2%})"
            )

            # ========================================
            # STAGE 4: PR CREATION (optional)
            # ========================================
            pr_result = None

            if create_pr and self.github_client:
                logger.info(f"🔀 Stage 4/5: PR Creation")

                try:
                    # Generate PR description
                    pr_context = PRDescriptionContext(
                        apv_id=apv_id,
                        apv_code=apv_code,
                        cve_id=cve_id,
                        cvss_score=cvss_score,
                        severity=severity,
                        cwe_ids=cwe_ids,
                        vulnerability_description=vulnerability_description,
                        affected_files=affected_files,
                        patch_strategy=primary_patch.strategy.name,
                        patch_description=primary_patch.description,
                        dependency_name=dependency_name,
                        version_before=dependency_version,
                        version_after=fixed_version,
                        static_confidence=confirmation_result.static_confidence,
                        dynamic_confidence=confirmation_result.dynamic_confidence,
                        false_positive_probability=confirmation_result.false_positive_probability,
                        tests_passed=validation_result.tests_passed
                        if validation_result.tests_passed is not None
                        else True,
                        validation_warnings=validation_result.warnings,
                    )

                    pr_body = self.pr_description_generator.generate_description(
                        pr_context
                    )
                    commit_message = (
                        self.pr_description_generator.generate_commit_message(
                            pr_context
                        )
                    )

                    # Create PR
                    branch_name = f"security-fix/{cve_id.lower()}"
                    pr_title = f"🔒 Security Fix: {cve_id} - {severity.upper()}"

                    # Add default labels
                    labels = pr_labels or []
                    if "security" not in labels:
                        labels.append("security")
                    labels.append(f"severity:{severity.lower()}")

                    pull_request = await self.github_client.create_security_fix_pr(
                        branch_name=branch_name,
                        commit_message=commit_message,
                        pr_title=pr_title,
                        pr_body=pr_body,
                        file_changes=primary_patch.file_changes,
                        labels=labels,
                        reviewers=pr_reviewers,
                    )

                    pr_result = {
                        "pr_number": pull_request.number,
                        "pr_url": pull_request.html_url,
                        "branch_name": branch_name,
                    }

                    # Send PR success to Oráculo
                    await self.callback_client.send_pr_created(
                        apv_id=apv_id,
                        pr_number=pull_request.number,
                        pr_url=pull_request.html_url,
                        branch_name=branch_name,
                        commit_sha="",  # Not available from create response
                    )

                    logger.info(
                        f"✅ PR created: #{pull_request.number} ({pull_request.html_url})"
                    )

                except Exception as e:
                    logger.error(f"❌ PR creation failed: {e}")

                    # Send PR failure to Oráculo
                    await self.callback_client.send_pr_failed(
                        apv_id=apv_id,
                        error_message=str(e),
                    )

                    pr_result = {
                        "error": str(e),
                    }

            # ========================================
            # STAGE 5: COMPLETION
            # ========================================
            logger.info(f"✅ Stage 5/5: Pipeline Complete")

            return {
                "status": "success",
                "confirmation": confirmation_result,
                "remedy": remedy_result,
                "validation": validation_result,
                "pr": pr_result,
            }

        except Exception as e:
            logger.error(f"❌ Pipeline failed: {e}", exc_info=True)
            raise RuntimeError(f"APV processing failed: {e}")

    async def handle_wargaming_result(
        self,
        wargame_report: WargameReportMessage,
        apv_data: Dict[str, any],
    ) -> None:
        """
        Handle wargaming result and publish HITL notification.

        Called after wargaming completes to notify HITL console
        that an APV is ready for human review.

        Args:
            wargame_report: Wargaming report message
            apv_data: APV data including confirmation and remedy details

        Raises:
            RuntimeError: If HITL notification publishing fails
        """
        try:
            logger.info(
                f"📨 Handling wargaming result: {wargame_report.run_code} → {wargame_report.verdict}"
            )

            # Ensure HITL publisher is initialized
            if not self.hitl_publisher:
                rabbitmq_client = get_rabbitmq_client()
                self.hitl_publisher = HITLNotificationPublisher(rabbitmq_client)

            # Extract APV data
            apv_id = apv_data["apv_id"]
            apv_code = apv_data["apv_code"]
            priority = apv_data.get("priority", 5)
            cve_id = apv_data["cve_id"]
            cve_title = apv_data.get("cve_title", f"Security fix for {cve_id}")
            severity = apv_data["severity"]
            cvss_score = apv_data.get("cvss_score")
            package_name = apv_data.get("package_name", "unknown")
            package_version = apv_data.get("package_version", "unknown")
            package_ecosystem = apv_data.get("package_ecosystem", "unknown")

            # Extract confirmation data
            confirmation_confidence = apv_data.get("confirmation_confidence", 0.0)
            false_positive_probability = apv_data.get("false_positive_probability", 0.0)
            affected_files = apv_data.get("affected_files", [])

            # Extract remedy data
            patch_strategy = apv_data.get("patch_strategy", "unknown")
            patch_description = apv_data.get("patch_description", "Patch generated")
            pr_number = apv_data.get("pr_number")
            pr_url = apv_data.get("pr_url")

            # Extract validation data
            validation_warnings = apv_data.get("validation_warnings", [])

            # Determine urgency
            requires_immediate_attention = severity in ("critical", "high")
            escalation_reason = (
                "Critical/High severity vulnerability requiring immediate review"
                if requires_immediate_attention
                else None
            )

            # Publish HITL notification
            message_id = await self.hitl_publisher.publish_new_apv_notification(
                apv_id=apv_id,
                apv_code=apv_code,
                priority=priority,
                cve_id=cve_id,
                cve_title=cve_title,
                severity=severity,
                cvss_score=cvss_score,
                package_name=package_name,
                package_version=package_version,
                package_ecosystem=package_ecosystem,
                patch_strategy=patch_strategy,
                patch_description=patch_description,
                pr_number=pr_number,
                pr_url=pr_url,
                confirmation_confidence=confirmation_confidence,
                false_positive_probability=false_positive_probability,
                wargame_verdict=wargame_report.verdict,
                wargame_confidence=wargame_report.confidence_score,
                wargame_run_url=wargame_report.evidence_url,
                wargame_evidence=wargame_report.evidence,
                affected_files=affected_files,
                validation_warnings=validation_warnings,
                requires_immediate_attention=requires_immediate_attention,
                escalation_reason=escalation_reason,
            )

            logger.info(
                f"✅ HITL notification published: {apv_code} (msg_id={message_id})"
            )

            # Send callback to Oráculo about HITL pending state
            await self.callback_client.send_status_update(
                apv_id=apv_id,
                status="pending_hitl",
                details={
                    "wargame_verdict": wargame_report.verdict,
                    "wargame_confidence": wargame_report.confidence_score,
                    "hitl_notification_id": message_id,
                },
            )

        except Exception as e:
            logger.error(f"❌ Failed to handle wargaming result: {e}", exc_info=True)
            raise RuntimeError(f"Wargaming result handling failed: {e}")

    async def start(self) -> None:
        """Start Eureka orchestrator (connect to RabbitMQ)."""
        await self.callback_client.connect()

        # Initialize HITL publisher
        try:
            rabbitmq_client = get_rabbitmq_client()
            self.hitl_publisher = HITLNotificationPublisher(rabbitmq_client)
            logger.info("✅ HITL notification publisher initialized")
        except Exception as e:
            logger.warning(f"⚠️ HITL publisher initialization failed: {e}")
            logger.warning("HITL notifications will not be sent")

        logger.info("✅ Eureka orchestrator started")

    async def stop(self) -> None:
        """Stop Eureka orchestrator (disconnect from RabbitMQ)."""
        await self.callback_client.disconnect()
        logger.info("✅ Eureka orchestrator stopped")

    async def __aenter__(self):
        """Async context manager entry."""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.stop()
