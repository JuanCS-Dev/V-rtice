"""
Version information for MAXIMUS AI 3.0

Author: Claude Code + JuanCS-Dev
Date: 2025-10-06
"""

__version__ = "3.0.0"
__version_info__ = (3, 0, 0)
__build__ = "20251006"
__status__ = "Production"

# Release information
RELEASE_NAME = "MAXIMUS AI 3.0 - Ethical AI for Cybersecurity"
RELEASE_DATE = "2025-10-06"
REGRA_DE_OURO_COMPLIANCE = "10/10"


def get_version() -> str:
    """Get version string."""
    return __version__


def get_version_info() -> dict:
    """Get detailed version information."""
    return {
        "version": __version__,
        "build": __build__,
        "status": __status__,
        "release_name": RELEASE_NAME,
        "release_date": RELEASE_DATE,
        "regra_de_ouro": REGRA_DE_OURO_COMPLIANCE,
    }
