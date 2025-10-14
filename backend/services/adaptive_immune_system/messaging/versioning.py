"""
Message Schema Versioning.

Implements schema versioning for RabbitMQ messages to support:
- Backwards compatibility
- Forward compatibility (graceful degradation)
- Schema evolution
- Version negotiation

Features:
- Semantic versioning (MAJOR.MINOR.PATCH)
- Version headers in messages
- Automatic version detection
- Schema migration support
- Compatibility checking

Versioning Strategy:
- MAJOR: Breaking changes (incompatible schema)
- MINOR: Backwards-compatible additions (new optional fields)
- PATCH: Backwards-compatible fixes (no schema change)
"""

import logging
from dataclasses import dataclass
from typing import Any, Dict, Optional, Type

from pydantic import BaseModel, ValidationError

logger = logging.getLogger(__name__)


@dataclass
class Version:
    """
    Semantic version.

    Format: MAJOR.MINOR.PATCH
    """

    major: int
    minor: int
    patch: int

    @classmethod
    def from_string(cls, version_string: str) -> "Version":
        """
        Parse version from string.

        Args:
            version_string: Version string (e.g., "1.2.3")

        Returns:
            Version instance

        Raises:
            ValueError: If version string is invalid
        """
        try:
            parts = version_string.split(".")
            if len(parts) != 3:
                raise ValueError(f"Invalid version format: {version_string}")

            return cls(
                major=int(parts[0]),
                minor=int(parts[1]),
                patch=int(parts[2]),
            )
        except (ValueError, IndexError) as e:
            raise ValueError(f"Invalid version string '{version_string}': {e}")

    def to_string(self) -> str:
        """
        Convert version to string.

        Returns:
            Version string (e.g., "1.2.3")
        """
        return f"{self.major}.{self.minor}.{self.patch}"

    def is_compatible_with(self, other: "Version") -> bool:
        """
        Check if this version is compatible with another.

        Compatibility rules:
        - Same MAJOR version required
        - MINOR/PATCH can differ (backwards compatible)

        Args:
            other: Version to check compatibility with

        Returns:
            True if compatible, False otherwise
        """
        return self.major == other.major

    def __lt__(self, other: "Version") -> bool:
        """Compare versions (less than)."""
        return (self.major, self.minor, self.patch) < (
            other.major,
            other.minor,
            other.patch,
        )

    def __le__(self, other: "Version") -> bool:
        """Compare versions (less than or equal)."""
        return (self.major, self.minor, self.patch) <= (
            other.major,
            other.minor,
            other.patch,
        )

    def __gt__(self, other: "Version") -> bool:
        """Compare versions (greater than)."""
        return (self.major, self.minor, self.patch) > (
            other.major,
            other.minor,
            other.patch,
        )

    def __ge__(self, other: "Version") -> bool:
        """Compare versions (greater than or equal)."""
        return (self.major, self.minor, self.patch) >= (
            other.major,
            other.minor,
            other.patch,
        )

    def __eq__(self, other: object) -> bool:
        """Compare versions (equal)."""
        if not isinstance(other, Version):
            return False
        return (self.major, self.minor, self.patch) == (
            other.major,
            other.minor,
            other.patch,
        )

    def __repr__(self) -> str:
        """String representation."""
        return f"Version({self.to_string()})"


class VersionedMessage:
    """
    Base class for versioned messages.

    Subclasses should define:
    - SCHEMA_VERSION: Current schema version
    - upgrade_from_vX_Y_Z methods for migrations
    """

    SCHEMA_VERSION: Version = Version(1, 0, 0)

    @classmethod
    def get_schema_version(cls) -> Version:
        """Get schema version for this message type."""
        return cls.SCHEMA_VERSION

    @classmethod
    def add_version_headers(cls, message: BaseModel) -> Dict[str, Any]:
        """
        Add version headers to message.

        Args:
            message: Pydantic message model

        Returns:
            Dict with message data + version headers
        """
        data = message.model_dump() if hasattr(message, 'model_dump') else message.dict()

        # Add version header
        data["_schema_version"] = cls.SCHEMA_VERSION.to_string()
        data["_message_type"] = cls.__name__

        return data

    @classmethod
    def extract_version(cls, data: Dict[str, Any]) -> Optional[Version]:
        """
        Extract version from message data.

        Args:
            data: Message data

        Returns:
            Version if present, None otherwise
        """
        version_string = data.get("_schema_version")

        if version_string is None:
            logger.warning(
                f"No schema version found in message (type={data.get('_message_type')})"
            )
            return None

        try:
            return Version.from_string(version_string)
        except ValueError as e:
            logger.error(f"Invalid schema version in message: {e}")
            return None

    @classmethod
    def migrate_message(
        cls,
        data: Dict[str, Any],
        from_version: Version,
        to_version: Version,
    ) -> Dict[str, Any]:
        """
        Migrate message from one version to another.

        Looks for migration methods in format: upgrade_from_v{major}_{minor}_{patch}

        Args:
            data: Message data
            from_version: Source version
            to_version: Target version

        Returns:
            Migrated message data

        Raises:
            ValueError: If migration not supported
        """
        # No migration needed if same version
        if from_version == to_version:
            return data

        # Check compatibility
        if not from_version.is_compatible_with(to_version):
            raise ValueError(
                f"Cannot migrate from {from_version} to {to_version} - "
                "incompatible MAJOR versions"
            )

        # Look for migration method
        method_name = (
            f"upgrade_from_v{from_version.major}_"
            f"{from_version.minor}_{from_version.patch}"
        )

        if hasattr(cls, method_name):
            migration_func = getattr(cls, method_name)
            logger.info(
                f"Migrating message from {from_version} to {to_version} "
                f"using {method_name}"
            )
            return migration_func(data)

        # No specific migration - try default (copy all fields)
        logger.warning(
            f"No migration method '{method_name}' found - using default migration"
        )
        return data

    @classmethod
    def parse_versioned(
        cls,
        data: Dict[str, Any],
        model_class: Type[BaseModel],
    ) -> BaseModel:
        """
        Parse versioned message with automatic migration.

        Args:
            data: Message data
            model_class: Pydantic model class

        Returns:
            Parsed message model

        Raises:
            ValidationError: If message invalid even after migration
        """
        # Extract version
        message_version = cls.extract_version(data)

        if message_version is None:
            # No version - assume latest and try to parse
            logger.warning("No version in message - assuming latest schema")
            return model_class(**data)

        # Check if migration needed
        current_version = cls.get_schema_version()

        if message_version < current_version:
            # Older message - migrate forward
            logger.info(
                f"Migrating message from {message_version} to {current_version}"
            )
            data = cls.migrate_message(data, message_version, current_version)

        elif message_version > current_version:
            # Newer message - attempt graceful degradation
            logger.warning(
                f"Message version {message_version} newer than current {current_version} - "
                "attempting graceful degradation"
            )
            # Try to parse anyway (Pydantic will ignore unknown fields)

        # Parse message
        try:
            return model_class(**data)
        except ValidationError as e:
            logger.error(
                f"Failed to parse message (version={message_version}): {e}"
            )
            raise


# --- Example Migrations ---


class ExampleVersionedMessage(VersionedMessage):
    """
    Example versioned message showing migrations.

    Version history:
    - v1.0.0: Initial version (fields: id, name)
    - v1.1.0: Added optional email field
    - v1.2.0: Added optional tags field
    - v2.0.0: Breaking change - renamed 'name' to 'full_name'
    """

    SCHEMA_VERSION = Version(1, 2, 0)

    @classmethod
    def upgrade_from_v1_0_0(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Migrate from v1.0.0 to v1.1.0.

        Changes:
        - Added email field (optional)
        """
        # Add default email if not present
        if "email" not in data:
            data["email"] = None

        logger.debug("Migrated from v1.0.0 to v1.1.0")
        return data

    @classmethod
    def upgrade_from_v1_1_0(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Migrate from v1.1.0 to v1.2.0.

        Changes:
        - Added tags field (optional list)
        """
        # Add default tags if not present
        if "tags" not in data:
            data["tags"] = []

        logger.debug("Migrated from v1.1.0 to v1.2.0")
        return data


# --- Version Registry ---


class MessageVersionRegistry:
    """
    Registry for message versions.

    Tracks all message types and their versions for monitoring and debugging.
    """

    def __init__(self):
        self._registry: Dict[str, Version] = {}

    def register(self, message_type: str, version: Version) -> None:
        """
        Register message type version.

        Args:
            message_type: Message type name
            version: Schema version
        """
        if message_type in self._registry:
            existing = self._registry[message_type]
            if existing != version:
                logger.warning(
                    f"Message type '{message_type}' version changed: "
                    f"{existing} → {version}"
                )

        self._registry[message_type] = version
        logger.debug(f"Registered {message_type} v{version.to_string()}")

    def get_version(self, message_type: str) -> Optional[Version]:
        """
        Get version for message type.

        Args:
            message_type: Message type name

        Returns:
            Version if registered, None otherwise
        """
        return self._registry.get(message_type)

    def list_all(self) -> Dict[str, str]:
        """
        List all registered message types and versions.

        Returns:
            Dict mapping message type to version string
        """
        return {
            msg_type: version.to_string()
            for msg_type, version in self._registry.items()
        }

    def check_compatibility(
        self,
        message_type: str,
        version: Version,
    ) -> bool:
        """
        Check if version is compatible with registered version.

        Args:
            message_type: Message type name
            version: Version to check

        Returns:
            True if compatible, False otherwise
        """
        registered = self.get_version(message_type)

        if registered is None:
            logger.warning(f"Message type '{message_type}' not registered")
            return True  # Allow unknown types

        return version.is_compatible_with(registered)


# Global registry
_global_registry = MessageVersionRegistry()


def get_message_registry() -> MessageVersionRegistry:
    """Get global message version registry."""
    return _global_registry


# --- Version Header Constants ---


class VersionHeaders:
    """Constants for version-related headers."""

    SCHEMA_VERSION = "_schema_version"
    MESSAGE_TYPE = "_message_type"
    PRODUCER_VERSION = "_producer_version"  # Version of service that produced message
    CREATED_AT = "_created_at"


# --- Compatibility Checker ---


def check_version_compatibility(
    producer_version: str,
    consumer_version: str,
) -> tuple[bool, Optional[str]]:
    """
    Check if producer and consumer versions are compatible.

    Args:
        producer_version: Producer schema version
        consumer_version: Consumer schema version

    Returns:
        (compatible, warning_message)
    """
    try:
        prod_ver = Version.from_string(producer_version)
        cons_ver = Version.from_string(consumer_version)

        if prod_ver.is_compatible_with(cons_ver):
            if prod_ver > cons_ver:
                return True, f"Consumer schema ({consumer_version}) older than producer ({producer_version})"
            elif prod_ver < cons_ver:
                return True, f"Consumer schema ({consumer_version}) newer than producer ({producer_version})"
            else:
                return True, None
        else:
            return False, f"Incompatible versions: producer={producer_version}, consumer={consumer_version}"

    except ValueError as e:
        return False, f"Invalid version format: {e}"
