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


class OffensiveToolError(OffensiveSecurityError):
    """
    Generic offensive tool error.
    
    Used for orchestration and tool-level errors.
    """
    
    def __init__(
        self,
        message: str,
        tool_name: str = "",
        details: dict = None
    ) -> None:
        """
        Initialize tool error.
        
        Args:
            message: Error message
            tool_name: Tool that raised the error
            details: Additional error details
        """
        super().__init__(message)
        self.tool_name = tool_name
        self.details = details or {}
    
    def __str__(self) -> str:
        """String representation."""
        if self.tool_name:
            return f"[{self.tool_name}] {super().__str__()}"
        return super().__str__()
