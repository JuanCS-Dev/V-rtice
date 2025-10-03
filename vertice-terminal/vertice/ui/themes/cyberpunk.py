"""
🌃 CYBERPUNK THEME - Tema Cyberpunk Completo
Neon colors, high contrast, futuristic
IMPLEMENTAÇÃO REAL - ZERO MOCKS
"""

from dataclasses import dataclass


@dataclass
class CyberpunkTheme:
    """Tema Cyberpunk - Neon e High Tech"""

    # Cores Primárias (Neon)
    PRIMARY: str = "#ff00ff"        # Magenta neon
    SECONDARY: str = "#00ffff"      # Ciano neon
    ACCENT: str = "#ffff00"         # Amarelo neon

    # Backgrounds
    BG_PRIMARY: str = "#0a0014"     # Roxo muito escuro
    BG_SECONDARY: str = "#1a0028"   # Roxo escuro
    BG_PANEL: str = "#280040"       # Roxo médio escuro
    BG_HOVER: str = "#350055"       # Roxo hover
    BG_ACTIVE: str = "#420066"      # Roxo ativo

    # Texto
    TEXT_PRIMARY: str = "#ffffff"
    TEXT_SECONDARY: str = "#e0e0e0"
    TEXT_MUTED: str = "#a0a0a0"
    TEXT_DIM: str = "#707070"

    # Status
    SUCCESS: str = "#00ff00"        # Verde neon
    WARNING: str = "#ff9900"        # Laranja neon
    ERROR: str = "#ff0066"          # Rosa neon
    INFO: str = "#00ccff"           # Azul neon

    # Bordas
    BORDER_PRIMARY: str = "#ff00ff"
    BORDER_SECONDARY: str = "#00ffff"
    BORDER_SUBTLE: str = "#660099"

    # Gradiente
    GRADIENT_START: str = "#ff00ff"
    GRADIENT_MID: str = "#00ffff"
    GRADIENT_END: str = "#ffff00"

    def get_gradient_colors(self) -> list[str]:
        """Retorna cores do gradiente"""
        return [self.GRADIENT_START, self.GRADIENT_MID, self.GRADIENT_END]

    def get_css(self) -> str:
        """Retorna CSS do tema"""
        return f"""
        /* Cyberpunk Theme */
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
CYBERPUNK_THEME = CyberpunkTheme()
