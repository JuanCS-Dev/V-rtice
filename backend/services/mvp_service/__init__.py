"""Backward compatibility shim for mvp_service.

This module provides backward compatibility for code that imports from mvp_service.
The service has been renamed to nis_service (Narrative Intelligence Service).

Deprecated: Use nis_service instead.
"""

import warnings

warnings.warn(
    "mvp_service is deprecated and will be removed in a future version. "
    "Use nis_service (Narrative Intelligence Service) instead.",
    DeprecationWarning,
    stacklevel=2,
)

# Re-export everything from nis_service for backward compatibility
try:
    from nis_service import *  # noqa: F401, F403
except ImportError:
    # If nis_service not found, this is expected during migration
    pass
