"""
Homeostatic Control Loop (HCL)
===============================

Implementação do Sistema Nervoso Autônomo digital.
MAPE-K loop: Monitor → Analyze → Plan → Execute → Knowledge

Analogia Biológica:
- Simpático (SNS): High-performance mode
- Parassimpático (SNPS): Energy-efficient mode
"""

import asyncio
import time
from typing import Dict, Any, Optional, Literal
from datetime import datetime
from pydantic import BaseModel
from enum import Enum


class OperationalMode(str, Enum):
    """Modos operacionais do sistema"""
    HIGH_PERFORMANCE = "high_performance"  # Sympathetic - baixa latência, recursos ilimitados
    BALANCED = "balanced"                   # Equilíbrio adaptativo
    ENERGY_EFFICIENT = "energy_efficient"  # Parasympathetic - conservação de recursos


class SystemState(BaseModel):
    """Estado atual do sistema"""
    timestamp: str
    mode: OperationalMode

    # Metrics
    cpu_usage: float  # 0-100%
    memory_usage: float  # 0-100%
    gpu_usage: Optional[float] = None  # 0-100%
    disk_io: float  # MB/s
    network_io: float  # MB/s

    # Performance
    avg_latency_ms: float
    requests_per_second: float
    error_rate: float  # 0-1

    # Health
    temperature: Optional[float] = None  # Celsius
    uptime_seconds: float

    # Derived
    is_healthy: bool = True
    needs_intervention: bool = False
    recommended_mode: Optional[OperationalMode] = None


class HomeostaticControlLoop:
    """
    Sistema de Auto-Regulação baseado em MAPE-K.

    Mantém o sistema em equilíbrio (homeostase), ajustando
    recursos dinamicamente baseado em carga e objetivos.
    """

    def __init__(
        self,
        check_interval_seconds: float = 5.0,
        enable_auto_scaling: bool = True,
        enable_predictive_allocation: bool = True
    ):
        self.check_interval = check_interval_seconds
        self.enable_auto_scaling = enable_auto_scaling
        self.enable_predictive = enable_predictive_allocation

        # Current state
        self.current_mode = OperationalMode.BALANCED
        self.is_running = False

        # Components (MAPE-K)
        from .system_monitor import SystemMonitor
        from .resource_analyzer import ResourceAnalyzer
        from .resource_planner import ResourcePlanner
        from .resource_executor import ResourceExecutor

        self.monitor = SystemMonitor()
        self.analyzer = ResourceAnalyzer()
        self.planner = ResourcePlanner()
        self.executor = ResourceExecutor()

        # Knowledge Base (histórico de estados)
        self.state_history: list[SystemState] = []
        self.max_history = 1000

        # Control loop task
        self._control_task: Optional[asyncio.Task] = None

    async def start(self):
        """Inicia o loop de controle homeostático"""
        if self.is_running:
            return

        self.is_running = True
        self._control_task = asyncio.create_task(self._control_loop())
        print("🧠 [HCL] Homeostatic Control Loop started")

    async def stop(self):
        """Para o loop de controle"""
        self.is_running = False
        if self._control_task:
            self._control_task.cancel()
            try:
                await self._control_task
            except asyncio.CancelledError:
                pass
        print("🧠 [HCL] Homeostatic Control Loop stopped")

    async def _control_loop(self):
        """
        Loop principal MAPE-K

        Executa continuamente:
        1. Monitor - Coletar métricas do sistema
        2. Analyze - Detectar anomalias e prever demanda
        3. Plan - Decidir ajustes de recursos
        4. Execute - Aplicar mudanças
        5. Knowledge - Armazenar resultado
        """
        while self.is_running:
            try:
                loop_start = time.time()

                # ===== MONITOR =====
                current_state = await self.monitor.collect_metrics()
                current_state.mode = self.current_mode

                # ===== ANALYZE =====
                analysis = await self.analyzer.analyze_state(
                    current_state=current_state,
                    history=self.state_history[-100:]  # Last 100 states
                )

                # ===== PLAN =====
                if analysis.requires_action:
                    plan = await self.planner.create_plan(
                        current_state=current_state,
                        analysis=analysis,
                        current_mode=self.current_mode
                    )

                    # ===== EXECUTE =====
                    if plan:
                        execution_result = await self.executor.execute_plan(plan)

                        # Update mode if changed
                        if plan.target_mode != self.current_mode:
                            old_mode = self.current_mode
                            self.current_mode = plan.target_mode
                            print(f"🔄 [HCL] Mode switch: {old_mode} → {self.current_mode}")

                # ===== KNOWLEDGE =====
                self.state_history.append(current_state)
                if len(self.state_history) > self.max_history:
                    self.state_history.pop(0)

                # Sleep until next check
                loop_duration = time.time() - loop_start
                sleep_time = max(0, self.check_interval - loop_duration)
                await asyncio.sleep(sleep_time)

            except Exception as e:
                print(f"❌ [HCL] Error in control loop: {e}")
                await asyncio.sleep(self.check_interval)

    def get_current_state(self) -> Optional[SystemState]:
        """Retorna o estado atual do sistema"""
        if self.state_history:
            return self.state_history[-1]
        return None

    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do loop de controle"""
        if not self.state_history:
            return {"status": "no_data"}

        recent_states = self.state_history[-20:]

        return {
            "status": "running" if self.is_running else "stopped",
            "current_mode": self.current_mode,
            "states_tracked": len(self.state_history),
            "avg_cpu_usage": sum(s.cpu_usage for s in recent_states) / len(recent_states),
            "avg_memory_usage": sum(s.memory_usage for s in recent_states) / len(recent_states),
            "avg_latency_ms": sum(s.avg_latency_ms for s in recent_states) / len(recent_states),
            "avg_requests_per_second": sum(s.requests_per_second for s in recent_states) / len(recent_states),
            "health_status": "healthy" if self.state_history[-1].is_healthy else "degraded",
            "uptime_hours": self.state_history[-1].uptime_seconds / 3600
        }

    async def force_mode_switch(self, target_mode: OperationalMode):
        """Força mudança de modo operacional"""
        if target_mode != self.current_mode:
            print(f"🔧 [HCL] Force mode switch: {self.current_mode} → {target_mode}")
            self.current_mode = target_mode

            # Apply mode immediately
            await self.executor.apply_mode(target_mode)
