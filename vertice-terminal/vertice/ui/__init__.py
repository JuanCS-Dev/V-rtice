"""
Vértice UI - Text User Interface
Interface primorosa que supera Gemini CLI
"""

from .app import VerticeApp, run_tui
from .themes import THEME

__all__ = ["VerticeApp", "run_tui", "THEME"]
