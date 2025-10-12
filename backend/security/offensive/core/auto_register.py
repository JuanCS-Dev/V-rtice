"""
Auto-registration of Offensive Tools.

Automatically registers all offensive tools with the MAXIMUS registry
on import. This ensures tools are available through the unified interface.
"""
from .tool_registry import register_tool, ToolCategory

# Import tool classes
from ..reconnaissance.scanner import NetworkScanner
from ..reconnaissance.dns_enum import DNSEnumerator
from ..exploitation.payload_gen import PayloadGenerator


def register_all_tools() -> None:
    """
    Register all offensive tools with registry.
    
    Called automatically on module import.
    """
    
    # Reconnaissance Tools
    register_tool(
        name="network_scanner",
        category=ToolCategory.RECONNAISSANCE,
        description="AI-enhanced network port scanner with service detection",
        tool_class=NetworkScanner,
        requires_auth=False,  # Defensive use OK
        risk_level="low"
    )
    
    register_tool(
        name="dns_enumerator",
        category=ToolCategory.RECONNAISSANCE,
        description="DNS enumeration and subdomain discovery",
        tool_class=DNSEnumerator,
        requires_auth=False,  # OSINT is low risk
        risk_level="low"
    )
    
    # Exploitation Tools
    register_tool(
        name="payload_generator",
        category=ToolCategory.EXPLOITATION,
        description="Dynamic payload generator with obfuscation",
        tool_class=PayloadGenerator,
        requires_auth=True,  # Requires authorization
        risk_level="high"
    )


# Auto-register on import
register_all_tools()
