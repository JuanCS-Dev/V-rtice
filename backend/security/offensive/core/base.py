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


class LegacyOffensiveTool(ABC):
    """
    Legacy base class for offensive security tools (Target-based interface).
    
    Kept for backward compatibility.
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


# New flexible base class
class OffensiveTool(ABC):
    """
    Enhanced base class for offensive security tools.
    
    Supports flexible kwargs-based interface for orchestration.
    """
    
    def __init__(self, name: str, category: str = "general", version: str = "1.0.0") -> None:
        """
        Initialize offensive tool.
        
        Args:
            name: Tool name
            category: Tool category
            version: Tool version
        """
        self.name = name
        self.category = category
        self.version = version
        self.operation_id: Optional[UUID] = None
    
    @abstractmethod
    async def execute(self, **kwargs) -> 'ToolResult':
        """
        Execute tool operation.
        
        Args:
            **kwargs: Tool-specific parameters
            
        Returns:
            ToolResult with execution results
        """
        pass
    
    async def validate(self) -> bool:
        """
        Validate tool functionality.
        
        Returns:
            True if tool is operational
        """
        return True
    
    def _generate_operation_id(self) -> UUID:
        """Generate unique operation ID."""
        return uuid4()


class ReconnaissanceTool(LegacyOffensiveTool):
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


class ExploitationTool(LegacyOffensiveTool):
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


class PostExploitationTool(LegacyOffensiveTool):
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


class IntelligenceTool(LegacyOffensiveTool):
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


# ============================================================================
# ENHANCED BASE CLASSES FOR ORCHESTRATION
# ============================================================================

@dataclass
class ToolMetadata:
    """
    Metadata for tool execution.
    
    Attributes:
        tool_name: Tool identifier
        execution_time: Execution duration in seconds
        success_rate: Historical success rate
        confidence_score: Confidence in results (0.0-1.0)
        resource_usage: Resource consumption metrics
    """
    tool_name: str
    execution_time: float = 0.0
    success_rate: float = 1.0
    confidence_score: float = 0.8
    resource_usage: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ToolResult:
    """
    Enhanced tool execution result.
    
    Attributes:
        success: Operation success status
        data: Result data
        message: Human-readable message
        metadata: Tool metadata
        timestamp: Execution timestamp
    """
    success: bool
    data: Any
    message: str = ""
    metadata: Optional[ToolMetadata] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
