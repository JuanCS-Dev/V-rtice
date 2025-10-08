"""Temperature Controller - Homeostatic Temperature Regulation

Extracted from LinfonodoDigital as part of FASE 3 Desacoplamento.

This module implements temperature-based homeostatic regulation including
temperature monitoring, decay, state computation, and activation level management.

Responsibilities:
- Temperature adjustment (inflammation/anti-inflammation)
- Temperature decay (anti-inflammatory drift)
- Homeostatic state computation (Repouso → Inflamação)
- Activation level calculation (agent wake/sleep percentages)
- Temperature monitoring loop

Biological Inspiration:
-----------------------
In biological systems, body temperature reflects immune activation:
- Normal (36.5-37.0°C): Homeostasis, minimal immune activity
- Fever (37.0-39.0°C): Immune activation, enhanced pathogen clearance
- High fever (39.0+°C): Cytokine storm, systemic inflammation
- Temperature decay: Anti-inflammatory feedback mechanisms

This digital implementation mirrors these biological mechanisms, using
temperature as a proxy for immune system activation level.

NO MOCK, NO PLACEHOLDER, NO TODO - Production ready.
DOUTRINA VERTICE compliant: Quality-first, production-ready code.

Authors: Juan & Claude Code
Version: 1.0.0
Date: 2025-10-07
"""

import logging
from enum import Enum
from typing import Any, Dict

from coordination.thread_safe_structures import ThreadSafeTemperature

logger = logging.getLogger(__name__)


class HomeostaticState(str, Enum):
    """Homeostatic states based on temperature."""

    REPOUSO = "repouso"  # 36.5-37.0°C: Homeostasis
    VIGILANCIA = "vigilancia"  # 37.0-37.5°C: Low-level surveillance
    ATENCAO = "atencao"  # 37.5-38.0°C: Increased attention
    ATIVACAO = "ativacao"  # 38.0-39.0°C: Active immune response
    INFLAMACAO = "inflamacao"  # 39.0+°C: Inflammation (cytokine storm)


class TemperatureController:
    """Controls homeostatic temperature and activation levels.

    This class implements temperature regulation logic extracted from
    LinfonodoDigital, including temperature adjustment, decay, state
    computation, and activation level management.

    Attributes:
        lymphnode_id: Lymphnode identifier
        temperature: ThreadSafeTemperature instance
        decay_rate: Temperature decay rate per cycle (default 0.98 = 2% decay)
        decay_interval_sec: Interval between decay cycles (default 30s)

    Example:
        >>> controller = TemperatureController(
        ...     lymphnode_id="lymph-1",
        ...     initial_temp=37.0,
        ... )
        >>> await controller.adjust_temperature(delta=+0.5)
        >>> state = await controller.get_homeostatic_state()
        >>> assert state == HomeostaticState.VIGILANCIA
    """

    # Temperature thresholds for homeostatic states
    THRESHOLD_INFLAMACAO = 39.0
    THRESHOLD_ATIVACAO = 38.0
    THRESHOLD_ATENCAO = 37.5
    THRESHOLD_VIGILANCIA = 37.0

    # Activation percentages per state
    ACTIVATION_INFLAMACAO = 0.8  # 80% agents active
    ACTIVATION_ATIVACAO = 0.5  # 50% agents active
    ACTIVATION_ATENCAO = 0.3  # 30% agents active
    ACTIVATION_VIGILANCIA = 0.15  # 15% agents active
    ACTIVATION_REPOUSO = 0.05  # 5% agents active

    def __init__(
        self,
        lymphnode_id: str,
        initial_temp: float = 37.0,
        min_temp: float = 36.0,
        max_temp: float = 42.0,
        decay_rate: float = 0.98,
        decay_interval_sec: float = 30.0,
    ):
        """Initialize TemperatureController.

        Args:
            lymphnode_id: Unique lymphnode identifier
            initial_temp: Initial temperature (default 37.0°C)
            min_temp: Minimum temperature (default 36.0°C)
            max_temp: Maximum temperature (default 42.0°C)
            decay_rate: Decay multiplier per cycle (default 0.98 = 2% decay)
            decay_interval_sec: Interval between decay cycles (default 30s)
        """
        self.lymphnode_id = lymphnode_id
        self.decay_rate = decay_rate
        self.decay_interval_sec = decay_interval_sec

        # Thread-safe temperature
        self.temperature = ThreadSafeTemperature(
            initial=initial_temp,
            min_temp=min_temp,
            max_temp=max_temp,
        )

        logger.info(
            f"TemperatureController initialized: "
            f"lymphnode={lymphnode_id}, temp={initial_temp}°C, "
            f"decay_rate={decay_rate}"
        )

    async def adjust_temperature(self, delta: float) -> float:
        """Adjust regional temperature.

        EXTRACTED from lymphnode.py:_adjust_temperature() (lines 316-329)

        Args:
            delta: Temperature change (positive = increase, negative = decrease)

        Returns:
            New temperature value
        """
        old_temp = await self.temperature.get()
        new_temp = await self.temperature.adjust(delta)

        logger.info(f"Lymphnode {self.lymphnode_id} temperature: {old_temp:.1f}°C → {new_temp:.1f}°C")

        return new_temp

    async def apply_decay(self) -> float:
        """Apply temperature decay (anti-inflammatory drift).

        EXTRACTED from lymphnode.py:_monitor_temperature() (line 831)

        Returns:
            New temperature value after decay
        """
        old_temp = await self.temperature.get()
        new_temp = await self.temperature.multiply(self.decay_rate)

        logger.debug(f"Lymphnode {self.lymphnode_id} temperature decay: {old_temp:.1f}°C → {new_temp:.1f}°C")

        return new_temp

    async def get_homeostatic_state(self) -> HomeostaticState:
        """Compute homeostatic state based on current temperature.

        EXTRACTED from lymphnode.py:get_homeostatic_state() (lines 195-213)

        Returns:
            HomeostaticState enum value
        """
        temp = await self.temperature.get()

        if temp >= self.THRESHOLD_INFLAMACAO:
            return HomeostaticState.INFLAMACAO
        elif temp >= self.THRESHOLD_ATIVACAO:
            return HomeostaticState.ATIVACAO
        elif temp >= self.THRESHOLD_ATENCAO:
            return HomeostaticState.ATENCAO
        elif temp >= self.THRESHOLD_VIGILANCIA:
            return HomeostaticState.VIGILANCIA
        else:
            return HomeostaticState.REPOUSO

    async def get_target_activation_percentage(self) -> float:
        """Get target activation percentage for current state.

        EXTRACTED from lymphnode.py:_regulate_homeostasis() (lines 869-887)

        Returns:
            Target activation percentage (0.0-1.0)
        """
        temp = await self.temperature.get()

        if temp >= self.THRESHOLD_INFLAMACAO:
            return self.ACTIVATION_INFLAMACAO
        elif temp >= self.THRESHOLD_ATIVACAO:
            return self.ACTIVATION_ATIVACAO
        elif temp >= self.THRESHOLD_ATENCAO:
            return self.ACTIVATION_ATENCAO
        elif temp >= self.THRESHOLD_VIGILANCIA:
            return self.ACTIVATION_VIGILANCIA
        else:
            return self.ACTIVATION_REPOUSO

    async def calculate_target_active_agents(self, total_agents: int) -> int:
        """Calculate target number of active agents.

        EXTRACTED from lymphnode.py:_regulate_homeostasis() (line 889)

        Args:
            total_agents: Total number of agents available

        Returns:
            Target number of active agents
        """
        percentage = await self.get_target_activation_percentage()
        return int(total_agents * percentage)

    async def get_current_temperature(self) -> float:
        """Get current temperature.

        Returns:
            Current temperature in °C
        """
        return await self.temperature.get()

    async def set_temperature(self, value: float) -> float:
        """Set temperature to specific value.

        Args:
            value: Temperature value to set

        Returns:
            New temperature (may be clamped to min/max)
        """
        await self.temperature.set(value)
        return await self.temperature.get()

    def get_state_name(self, state: HomeostaticState) -> str:
        """Get human-readable name for homeostatic state.

        Args:
            state: HomeostaticState enum

        Returns:
            Uppercase state name
        """
        return state.value.upper()

    async def get_stats(self) -> Dict[str, Any]:
        """Get temperature controller statistics.

        Returns:
            Dict with temperature stats
        """
        current_temp = await self.temperature.get()
        state = await self.get_homeostatic_state()
        activation_pct = await self.get_target_activation_percentage()

        return {
            "lymphnode_id": self.lymphnode_id,
            "current_temperature": current_temp,
            "homeostatic_state": state.value,
            "target_activation_percentage": activation_pct,
            "decay_rate": self.decay_rate,
            "decay_interval_sec": self.decay_interval_sec,
            "temperature_config": {
                "min": self.temperature._min,
                "max": self.temperature._max,
            },
        }

    def __repr__(self) -> str:
        import asyncio

        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                temp_str = "?.?°C"
            else:
                temp = loop.run_until_complete(self.temperature.get())
                temp_str = f"{temp:.1f}°C"
        except:
            temp_str = "?.?°C"

        return f"TemperatureController(lymphnode={self.lymphnode_id}, temp={temp_str})"
