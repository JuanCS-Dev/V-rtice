"""Unit tests for APV (Actionable Prioritized Vulnerability) model.

Tests cover:
- Model validation
- Field validators
- Computed properties
- Priority calculation logic
- Strategy selection logic
- Complexity calculation
- Edge cases and error handling

Author: MAXIMUS Team
Date: 2025-10-11
Compliance: TDD | Coverage ≥90% | NO MOCK for models
"""

import pytest
from datetime import datetime
from pydantic import ValidationError

import sys
from pathlib import Path

# Add parent directories to path for imports
service_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(service_root))

from services.maximus_oraculo.models.apv import (
    APV,
    PriorityLevel,
    RemediationStrategy,
    RemediationComplexity,
    CVSSScore,
    ASTGrepPattern,
    AffectedPackage,
)


class TestCVSSScore:
    """Test CVSS score model."""
    
    def test_valid_cvss_score(self):
        """Test valid CVSS score creation."""
        cvss = CVSSScore(
            version="3.1",
            base_score=9.8,
            severity="CRITICAL",
            vector_string="CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H"
        )
        
        assert cvss.version == "3.1"
        assert cvss.base_score == 9.8
        assert cvss.severity == "CRITICAL"
        assert "CVSS:3.1" in cvss.vector_string
    
    def test_cvss_score_validation(self):
        """Test CVSS score must be between 0 and 10."""
        with pytest.raises(ValidationError) as exc_info:
            CVSSScore(
                version="3.1",
                base_score=11.0,  # Invalid: > 10
                severity="CRITICAL",
                vector_string="CVSS:3.1/AV:N"
            )
        
        assert "base_score" in str(exc_info.value)
    
    def test_severity_normalization(self):
        """Test severity is normalized to uppercase."""
        cvss = CVSSScore(
            version="3.1",
            base_score=5.0,
            severity="medium",  # lowercase
            vector_string="CVSS:3.1/AV:N"
        )
        
        assert cvss.severity == "MEDIUM"
    
    def test_invalid_severity(self):
        """Test invalid severity raises error."""
        with pytest.raises(ValidationError) as exc_info:
            CVSSScore(
                version="3.1",
                base_score=5.0,
                severity="INVALID",
                vector_string="CVSS:3.1/AV:N"
            )
        
        assert "severity" in str(exc_info.value).lower()


class TestASTGrepPattern:
    """Test ast-grep pattern model."""
    
    def test_valid_pattern(self):
        """Test valid ast-grep pattern."""
        pattern = ASTGrepPattern(
            language="python",
            pattern="eval($ARG)",
            severity="critical",
            description="Detects eval() usage"
        )
        
        assert pattern.language == "python"
        assert pattern.pattern == "eval($ARG)"
        assert pattern.severity == "critical"
    
    def test_language_normalization(self):
        """Test language is normalized to lowercase."""
        pattern = ASTGrepPattern(
            language="PYTHON",
            pattern="eval($ARG)",
            severity="critical"
        )
        
        assert pattern.language == "python"
    
    def test_unsupported_language(self):
        """Test unsupported language raises error."""
        with pytest.raises(ValidationError) as exc_info:
            ASTGrepPattern(
                language="cobol",  # Not supported
                pattern="some pattern",
                severity="low"
            )
        
        assert "language" in str(exc_info.value).lower()


class TestAffectedPackage:
    """Test affected package model."""
    
    def test_valid_package(self):
        """Test valid affected package."""
        pkg = AffectedPackage(
            ecosystem="PyPI",
            name="django",
            affected_versions=[">=3.0,<4.2.8"],
            fixed_versions=["4.2.8"]
        )
        
        assert pkg.ecosystem == "PyPI"
        assert pkg.name == "django"
        assert len(pkg.affected_versions) == 1
        assert len(pkg.fixed_versions) == 1
    
    def test_has_fix_property(self):
        """Test has_fix computed property."""
        # Package with fix
        pkg_with_fix = AffectedPackage(
            ecosystem="PyPI",
            name="requests",
            affected_versions=["<2.28.0"],
            fixed_versions=["2.28.0"]
        )
        assert pkg_with_fix.has_fix is True
        
        # Package without fix (zero-day)
        pkg_no_fix = AffectedPackage(
            ecosystem="PyPI",
            name="vulnerable-lib",
            affected_versions=["*"],
            fixed_versions=[]
        )
        assert pkg_no_fix.has_fix is False
    
    def test_invalid_ecosystem(self):
        """Test invalid ecosystem raises error."""
        with pytest.raises(ValidationError) as exc_info:
            AffectedPackage(
                ecosystem="InvalidEcosystem",
                name="package",
                affected_versions=["*"]
            )
        
        assert "ecosystem" in str(exc_info.value).lower()


class TestAPVModel:
    """Test APV core model."""
    
    @pytest.fixture
    def minimal_apv_data(self) -> dict:
        """Minimal valid APV data."""
        return {
            "cve_id": "CVE-2024-12345",
            "published": datetime(2024, 10, 1),
            "modified": datetime(2024, 10, 5),
            "summary": "SQL Injection vulnerability in Django",
            "details": "Django versions < 4.2.8 vulnerable to SQL injection in raw() method",
            "priority": "critical",
            "affected_packages": [{
                "ecosystem": "PyPI",
                "name": "django",
                "affected_versions": [">=3.0,<4.2.8"],
                "fixed_versions": ["4.2.8"]
            }],
            "recommended_strategy": "dependency_upgrade",
            "remediation_complexity": "low",
            "source_feed": "OSV.dev"
        }
    
    @pytest.fixture
    def full_apv_data(self, minimal_apv_data) -> dict:
        """Full APV data with all optional fields."""
        data = minimal_apv_data.copy()
        data.update({
            "aliases": ["GHSA-xxxx-yyyy-zzzz"],
            "cvss": {
                "version": "3.1",
                "base_score": 9.8,
                "severity": "CRITICAL",
                "vector_string": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H"
            },
            "ast_grep_patterns": [{
                "language": "python",
                "pattern": "Model.objects.raw($QUERY)",
                "severity": "critical"
            }],
            "maximus_context": {
                "affected_services": ["maximus_core_service", "maximus_api_gateway"],
                "exploit_available": False
            }
        })
        return data
    
    def test_create_minimal_apv(self, minimal_apv_data):
        """Test creating APV with minimal required fields."""
        apv = APV(**minimal_apv_data)
        
        assert apv.cve_id == "CVE-2024-12345"
        assert apv.priority == PriorityLevel.CRITICAL
        assert len(apv.affected_packages) == 1
        assert apv.source_feed == "OSV.dev"
    
    def test_create_full_apv(self, full_apv_data):
        """Test creating APV with all fields."""
        apv = APV(**full_apv_data)
        
        assert apv.cve_id == "CVE-2024-12345"
        assert len(apv.aliases) == 1
        assert apv.cvss is not None
        assert apv.cvss.base_score == 9.8
        assert len(apv.ast_grep_patterns) == 1
        assert len(apv.affected_services) == 2
    
    def test_processed_at_auto_generated(self, minimal_apv_data):
        """Test processed_at is auto-generated."""
        apv = APV(**minimal_apv_data)
        
        assert apv.processed_at is not None
        assert isinstance(apv.processed_at, datetime)
        # Should be recent (within last minute)
        time_diff = (datetime.utcnow() - apv.processed_at).total_seconds()
        assert time_diff < 60
    
    def test_missing_required_field(self, minimal_apv_data):
        """Test validation error when required field is missing."""
        del minimal_apv_data['cve_id']
        
        with pytest.raises(ValidationError) as exc_info:
            APV(**minimal_apv_data)
        
        assert "cve_id" in str(exc_info.value).lower()
    
    def test_invalid_priority(self, minimal_apv_data):
        """Test invalid priority value raises error."""
        minimal_apv_data['priority'] = "invalid_priority"
        
        with pytest.raises(ValidationError) as exc_info:
            APV(**minimal_apv_data)
        
        assert "priority" in str(exc_info.value).lower()


class TestAPVPriorityCalculation:
    """Test APV automatic priority calculation."""
    
    def test_priority_critical_high_cvss_with_exploit(self):
        """Test CRITICAL priority: CVSS >= 9.0 + exploit available."""
        apv = APV(
            cve_id="CVE-2024-99999",
            published=datetime.now(),
            modified=datetime.now(),
            summary="Test vulnerability",
            details="Test details with sufficient length",
            cvss=CVSSScore(
                version="3.1",
                base_score=9.5,
                severity="CRITICAL",
                vector_string="CVSS:3.1/AV:N"
            ),
            affected_packages=[{
                "ecosystem": "PyPI",
                "name": "test",
                "affected_versions": ["*"]
            }],
            maximus_context={
                "exploit_available": True
            },
            recommended_strategy="dependency_upgrade",
            remediation_complexity="low",
            source_feed="test"
        )
        
        assert apv.priority == PriorityLevel.CRITICAL
    
    def test_priority_high_medium_cvss_many_services(self):
        """Test HIGH priority: CVSS >= 7.0 + affected_services > 3."""
        apv = APV(
            cve_id="CVE-2024-99998",
            published=datetime.now(),
            modified=datetime.now(),
            summary="Test vulnerability",
            details="Test details with sufficient length",
            cvss=CVSSScore(
                version="3.1",
                base_score=7.5,
                severity="HIGH",
                vector_string="CVSS:3.1/AV:N"
            ),
            affected_packages=[{
                "ecosystem": "PyPI",
                "name": "test",
                "affected_versions": ["*"]
            }],
            maximus_context={
                "affected_services": ["svc1", "svc2", "svc3", "svc4"]
            },
            recommended_strategy="dependency_upgrade",
            remediation_complexity="low",
            source_feed="test"
        )
        
        assert apv.priority == PriorityLevel.HIGH
    
    def test_priority_medium_moderate_cvss(self):
        """Test MEDIUM priority: CVSS >= 4.0."""
        apv = APV(
            cve_id="CVE-2024-99997",
            published=datetime.now(),
            modified=datetime.now(),
            summary="Test vulnerability",
            details="Test details with sufficient length",
            cvss=CVSSScore(
                version="3.1",
                base_score=5.0,
                severity="MEDIUM",
                vector_string="CVSS:3.1/AV:N"
            ),
            affected_packages=[{
                "ecosystem": "PyPI",
                "name": "test",
                "affected_versions": ["*"]
            }],
            recommended_strategy="dependency_upgrade",
            remediation_complexity="low",
            source_feed="test"
        )
        
        assert apv.priority == PriorityLevel.MEDIUM
    
    def test_priority_low_low_cvss(self):
        """Test LOW priority: CVSS < 4.0."""
        apv = APV(
            cve_id="CVE-2024-99996",
            published=datetime.now(),
            modified=datetime.now(),
            summary="Test vulnerability",
            details="Test details with sufficient length",
            cvss=CVSSScore(
                version="3.1",
                base_score=2.0,
                severity="LOW",
                vector_string="CVSS:3.1/AV:L"
            ),
            affected_packages=[{
                "ecosystem": "PyPI",
                "name": "test",
                "affected_versions": ["*"]
            }],
            recommended_strategy="dependency_upgrade",
            remediation_complexity="low",
            source_feed="test"
        )
        
        assert apv.priority == PriorityLevel.LOW


class TestAPVStrategyCalculation:
    """Test APV automatic strategy selection."""
    
    def test_strategy_dependency_upgrade_has_fix(self):
        """Test DEPENDENCY_UPGRADE: fixed version available."""
        apv = APV(
            cve_id="CVE-2024-10001",
            published=datetime.now(),
            modified=datetime.now(),
            summary="Test vulnerability",
            details="Test details with sufficient length",
            priority="high",
            affected_packages=[{
                "ecosystem": "PyPI",
                "name": "requests",
                "affected_versions": ["<2.28.0"],
                "fixed_versions": ["2.28.0"]
            }],
            remediation_complexity="low",
            source_feed="test"
        )
        
        assert apv.recommended_strategy == RemediationStrategy.DEPENDENCY_UPGRADE
    
    def test_strategy_code_patch_no_fix_has_pattern(self):
        """Test CODE_PATCH: no fix but has ast-grep pattern."""
        apv = APV(
            cve_id="CVE-2024-10002",
            published=datetime.now(),
            modified=datetime.now(),
            summary="Test vulnerability",
            details="Test details with sufficient length",
            priority="high",
            affected_packages=[{
                "ecosystem": "PyPI",
                "name": "custom-lib",
                "affected_versions": ["*"],
                "fixed_versions": []
            }],
            ast_grep_patterns=[{
                "language": "python",
                "pattern": "eval($ARG)",
                "severity": "high"
            }],
            remediation_complexity="medium",
            source_feed="test"
        )
        
        assert apv.recommended_strategy == RemediationStrategy.CODE_PATCH
    
    def test_strategy_waf_zero_day(self):
        """Test COAGULATION_WAF: zero-day without pattern."""
        apv = APV(
            cve_id="CVE-2024-10003",
            published=datetime.now(),
            modified=datetime.now(),
            summary="Test vulnerability",
            details="Test details with sufficient length",
            priority="critical",
            affected_packages=[{
                "ecosystem": "PyPI",
                "name": "zero-day-lib",
                "affected_versions": ["*"],
                "fixed_versions": []
            }],
            remediation_complexity="high",
            source_feed="test"
        )
        
        assert apv.recommended_strategy == RemediationStrategy.COAGULATION_WAF
    
    def test_strategy_manual_review_critical_complexity(self):
        """Test MANUAL_REVIEW: critical complexity."""
        apv = APV(
            cve_id="CVE-2024-10004",
            published=datetime.now(),
            modified=datetime.now(),
            summary="Test vulnerability",
            details="Test details with sufficient length",
            priority="high",
            affected_packages=[{
                "ecosystem": "PyPI",
                "name": "complex-lib",
                "affected_versions": ["*"]
            }],
            remediation_complexity="critical",
            source_feed="test"
        )
        
        assert apv.recommended_strategy == RemediationStrategy.MANUAL_REVIEW


class TestAPVComplexityCalculation:
    """Test APV automatic complexity calculation."""
    
    def test_complexity_low_single_package(self):
        """Test LOW complexity: single package, simple upgrade."""
        apv = APV(
            cve_id="CVE-2024-11001",
            published=datetime.now(),
            modified=datetime.now(),
            summary="Test vulnerability",
            details="Test details with sufficient length",
            priority="medium",
            affected_packages=[{
                "ecosystem": "PyPI",
                "name": "simple-lib",
                "affected_versions": ["<1.0.0"],
                "fixed_versions": ["1.0.0"]
            }],
            recommended_strategy="dependency_upgrade",
            source_feed="test"
        )
        
        assert apv.remediation_complexity == RemediationComplexity.LOW
    
    def test_complexity_medium_multiple_packages(self):
        """Test MEDIUM complexity: 2-3 packages affected with fixes."""
        apv = APV(
            cve_id="CVE-2024-11002",
            published=datetime.now(),
            modified=datetime.now(),
            summary="Test vulnerability",
            details="Test details with sufficient length",
            priority="medium",
            affected_packages=[
                {
                    "ecosystem": "PyPI",
                    "name": "lib1",
                    "affected_versions": ["*"],
                    "fixed_versions": ["1.0.0"]  # Has fix
                },
                {
                    "ecosystem": "PyPI",
                    "name": "lib2",
                    "affected_versions": ["*"],
                    "fixed_versions": ["2.0.0"]  # Has fix
                }
            ],
            recommended_strategy="dependency_upgrade",
            source_feed="test"
        )
        
        assert apv.remediation_complexity == RemediationComplexity.MEDIUM
    
    def test_complexity_high_many_packages(self):
        """Test HIGH complexity: > 3 packages affected."""
        apv = APV(
            cve_id="CVE-2024-11003",
            published=datetime.now(),
            modified=datetime.now(),
            summary="Test vulnerability",
            details="Test details with sufficient length",
            priority="high",
            affected_packages=[
                {"ecosystem": "PyPI", "name": f"lib{i}", "affected_versions": ["*"]}
                for i in range(4)
            ],
            recommended_strategy="dependency_upgrade",
            source_feed="test"
        )
        
        assert apv.remediation_complexity == RemediationComplexity.HIGH


class TestAPVComputedProperties:
    """Test APV computed properties."""
    
    def test_is_critical_property(self):
        """Test is_critical computed property."""
        critical_apv = APV(
            cve_id="CVE-2024-12001",
            published=datetime.now(),
            modified=datetime.now(),
            summary="Test vulnerability critical",
            details="Test details with sufficient length for validation",
            priority="critical",
            affected_packages=[{"ecosystem": "PyPI", "name": "test", "affected_versions": ["*"]}],
            recommended_strategy="dependency_upgrade",
            remediation_complexity="low",
            source_feed="test"
        )
        
        assert critical_apv.is_critical is True
        
        low_apv = APV(
            cve_id="CVE-2024-12002",
            published=datetime.now(),
            modified=datetime.now(),
            summary="Test vulnerability low priority",
            details="Test details with sufficient length for validation",
            priority="low",
            affected_packages=[{"ecosystem": "PyPI", "name": "test", "affected_versions": ["*"]}],
            recommended_strategy="dependency_upgrade",
            remediation_complexity="low",
            source_feed="test"
        )
        
        assert low_apv.is_critical is False
    
    def test_requires_immediate_action_property(self):
        """Test requires_immediate_action property."""
        high_apv = APV(
            cve_id="CVE-2024-12003",
            published=datetime.now(),
            modified=datetime.now(),
            summary="Test vulnerability high priority",
            details="Test details with sufficient length for validation",
            priority="high",
            affected_packages=[{"ecosystem": "PyPI", "name": "test", "affected_versions": ["*"]}],
            recommended_strategy="dependency_upgrade",
            remediation_complexity="low",
            source_feed="test"
        )
        
        assert high_apv.requires_immediate_action is True
        
        medium_apv = APV(
            cve_id="CVE-2024-12004",
            published=datetime.now(),
            modified=datetime.now(),
            summary="Test vulnerability medium priority",
            details="Test details with sufficient length for validation",
            priority="medium",
            affected_packages=[{"ecosystem": "PyPI", "name": "test", "affected_versions": ["*"]}],
            recommended_strategy="dependency_upgrade",
            remediation_complexity="low",
            source_feed="test"
        )
        
        assert medium_apv.requires_immediate_action is False
    
    def test_has_automated_fix_property(self):
        """Test has_automated_fix property."""
        upgrade_apv = APV(
            cve_id="CVE-2024-12005",
            published=datetime.now(),
            modified=datetime.now(),
            summary="Test vulnerability with automated fix",
            details="Test details with sufficient length for validation",
            priority="high",
            affected_packages=[{"ecosystem": "PyPI", "name": "test", "affected_versions": ["*"], "fixed_versions": ["1.0.0"]}],
            recommended_strategy="dependency_upgrade",
            remediation_complexity="low",
            source_feed="test"
        )
        
        assert upgrade_apv.has_automated_fix is True
        
        manual_apv = APV(
            cve_id="CVE-2024-12006",
            published=datetime.now(),
            modified=datetime.now(),
            summary="Test vulnerability needs manual review",
            details="Test details with sufficient length for validation",
            priority="high",
            affected_packages=[{"ecosystem": "PyPI", "name": "test", "affected_versions": ["*"]}],
            recommended_strategy="manual_review",
            remediation_complexity="critical",
            source_feed="test"
        )
        
        assert manual_apv.has_automated_fix is False


class TestAPVSerialization:
    """Test APV serialization methods."""
    
    def test_to_kafka_message(self):
        """Test serialization for Kafka."""
        apv = APV(
            cve_id="CVE-2024-13001",
            published=datetime.now(),
            modified=datetime.now(),
            summary="Test vulnerability",
            details="Test details with sufficient length",
            priority="high",
            affected_packages=[{
                "ecosystem": "PyPI",
                "name": "test-lib",
                "affected_versions": ["<1.0.0"],
                "fixed_versions": ["1.0.0"]
            }],
            recommended_strategy="dependency_upgrade",
            remediation_complexity="low",
            source_feed="OSV.dev"
        )
        
        kafka_msg = apv.to_kafka_message()
        
        assert isinstance(kafka_msg, dict)
        assert kafka_msg['cve_id'] == "CVE-2024-13001"
        assert kafka_msg['priority'] == "high"
        assert 'affected_packages' in kafka_msg
    
    def test_to_database_record(self):
        """Test serialization for PostgreSQL."""
        apv = APV(
            cve_id="CVE-2024-13002",
            published=datetime.now(),
            modified=datetime.now(),
            summary="Test vulnerability",
            details="Test details with sufficient length",
            priority="critical",
            affected_packages=[{
                "ecosystem": "PyPI",
                "name": "test-lib",
                "affected_versions": ["*"]
            }],
            maximus_context={
                "affected_services": ["service1", "service2"]
            },
            recommended_strategy="code_patch",
            remediation_complexity="medium",
            source_feed="NVD"
        )
        
        db_record = apv.to_database_record()
        
        assert isinstance(db_record, dict)
        assert db_record['cve_id'] == "CVE-2024-13002"
        assert db_record['priority'] == "critical"
        assert db_record['source_feed'] == "NVD"
        assert len(db_record['affected_services']) == 2
        assert 'apv_object' in db_record
        assert 'enriched_vulnerability' in db_record


# ==================== INTEGRATION TESTS ====================

class TestAPVEndToEnd:
    """End-to-end APV creation tests."""
    
    def test_realistic_django_cve(self):
        """Test realistic Django SQL injection APV."""
        apv = APV(
            cve_id="CVE-2024-45678",
            aliases=["GHSA-abcd-1234-efgh"],
            published=datetime(2024, 10, 1),
            modified=datetime(2024, 10, 5),
            summary="SQL Injection in Django Model.objects.raw()",
            details="Django versions 3.0 to 4.2.7 are vulnerable to SQL injection when using Model.objects.raw() with unsanitized user input. Attackers can execute arbitrary SQL commands.",
            cvss=CVSSScore(
                version="3.1",
                base_score=9.8,
                severity="CRITICAL",
                vector_string="CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H"
            ),
            affected_packages=[{
                "ecosystem": "PyPI",
                "name": "django",
                "affected_versions": [">=3.0,<4.2.8"],
                "fixed_versions": ["4.2.8", "5.0.0"],
                "purl": "pkg:pypi/django"
            }],
            ast_grep_patterns=[{
                "language": "python",
                "pattern": "Model.objects.raw($QUERY)",
                "severity": "critical",
                "description": "Detects potentially vulnerable raw SQL usage"
            }],
            maximus_context={
                "affected_services": ["maximus_core_service", "maximus_api_gateway"],
                "deployment_impact": "medium",
                "rollback_available": True,
                "exploit_available": False,
                "breaking_changes_likely": False
            },
            source_feed="OSV.dev",
            oraculo_version="1.0.0"
        )
        
        # Validate all computed fields
        assert apv.is_critical is True
        assert apv.requires_immediate_action is True
        assert apv.has_automated_fix is True
        assert apv.priority == PriorityLevel.CRITICAL
        assert apv.recommended_strategy == RemediationStrategy.DEPENDENCY_UPGRADE
        assert apv.remediation_complexity == RemediationComplexity.LOW
        assert len(apv.affected_services) == 2
        
        # Validate serialization
        kafka_msg = apv.to_kafka_message()
        assert kafka_msg['cve_id'] == "CVE-2024-45678"
        
        db_record = apv.to_database_record()
        assert db_record['priority'] == "critical"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
