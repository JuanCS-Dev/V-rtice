"""
🎨 Theme Manager - Sistema de Gerenciamento de Temas
Troca de temas em tempo real
IMPLEMENTAÇÃO REAL - ZERO MOCKS
"""

from typing import Dict, Any, Optional
from pathlib import Path
import json

from .vertice_design_system import VerticeTheme, THEME
from .cyberpunk import CYBERPUNK_THEME
from .matrix import MATRIX_THEME
from .minimal_dark import MINIMAL_DARK_THEME


class ThemeManager:
    """
    Gerenciador de temas REAL.
    Salva preferência, troca em tempo real, suporta temas customizados.
    """

    # Temas disponíveis
    THEMES = {
        "vertice": THEME,           # Padrão: Verde → Azul
        "cyberpunk": CYBERPUNK_THEME,  # Magenta → Ciano → Amarelo
        "matrix": MATRIX_THEME,        # Verde Matrix
        "minimal": MINIMAL_DARK_THEME, # Preto e Branco
    }

    def __init__(self):
        self.current_theme_name = "vertice"
        self.current_theme = self.THEMES[self.current_theme_name]
        self.config_path = Path.home() / ".vertice" / "theme_config.json"

        # Carrega tema salvo
        self._load_saved_theme()

    def _load_saved_theme(self) -> None:
        """Carrega tema salvo do arquivo de config"""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                    theme_name = config.get('theme', 'vertice')

                    if theme_name in self.THEMES:
                        self.current_theme_name = theme_name
                        self.current_theme = self.THEMES[theme_name]
            except Exception:
                # Se falhar, usa padrão
                pass

    def _save_theme(self) -> None:
        """Salva tema atual no arquivo de config"""
        # Cria diretório se não existe
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(self.config_path, 'w') as f:
                json.dump({'theme': self.current_theme_name}, f)
        except Exception:
            # Falha silenciosa
            pass

    def set_theme(self, theme_name: str) -> bool:
        """
        Define tema atual.

        Args:
            theme_name: Nome do tema ('vertice', 'cyberpunk', 'matrix', 'minimal')

        Returns:
            True se tema foi alterado, False se tema não existe
        """
        if theme_name not in self.THEMES:
            return False

        self.current_theme_name = theme_name
        self.current_theme = self.THEMES[theme_name]

        # Salva preferência
        self._save_theme()

        return True

    def get_current_theme(self) -> Any:
        """Retorna tema atual"""
        return self.current_theme

    def get_theme_name(self) -> str:
        """Retorna nome do tema atual"""
        return self.current_theme_name

    def get_available_themes(self) -> list[str]:
        """Retorna lista de temas disponíveis"""
        return list(self.THEMES.keys())

    def get_theme_colors(self) -> Dict[str, str]:
        """Retorna dicionário de cores do tema atual"""
        theme = self.current_theme

        # Para VerticeTheme (tema padrão)
        if hasattr(theme, 'colors'):
            return {
                'primary': theme.colors.VERDE_NEON,
                'secondary': theme.colors.CIANO_BRILHO,
                'accent': theme.colors.AZUL_PROFUNDO,
                'background': theme.colors.BG_PRIMARY,
                'surface': theme.colors.BG_SECONDARY,
                'panel': theme.colors.BG_PANEL,
                'text': theme.colors.BRANCO,
                'text_muted': theme.colors.CINZA_TEXTO,
                'success': theme.colors.SUCCESS,
                'warning': theme.colors.WARNING,
                'error': theme.colors.ERROR,
                'info': theme.colors.INFO,
                'border': theme.colors.CIANO_BRILHO,
                'border_subtle': theme.colors.CINZA_MEDIO,
            }
        # Para outros temas (dataclass)
        else:
            return {
                'primary': theme.PRIMARY,
                'secondary': theme.SECONDARY,
                'accent': theme.ACCENT,
                'background': theme.BG_PRIMARY,
                'surface': theme.BG_SECONDARY,
                'panel': theme.BG_PANEL,
                'text': theme.TEXT_PRIMARY,
                'text_muted': theme.TEXT_MUTED,
                'success': theme.SUCCESS,
                'warning': theme.WARNING,
                'error': theme.ERROR,
                'info': theme.INFO,
                'border': theme.BORDER_PRIMARY,
                'border_subtle': theme.BORDER_SUBTLE,
            }

    def get_gradient_colors(self) -> list[str]:
        """Retorna cores do gradiente do tema atual"""
        return self.current_theme.get_gradient_colors()

    def get_css(self) -> str:
        """Retorna CSS do tema atual para aplicação"""
        theme = self.current_theme

        if hasattr(theme, 'get_css'):
            # Temas novos têm método get_css
            return theme.get_css()
        else:
            # Tema padrão (VerticeTheme)
            colors = self.get_theme_colors()
            return f"""
            $primary: {colors['primary']};
            $secondary: {colors['secondary']};
            $accent: {colors['accent']};

            $background: {colors['background']};
            $surface: {colors['surface']};
            $panel: {colors['panel']};

            $text: {colors['text']};
            $text-muted: {colors['text_muted']};

            $success: {colors['success']};
            $warning: {colors['warning']};
            $error: {colors['error']};
            $info: {colors['info']};

            $border: {colors['border']};
            $border-subtle: {colors['border_subtle']};
            """

    def get_theme_description(self, theme_name: str) -> str:
        """Retorna descrição do tema"""
        descriptions = {
            "vertice": "🌈 Verde → Azul | Gradiente primoroso padrão",
            "cyberpunk": "🌃 Neon | Magenta → Ciano → Amarelo futurista",
            "matrix": "🟢 Matrix | Verde clássico no preto",
            "minimal": "⚫ Minimal | Preto e branco ultra limpo",
        }
        return descriptions.get(theme_name, "Tema customizado")


# Instância global
theme_manager = ThemeManager()
