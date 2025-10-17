"""Tests for backend/shared/enums.py - 100% coverage via reflection.

Strategy: Automated testing of all 28 enum classes using reflection
to minimize test code while maximizing coverage.
"""

import inspect
import pytest
from enum import Enum
from backend.shared import enums


def get_all_enum_classes():
    """Extract all Enum classes from enums module via reflection."""
    return [
        (name, obj)
        for name, obj in inspect.getmembers(enums, inspect.isclass)
        if issubclass(obj, Enum) and obj is not Enum
    ]


class TestEnumsReflection:
    """Reflection-based tests for all enum classes."""

    @pytest.mark.parametrize("enum_name,enum_class", get_all_enum_classes())
    def test_enum_has_members(self, enum_name, enum_class):
        """All enums must have at least one member."""
        assert len(enum_class) > 0, f"{enum_name} has no members"

    @pytest.mark.parametrize("enum_name,enum_class", get_all_enum_classes())
    def test_enum_members_are_strings(self, enum_name, enum_class):
        """All enum members must have string values (for JSON serialization)."""
        for member in enum_class:
            assert isinstance(member.value, str), (
                f"{enum_name}.{member.name} value is not a string: {type(member.value)}"
            )

    @pytest.mark.parametrize("enum_name,enum_class", get_all_enum_classes())
    def test_enum_str_inheritance(self, enum_name, enum_class):
        """All enums must inherit from str for FastAPI compatibility."""
        assert issubclass(enum_class, str), (
            f"{enum_name} does not inherit from str"
        )

    @pytest.mark.parametrize("enum_name,enum_class", get_all_enum_classes())
    def test_enum_member_access(self, enum_name, enum_class):
        """All enum members must be accessible by name and value."""
        for member in enum_class:
            # Access by name
            assert enum_class[member.name] == member
            # Access by value
            assert enum_class(member.value) == member

    @pytest.mark.parametrize("enum_name,enum_class", get_all_enum_classes())
    def test_enum_member_uniqueness(self, enum_name, enum_class):
        """All enum member values must be unique."""
        values = [member.value for member in enum_class]
        assert len(values) == len(set(values)), (
            f"{enum_name} has duplicate values"
        )

    @pytest.mark.parametrize("enum_name,enum_class", get_all_enum_classes())
    def test_enum_iteration(self, enum_name, enum_class):
        """Enums must be iterable."""
        members = list(enum_class)
        assert len(members) > 0
        assert all(isinstance(m, enum_class) for m in members)

    @pytest.mark.parametrize("enum_name,enum_class", get_all_enum_classes())
    def test_enum_comparison(self, enum_name, enum_class):
        """Enum members must support equality comparison."""
        members = list(enum_class)
        if len(members) >= 2:
            assert members[0] == members[0]
            assert members[0] != members[1]

    @pytest.mark.parametrize("enum_name,enum_class", get_all_enum_classes())
    def test_enum_string_representation(self, enum_name, enum_class):
        """Enum members must have proper string representation."""
        for member in enum_class:
            # __repr__ should be descriptive (contains class name and member name)
            repr_str = repr(member)
            assert enum_name in repr_str or member.name in repr_str
            # Value should be accessible
            assert member.value is not None

    @pytest.mark.parametrize("enum_name,enum_class", get_all_enum_classes())
    def test_enum_hash(self, enum_name, enum_class):
        """Enum members must be hashable (for use in sets/dicts)."""
        members = list(enum_class)
        # Should be able to create a set
        member_set = set(members)
        assert len(member_set) == len(members)
        # Should be able to use as dict keys
        member_dict = {m: m.value for m in members}
        assert len(member_dict) == len(members)


class TestSpecificEnums:
    """Targeted tests for specific enum classes with business logic."""

    def test_service_status_enum(self):
        """Test ServiceStatus enum specifically."""
        from backend.shared.enums import ServiceStatus
        
        assert ServiceStatus.HEALTHY.value == "healthy"
        assert ServiceStatus.UNHEALTHY.value == "unhealthy"
        assert ServiceStatus.DEGRADED.value == "degraded"
        assert len(ServiceStatus) >= 5

    def test_threat_level_enum(self):
        """Test ThreatLevel enum specifically."""
        from backend.shared.enums import ThreatLevel
        
        # NIST 800-61 aligned levels
        assert hasattr(ThreatLevel, "CRITICAL") or hasattr(ThreatLevel, "HIGH")
        assert len(ThreatLevel) >= 3

    def test_analysis_status_enum(self):
        """Test AnalysisStatus enum for async jobs."""
        from backend.shared.enums import AnalysisStatus
        
        assert AnalysisStatus.PENDING.value == "pending"
        assert AnalysisStatus.RUNNING.value == "running"
        assert AnalysisStatus.COMPLETED.value == "completed"
        assert AnalysisStatus.FAILED.value == "failed"

    def test_scan_status_enum(self):
        """Test ScanStatus enum for security scans."""
        from backend.shared.enums import ScanStatus
        
        assert ScanStatus.PENDING.value == "pending"
        assert ScanStatus.RUNNING.value == "running"
        assert ScanStatus.COMPLETED.value == "completed"

    def test_enum_json_serialization(self):
        """Enums must be JSON-serializable (via .value)."""
        from backend.shared.enums import ServiceStatus
        import json
        
        status = ServiceStatus.HEALTHY
        # FastAPI auto-serializes to .value
        assert json.dumps(status.value) == '"healthy"'

    def test_enum_in_comparisons(self):
        """Enums must work in conditional expressions."""
        from backend.shared.enums import ServiceStatus
        
        status = ServiceStatus.HEALTHY
        
        if status == ServiceStatus.HEALTHY:
            result = True
        else:
            result = False
        
        assert result is True

    def test_enum_invalid_value(self):
        """Creating enum from invalid value must raise ValueError."""
        from backend.shared.enums import ServiceStatus
        
        with pytest.raises(ValueError):
            ServiceStatus("invalid_status")

    def test_enum_case_sensitivity(self):
        """Enum values are case-sensitive."""
        from backend.shared.enums import ServiceStatus
        
        with pytest.raises(ValueError):
            ServiceStatus("HEALTHY")  # Should be "healthy"


class TestEnumCoverage:
    """Ensure all enum classes are tested."""

    def test_all_enums_imported(self):
        """Verify we can import all enum classes."""
        enum_classes = get_all_enum_classes()
        assert len(enum_classes) >= 28, (
            f"Expected at least 28 enum classes, found {len(enum_classes)}"
        )

    def test_no_empty_enums(self):
        """No enum should be empty."""
        enum_classes = get_all_enum_classes()
        for name, enum_class in enum_classes:
            assert len(enum_class) > 0, f"{name} is empty"

    def test_all_enums_documented(self):
        """All enum classes should have docstrings."""
        enum_classes = get_all_enum_classes()
        for name, enum_class in enum_classes:
            assert enum_class.__doc__ is not None, (
                f"{name} has no docstring"
            )
            assert len(enum_class.__doc__.strip()) > 0, (
                f"{name} has empty docstring"
            )
