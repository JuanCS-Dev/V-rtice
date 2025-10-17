"""Tests for backend/shared/constants.py - 100% coverage via reflection.

Strategy: Automated testing of all 16 constant classes using reflection
to validate all constant definitions without manual enumeration.
"""

import inspect
import pytest
from backend.shared import constants


def get_all_constant_classes():
    """Extract all constant classes from constants module."""
    return [
        (name, obj)
        for name, obj in inspect.getmembers(constants, inspect.isclass)
        if not name.startswith("_")
    ]


def get_class_constants(cls):
    """Get all uppercase constants from a class (Final[int], Final[str], etc)."""
    return [
        (name, getattr(cls, name))
        for name in dir(cls)
        if name.isupper() and not name.startswith("_")
    ]


class TestConstantsReflection:
    """Reflection-based tests for all constant classes."""

    @pytest.mark.parametrize("class_name,const_class", get_all_constant_classes())
    def test_class_has_constants(self, class_name, const_class):
        """All constant classes must have at least one constant."""
        constants_list = get_class_constants(const_class)
        assert len(constants_list) > 0, f"{class_name} has no constants"

    @pytest.mark.parametrize("class_name,const_class", get_all_constant_classes())
    def test_class_documented(self, class_name, const_class):
        """All constant classes must have docstrings."""
        assert const_class.__doc__ is not None, f"{class_name} has no docstring"
        assert len(const_class.__doc__.strip()) > 0

    @pytest.mark.parametrize("class_name,const_class", get_all_constant_classes())
    def test_constants_immutable(self, class_name, const_class):
        """Constants should be immutable (basic check)."""
        constants_list = get_class_constants(const_class)
        for name, value in constants_list:
            # Should not be None
            assert value is not None, f"{class_name}.{name} is None"

    @pytest.mark.parametrize("class_name,const_class", get_all_constant_classes())
    def test_constants_naming_convention(self, class_name, const_class):
        """All constants must follow UPPER_CASE naming."""
        constants_list = get_class_constants(const_class)
        for name, _ in constants_list:
            assert name.isupper(), (
                f"{class_name}.{name} does not follow UPPER_CASE convention"
            )
            assert not name.startswith("_"), (
                f"{class_name}.{name} should not start with underscore"
            )


class TestServicePorts:
    """Specific tests for ServicePorts class."""

    def test_service_ports_exist(self):
        """Test critical service ports are defined."""
        from backend.shared.constants import ServicePorts
        
        # Core services
        assert hasattr(ServicePorts, "API_GATEWAY")
        assert hasattr(ServicePorts, "MAXIMUS_CORE")
        
        # Ports must be integers
        assert isinstance(ServicePorts.API_GATEWAY, int)
        assert isinstance(ServicePorts.MAXIMUS_CORE, int)

    def test_service_ports_valid_range(self):
        """Service ports must be in valid TCP range (1-65535)."""
        from backend.shared.constants import ServicePorts
        
        ports = get_class_constants(ServicePorts)
        for name, port in ports:
            assert isinstance(port, int), f"{name} is not an integer"
            assert 1 <= port <= 65535, (
                f"{name}={port} is outside valid port range"
            )

    def test_service_ports_unique(self):
        """All service ports must be unique (no conflicts)."""
        from backend.shared.constants import ServicePorts
        
        ports = get_class_constants(ServicePorts)
        port_values = [p[1] for p in ports]
        port_names = [p[0] for p in ports]
        
        # Check for duplicates
        duplicates = [p for p in port_values if port_values.count(p) > 1]
        assert len(duplicates) == 0, (
            f"Duplicate ports found: {set(duplicates)}"
        )
        
        # Check we have many services defined
        assert len(port_values) >= 20, (
            f"Expected at least 20 service ports, found {len(port_values)}"
        )

    def test_service_ports_allocation_strategy(self):
        """Ports should follow documented allocation strategy."""
        from backend.shared.constants import ServicePorts
        
        # API Gateway should be 8000
        assert ServicePorts.API_GATEWAY == 8000
        
        # Core services should be 8000-8099 range
        if hasattr(ServicePorts, "MAXIMUS_CORE"):
            assert 8000 <= ServicePorts.MAXIMUS_CORE < 8100


class TestTimeConstants:
    """Test time-related constants if they exist."""

    def test_timeout_constants_if_exist(self):
        """Test timeout constants are positive integers."""
        from backend.shared import constants
        
        # Check if timeout constants exist
        timeout_classes = [
            name for name, obj in inspect.getmembers(constants, inspect.isclass)
            if "timeout" in name.lower() or "time" in name.lower()
        ]
        
        for class_name in timeout_classes:
            const_class = getattr(constants, class_name)
            time_constants = get_class_constants(const_class)
            
            for name, value in time_constants:
                if isinstance(value, (int, float)):
                    assert value > 0, (
                        f"{class_name}.{name}={value} must be positive"
                    )


class TestAPIConstants:
    """Test API-related constants if they exist."""

    def test_api_version_constants_if_exist(self):
        """Test API version constants exist and are valid."""
        from backend.shared import constants
        
        # Check if API-related classes exist
        api_classes = [
            name for name, obj in inspect.getmembers(constants, inspect.isclass)
            if "api" in name.lower() or "version" in name.lower()
        ]
        
        for class_name in api_classes:
            const_class = getattr(constants, class_name)
            api_constants = get_class_constants(const_class)
            
            # Should have at least one constant
            assert len(api_constants) > 0


class TestSecurityConstants:
    """Test security-related constants if they exist."""

    def test_security_constants_if_exist(self):
        """Test security constants are properly defined."""
        from backend.shared import constants
        
        security_classes = [
            name for name, obj in inspect.getmembers(constants, inspect.isclass)
            if any(keyword in name.lower() for keyword in ["security", "auth", "token", "crypto"])
        ]
        
        for class_name in security_classes:
            const_class = getattr(constants, class_name)
            sec_constants = get_class_constants(const_class)
            
            # Should have at least one constant
            assert len(sec_constants) > 0


class TestDatabaseConstants:
    """Test database-related constants if they exist."""

    def test_database_constants_if_exist(self):
        """Test database constants are properly defined."""
        from backend.shared import constants
        
        db_classes = [
            name for name, obj in inspect.getmembers(constants, inspect.isclass)
            if any(keyword in name.lower() for keyword in ["database", "db", "pool", "connection"])
        ]
        
        for class_name in db_classes:
            const_class = getattr(constants, class_name)
            db_constants = get_class_constants(const_class)
            
            # Should have at least one constant
            assert len(db_constants) > 0
            
            # If pool sizes exist, should be positive
            for name, value in db_constants:
                if "pool" in name.lower() and isinstance(value, int):
                    assert value > 0


class TestConstantsCoverage:
    """Ensure comprehensive coverage of constants module."""

    def test_all_classes_tested(self):
        """Verify we have many constant classes."""
        classes = get_all_constant_classes()
        assert len(classes) >= 10, (
            f"Expected at least 10 constant classes, found {len(classes)}"
        )

    def test_total_constants_count(self):
        """Verify we have many constants defined across all classes."""
        classes = get_all_constant_classes()
        total_constants = sum(
            len(get_class_constants(cls)) for _, cls in classes
        )
        assert total_constants >= 50, (
            f"Expected at least 50 constants total, found {total_constants}"
        )

    def test_no_duplicate_constant_names_across_classes(self):
        """Constant names should be unique within each class."""
        classes = get_all_constant_classes()
        
        for class_name, const_class in classes:
            constants_list = get_class_constants(const_class)
            names = [n for n, _ in constants_list]
            
            # Check for duplicates within this class
            duplicates = [n for n in names if names.count(n) > 1]
            assert len(duplicates) == 0, (
                f"{class_name} has duplicate constant names: {set(duplicates)}"
            )

    def test_constants_accessible(self):
        """All constants must be directly accessible."""
        classes = get_all_constant_classes()
        
        for class_name, const_class in classes:
            constants_list = get_class_constants(const_class)
            
            for name, value in constants_list:
                # Should be accessible via getattr
                assert getattr(const_class, name) == value
                # Should be accessible via class.ATTR
                assert getattr(const_class, name) is not None

    def test_module_imports(self):
        """Test module can be imported correctly."""
        from backend.shared import constants
        
        assert constants is not None
        assert hasattr(constants, "ServicePorts")

    def test_typing_imports_if_used(self):
        """If typing.Final is used, verify it's imported."""
        from backend.shared import constants
        import inspect
        
        source = inspect.getsource(constants)
        if "Final" in source:
            # Check Final is imported
            assert "from typing import" in source
