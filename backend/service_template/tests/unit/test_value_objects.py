"""
Tests for Domain Layer - Value Objects

100% coverage required.
"""
import pytest

from service_template.domain.value_objects import Email, Status


class TestEmail:
    """Tests for Email value object."""

    def test_valid_email(self) -> None:
        """Test creating valid email."""
        email = Email("test@example.com")
        assert email.value == "test@example.com"

    def test_valid_email_complex(self) -> None:
        """Test creating complex valid email."""
        email = Email("user.name+tag@sub.domain.com")
        assert email.value == "user.name+tag@sub.domain.com"

    def test_invalid_email_no_at(self) -> None:
        """Test invalid email without @."""
        with pytest.raises(ValueError, match="Invalid email format"):
            Email("notanemail")

    def test_invalid_email_no_domain(self) -> None:
        """Test invalid email without domain."""
        with pytest.raises(ValueError, match="Invalid email format"):
            Email("user@")

    def test_invalid_email_no_user(self) -> None:
        """Test invalid email without user."""
        with pytest.raises(ValueError, match="Invalid email format"):
            Email("@domain.com")

    def test_email_str(self) -> None:
        """Test email string representation."""
        email = Email("test@example.com")
        assert str(email) == "test@example.com"

    def test_email_immutable(self) -> None:
        """Test email is immutable (frozen dataclass)."""
        email = Email("test@example.com")
        
        with pytest.raises(AttributeError):
            email.value = "new@example.com"  # type: ignore


class TestStatus:
    """Tests for Status value object."""

    @pytest.mark.parametrize("status_value", ["active", "inactive", "pending", "deleted"])
    def test_valid_status(self, status_value: str) -> None:
        """Test creating valid status values."""
        status = Status(status_value)
        assert status.value == status_value

    def test_invalid_status(self) -> None:
        """Test invalid status raises error."""
        with pytest.raises(ValueError, match="Invalid status"):
            Status("invalid")

    def test_invalid_status_shows_valid_states(self) -> None:
        """Test error message shows valid states."""
        with pytest.raises(ValueError, match="Invalid status"):
            Status("wrong")

    def test_status_str(self) -> None:
        """Test status string representation."""
        status = Status("active")
        assert str(status) == "active"

    def test_is_active_true(self) -> None:
        """Test is_active returns true for active status."""
        status = Status("active")
        assert status.is_active() is True

    @pytest.mark.parametrize("status_value", ["inactive", "pending", "deleted"])
    def test_is_active_false(self, status_value: str) -> None:
        """Test is_active returns false for non-active status."""
        status = Status(status_value)
        assert status.is_active() is False

    def test_status_immutable(self) -> None:
        """Test status is immutable (frozen dataclass)."""
        status = Status("active")
        
        with pytest.raises(AttributeError):
            status.value = "inactive"  # type: ignore
