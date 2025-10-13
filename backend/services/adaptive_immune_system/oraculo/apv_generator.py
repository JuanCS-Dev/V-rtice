"""
APV Generator - Generates Ameaças Potenciais Verificadas (Verified Potential Threats).

Matches CVEs from threat feeds to actual dependencies in the codebase,
generating APVs with vulnerable code signatures for precise detection.
"""

import logging
import re
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple
from uuid import UUID, uuid4

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from ..database import DatabaseClient
from ..database.models import APV, Dependency, Threat
from ..models.apv import APVCreate, APVDispatchMessage
from packaging import version as pkg_version

logger = logging.getLogger(__name__)


class VulnerableCodeSignature:
    """
    Generates code signatures for detecting vulnerable code patterns.

    Supports multiple signature types:
    - regex: Regular expression patterns
    - ast-grep: AST-based pattern matching
    - semgrep: Semgrep YAML rules
    """

    @staticmethod
    def generate_python_signature(
        cve_id: str,
        package_name: str,
        vulnerable_version: str,
        cwe_ids: List[str],
    ) -> Optional[Tuple[str, str]]:
        """
        Generate Python code signature based on CVE and CWE.

        Args:
            cve_id: CVE identifier
            package_name: Vulnerable package name
            vulnerable_version: Vulnerable version
            cwe_ids: List of CWE IDs

        Returns:
            Tuple of (signature_pattern, signature_type) or None
        """
        # Map common CWEs to code patterns
        if "CWE-89" in cwe_ids:  # SQL Injection
            return (
                rf"import\s+{re.escape(package_name)}.*?\.execute\s*\(\s*['\"].*?%s.*?['\"]",
                "regex",
            )

        if "CWE-79" in cwe_ids:  # XSS
            return (
                rf"from\s+{re.escape(package_name)}\s+import.*?render.*?\(\s*request\.",
                "regex",
            )

        if "CWE-502" in cwe_ids:  # Deserialization
            return (
                rf"import\s+(pickle|yaml|marshal).*?\.load\s*\(",
                "regex",
            )

        if "CWE-22" in cwe_ids:  # Path Traversal
            return (
                rf"open\s*\(\s*.*?\+.*?\)",
                "regex",
            )

        # Default: detect import statements
        return (
            rf"(?:from\s+{re.escape(package_name)}|import\s+{re.escape(package_name)})",
            "regex",
        )

    @staticmethod
    def generate_javascript_signature(
        cve_id: str,
        package_name: str,
        vulnerable_version: str,
        cwe_ids: List[str],
    ) -> Optional[Tuple[str, str]]:
        """
        Generate JavaScript code signature.

        Args:
            cve_id: CVE identifier
            package_name: Vulnerable package name
            vulnerable_version: Vulnerable version
            cwe_ids: List of CWE IDs

        Returns:
            Tuple of (signature_pattern, signature_type) or None
        """
        # Map common CWEs to code patterns
        if "CWE-79" in cwe_ids:  # XSS
            return (
                rf"require\s*\(['\"]{ re.escape(package_name)}['\"]\).*?\.html\s*\(",
                "regex",
            )

        if "CWE-1321" in cwe_ids:  # Prototype Pollution
            return (
                rf"require\s*\(['\"]{ re.escape(package_name)}['\"]\).*?\.merge\s*\(",
                "regex",
            )

        # Default: detect require/import statements
        return (
            rf"(?:require\s*\(['\"]{ re.escape(package_name)}['\"]\)|import.*?from\s+['\"]{ re.escape(package_name)}['\"])",
            "regex",
        )


class APVGenerator:
    """
    Generates APVs by matching CVEs to dependencies.

    Features:
    - Version range matching (semver)
    - Vulnerable code signature generation
    - Ecosystem-specific logic
    - Deduplication by CVE + dependency
    """

    def __init__(self, db_client: DatabaseClient):
        """
        Initialize APV generator.

        Args:
            db_client: Database client instance
        """
        self.db_client = db_client
        self.signature_generator = VulnerableCodeSignature()

        logger.info("APVGenerator initialized")

    def generate_apvs(
        self,
        project: str,
        limit: Optional[int] = None,
    ) -> List[APV]:
        """
        Generate APVs for a project by matching threats to dependencies.

        Args:
            project: Project identifier
            limit: Maximum number of APVs to generate (for testing)

        Returns:
            List of generated APV instances
        """
        logger.info(f"🔍 Generating APVs for project: {project}")

        with self.db_client.get_session() as session:
            # Get all dependencies for project
            dependencies = (
                session.query(Dependency)
                .filter(Dependency.project == project)
                .all()
            )

            if not dependencies:
                logger.warning(f"No dependencies found for project: {project}")
                return []

            logger.info(f"Found {len(dependencies)} dependencies to analyze")

            # Get all threats
            threats = session.query(Threat).all()

            if not threats:
                logger.warning("No threats found in database")
                return []

            logger.info(f"Found {len(threats)} threats to match against")

            # Match threats to dependencies
            apvs = []
            matches = 0

            for dep in dependencies:
                for threat in threats:
                    # Check if threat affects this dependency
                    if self._is_vulnerable(dep, threat):
                        # Check if APV already exists
                        existing = (
                            session.query(APV)
                            .filter(
                                APV.project == project,
                                APV.cve_id == threat.cve_id,
                                APV.dependency_name == dep.name,
                                APV.dependency_version == dep.version,
                            )
                            .first()
                        )

                        if existing:
                            logger.debug(
                                f"APV already exists: {threat.cve_id} -> {dep.name}@{dep.version}"
                            )
                            continue

                        # Generate APV
                        apv = self._create_apv(session, project, dep, threat)
                        apvs.append(apv)
                        matches += 1

                        logger.info(
                            f"✅ APV created: {apv.apv_code} - "
                            f"{threat.cve_id} affects {dep.name}@{dep.version}"
                        )

                        if limit and matches >= limit:
                            logger.info(f"Reached limit of {limit} APVs")
                            break

                if limit and matches >= limit:
                    break

            logger.info(
                f"✅ APV generation complete: {len(apvs)} APVs created, "
                f"{len(dependencies)} dependencies analyzed, "
                f"{len(threats)} threats evaluated"
            )

            return apvs

    def _is_vulnerable(self, dep: Dependency, threat: Threat) -> bool:
        """
        Check if dependency is vulnerable to threat.

        Args:
            dep: Dependency instance
            threat: Threat instance

        Returns:
            True if dependency is vulnerable
        """
        # Map ecosystem names
        ecosystem_map = {
            "pypi": ["pypi", "python", "pip"],
            "npm": ["npm", "node", "javascript"],
            "go": ["go", "golang"],
            "cargo": ["cargo", "rust", "crates.io"],
            "maven": ["maven", "java"],
            "composer": ["composer", "php"],
            "rubygems": ["rubygems", "ruby"],
            "nuget": ["nuget", "dotnet", "csharp"],
        }

        # Check ecosystem match
        threat_ecosystems = threat.ecosystems or []
        dep_ecosystem_variants = ecosystem_map.get(dep.ecosystem.lower(), [dep.ecosystem.lower()])

        ecosystem_match = any(
            threat_eco.lower() in dep_ecosystem_variants
            for threat_eco in threat_ecosystems
        )

        if not ecosystem_match and threat_ecosystems:
            return False

        # Check if threat has affected_packages data
        if threat.affected_packages:
            affected = threat.affected_packages

            # Check package name match
            if isinstance(affected, dict):
                pkg_name = affected.get("name", "").lower()
                if pkg_name and pkg_name != dep.name.lower():
                    return False

                # Check version range
                vulnerable_range = affected.get("vulnerable_range", "")
                fixed_version = affected.get("fixed_version", "")

                if vulnerable_range:
                    return self._is_version_vulnerable(
                        dep.version, vulnerable_range, fixed_version
                    )

        # If no specific package info, rely on ecosystem match and CVE description
        # (This is a conservative approach - manual review recommended)
        return ecosystem_match

    def _is_version_vulnerable(
        self,
        installed_version: str,
        vulnerable_range: str,
        fixed_version: Optional[str],
    ) -> bool:
        """
        Check if installed version is within vulnerable range.

        Args:
            installed_version: Installed package version
            vulnerable_range: Vulnerable version range (e.g., ">= 1.0.0, < 2.0.0")
            fixed_version: First patched version

        Returns:
            True if version is vulnerable
        """
        try:
            installed = pkg_version.parse(installed_version)

            # Check if version is less than fixed version
            if fixed_version:
                fixed = pkg_version.parse(fixed_version)
                if installed < fixed:
                    return True

            # Parse vulnerable range
            # Common formats: ">= 1.0.0, < 2.0.0", ">= 1.0.0", "< 2.0.0", "= 1.0.0"
            if not vulnerable_range:
                return False

            # Split on comma for multiple constraints
            constraints = [c.strip() for c in vulnerable_range.split(",")]

            for constraint in constraints:
                # Parse constraint
                match = re.match(r"([<>=!]+)\s*(.+)", constraint)
                if not match:
                    continue

                operator = match.group(1).strip()
                version_str = match.group(2).strip()
                constraint_version = pkg_version.parse(version_str)

                # Apply constraint
                if operator == ">=":
                    if not (installed >= constraint_version):
                        return False
                elif operator == "<=":
                    if not (installed <= constraint_version):
                        return False
                elif operator == ">":
                    if not (installed > constraint_version):
                        return False
                elif operator == "<":
                    if not (installed < constraint_version):
                        return False
                elif operator == "==":
                    if not (installed == constraint_version):
                        return False
                elif operator == "!=":
                    if not (installed != constraint_version):
                        return False

            return True

        except Exception as e:
            logger.warning(f"Failed to parse version: {e}")
            return False

    def _create_apv(
        self,
        session: Session,
        project: str,
        dep: Dependency,
        threat: Threat,
    ) -> APV:
        """
        Create APV from matched dependency and threat.

        Args:
            session: Database session
            project: Project identifier
            dep: Dependency instance
            threat: Threat instance

        Returns:
            APV instance
        """
        # Generate APV code
        apv_code = self._generate_apv_code(session)

        # Generate vulnerable code signature
        signature, signature_type = self._generate_signature(dep, threat)

        # Calculate priority (1-10, higher = more critical)
        priority = self._calculate_priority(threat, dep)

        # Determine affected files (placeholder - would be populated by code scanner)
        affected_files = []

        # Create APV
        apv = APV(
            apv_code=apv_code,
            project=project,
            cve_id=threat.cve_id,
            threat_id=threat.id,
            dependency_name=dep.name,
            dependency_version=dep.version,
            dependency_ecosystem=dep.ecosystem,
            dependency_id=dep.id,
            priority=priority,
            status="pending_triage",
            vulnerable_code_signature=signature,
            vulnerable_code_type=signature_type,
            affected_files=affected_files,
            cvss_score=threat.cvss_score,
            severity=threat.severity,
            description=threat.description,
            cwe_ids=threat.cwe_ids or [],
            references=threat.references or [],
        )

        session.add(apv)
        session.commit()
        session.refresh(apv)

        return apv

    def _generate_apv_code(self, session: Session) -> str:
        """
        Generate unique APV code.

        Format: APV-YYYYMMDD-NNN

        Args:
            session: Database session

        Returns:
            APV code string
        """
        date_str = datetime.utcnow().strftime("%Y%m%d")

        # Get count of APVs created today
        count = (
            session.query(APV)
            .filter(APV.apv_code.like(f"APV-{date_str}-%"))
            .count()
        )

        sequence = count + 1

        return f"APV-{date_str}-{sequence:03d}"

    def _generate_signature(
        self,
        dep: Dependency,
        threat: Threat,
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Generate vulnerable code signature.

        Args:
            dep: Dependency instance
            threat: Threat instance

        Returns:
            Tuple of (signature_pattern, signature_type)
        """
        cwe_ids = threat.cwe_ids or []

        if dep.ecosystem == "pypi":
            return self.signature_generator.generate_python_signature(
                threat.cve_id,
                dep.name,
                dep.version,
                cwe_ids,
            ) or (None, None)

        elif dep.ecosystem == "npm":
            return self.signature_generator.generate_javascript_signature(
                threat.cve_id,
                dep.name,
                dep.version,
                cwe_ids,
            ) or (None, None)

        # Add more ecosystems as needed

        return None, None

    def _calculate_priority(self, threat: Threat, dep: Dependency) -> int:
        """
        Calculate APV priority (1-10).

        Factors:
        - CVSS score (40%)
        - Severity (30%)
        - Direct vs transitive dependency (20%)
        - Threat recency (10%)

        Args:
            threat: Threat instance
            dep: Dependency instance

        Returns:
            Priority score (1-10)
        """
        score = 0.0

        # Factor 1: CVSS score (0-10) -> 40% weight
        if threat.cvss_score:
            score += (threat.cvss_score / 10.0) * 4.0

        # Factor 2: Severity (30% weight)
        severity_weights = {
            "critical": 3.0,
            "high": 2.5,
            "medium": 1.5,
            "low": 0.5,
        }
        if threat.severity:
            score += severity_weights.get(threat.severity.lower(), 1.0)

        # Factor 3: Direct dependency (20% weight)
        if dep.is_direct:
            score += 2.0
        else:
            score += 0.5

        # Factor 4: Threat recency (10% weight)
        if threat.published_date:
            days_old = (datetime.utcnow() - threat.published_date).days
            if days_old < 30:
                score += 1.0
            elif days_old < 90:
                score += 0.7
            elif days_old < 365:
                score += 0.4

        # Normalize to 1-10 range
        priority = int(min(max(score, 1), 10))

        return priority

    def create_dispatch_message(self, apv: APV) -> APVDispatchMessage:
        """
        Create RabbitMQ dispatch message for APV.

        Args:
            apv: APV instance

        Returns:
            APVDispatchMessage for RabbitMQ
        """
        return APVDispatchMessage(
            apv_id=apv.id,
            apv_code=apv.apv_code,
            priority=apv.priority,
            cve_id=apv.cve_id,
            dependency_name=apv.dependency_name,
            dependency_version=apv.dependency_version,
            dependency_ecosystem=apv.dependency_ecosystem,
            vulnerable_code_signature=apv.vulnerable_code_signature,
            vulnerable_code_type=apv.vulnerable_code_type,
            affected_files=apv.affected_files or [],
            dispatched_at=datetime.utcnow(),
        )
