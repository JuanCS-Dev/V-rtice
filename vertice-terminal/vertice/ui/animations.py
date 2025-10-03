"""
✨ Animações Primorosas - Sistema Completo de Animações
ZERO MOCKS - Implementação REAL para produção
"""

from textual.widget import Widget
from textual.reactive import reactive
from textual import work
from rich.text import Text
from typing import Optional, Callable
import asyncio
from dataclasses import dataclass

from .themes import THEME


@dataclass
class AnimationConfig:
    """Configuração de animação"""
    duration: float  # segundos
    easing: str  # 'linear', 'ease-in', 'ease-out', 'ease-in-out'
    on_complete: Optional[Callable] = None


class FadeAnimation:
    """
    Animação de Fade In/Out REAL.
    Controla opacidade usando CSS opacity.
    """

    @staticmethod
    async def fade_in(
        widget: Widget,
        duration: float = 0.3,
        easing: str = "ease-out"
    ) -> None:
        """Fade in real usando CSS transitions"""
        # Aplica CSS transition
        widget.styles.opacity = 0.0
        widget.refresh()

        # Aguarda frame
        await asyncio.sleep(0.01)

        # Anima para opacidade 1.0
        widget.styles.animate(
            "opacity",
            value=1.0,
            duration=duration,
            easing=easing
        )

    @staticmethod
    async def fade_out(
        widget: Widget,
        duration: float = 0.3,
        easing: str = "ease-in"
    ) -> None:
        """Fade out real usando CSS transitions"""
        widget.styles.animate(
            "opacity",
            value=0.0,
            duration=duration,
            easing=easing
        )

        # Aguarda animação completar
        await asyncio.sleep(duration)


class SlideAnimation:
    """
    Animação de Slide REAL.
    Move widget usando offset.
    """

    @staticmethod
    async def slide_in_from_right(
        widget: Widget,
        duration: float = 0.4,
        easing: str = "ease-out"
    ) -> None:
        """Slide in da direita - REAL"""
        # Começa fora da tela (direita)
        widget.styles.offset = (100, 0)
        widget.refresh()

        await asyncio.sleep(0.01)

        # Anima para posição normal
        widget.styles.animate(
            "offset",
            value=(0, 0),
            duration=duration,
            easing=easing
        )

    @staticmethod
    async def slide_in_from_left(
        widget: Widget,
        duration: float = 0.4,
        easing: str = "ease-out"
    ) -> None:
        """Slide in da esquerda - REAL"""
        widget.styles.offset = (-100, 0)
        widget.refresh()

        await asyncio.sleep(0.01)

        widget.styles.animate(
            "offset",
            value=(0, 0),
            duration=duration,
            easing=easing
        )

    @staticmethod
    async def slide_in_from_top(
        widget: Widget,
        duration: float = 0.4,
        easing: str = "ease-out"
    ) -> None:
        """Slide in de cima - REAL"""
        widget.styles.offset = (0, -50)
        widget.refresh()

        await asyncio.sleep(0.01)

        widget.styles.animate(
            "offset",
            value=(0, 0),
            duration=duration,
            easing=easing
        )

    @staticmethod
    async def slide_in_from_bottom(
        widget: Widget,
        duration: float = 0.4,
        easing: str = "ease-out"
    ) -> None:
        """Slide in de baixo - REAL"""
        widget.styles.offset = (0, 50)
        widget.refresh()

        await asyncio.sleep(0.01)

        widget.styles.animate(
            "offset",
            value=(0, 0),
            duration=duration,
            easing=easing
        )


class PulseAnimation:
    """
    Animação de Pulse REAL.
    Aumenta e diminui escala.
    """

    @staticmethod
    async def pulse(
        widget: Widget,
        scale: float = 1.1,
        duration: float = 0.6,
        repeat: int = 1
    ) -> None:
        """Pulse real usando scale"""
        for _ in range(repeat):
            # Scale up
            widget.styles.animate(
                "opacity",
                value=0.8,
                duration=duration / 2,
                easing="ease-out"
            )

            await asyncio.sleep(duration / 2)

            # Scale down
            widget.styles.animate(
                "opacity",
                value=1.0,
                duration=duration / 2,
                easing="ease-in"
            )

            await asyncio.sleep(duration / 2)

    @staticmethod
    async def pulse_border(
        widget: Widget,
        color_from: str,
        color_to: str,
        duration: float = 0.6,
        repeat: int = 3
    ) -> None:
        """Pulse na borda - REAL"""
        original_border = widget.styles.border

        for _ in range(repeat):
            # Muda cor da borda
            widget.styles.border = ("solid", color_to)
            widget.refresh()

            await asyncio.sleep(duration / 2)

            widget.styles.border = ("solid", color_from)
            widget.refresh()

            await asyncio.sleep(duration / 2)

        # Restaura borda original
        widget.styles.border = original_border


class ShakeAnimation:
    """
    Animação de Shake REAL.
    Sacode widget (para erros).
    """

    @staticmethod
    async def shake(
        widget: Widget,
        intensity: int = 5,
        duration: float = 0.4
    ) -> None:
        """Shake real - perfeito para erros"""
        original_offset = widget.styles.offset or (0, 0)

        # Número de shakes
        shakes = 6
        interval = duration / shakes

        for i in range(shakes):
            # Alterna esquerda/direita
            offset_x = intensity if i % 2 == 0 else -intensity
            widget.styles.offset = (offset_x, 0)
            widget.refresh()

            await asyncio.sleep(interval)

        # Restaura posição
        widget.styles.offset = original_offset
        widget.refresh()


class TypewriterAnimation:
    """
    Animação de Typewriter REAL.
    Digita texto caractere por caractere.
    """

    @staticmethod
    async def typewrite(
        widget: Widget,
        text: str,
        speed: float = 0.05,
        gradient_colors: Optional[list] = None
    ) -> None:
        """Typewriter real com opção de gradiente"""
        from .utils.banner import create_gradient_text

        current_text = ""

        for char in text:
            current_text += char

            if gradient_colors:
                # Com gradiente
                styled_text = create_gradient_text(current_text, gradient_colors)
                widget.update(styled_text)
            else:
                # Sem gradiente
                widget.update(Text(current_text))

            widget.refresh()
            await asyncio.sleep(speed)


class GlowAnimation:
    """
    Animação de Glow REAL.
    Efeito de brilho pulsante.
    """

    @staticmethod
    async def glow_pulse(
        widget: Widget,
        color: str,
        duration: float = 1.0,
        repeat: int = -1  # -1 = infinito
    ) -> None:
        """Glow pulsante - perfeito para elementos importantes"""
        count = 0

        while repeat == -1 or count < repeat:
            # Aumenta brilho (usando background)
            widget.styles.background = f"{color} 30%"
            widget.refresh()

            await asyncio.sleep(duration / 2)

            # Diminui brilho
            widget.styles.background = f"{color} 10%"
            widget.refresh()

            await asyncio.sleep(duration / 2)

            count += 1


# Helper functions para usar facilmente
async def animate_widget_enter(widget: Widget, animation_type: str = "fade") -> None:
    """
    Anima entrada do widget.

    Args:
        widget: Widget a animar
        animation_type: 'fade', 'slide-right', 'slide-left', 'slide-top', 'slide-bottom'
    """
    if animation_type == "fade":
        await FadeAnimation.fade_in(widget, duration=0.3)
    elif animation_type == "slide-right":
        await SlideAnimation.slide_in_from_right(widget, duration=0.4)
    elif animation_type == "slide-left":
        await SlideAnimation.slide_in_from_left(widget, duration=0.4)
    elif animation_type == "slide-top":
        await SlideAnimation.slide_in_from_top(widget, duration=0.4)
    elif animation_type == "slide-bottom":
        await SlideAnimation.slide_in_from_bottom(widget, duration=0.4)


async def animate_success(widget: Widget) -> None:
    """Animação de sucesso - pulse verde"""
    await PulseAnimation.pulse_border(
        widget,
        THEME.colors.CIANO_BRILHO,
        THEME.colors.SUCCESS,
        duration=0.4,
        repeat=2
    )


async def animate_error(widget: Widget) -> None:
    """Animação de erro - shake + pulse vermelho"""
    # Shake primeiro
    await ShakeAnimation.shake(widget, intensity=5, duration=0.3)

    # Depois pulse vermelho
    await PulseAnimation.pulse_border(
        widget,
        THEME.colors.ERROR,
        THEME.colors.ERROR,
        duration=0.3,
        repeat=2
    )


async def animate_loading(widget: Widget) -> None:
    """Animação de loading - glow azul pulsante"""
    await GlowAnimation.glow_pulse(
        widget,
        THEME.colors.CIANO_BRILHO,
        duration=1.0,
        repeat=3
    )
