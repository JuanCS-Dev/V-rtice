"""
🟢 MATRIX THEME - Tema Matrix Completo
Green on black, hacker aesthetic
IMPLEMENTAÇÃO REAL - ZERO MOCKS
"""

from dataclasses import dataclass


@dataclass
class MatrixTheme:
    """Tema Matrix - Verde no Preto Clássico"""

    # Cores Primárias (Matrix Green)
    PRIMARY: str = "#00ff41"        # Verde Matrix brilhante
    SECONDARY: str = "#00cc33"      # Verde Matrix médio
    ACCENT: str = "#008f11"         # Verde Matrix escuro

    # Backgrounds
    BG_PRIMARY: str = "#000000"     # Preto puro
    BG_SECONDARY: str = "#001100"   # Verde muito escuro
    BG_PANEL: str = "#002200"       # Verde escuro
    BG_HOVER: str = "#003300"       # Verde hover
    BG_ACTIVE: str = "#004400"      # Verde ativo

    # Texto
    TEXT_PRIMARY: str = "#00ff41"   # Verde brilhante
    TEXT_SECONDARY: str = "#00cc33" # Verde médio
    TEXT_MUTED: str = "#008f11"     # Verde escuro
    TEXT_DIM: str = "#006611"       # Verde dim

    # Status
    SUCCESS: str = "#00ff41"        # Verde Matrix
    WARNING: str = "#ffff00"        # Amarelo (único colorido)
    ERROR: str = "#ff0000"          # Vermelho (único colorido)
    INFO: str = "#00cc33"           # Verde médio

    # Bordas
    BORDER_PRIMARY: str = "#00ff41"
    BORDER_SECONDARY: str = "#00cc33"
    BORDER_SUBTLE: str = "#006611"

    # Gradiente (tons de verde)
    GRADIENT_START: str = "#00ff41"
    GRADIENT_MID: str = "#00cc33"
    GRADIENT_END: str = "#008f11"

    def get_gradient_colors(self) -> list[str]:
        """Retorna cores do gradiente"""
        return [self.GRADIENT_START, self.GRADIENT_MID, self.GRADIENT_END]

    def get_css(self) -> str:
        """Retorna CSS do tema"""
        return f"""
        /* Matrix Theme */
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
MATRIX_THEME = MatrixTheme()
