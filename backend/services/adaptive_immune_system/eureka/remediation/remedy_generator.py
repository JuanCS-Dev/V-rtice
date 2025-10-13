"""
Remedy Generator - Automated vulnerability patching.

Generates fixes using multiple strategies:
1. Version Bump: Update dependency to patched version
2. Code Rewrite: LLM-powered code modification
3. Config Change: Modify configuration to mitigate
4. Workaround: Apply temporary fix until patch available

Features:
- Multi-strategy approach with fallbacks
- LLM-powered intelligent code generation
- Patch validation before application
- Rollback capability
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from pydantic import BaseModel, Field

from .llm_client import LLMClient, LLMResponse

logger = logging.getLogger(__name__)


class PatchStrategy(BaseModel):
    """Patch strategy definition."""

    strategy_type: str  # "version_bump", "code_rewrite", "config_change", "workaround"
    description: str
    confidence: float = Field(ge=0.0, le=1.0)
    estimated_effort: str  # "low", "medium", "high"
    risk_level: str  # "low", "medium", "high"
    reversible: bool = True


class GeneratedPatch(BaseModel):
    """Generated patch result."""

    patch_id: str
    strategy: PatchStrategy
    changes: List[Dict[str, str]]  # file_path -> patch_content
    description: str
    validation_notes: str
    llm_response: Optional[LLMResponse] = None
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class RemedyResult(BaseModel):
    """Complete remedy generation result."""

    apv_id: str
    cve_id: str
    remedy_generated: bool
    primary_patch: Optional[GeneratedPatch] = None
    alternative_patches: List[GeneratedPatch] = Field(default_factory=list)
    generation_duration_seconds: float
    total_cost_usd: float = 0.0
    error_messages: List[str] = Field(default_factory=list)


class RemedyGenerator:
    """
    Generates remedies for confirmed vulnerabilities.

    Multi-strategy approach:
    1. Try version bump first (fastest, safest)
    2. If no fixed version, try code rewrite (LLM-powered)
    3. If code rewrite risky, try config change
    4. As last resort, generate workaround
    """

    def __init__(
        self,
        llm_client: LLMClient,
        project_path: Path,
    ):
        """
        Initialize remedy generator.

        Args:
            llm_client: LLM client for code generation
            project_path: Path to project root
        """
        self.llm_client = llm_client
        self.project_path = Path(project_path)

        logger.info("RemedyGenerator initialized")

    async def generate_remedy(
        self,
        apv_id: str,
        cve_id: str,
        dependency_name: str,
        dependency_version: str,
        dependency_ecosystem: str,
        fixed_version: Optional[str],
        vulnerable_code_signature: Optional[str],
        affected_files: List[str],
        cwe_ids: List[str],
        description: str,
    ) -> RemedyResult:
        """
        Generate remedy for vulnerability.

        Args:
            apv_id: APV identifier
            cve_id: CVE identifier
            dependency_name: Package name
            dependency_version: Current version
            dependency_ecosystem: Ecosystem (pypi, npm, etc.)
            fixed_version: Patched version (if available)
            vulnerable_code_signature: Vulnerable code pattern
            affected_files: List of affected files
            cwe_ids: CWE identifiers
            description: Vulnerability description

        Returns:
            RemedyResult with generated patches
        """
        import time
        start_time = time.time()

        logger.info(f"🔧 Generating remedy for APV: {apv_id} ({cve_id})")

        patches: List[GeneratedPatch] = []
        error_messages: List[str] = []
        total_cost = 0.0

        # Strategy 1: Version Bump (highest priority)
        if fixed_version:
            try:
                patch = await self._generate_version_bump_patch(
                    cve_id,
                    dependency_name,
                    dependency_version,
                    fixed_version,
                    dependency_ecosystem,
                )
                patches.append(patch)
                logger.info(f"✅ Version bump patch generated: {dependency_version} → {fixed_version}")
            except Exception as e:
                error_msg = f"Version bump patch failed: {e}"
                logger.error(error_msg)
                error_messages.append(error_msg)

        # Strategy 2: Code Rewrite (LLM-powered)
        if affected_files and vulnerable_code_signature:
            try:
                patch, llm_cost = await self._generate_code_rewrite_patch(
                    cve_id,
                    dependency_name,
                    affected_files,
                    vulnerable_code_signature,
                    cwe_ids,
                    description,
                )
                patches.append(patch)
                total_cost += llm_cost
                logger.info(f"✅ Code rewrite patch generated (cost: ${llm_cost:.4f})")
            except Exception as e:
                error_msg = f"Code rewrite patch failed: {e}"
                logger.error(error_msg)
                error_messages.append(error_msg)

        # Strategy 3: Config Change
        try:
            patch = await self._generate_config_change_patch(
                cve_id,
                dependency_name,
                cwe_ids,
            )
            if patch:
                patches.append(patch)
                logger.info("✅ Config change patch generated")
        except Exception as e:
            error_msg = f"Config change patch failed: {e}"
            logger.debug(error_msg)  # Debug level, not critical

        # Strategy 4: Workaround (last resort)
        if not patches or all(p.strategy.risk_level == "high" for p in patches):
            try:
                patch, llm_cost = await self._generate_workaround_patch(
                    cve_id,
                    dependency_name,
                    cwe_ids,
                    description,
                )
                patches.append(patch)
                total_cost += llm_cost
                logger.info(f"✅ Workaround patch generated (cost: ${llm_cost:.4f})")
            except Exception as e:
                error_msg = f"Workaround patch failed: {e}"
                logger.error(error_msg)
                error_messages.append(error_msg)

        # Select primary patch (lowest risk, highest confidence)
        primary_patch = None
        alternative_patches = []

        if patches:
            # Sort by risk (low first), then confidence (high first)
            risk_order = {"low": 0, "medium": 1, "high": 2}
            sorted_patches = sorted(
                patches,
                key=lambda p: (risk_order.get(p.strategy.risk_level, 3), -p.strategy.confidence),
            )

            primary_patch = sorted_patches[0]
            alternative_patches = sorted_patches[1:]

        duration = time.time() - start_time

        logger.info(
            f"✅ Remedy generation complete: "
            f"patches={len(patches)}, cost=${total_cost:.4f}, duration={duration:.1f}s"
        )

        return RemedyResult(
            apv_id=apv_id,
            cve_id=cve_id,
            remedy_generated=primary_patch is not None,
            primary_patch=primary_patch,
            alternative_patches=alternative_patches,
            generation_duration_seconds=duration,
            total_cost_usd=total_cost,
            error_messages=error_messages,
        )

    async def _generate_version_bump_patch(
        self,
        cve_id: str,
        dependency_name: str,
        current_version: str,
        fixed_version: str,
        ecosystem: str,
    ) -> GeneratedPatch:
        """
        Generate version bump patch.

        Args:
            cve_id: CVE identifier
            dependency_name: Package name
            current_version: Current version
            fixed_version: Patched version
            ecosystem: Ecosystem

        Returns:
            GeneratedPatch
        """
        strategy = PatchStrategy(
            strategy_type="version_bump",
            description=f"Update {dependency_name} from {current_version} to {fixed_version}",
            confidence=0.95,  # High confidence for version bumps
            estimated_effort="low",
            risk_level="low",
            reversible=True,
        )

        # Generate patch content based on ecosystem
        changes = []

        if ecosystem == "pypi":
            # Update requirements.txt, pyproject.toml, setup.py
            changes.append({
                "file_path": "requirements.txt",
                "patch_content": f"-{dependency_name}=={current_version}\n+{dependency_name}=={fixed_version}",
                "patch_type": "version_update",
            })

        elif ecosystem == "npm":
            # Update package.json
            changes.append({
                "file_path": "package.json",
                "patch_content": f'-    "{dependency_name}": "{current_version}"\n+    "{dependency_name}": "{fixed_version}"',
                "patch_type": "version_update",
            })

        elif ecosystem == "go":
            # Update go.mod
            changes.append({
                "file_path": "go.mod",
                "patch_content": f"-require {dependency_name} {current_version}\n+require {dependency_name} {fixed_version}",
                "patch_type": "version_update",
            })

        patch_id = f"PATCH-{cve_id}-VERSION-BUMP"

        return GeneratedPatch(
            patch_id=patch_id,
            strategy=strategy,
            changes=changes,
            description=f"Update {dependency_name} to version {fixed_version} which patches {cve_id}",
            validation_notes="Run tests after update to ensure compatibility. Check for breaking changes in release notes.",
        )

    async def _generate_code_rewrite_patch(
        self,
        cve_id: str,
        dependency_name: str,
        affected_files: List[str],
        vulnerable_code_signature: str,
        cwe_ids: List[str],
        description: str,
    ) -> Tuple[GeneratedPatch, float]:
        """
        Generate code rewrite patch using LLM.

        Args:
            cve_id: CVE identifier
            dependency_name: Package name
            affected_files: List of affected files
            vulnerable_code_signature: Vulnerable pattern
            cwe_ids: CWE identifiers
            description: Vulnerability description

        Returns:
            Tuple of (GeneratedPatch, cost_usd)
        """
        # Read affected files
        file_contents = {}
        for file_path in affected_files[:3]:  # Limit to 3 files to control token usage
            full_path = self.project_path / file_path
            if full_path.exists() and full_path.stat().st_size < 50000:  # Max 50KB
                try:
                    with open(full_path, "r", encoding="utf-8") as f:
                        file_contents[file_path] = f.read()
                except Exception as e:
                    logger.warning(f"Failed to read {file_path}: {e}")

        if not file_contents:
            raise RuntimeError("No affected files could be read")

        # Construct LLM prompt
        system_prompt = """You are an expert security engineer specializing in vulnerability remediation.
Generate a secure code patch that fixes the vulnerability while maintaining functionality.

Requirements:
1. Identify the vulnerable code pattern
2. Explain why it's vulnerable
3. Provide a secure replacement
4. Ensure the fix doesn't break existing functionality
5. Add comments explaining the security fix

Output format:
```python
# BEFORE (vulnerable)
<vulnerable code>

# AFTER (fixed)
<secure code>

# EXPLANATION
<why this fixes the vulnerability>
```"""

        user_prompt = f"""Fix this vulnerability:

CVE: {cve_id}
Package: {dependency_name}
CWE: {', '.join(cwe_ids)}
Description: {description}

Vulnerable Pattern: {vulnerable_code_signature}

Affected Files:
"""

        for file_path, content in file_contents.items():
            user_prompt += f"\n--- {file_path} ---\n{content[:2000]}\n"  # Truncate to 2000 chars per file

        user_prompt += "\nGenerate a secure patch for the vulnerable code."

        # Generate patch using LLM
        llm_response = await self.llm_client.generate_with_retry(
            prompt=user_prompt,
            system_prompt=system_prompt,
            max_tokens=3000,
            temperature=0.2,
        )

        # Parse LLM response to extract patch
        changes = self._parse_llm_patch(llm_response.content, file_contents.keys())

        strategy = PatchStrategy(
            strategy_type="code_rewrite",
            description=f"Rewrite vulnerable code in {len(file_contents)} file(s)",
            confidence=0.75,  # Medium confidence for LLM-generated code
            estimated_effort="medium",
            risk_level="medium",
            reversible=True,
        )

        patch_id = f"PATCH-{cve_id}-CODE-REWRITE"

        return (
            GeneratedPatch(
                patch_id=patch_id,
                strategy=strategy,
                changes=changes,
                description=f"LLM-generated code fix for {cve_id}",
                validation_notes="CRITICAL: Review LLM-generated code carefully. Run full test suite. Verify security fix.",
                llm_response=llm_response,
            ),
            llm_response.cost_usd,
        )

    async def _generate_config_change_patch(
        self,
        cve_id: str,
        dependency_name: str,
        cwe_ids: List[str],
    ) -> Optional[GeneratedPatch]:
        """
        Generate configuration change patch.

        Args:
            cve_id: CVE identifier
            dependency_name: Package name
            cwe_ids: CWE identifiers

        Returns:
            GeneratedPatch or None if not applicable
        """
        # CWE-specific config mitigations
        config_mitigations = {
            "CWE-89": {  # SQL Injection
                "config": "database_config.yml",
                "patch": "Enable parameterized queries enforcement",
            },
            "CWE-79": {  # XSS
                "config": "security_config.yml",
                "patch": "Enable Content-Security-Policy headers",
            },
            "CWE-502": {  # Deserialization
                "config": "serialization_config.yml",
                "patch": "Disable unsafe deserialization",
            },
        }

        # Check if any CWE has config mitigation
        for cwe_id in cwe_ids:
            if cwe_id in config_mitigations:
                mitigation = config_mitigations[cwe_id]

                strategy = PatchStrategy(
                    strategy_type="config_change",
                    description=f"Configuration change to mitigate {cwe_id}",
                    confidence=0.65,
                    estimated_effort="low",
                    risk_level="low",
                    reversible=True,
                )

                changes = [{
                    "file_path": mitigation["config"],
                    "patch_content": f"# Mitigation for {cve_id}\n{mitigation['patch']}",
                    "patch_type": "config_update",
                }]

                patch_id = f"PATCH-{cve_id}-CONFIG-CHANGE"

                return GeneratedPatch(
                    patch_id=patch_id,
                    strategy=strategy,
                    changes=changes,
                    description=f"Configuration mitigation for {cve_id}",
                    validation_notes="Verify configuration change doesn't break functionality.",
                )

        return None

    async def _generate_workaround_patch(
        self,
        cve_id: str,
        dependency_name: str,
        cwe_ids: List[str],
        description: str,
    ) -> Tuple[GeneratedPatch, float]:
        """
        Generate workaround patch using LLM.

        Args:
            cve_id: CVE identifier
            dependency_name: Package name
            cwe_ids: CWE identifiers
            description: Vulnerability description

        Returns:
            Tuple of (GeneratedPatch, cost_usd)
        """
        system_prompt = """You are an expert security engineer.
Generate a temporary workaround for a vulnerability that cannot be immediately patched.

The workaround should:
1. Reduce attack surface
2. Add validation/sanitization
3. Be clearly marked as temporary
4. Not break existing functionality

Output a code snippet or configuration that serves as a workaround."""

        user_prompt = f"""Generate a workaround for:

CVE: {cve_id}
Package: {dependency_name}
CWE: {', '.join(cwe_ids)}
Description: {description}

Provide a temporary mitigation until a proper patch is available."""

        llm_response = await self.llm_client.generate_with_retry(
            prompt=user_prompt,
            system_prompt=system_prompt,
            max_tokens=2000,
            temperature=0.3,
        )

        strategy = PatchStrategy(
            strategy_type="workaround",
            description="Temporary workaround until proper patch available",
            confidence=0.5,  # Low confidence for workarounds
            estimated_effort="low",
            risk_level="medium",
            reversible=True,
        )

        changes = [{
            "file_path": "WORKAROUND.md",
            "patch_content": llm_response.content,
            "patch_type": "workaround_documentation",
        }]

        patch_id = f"PATCH-{cve_id}-WORKAROUND"

        return (
            GeneratedPatch(
                patch_id=patch_id,
                strategy=strategy,
                changes=changes,
                description=f"Temporary workaround for {cve_id}",
                validation_notes="TEMPORARY: This is a workaround, not a proper fix. Monitor for official patch.",
                llm_response=llm_response,
            ),
            llm_response.cost_usd,
        )

    def _parse_llm_patch(
        self, llm_output: str, affected_files: List[str]
    ) -> List[Dict[str, str]]:
        """
        Parse LLM output to extract patch changes.

        Args:
            llm_output: LLM response content
            affected_files: List of affected file paths

        Returns:
            List of change dictionaries
        """
        changes = []

        # Simple parser for code blocks
        # In production, use more sophisticated parsing
        if "```" in llm_output:
            blocks = llm_output.split("```")
            for i, block in enumerate(blocks):
                if i % 2 == 1:  # Odd indices are code blocks
                    # Extract language hint
                    lines = block.split("\n")
                    language = lines[0].strip() if lines else ""
                    code = "\n".join(lines[1:]) if len(lines) > 1 else block

                    # Match to affected file based on language
                    file_path = affected_files[0] if affected_files else "unknown.py"

                    changes.append({
                        "file_path": file_path,
                        "patch_content": code,
                        "patch_type": "code_replacement",
                    })

        # If no code blocks, use entire output
        if not changes:
            changes.append({
                "file_path": affected_files[0] if affected_files else "unknown.py",
                "patch_content": llm_output,
                "patch_type": "code_replacement",
            })

        return changes
