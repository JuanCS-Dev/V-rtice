"""
Workflow Generator - Generates GitHub Actions workflows for wargaming.

Creates dynamic workflows that:
- Clone repository and checkout branches
- Run exploit before patch (should succeed = vulnerable)
- Apply patch (checkout PR branch)
- Run exploit after patch (should fail = fixed)
- Collect evidence (logs, exit codes, screenshots)
- Report results back to system
"""

import logging
from typing import Any, Dict, List, Optional

import yaml
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class WorkflowStep(BaseModel):
    """GitHub Actions workflow step."""

    name: str
    id: Optional[str] = None
    run: Optional[str] = None
    uses: Optional[str] = None
    with_: Optional[Dict[str, str]] = Field(default=None, alias="with")
    env: Optional[Dict[str, str]] = None
    continue_on_error: Optional[bool] = None
    timeout_minutes: Optional[int] = None


class WorkflowJob(BaseModel):
    """GitHub Actions workflow job."""

    name: str
    runs_on: str = "ubuntu-latest"
    timeout_minutes: int = 30
    steps: List[WorkflowStep]
    env: Optional[Dict[str, str]] = None


class WorkflowConfig(BaseModel):
    """GitHub Actions workflow configuration."""

    name: str
    on: Dict[str, Any]  # Trigger configuration
    env: Optional[Dict[str, str]] = None
    jobs: Dict[str, WorkflowJob]


class ExploitContext(BaseModel):
    """Context for exploit execution."""

    language: str  # "python", "javascript", "bash"
    setup_commands: List[str]  # Commands to setup environment
    exploit_script: str  # Exploit code/script
    expected_exit_before: int = 1  # Exit code if vulnerable (before patch)
    expected_exit_after: int = 0  # Exit code if fixed (after patch)
    timeout_minutes: int = 5


class WorkflowGenerator:
    """
    Generates GitHub Actions workflows for security wargaming.

    Features:
    - Dynamic workflow generation from templates
    - Multi-language exploit support (Python, JavaScript, Go)
    - Evidence collection (logs, exit codes)
    - Result reporting via artifacts
    """

    def __init__(self, repository_owner: str, repository_name: str):
        """
        Initialize workflow generator.

        Args:
            repository_owner: GitHub repository owner
            repository_name: GitHub repository name
        """
        self.repository_owner = repository_owner
        self.repository_name = repository_name

        logger.info(
            f"WorkflowGenerator initialized: {repository_owner}/{repository_name}"
        )

    def generate_workflow(
        self,
        apv_code: str,
        cve_id: str,
        pr_branch: str,
        base_branch: str,
        exploit_context: ExploitContext,
        affected_files: List[str],
    ) -> str:
        """
        Generate GitHub Actions workflow YAML.

        Args:
            apv_code: APV code (e.g., APV-20251013-001)
            cve_id: CVE identifier
            pr_branch: PR branch name (with patch)
            base_branch: Base branch (without patch)
            exploit_context: Exploit execution context
            affected_files: Files affected by vulnerability

        Returns:
            YAML string for GitHub Actions workflow
        """
        logger.info(f"Generating workflow for {apv_code} ({cve_id})")

        # Build workflow configuration
        workflow = self._build_workflow_config(
            apv_code=apv_code,
            cve_id=cve_id,
            pr_branch=pr_branch,
            base_branch=base_branch,
            exploit_context=exploit_context,
            affected_files=affected_files,
        )

        # Convert to YAML
        workflow_yaml = self._to_yaml(workflow)

        logger.info(f"Generated workflow: {len(workflow_yaml)} bytes")

        return workflow_yaml

    def _build_workflow_config(
        self,
        apv_code: str,
        cve_id: str,
        pr_branch: str,
        base_branch: str,
        exploit_context: ExploitContext,
        affected_files: List[str],
    ) -> WorkflowConfig:
        """Build workflow configuration object."""
        # Workflow name
        workflow_name = f"Security Wargame: {cve_id} ({apv_code})"

        # Trigger: manual dispatch only (triggered programmatically)
        workflow_on = {
            "workflow_dispatch": {
                "inputs": {
                    "apv_code": {
                        "description": "APV Code",
                        "required": True,
                        "default": apv_code,
                    },
                    "pr_branch": {
                        "description": "PR Branch (with patch)",
                        "required": True,
                        "default": pr_branch,
                    },
                }
            }
        }

        # Build steps
        steps = self._build_workflow_steps(
            apv_code=apv_code,
            cve_id=cve_id,
            pr_branch=pr_branch,
            base_branch=base_branch,
            exploit_context=exploit_context,
            affected_files=affected_files,
        )

        # Build job
        job = WorkflowJob(
            name="Wargame Test",
            runs_on="ubuntu-latest",
            timeout_minutes=30,
            steps=steps,
            env={
                "APV_CODE": apv_code,
                "CVE_ID": cve_id,
                "PR_BRANCH": pr_branch,
                "BASE_BRANCH": base_branch,
            },
        )

        # Build workflow
        workflow = WorkflowConfig(
            name=workflow_name,
            on=workflow_on,
            jobs={"wargame": job},
        )

        return workflow

    def _build_workflow_steps(
        self,
        apv_code: str,
        cve_id: str,
        pr_branch: str,
        base_branch: str,
        exploit_context: ExploitContext,
        affected_files: List[str],
    ) -> List[WorkflowStep]:
        """Build workflow steps."""
        steps = []

        # Step 1: Checkout base branch (vulnerable)
        steps.append(
            WorkflowStep(
                name="Checkout base branch (vulnerable code)",
                uses="actions/checkout@v4",
                with_={
                    "ref": base_branch,
                    "fetch-depth": 0,
                },
            )
        )

        # Step 2: Setup environment
        setup_steps = self._build_setup_steps(exploit_context)
        steps.extend(setup_steps)

        # Step 3: Run exploit (before patch)
        steps.append(
            WorkflowStep(
                name="🎯 Test exploit BEFORE patch (should succeed = vulnerable)",
                id="test_before",
                run=self._build_exploit_script(
                    exploit_context, phase="before"
                ),
                continue_on_error=True,
                timeout_minutes=exploit_context.timeout_minutes,
            )
        )

        # Step 4: Checkout PR branch (patched)
        steps.append(
            WorkflowStep(
                name="Checkout PR branch (patched code)",
                uses="actions/checkout@v4",
                with_={
                    "ref": pr_branch,
                    "clean": "false",  # Keep environment setup
                },
            )
        )

        # Step 5: Run exploit (after patch)
        steps.append(
            WorkflowStep(
                name="🛡️ Test exploit AFTER patch (should fail = fixed)",
                id="test_after",
                run=self._build_exploit_script(
                    exploit_context, phase="after"
                ),
                continue_on_error=True,
                timeout_minutes=exploit_context.timeout_minutes,
            )
        )

        # Step 6: Collect evidence
        steps.append(
            WorkflowStep(
                name="📊 Collect evidence and generate report",
                id="collect_evidence",
                run=self._build_evidence_collection_script(
                    apv_code, cve_id, exploit_context
                ),
            )
        )

        # Step 7: Upload evidence as artifact
        steps.append(
            WorkflowStep(
                name="📤 Upload evidence artifact",
                uses="actions/upload-artifact@v4",
                with_={
                    "name": f"wargame-evidence-{apv_code}",
                    "path": "wargame-evidence.json",
                    "retention-days": "30",
                },
            )
        )

        # Step 8: Report verdict
        steps.append(
            WorkflowStep(
                name="🏁 Report verdict",
                id="report_verdict",
                run=self._build_verdict_report_script(apv_code, cve_id),
            )
        )

        return steps

    def _build_setup_steps(
        self, exploit_context: ExploitContext
    ) -> List[WorkflowStep]:
        """Build environment setup steps based on language."""
        steps = []

        if exploit_context.language == "python":
            steps.append(
                WorkflowStep(
                    name="Setup Python",
                    uses="actions/setup-python@v5",
                    with_={"python-version": "3.11"},
                )
            )

        elif exploit_context.language == "javascript":
            steps.append(
                WorkflowStep(
                    name="Setup Node.js",
                    uses="actions/setup-node@v4",
                    with_={"node-version": "20"},
                )
            )

        elif exploit_context.language == "go":
            steps.append(
                WorkflowStep(
                    name="Setup Go",
                    uses="actions/setup-go@v5",
                    with_={"go-version": "1.21"},
                )
            )

        # Run custom setup commands
        if exploit_context.setup_commands:
            setup_script = "\n".join(exploit_context.setup_commands)
            steps.append(
                WorkflowStep(
                    name="Install dependencies",
                    run=setup_script,
                )
            )

        return steps

    def _build_exploit_script(
        self, exploit_context: ExploitContext, phase: str
    ) -> str:
        """Build exploit execution script."""
        # Save exploit to file
        exploit_file = f"exploit_{phase}.{self._get_file_extension(exploit_context.language)}"

        script = f"""
# Save exploit script
cat > {exploit_file} << 'EXPLOIT_EOF'
{exploit_context.exploit_script}
EXPLOIT_EOF

# Run exploit
echo "::group::Running exploit ({phase} patch)"
set +e  # Don't exit on error

"""

        # Run command based on language
        if exploit_context.language == "python":
            script += f"python {exploit_file}\n"
        elif exploit_context.language == "javascript":
            script += f"node {exploit_file}\n"
        elif exploit_context.language == "go":
            script += f"go run {exploit_file}\n"
        elif exploit_context.language == "bash":
            script += f"bash {exploit_file}\n"

        script += """
EXPLOIT_EXIT_CODE=$?
echo "::endgroup::"

# Save exit code
echo "$EXPLOIT_EXIT_CODE" > exploit_exit_""" + phase + """.txt
echo "Exploit exit code: $EXPLOIT_EXIT_CODE"

# Exit with exploit code (will be captured by continue-on-error)
exit $EXPLOIT_EXIT_CODE
"""

        return script.strip()

    def _build_evidence_collection_script(
        self, apv_code: str, cve_id: str, exploit_context: ExploitContext
    ) -> str:
        """Build evidence collection script."""
        script = f"""
# Collect evidence from both phases
EXIT_BEFORE=$(cat exploit_exit_before.txt 2>/dev/null || echo "999")
EXIT_AFTER=$(cat exploit_exit_after.txt 2>/dev/null || echo "999")

# Expected results
EXPECTED_EXIT_BEFORE={exploit_context.expected_exit_before}
EXPECTED_EXIT_AFTER={exploit_context.expected_exit_after}

# Calculate verdict
VERDICT="inconclusive"
if [ "$EXIT_BEFORE" == "$EXPECTED_EXIT_BEFORE" ] && [ "$EXIT_AFTER" == "$EXPECTED_EXIT_AFTER" ]; then
  VERDICT="success"
  echo "✅ VERDICT: SUCCESS - Patch fixes vulnerability"
elif [ "$EXIT_BEFORE" == "$EXPECTED_EXIT_BEFORE" ] && [ "$EXIT_AFTER" != "$EXPECTED_EXIT_AFTER" ]; then
  VERDICT="partial"
  echo "⚠️ VERDICT: PARTIAL - Vulnerability exists, patch behavior unexpected"
elif [ "$EXIT_BEFORE" != "$EXPECTED_EXIT_BEFORE" ] && [ "$EXIT_AFTER" == "$EXPECTED_EXIT_AFTER" ]; then
  VERDICT="failure"
  echo "❌ VERDICT: FAILURE - Could not reproduce vulnerability"
else
  VERDICT="inconclusive"
  echo "❓ VERDICT: INCONCLUSIVE - Unexpected behavior"
fi

# Generate evidence JSON
cat > wargame-evidence.json << EOF
{{
  "apv_code": "{apv_code}",
  "cve_id": "{cve_id}",
  "verdict": "$VERDICT",
  "exploit_exit_before": $EXIT_BEFORE,
  "exploit_exit_after": $EXIT_AFTER,
  "expected_exit_before": $EXPECTED_EXIT_BEFORE,
  "expected_exit_after": $EXPECTED_EXIT_AFTER,
  "workflow_run_id": "${{{{ github.run_id }}}}",
  "workflow_run_number": "${{{{ github.run_number }}}}",
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}}
EOF

echo "Evidence collected:"
cat wargame-evidence.json
"""
        return script.strip()

    def _build_verdict_report_script(self, apv_code: str, cve_id: str) -> str:
        """Build verdict reporting script."""
        script = f"""
# Read verdict from evidence
VERDICT=$(jq -r '.verdict' wargame-evidence.json)

echo "::notice title=Wargame Verdict::$VERDICT"

# Set output for downstream steps
echo "verdict=$VERDICT" >> $GITHUB_OUTPUT

# Summary
echo "## 🎮 Wargame Results: {apv_code}" >> $GITHUB_STEP_SUMMARY
echo "" >> $GITHUB_STEP_SUMMARY
echo "**CVE**: {cve_id}" >> $GITHUB_STEP_SUMMARY
echo "**Verdict**: $VERDICT" >> $GITHUB_STEP_SUMMARY
echo "" >> $GITHUB_STEP_SUMMARY
cat wargame-evidence.json | jq '.' >> $GITHUB_STEP_SUMMARY
"""
        return script.strip()

    def _get_file_extension(self, language: str) -> str:
        """Get file extension for language."""
        extensions = {
            "python": "py",
            "javascript": "js",
            "go": "go",
            "bash": "sh",
        }
        return extensions.get(language, "txt")

    def _to_yaml(self, workflow: WorkflowConfig) -> str:
        """Convert workflow config to YAML string."""
        # Convert Pydantic model to dict
        workflow_dict = workflow.model_dump(exclude_none=True, by_alias=True)

        # Generate YAML
        yaml_str = yaml.dump(
            workflow_dict,
            default_flow_style=False,
            sort_keys=False,
            allow_unicode=True,
        )

        return yaml_str
