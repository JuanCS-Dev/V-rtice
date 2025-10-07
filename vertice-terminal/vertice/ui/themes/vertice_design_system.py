"""
🎨 VÉRTICE DESIGN SYSTEM
Design system completo baseado no gradiente primoroso Verde → Azul
Inspirado no Gemini CLI mas MELHOR
"""

from dataclasses import dataclass
from typing import Dict


@dataclass
class ColorPalette:
    """
    Paleta de cores oficial Vértice - Gradiente Verde → Azul
    Alinhada ao Blueprint UI/UX v1.2 (Gemini-style refinado)
    """

    # Cores Primárias (Gradiente Principal) - Mantidas do design original
    VERDE_NEON: str = "#00ff87"      # Início do gradiente
    CIANO_BRILHO: str = "#00d4ff"    # Meio
    AZUL_PROFUNDO: str = "#0080ff"   # Fim
    AZUL_ESCURO: str = "#0040ff"     # Sombra profunda
    AZUL_NOTURNO: str = "#0020ff"    # Mais escuro

    # Cores Secundárias
    VERDE_AGUA: str = "#00ffcc"      # Variação verde-ciano
    CIANO_CLARO: str = "#66e0ff"     # Ciano mais claro
    AZUL_CELESTE: str = "#4da6ff"    # Azul médio

    # Texto (Blueprint refinado - Rich color names)
    TEXTO_PRIMARIO: str = "bright_white"    # Texto principal (Rich)
    TEXTO_SECUNDARIO: str = "grey70"        # Texto secundário (Rich)
    BRANCO: str = "#ffffff"                 # Hex fallback
    CINZA_TEXTO: str = "#888888"            # Hex fallback

    # Neutros (Backgrounds)
    PRETO: str = "#000000"
    CINZA_ESCURO: str = "#1a1a1a"
    CINZA_MEDIO: str = "#2d2d2d"
    CINZA_CLARO: str = "#4a4a4a"
    BG_PRIMARY: str = "#0a0a0a"      # Fundo principal (quase preto)
    BG_SECONDARY: str = "#121212"    # Fundo secundário
    BG_PANEL: str = "#1a1a1a"        # Painéis
    BG_HOVER: str = "#252525"        # Hover states
    BG_ACTIVE: str = "#2d2d2d"       # Active states

    # Status Colors (Blueprint refinado)
    SUCCESS: str = "green_yellow"           # Rich name (Blueprint)
    SUCCESS_HEX: str = "#adff2f"            # Hex equivalente
    ERROR: str = "bright_red"               # Rich name (Blueprint)
    ERROR_HEX: str = "#ff0000"              # Hex equivalente
    WARNING: str = "gold1"                  # Rich name (Blueprint)
    WARNING_HEX: str = "#ffd700"            # Hex equivalente
    INFO: str = "#00d4ff"                   # Mantido do original

    # Acentos (Blueprint refinado)
    ACENTO_PRINCIPAL: str = "deep_sky_blue1"   # Rich name (Blueprint)
    ACENTO_SECUNDARIO: str = "medium_purple"   # Rich name (Blueprint)

    # Bordas (Blueprint refinado)
    BORDA_PADRAO: str = "grey50"            # Rich name (Blueprint)
    BORDA_PANEL: str = "#4a4a4a"            # Hex fallback


@dataclass
class Typography:
    """Sistema de tipografia - Monoespaçadas premium"""

    # Font Families (ordem de preferência)
    FONT_MONO: tuple = (
        "JetBrains Mono",
        "Fira Code",
        "Source Code Pro",
        "Monaco",
        "Consolas",
        "monospace"
    )

    # Font Sizes (em caracteres/linhas para terminal)
    SIZE_TINY: int = 8
    SIZE_SMALL: int = 10
    SIZE_NORMAL: int = 12
    SIZE_LARGE: int = 14
    SIZE_XLARGE: int = 16
    SIZE_HUGE: int = 20

    # Line Heights
    LINE_HEIGHT_TIGHT: float = 1.2
    LINE_HEIGHT_NORMAL: float = 1.5
    LINE_HEIGHT_RELAXED: float = 1.8


@dataclass
class Spacing:
    """Sistema de espaçamento - Base 4px"""

    # Spacing Scale (multiplicadores de 4px)
    NONE: int = 0
    XXS: int = 1    # 4px
    XS: int = 2     # 8px
    SM: int = 3     # 12px
    MD: int = 4     # 16px
    LG: int = 6     # 24px
    XL: int = 8     # 32px
    XXL: int = 12   # 48px
    MAX_SPACING: int = 16  # 64px


class Animation:
    """Configurações de animação e timing"""

    # Durations (em milissegundos)
    INSTANT: int = 0
    FAST: int = 150
    NORMAL: int = 250
    SLOW: int = 400
    VERY_SLOW: int = 600

    # Easing functions (CSS-like)
    EASE_IN: str = "ease-in"
    EASE_OUT: str = "ease-out"
    EASE_IN_OUT: str = "ease-in-out"
    LINEAR: str = "linear"

    # Spinners (tuples são imutáveis)
    SPINNER_DOTS: tuple = ('⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏')
    SPINNER_LINE: tuple = ('─', '\\', '|', '/')
    SPINNER_CLOCK: tuple = ('🕐', '🕑', '🕒', '🕓', '🕔', '🕕', '🕖', '🕗', '🕘', '🕙', '🕚', '🕛')
    SPINNER_ARROW: tuple = ('←', '↖', '↑', '↗', '→', '↘', '↓', '↙')


@dataclass
class Symbols:
    """Símbolos Unicode elegantes"""

    # Status
    SUCCESS: str = "✓"
    ERROR: str = "✗"
    WARNING: str = "⚠"
    INFO: str = "ℹ"
    QUESTION: str = "?"

    # UI Elements
    ARROW_RIGHT: str = "→"
    ARROW_LEFT: str = "←"
    ARROW_UP: str = "↑"
    ARROW_DOWN: str = "↓"
    BULLET: str = "•"
    DIAMOND: str = "◆"
    SQUARE: str = "■"
    CIRCLE: str = "●"

    # Progress
    PROGRESS_FULL: str = "█"
    PROGRESS_EMPTY: str = "░"
    PROGRESS_PARTIAL: str = "▓"

    # Borders (Box Drawing)
    BOX_TOP_LEFT: str = "╭"
    BOX_TOP_RIGHT: str = "╮"
    BOX_BOTTOM_LEFT: str = "╰"
    BOX_BOTTOM_RIGHT: str = "╯"
    BOX_HORIZONTAL: str = "─"
    BOX_VERTICAL: str = "│"
    BOX_CROSS: str = "┼"


class VerticeTheme:
    """Tema principal Vértice - Cyberpunk Elegante"""

    def __init__(self):
        self.colors = ColorPalette()
        self.typography = Typography()
        self.spacing = Spacing()
        self.animation = Animation()
        self.symbols = Symbols()

    def get_gradient_colors(self) -> list[str]:
        """Retorna lista de cores do gradiente principal"""
        return [
            self.colors.VERDE_NEON,
            self.colors.CIANO_BRILHO,
            self.colors.AZUL_PROFUNDO
        ]

    def get_theme_dict(self) -> Dict[str, str]:
        """
        Retorna tema como dicionário para Textual
        Alinhado ao Blueprint UI/UX v1.2
        """
        return {
            # Primary colors
            "primary": self.colors.VERDE_NEON,
            "secondary": self.colors.CIANO_BRILHO,
            "accent": self.colors.ACENTO_PRINCIPAL,

            # Backgrounds
            "background": self.colors.BG_PRIMARY,
            "surface": self.colors.BG_SECONDARY,
            "panel": self.colors.BG_PANEL,

            # Text (usando Rich color names do Blueprint)
            "text": self.colors.TEXTO_PRIMARIO,
            "text-muted": self.colors.TEXTO_SECUNDARIO,

            # Status (usando Rich color names do Blueprint)
            "success": self.colors.SUCCESS,
            "warning": self.colors.WARNING,
            "error": self.colors.ERROR,
            "info": self.colors.INFO,

            # Borders (usando Rich color names do Blueprint)
            "border": self.colors.BORDA_PADRAO,
            "border-subtle": self.colors.CINZA_MEDIO,
        }


# Instância global do tema
THEME = VerticeTheme()

# Export conveniente
__all__ = [
    "ColorPalette",
    "Typography",
    "Spacing",
    "Animation",
    "Symbols",
    "VerticeTheme",
    "THEME"
]
