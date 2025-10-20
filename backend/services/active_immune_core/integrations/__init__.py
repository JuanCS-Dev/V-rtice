"""
Active Immune Core - External Integrations

Unified integration layer for:
- Reactive Fabric (threat detections)
- Monitoring systems
- SIEM
- Analytics

NO MOCKS, NO PLACEHOLDERS, NO TODOS.

Authors: Juan & Claude
Version: 1.0.0
"""

from .reactive_fabric_adapter import ReactiveFabricAdapter

__all__ = ["ReactiveFabricAdapter"]
