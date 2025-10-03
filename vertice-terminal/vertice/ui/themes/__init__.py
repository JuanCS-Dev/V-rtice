"""
Vértice UI Themes
Design system e temas para interface TUI
"""

from .vertice_design_system import (
    ColorPalette,
    Typography,
    Spacing,
    Animation,
    Symbols,
    VerticeTheme,
    THEME
)
from .theme_manager import theme_manager
from .cyberpunk import CYBERPUNK_THEME
from .matrix import MATRIX_THEME
from .minimal_dark import MINIMAL_DARK_THEME

__all__ = [
    "ColorPalette",
    "Typography",
    "Spacing",
    "Animation",
    "Symbols",
    "VerticeTheme",
    "THEME",
    "theme_manager",
    "CYBERPUNK_THEME",
    "MATRIX_THEME",
    "MINIMAL_DARK_THEME",
]
