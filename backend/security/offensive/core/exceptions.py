"""
Offensive Security Exceptions
=============================

Custom exception hierarchy for offensive security operations.
"""


class OffensiveSecurityError(Exception):
    """Base exception for all offensive security errors."""
    pass


class ReconnaissanceError(OffensiveSecurityError):
    """Reconnaissance operation failed."""
    pass


class ExploitationError(OffensiveSecurityError):
    """Exploitation attempt failed."""
    pass


class PostExploitationError(OffensiveSecurityError):
    """Post-exploitation operation failed."""
    pass


class IntelligenceError(OffensiveSecurityError):
    """Intelligence gathering failed."""
    pass


class TargetUnreachableError(ReconnaissanceError):
    """Target system is unreachable."""
    pass


class ExploitFailedError(ExploitationError):
    """Exploit execution failed."""
    pass


class PayloadDeliveryError(PostExploitationError):
    """Payload delivery failed."""
    pass


class CredentialNotFoundError(IntelligenceError):
    """Credentials not found."""
    pass


class AuthenticationError(OffensiveSecurityError):
    """Authentication to target failed."""
    pass


class EthicalBoundaryViolation(OffensiveSecurityError):
    """Operation would violate ethical boundaries."""
    pass
