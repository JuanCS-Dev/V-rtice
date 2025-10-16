"""
Comprehensive tests for validate_ports.py - 100% coverage required.
"""
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

# Add parent dir to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from validate_ports import (
    load_registry,
    validate_uniqueness,
    validate_ranges,
    validate_completeness,
    validate_metadata,
    main,
)


@pytest.fixture
def valid_registry():
    """Valid port registry for testing."""
    return {
        "metadata": {
            "version": "1.0.0",
            "total_services": 3,
        },
        "core": {
            "api_gateway": 8000,
        },
        "maximus": {
            "maximus_core": 8100,
            "maximus_eureka": 8101,
        },
    }


@pytest.fixture
def temp_registry_file(valid_registry):
    """Create temporary registry file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(valid_registry, f)
        return Path(f.name)


@pytest.fixture
def temp_services_dir():
    """Create temporary services directory."""
    tmpdir = Path(tempfile.mkdtemp())
    (tmpdir / "api_gateway").mkdir()
    (tmpdir / "maximus_core").mkdir()
    (tmpdir / "maximus_eureka").mkdir()
    return tmpdir


class TestLoadRegistry:
    """Tests for load_registry function."""

    def test_load_valid_registry(self, temp_registry_file):
        """Test loading a valid registry file."""
        with patch('validate_ports.Path') as mock_path:
            mock_path.return_value.parent.parent = temp_registry_file.parent
            mock_path.return_value.exists.return_value = True
            
            # Mock open to use temp file
            with patch('builtins.open', open):
                with patch.object(Path, '__truediv__', return_value=temp_registry_file):
                    result = load_registry()
                    assert "metadata" in result
                    assert "core" in result

    def test_load_missing_file(self):
        """Test loading non-existent file."""
        with patch('validate_ports.Path') as mock_path:
            mock_path.return_value.parent.parent = Path('/nonexistent')
            mock_path.return_value.exists.return_value = False
            instance = mock_path.return_value
            instance.__truediv__ = lambda self, other: Path('/nonexistent/ports.yaml')
            
            with pytest.raises(SystemExit) as exc_info:
                load_registry()
            assert exc_info.value.code == 1

    def test_load_invalid_yaml(self, tmp_path):
        """Test loading invalid YAML."""
        bad_file = tmp_path / "bad.yaml"
        bad_file.write_text("invalid: yaml: content:")
        
        with patch('validate_ports.Path') as mock_path:
            mock_path.return_value.parent.parent = tmp_path
            instance = mock_path.return_value
            instance.__truediv__ = lambda self, other: bad_file
            instance.exists.return_value = True
            
            with pytest.raises(SystemExit) as exc_info:
                load_registry()
            assert exc_info.value.code == 1


class TestValidateUniqueness:
    """Tests for validate_uniqueness function."""

    def test_no_conflicts(self, valid_registry):
        """Test registry with no port conflicts."""
        errors = validate_uniqueness(valid_registry)
        assert len(errors) == 0

    def test_port_conflict(self):
        """Test registry with port conflicts."""
        registry = {
            "core": {"service1": 8000},
            "maximus": {"service2": 8000},  # Conflict!
        }
        errors = validate_uniqueness(registry)
        assert len(errors) == 1
        assert "CONFLICT" in errors[0]

    def test_non_dict_category(self):
        """Test non-dict category."""
        registry = {
            "core": "not a dict",
        }
        errors = validate_uniqueness(registry)
        assert len(errors) == 1
        assert "must be dict" in errors[0]

    def test_non_int_port(self):
        """Test non-integer port."""
        registry = {
            "core": {"service1": "8000"},  # String instead of int
        }
        errors = validate_uniqueness(registry)
        assert len(errors) == 1
        assert "must be int" in errors[0]

    def test_metadata_skipped(self):
        """Test that metadata is skipped."""
        registry = {
            "metadata": {"version": "1.0.0"},
            "core": {"service1": 8000},
        }
        errors = validate_uniqueness(registry)
        assert len(errors) == 0


class TestValidateRanges:
    """Tests for validate_ranges function."""

    def test_valid_ranges(self, valid_registry):
        """Test ports within correct ranges."""
        errors = validate_ranges(valid_registry)
        assert len(errors) == 0

    def test_port_outside_range(self):
        """Test port outside category range."""
        registry = {
            "core": {"service1": 9999},  # Outside 8000-8099
        }
        errors = validate_ranges(registry)
        assert len(errors) == 1
        assert "outside range" in errors[0]

    def test_unknown_category(self):
        """Test unknown category."""
        registry = {
            "unknown_cat": {"service1": 8000},
        }
        errors = validate_ranges(registry)
        assert len(errors) == 1
        assert "Unknown category" in errors[0]

    def test_non_dict_category_skipped(self):
        """Test non-dict category is skipped."""
        registry = {
            "core": "not a dict",
        }
        errors = validate_ranges(registry)
        # Category exists but is not dict, so it's just skipped (no errors)
        assert len(errors) == 0

    def test_non_int_port_skipped(self):
        """Test non-int port is skipped in range check."""
        registry = {
            "core": {"service1": "8000"},
        }
        errors = validate_ranges(registry)
        assert len(errors) == 0  # Skipped, not a range error


class TestValidateCompleteness:
    """Tests for validate_completeness function."""

    def test_all_services_mapped(self, valid_registry, temp_services_dir):
        """Test all filesystem services are in YAML."""
        with patch('validate_ports.Path') as mock_path:
            instance = mock_path.return_value.parent.parent
            instance.__truediv__ = lambda self, other: temp_services_dir
            instance.exists.return_value = True
            mock_path.return_value.iterdir.return_value = temp_services_dir.iterdir()
            
            errors = validate_completeness(valid_registry)
            assert len(errors) == 0

    def test_unmapped_service(self, valid_registry, temp_services_dir):
        """Test service in filesystem but not in YAML."""
        (temp_services_dir / "extra_service").mkdir()
        
        with patch('validate_ports.Path') as mock_path:
            instance = mock_path.return_value.parent.parent
            instance.__truediv__ = lambda self, other: temp_services_dir
            instance.exists.return_value = True
            mock_path.return_value.iterdir.return_value = temp_services_dir.iterdir()
            
            errors = validate_completeness(valid_registry)
            assert len(errors) == 1
            assert "NOT in ports.yaml" in errors[0]

    def test_nonexistent_service(self, temp_services_dir):
        """Test service in YAML but not in filesystem."""
        # Clean temp dir first
        for d in temp_services_dir.iterdir():
            d.rmdir()
        
        registry = {
            "core": {"nonexistent_service": 8000},
        }
        
        with patch('validate_ports.Path') as mock_path:
            instance = mock_path.return_value.parent.parent
            instance.__truediv__ = lambda self, other: temp_services_dir
            instance.exists.return_value = True
            mock_path.return_value.iterdir.return_value = temp_services_dir.iterdir()
            
            errors = validate_completeness(registry)
            assert len(errors) == 1
            assert "NOT in filesystem" in errors[0]

    def test_services_dir_missing(self):
        """Test missing services directory."""
        registry = {"core": {"service1": 8000}}
        
        with patch('validate_ports.Path') as mock_path:
            instance = mock_path.return_value.parent.parent
            instance.__truediv__ = lambda self, other: Path("/nonexistent")
            instance.exists.return_value = False
            
            errors = validate_completeness(registry)
            assert len(errors) == 1
            assert "not found" in errors[0]


class TestValidateMetadata:
    """Tests for validate_metadata function."""

    def test_valid_metadata(self, valid_registry):
        """Test valid metadata."""
        errors = validate_metadata(valid_registry)
        assert len(errors) == 0

    def test_missing_metadata(self):
        """Test missing metadata section."""
        registry = {"core": {"service1": 8000}}
        errors = validate_metadata(registry)
        assert len(errors) == 1
        assert "Missing 'metadata'" in errors[0]

    def test_count_mismatch(self):
        """Test metadata count mismatch."""
        registry = {
            "metadata": {"total_services": 10},  # Wrong count
            "core": {"service1": 8000},
        }
        errors = validate_metadata(registry)
        assert len(errors) == 1
        assert "mismatch" in errors[0]


class TestMain:
    """Tests for main function."""

    def test_main_success(self, valid_registry, temp_registry_file, temp_services_dir, capsys):
        """Test main with valid registry."""
        with patch('validate_ports.load_registry', return_value=valid_registry):
            with patch('validate_ports.Path') as mock_path:
                instance = mock_path.return_value.parent.parent
                instance.__truediv__ = lambda self, other: temp_services_dir
                instance.exists.return_value = True
                mock_path.return_value.iterdir.return_value = temp_services_dir.iterdir()
                
                result = main()
                assert result == 0
                
                captured = capsys.readouterr()
                assert "✅ PORT REGISTRY VALID" in captured.out

    def test_main_with_errors(self, capsys):
        """Test main with validation errors."""
        bad_registry = {
            "metadata": {"total_services": 1},
            "core": {"service1": 8000, "service2": 8000},  # Conflict
        }
        
        with patch('validate_ports.load_registry', return_value=bad_registry):
            with patch('validate_ports.Path') as mock_path:
                instance = mock_path.return_value.parent.parent
                instance.__truediv__ = lambda self, other: Path("/nonexistent")
                instance.exists.return_value = False
                
                result = main()
                assert result == 1
                
                captured = capsys.readouterr()
                assert "❌ VALIDATION FAILED" in captured.out

    def test_main_load_failure(self, capsys):
        """Test main when loading fails."""
        with patch('validate_ports.load_registry', side_effect=SystemExit(1)):
            result = main()
            assert result == 1


# Integration test
def test_full_validation_cycle(valid_registry, temp_registry_file, temp_services_dir):
    """Full integration test of validation cycle."""
    with patch('validate_ports.load_registry', return_value=valid_registry):
        with patch('validate_ports.Path') as mock_path:
            instance = mock_path.return_value.parent.parent
            instance.__truediv__ = lambda self, other: temp_services_dir
            instance.exists.return_value = True
            mock_path.return_value.iterdir.return_value = temp_services_dir.iterdir()
            
            # Run all validations
            errors_uniqueness = validate_uniqueness(valid_registry)
            errors_ranges = validate_ranges(valid_registry)
            errors_completeness = validate_completeness(valid_registry)
            errors_metadata = validate_metadata(valid_registry)
            
            # All should pass
            assert len(errors_uniqueness) == 0
            assert len(errors_ranges) == 0
            assert len(errors_completeness) == 0
            assert len(errors_metadata) == 0
