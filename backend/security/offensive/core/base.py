"""
Base Classes for Offensive Tools
================================

Abstract base classes providing common interface for offensive security tools.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4


class OperationStatus(str, Enum):
    """Status of offensive operation."""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Severity(str, Enum):
    """Severity level of findings."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class Target:
    """
    Target specification for offensive operations.
    
    Attributes:
        host: Target hostname or IP address
        ports: List of target ports
        services: Identified services
        metadata: Additional target information
    """
    host: str
    ports: List[int] = field(default_factory=list)
    services: Dict[int, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self) -> None:
        """Validate target specification."""
        if not self.host:
            raise ValueError("Target host cannot be empty")


@dataclass
class OperationResult:
    """
    Result of offensive security operation.
    
    Attributes:
        operation_id: Unique operation identifier
        status: Operation status
        target: Target specification
        findings: List of findings
        timestamp: Operation timestamp
        duration: Operation duration in seconds
        metadata: Additional result information
    """
    operation_id: UUID
    status: OperationStatus
    target: Target
    findings: List[Dict[str, Any]] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    duration: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class OffensiveTool(ABC):
    """
    Abstract base class for offensive security tools.
    
    All offensive tools must inherit from this class and implement
    the execute method.
    """
    
    def __init__(self, name: str, version: str) -> None:
        """
        Initialize offensive tool.
        
        Args:
            name: Tool name
            version: Tool version
        """
        self.name = name
        self.version = version
        self.operation_id: Optional[UUID] = None
    
    @abstractmethod
    async def execute(
        self,
        target: Target,
        options: Optional[Dict[str, Any]] = None
    ) -> OperationResult:
        """
        Execute offensive operation.
        
        Args:
            target: Target specification
            options: Operation-specific options
            
        Returns:
            OperationResult with findings
            
        Raises:
            OffensiveSecurityError: If operation fails
        """
        pass
    
    @abstractmethod
    async def validate_target(self, target: Target) -> bool:
        """
        Validate target before operation.
        
        Args:
            target: Target to validate
            
        Returns:
            True if target is valid and reachable
        """
        pass
    
    def _generate_operation_id(self) -> UUID:
        """Generate unique operation ID."""
        return uuid4()


class ReconnaissanceTool(OffensiveTool):
    """Base class for reconnaissance tools."""
    
    async def discover(self, target: Target) -> List[Dict[str, Any]]:
        """
        Discover target assets.
        
        Args:
            target: Target specification
            
        Returns:
            List of discovered assets
        """
        raise NotImplementedError("Subclass must implement discover()")


class ExploitationTool(OffensiveTool):
    """Base class for exploitation tools."""
    
    async def exploit(
        self,
        target: Target,
        vulnerability: str
    ) -> OperationResult:
        """
        Exploit vulnerability on target.
        
        Args:
            target: Target specification
            vulnerability: Vulnerability identifier
            
        Returns:
            Exploitation result
        """
        raise NotImplementedError("Subclass must implement exploit()")


class PostExploitationTool(OffensiveTool):
    """Base class for post-exploitation tools."""
    
    async def maintain_access(self, target: Target) -> bool:
        """
        Establish persistence on target.
        
        Args:
            target: Compromised target
            
        Returns:
            True if persistence established
        """
        raise NotImplementedError("Subclass must implement maintain_access()")


class IntelligenceTool(OffensiveTool):
    """Base class for intelligence gathering tools."""
    
    async def gather(
        self,
        target: Target,
        query: str
    ) -> List[Dict[str, Any]]:
        """
        Gather intelligence on target.
        
        Args:
            target: Target specification
            query: Intelligence query
            
        Returns:
            List of intelligence findings
        """
        raise NotImplementedError("Subclass must implement gather()")
