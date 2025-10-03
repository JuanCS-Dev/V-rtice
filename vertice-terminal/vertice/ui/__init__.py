"""
Vértice UI - Text User Interface
Interface primorosa que supera Gemini CLI
✅ PRODUCTION READY - ZERO MOCKS
"""

from .app import VerticeApp, run_tui
from .themes import THEME, theme_manager
from .animations import (
    FadeAnimation,
    SlideAnimation,
    PulseAnimation,
    ShakeAnimation,
    TypewriterAnimation,
    GlowAnimation,
    animate_widget_enter,
    animate_success,
    animate_error,
    animate_loading
)

__all__ = [
    "VerticeApp",
    "run_tui",
    "THEME",
    "theme_manager",
    "FadeAnimation",
    "SlideAnimation",
    "PulseAnimation",
    "ShakeAnimation",
    "TypewriterAnimation",
    "GlowAnimation",
    "animate_widget_enter",
    "animate_success",
    "animate_error",
    "animate_loading",
]
