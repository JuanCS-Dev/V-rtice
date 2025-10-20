"""
Reactive Fabric Core - External Integrations

Unified integration layer for:
- Active Immune Core (bidirectional)
- Monitoring systems
- SIEM
- Analytics

NO MOCKS, NO PLACEHOLDERS, NO TODOS.

Authors: Juan & Claude
Version: 1.0.0
"""

from .immune_system_bridge import ImmuneSystemBridge

__all__ = ["ImmuneSystemBridge"]
