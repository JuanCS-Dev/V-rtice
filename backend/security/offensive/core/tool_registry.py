"""
MAXIMUS Tool Registry.

Central registry for all offensive and intelligence gathering tools.
Provides unified interface for tool discovery, execution, and management
with MAXIMUS integration.

Philosophy: Single source of truth for tool ecosystem.
"""
from typing import Dict, List, Optional, Type
from dataclasses import dataclass
from enum import Enum

from .base import OffensiveTool
from .maximus_adapter import MAXIMUSToolAdapter, MAXIMUSToolContext, OperationMode


class ToolCategory(Enum):
    """Tool categories."""
    RECONNAISSANCE = "reconnaissance"
    EXPLOITATION = "exploitation"
    POST_EXPLOITATION = "post_exploitation"
    OSINT = "osint"
    DEFENSIVE = "defensive"
    INTELLIGENCE = "intelligence"


@dataclass
class ToolInfo:
    """Tool information."""
    name: str
    category: ToolCategory
    description: str
    tool_class: Type[OffensiveTool]
    requires_auth: bool = True
    risk_level: str = "medium"
    
    def __post_init__(self):
        """Validate tool info."""
        if self.risk_level not in ["low", "medium", "high", "critical"]:
            raise ValueError(f"Invalid risk level: {self.risk_level}")


class ToolRegistry:
    """
    Central registry for MAXIMUS tools.
    
    Manages tool lifecycle:
    - Registration and discovery
    - Instantiation with MAXIMUS wrapper
    - Capability queries
    - Ethical boundary enforcement
    
    Singleton pattern ensures consistent tool management.
    """
    
    _instance: Optional["ToolRegistry"] = None
    
    def __new__(cls):
        """Enforce singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize registry."""
        if self._initialized:
            return
        
        self._tools: Dict[str, ToolInfo] = {}
        self._instances: Dict[str, OffensiveTool] = {}
        self._adapters: Dict[str, MAXIMUSToolAdapter] = {}
        self._initialized = True
    
    def register_tool(self, tool_info: ToolInfo) -> None:
        """
        Register tool.
        
        Args:
            tool_info: Tool information
            
        Raises:
            ValueError: If tool already registered
        """
        if tool_info.name in self._tools:
            raise ValueError(f"Tool already registered: {tool_info.name}")
        
        self._tools[tool_info.name] = tool_info
    
    def get_tool(
        self,
        name: str,
        with_maximus: bool = True
    ) -> OffensiveTool | MAXIMUSToolAdapter:
        """
        Get tool instance.
        
        Args:
            name: Tool name
            with_maximus: Wrap with MAXIMUS adapter
            
        Returns:
            Tool instance or MAXIMUS adapter
            
        Raises:
            KeyError: If tool not found
        """
        if name not in self._tools:
            raise KeyError(f"Tool not found: {name}")
        
        # Lazy instantiation
        if name not in self._instances:
            tool_info = self._tools[name]
            self._instances[name] = tool_info.tool_class()
        
        if not with_maximus:
            return self._instances[name]
        
        # Wrap with MAXIMUS adapter
        if name not in self._adapters:
            self._adapters[name] = MAXIMUSToolAdapter(
                self._instances[name]
            )
        
        return self._adapters[name]
    
    def list_tools(
        self,
        category: Optional[ToolCategory] = None
    ) -> List[ToolInfo]:
        """
        List registered tools.
        
        Args:
            category: Optional category filter
            
        Returns:
            List of tool information
        """
        tools = list(self._tools.values())
        
        if category:
            tools = [t for t in tools if t.category == category]
        
        return tools
    
    def get_tool_info(self, name: str) -> ToolInfo:
        """
        Get tool information.
        
        Args:
            name: Tool name
            
        Returns:
            Tool information
            
        Raises:
            KeyError: If tool not found
        """
        if name not in self._tools:
            raise KeyError(f"Tool not found: {name}")
        
        return self._tools[name]
    
    def is_registered(self, name: str) -> bool:
        """
        Check if tool registered.
        
        Args:
            name: Tool name
            
        Returns:
            True if registered
        """
        return name in self._tools
    
    def unregister_tool(self, name: str) -> None:
        """
        Unregister tool.
        
        Args:
            name: Tool name
            
        Raises:
            KeyError: If tool not found
        """
        if name not in self._tools:
            raise KeyError(f"Tool not found: {name}")
        
        # Cleanup instances
        if name in self._instances:
            del self._instances[name]
        if name in self._adapters:
            del self._adapters[name]
        
        del self._tools[name]
    
    def clear(self) -> None:
        """Clear all registered tools."""
        self._tools.clear()
        self._instances.clear()
        self._adapters.clear()
    
    def get_stats(self) -> Dict:
        """
        Get registry statistics.
        
        Returns:
            Registry statistics
        """
        return {
            "total_tools": len(self._tools),
            "instantiated": len(self._instances),
            "with_adapters": len(self._adapters),
            "by_category": {
                category.value: len([
                    t for t in self._tools.values()
                    if t.category == category
                ])
                for category in ToolCategory
            }
        }


# Global registry instance
registry = ToolRegistry()


def register_tool(
    name: str,
    category: ToolCategory,
    description: str,
    tool_class: Type[OffensiveTool],
    requires_auth: bool = True,
    risk_level: str = "medium"
) -> None:
    """
    Register tool with registry.
    
    Convenience function for tool registration.
    
    Args:
        name: Tool name
        category: Tool category
        description: Tool description
        tool_class: Tool class
        requires_auth: Whether tool requires authorization
        risk_level: Risk level (low, medium, high, critical)
    """
    tool_info = ToolInfo(
        name=name,
        category=category,
        description=description,
        tool_class=tool_class,
        requires_auth=requires_auth,
        risk_level=risk_level
    )
    
    registry.register_tool(tool_info)


def get_tool(
    name: str,
    with_maximus: bool = True
) -> OffensiveTool | MAXIMUSToolAdapter:
    """
    Get tool from registry.
    
    Args:
        name: Tool name
        with_maximus: Wrap with MAXIMUS adapter
        
    Returns:
        Tool instance or MAXIMUS adapter
    """
    return registry.get_tool(name, with_maximus)
