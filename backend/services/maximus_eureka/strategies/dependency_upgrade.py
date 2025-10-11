"""
Dependency Upgrade Strategy - MAXIMUS Eureka Remediation.

Generates patches for vulnerability fixes via dependency version upgrades.
Most deterministic and safest strategy - preferred when available.

Theoretical Foundation:
    Dependency upgrade is deterministic remediation: if package maintainers
    released a fix version, upgrading is safest path to resolution.
    
    Strategy logic:
    1. Check if APV has fix_available=True and fixed_versions listed
    2. Parse dependency manifest (pyproject.toml, requirements.txt, package.json)
    3. Generate unified diff upgrading affected package to fixed version
    4. Validate version constraints (don't break other dependencies)
    
    Advantages:
    - Deterministic (no LLM, no heuristics)
    - Maintainer-verified fix
    - High confidence score (0.95+)
    
    Limitations:
    - Only works if fix available
    - May have breaking changes (mitigated by semver)
    
Author: MAXIMUS Team
Date: 2025-01-10
Glory to YHWH - Provider of all solutions
"""

import logging
from pathlib import Path
from typing import Optional, List, Dict
import re

# Import APV from Oráculo
import sys

oraculo_path = Path(__file__).parent.parent.parent / "maximus_oraculo"
if str(oraculo_path) not in sys.path:
    sys.path.insert(0, str(oraculo_path))

from models.apv import APV, RemediationStrategy, AffectedPackage

# Import Eureka models
eureka_path = Path(__file__).parent.parent
if str(eureka_path) not in sys.path:
    sys.path.insert(0, str(eureka_path))

from eureka_models.confirmation.confirmation_result import ConfirmationResult
from eureka_models.patch import Patch
from strategies.base_strategy import BaseStrategy, StrategyFailedError

logger = logging.getLogger(__name__)


class DependencyUpgradeStrategy(BaseStrategy):
    """
    Generates dependency upgrade patches.
    
    Handles:
    - Python: pyproject.toml, requirements.txt, Pipfile
    - JavaScript: package.json, yarn.lock
    - Go: go.mod
    - Java: pom.xml, build.gradle
    - Rust: Cargo.toml
    
    Phase 3 scope: Python (pyproject.toml) implementation
    Future: Expand to other ecosystems
    
    Usage:
        >>> strategy = DependencyUpgradeStrategy(codebase_root=Path("/app"))
        >>> if await strategy.can_handle(apv, confirmation):
        ...     patch = await strategy.apply_strategy(apv, confirmation)
        ...     print(f"Upgraded {patch.files_modified}")
    """
    
    def __init__(self, codebase_root: Path):
        """
        Initialize dependency upgrade strategy.
        
        Args:
            codebase_root: Root directory of codebase
        """
        self.codebase_root = codebase_root
        logger.info(f"DependencyUpgradeStrategy initialized for {codebase_root}")
    
    @property
    def strategy_type(self) -> RemediationStrategy:
        """Return strategy type."""
        return RemediationStrategy.DEPENDENCY_UPGRADE
    
    async def can_handle(
        self, apv: APV, confirmation: ConfirmationResult
    ) -> bool:
        """
        Check if dependency upgrade is applicable.
        
        Requirements:
        1. At least one affected package has fixed_versions
        2. Dependency manifest exists in codebase
        
        Args:
            apv: APV to evaluate
            confirmation: Confirmation result (unused but required by interface)
            
        Returns:
            True if upgrade strategy applicable
        """
        # Check if any package has fix available
        has_fix = any(
            pkg.fixed_versions and len(pkg.fixed_versions) > 0
            for pkg in apv.affected_packages
        )
        
        if not has_fix:
            logger.debug(
                f"{apv.cve_id}: No fixed versions available, "
                "dependency upgrade not applicable"
            )
            return False
        
        # Check if dependency manifest exists
        manifest_files = self._find_manifest_files()
        if not manifest_files:
            logger.debug(
                f"{apv.cve_id}: No dependency manifests found, "
                "dependency upgrade not applicable"
            )
            return False
        
        logger.info(
            f"✅ {apv.cve_id}: Dependency upgrade applicable "
            f"(found {len(manifest_files)} manifests)"
        )
        return True
    
    async def apply_strategy(
        self, apv: APV, confirmation: ConfirmationResult
    ) -> Patch:
        """
        Generate dependency upgrade patch.
        
        Algorithm:
        1. Find dependency manifests
        2. For each affected package with fix:
           - Parse manifest
           - Find package declaration
           - Generate diff upgrading to fixed version
        3. Combine diffs into single patch
        
        Args:
            apv: APV with vulnerability details
            confirmation: Confirmation result
            
        Returns:
            Patch with unified diff
            
        Raises:
            StrategyFailedError: If patch generation fails
        """
        logger.info(f"🔧 Generating dependency upgrade patch for {apv.cve_id}")
        
        try:
            # Find manifests
            manifest_files = self._find_manifest_files()
            if not manifest_files:
                raise StrategyFailedError("No dependency manifests found")
            
            # Generate diffs for each affected package
            all_diffs: List[str] = []
            modified_files: List[str] = []
            
            for pkg in apv.affected_packages:
                if not pkg.fixed_versions or len(pkg.fixed_versions) == 0:
                    continue
                
                # Get first fixed version (highest priority)
                fixed_version = pkg.fixed_versions[0]
                
                # Find manifest containing this package
                for manifest_path in manifest_files:
                    diff = await self._generate_upgrade_diff(
                        manifest_path, pkg, fixed_version
                    )
                    if diff:
                        all_diffs.append(diff)
                        modified_files.append(str(manifest_path.relative_to(self.codebase_root)))
                        break
            
            if not all_diffs:
                raise StrategyFailedError(
                    f"Could not generate upgrade diff for any package in {apv.cve_id}"
                )
            
            # Combine diffs
            combined_diff = "\n".join(all_diffs)
            
            # Create patch
            patch = Patch(
                patch_id=self._generate_patch_id(apv.cve_id),
                cve_id=apv.cve_id,
                strategy_used=RemediationStrategy.DEPENDENCY_UPGRADE,
                diff_content=combined_diff,
                files_modified=modified_files,
                confidence_score=0.95,  # High confidence - deterministic upgrade
            )
            
            logger.info(
                f"✅ Generated dependency upgrade patch for {apv.cve_id}: "
                f"{len(modified_files)} files modified"
            )
            
            return patch
            
        except Exception as e:
            logger.error(
                f"❌ Failed to generate dependency upgrade patch for {apv.cve_id}: {e}",
                exc_info=True,
            )
            raise StrategyFailedError(f"Dependency upgrade failed: {e}") from e
    
    def _find_manifest_files(self) -> List[Path]:
        """
        Find dependency manifest files in codebase.
        
        Returns:
            List of manifest file paths
        """
        manifest_names = [
            "pyproject.toml",
            "requirements.txt",
            "Pipfile",
            "package.json",
            "go.mod",
            "Cargo.toml",
            "pom.xml",
            "build.gradle",
        ]
        
        manifests: List[Path] = []
        
        for name in manifest_names:
            # Check root
            root_manifest = self.codebase_root / name
            if root_manifest.exists():
                manifests.append(root_manifest)
            
            # Check subdirectories (one level deep)
            for manifest in self.codebase_root.glob(f"*/{name}"):
                if manifest.is_file():
                    manifests.append(manifest)
        
        return manifests
    
    async def _generate_upgrade_diff(
        self, manifest_path: Path, package: AffectedPackage, fixed_version: str
    ) -> Optional[str]:
        """
        Generate unified diff for dependency upgrade.
        
        Phase 3 scope: pyproject.toml only
        Future: Support other manifest types
        
        Args:
            manifest_path: Path to manifest file
            package: Affected package
            fixed_version: Version to upgrade to
            
        Returns:
            Unified diff string or None if package not found
        """
        if manifest_path.name != "pyproject.toml":
            logger.debug(f"Skipping {manifest_path.name} - not yet supported")
            return None
        
        # Read manifest
        content = manifest_path.read_text()
        lines = content.splitlines(keepends=True)
        
        # Find package declaration
        # Pattern: package-name = "^X.Y.Z" or package-name = ">=X.Y.Z,<A.B.C"
        package_pattern = re.compile(
            rf'^(\s*)({re.escape(package.name)})\s*=\s*"([^"]+)"',
            re.MULTILINE,
        )
        
        match = package_pattern.search(content)
        if not match:
            logger.debug(f"Package {package.name} not found in {manifest_path}")
            return None
        
        # Generate diff
        line_num = content[:match.start()].count('\n') + 1
        indent, pkg_name, old_version_spec = match.groups()
        
        # Construct new version spec (keep operator if present)
        if old_version_spec.startswith('^'):
            new_version_spec = f"^{fixed_version}"
        elif old_version_spec.startswith('>='):
            # Keep lower bound semantics
            new_version_spec = f">={fixed_version}"
        else:
            # Exact version or other format
            new_version_spec = fixed_version
        
        old_line = f'{indent}{pkg_name} = "{old_version_spec}"\n'
        new_line = f'{indent}{pkg_name} = "{new_version_spec}"\n'
        
        # Generate unified diff format
        rel_path = manifest_path.relative_to(self.codebase_root)
        diff = (
            f"--- a/{rel_path}\n"
            f"+++ b/{rel_path}\n"
            f"@@ -{line_num},1 +{line_num},1 @@\n"
            f"-{old_line}"
            f"+{new_line}"
        )
        
        logger.debug(
            f"Generated diff for {package.name}: "
            f"{old_version_spec} → {new_version_spec}"
        )
        
        return diff
