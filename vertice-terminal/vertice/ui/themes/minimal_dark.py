"""
⚫ MINIMAL DARK THEME - Tema Minimalista Escuro
Black & white, ultra clean, professional
IMPLEMENTAÇÃO REAL - ZERO MOCKS
"""

from dataclasses import dataclass


@dataclass
class MinimalDarkTheme:
    """Tema Minimalista Escuro - Preto e Branco Elegante"""

    # Cores Primárias (Monocromático)
    PRIMARY: str = "#ffffff"        # Branco puro
    SECONDARY: str = "#e0e0e0"      # Cinza muito claro
    ACCENT: str = "#b0b0b0"         # Cinza claro

    # Backgrounds
    BG_PRIMARY: str = "#000000"     # Preto puro
    BG_SECONDARY: str = "#0a0a0a"   # Preto quase puro
    BG_PANEL: str = "#1a1a1a"       # Cinza muito escuro
    BG_HOVER: str = "#2a2a2a"       # Cinza escuro hover
    BG_ACTIVE: str = "#3a3a3a"      # Cinza escuro ativo

    # Texto
    TEXT_PRIMARY: str = "#ffffff"
    TEXT_SECONDARY: str = "#e0e0e0"
    TEXT_MUTED: str = "#888888"
    TEXT_DIM: str = "#555555"

    # Status (minimalista)
    SUCCESS: str = "#ffffff"        # Branco
    WARNING: str = "#cccccc"        # Cinza claro
    ERROR: str = "#888888"          # Cinza médio
    INFO: str = "#aaaaaa"           # Cinza

    # Bordas
    BORDER_PRIMARY: str = "#ffffff"
    BORDER_SECONDARY: str = "#888888"
    BORDER_SUBTLE: str = "#333333"

    # Gradiente (tons de cinza)
    GRADIENT_START: str = "#ffffff"
    GRADIENT_MID: str = "#b0b0b0"
    GRADIENT_END: str = "#606060"

    def get_gradient_colors(self) -> list[str]:
        """Retorna cores do gradiente"""
        return [self.GRADIENT_START, self.GRADIENT_MID, self.GRADIENT_END]

    def get_css(self) -> str:
        """Retorna CSS do tema"""
        return f"""
        /* Minimal Dark Theme */
        $primary: {self.PRIMARY};
        $secondary: {self.SECONDARY};
        $accent: {self.ACCENT};

        $background: {self.BG_PRIMARY};
        $surface: {self.BG_SECONDARY};
        $panel: {self.BG_PANEL};

        $text: {self.TEXT_PRIMARY};
        $text-muted: {self.TEXT_MUTED};

        $success: {self.SUCCESS};
        $warning: {self.WARNING};
        $error: {self.ERROR};
        $info: {self.INFO};

        $border: {self.BORDER_PRIMARY};
        $border-subtle: {self.BORDER_SUBTLE};
        """


# Instância global
MINIMAL_DARK_THEME = MinimalDarkTheme()
