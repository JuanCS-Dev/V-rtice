"""Vértice Tegumentar Module - Adaptive, Biomimetic Firewall.

This package implements the three-layer tegumentar architecture:

- Epiderme: stateless edge filtering, eBPF reflex arc, DDoS absorption.
- Derme: deep packet inspection, hybrid IPS, sensory signal generation.
- Hipoderme: permeability control, SOAR wound healing, cognitive interface.

All public entry points should be re-exported here so other services can
consume the firewall capabilities without needing to know the internal
package layout.
"""

__all__ = ["TegumentarSettings", "TegumentarModule", "get_settings"]


def __getattr__(name):
    if name == "TegumentarSettings":
        from .config import TegumentarSettings as _TegumentarSettings

        return _TegumentarSettings
    if name == "TegumentarModule":
        from .orchestrator import TegumentarModule as _TegumentarModule

        return _TegumentarModule
    if name == "get_settings":
        from .config import get_settings as _get_settings

        return _get_settings
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
