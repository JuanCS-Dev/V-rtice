"""C2L Command Executor with multi-layer kill switch."""

import time
from datetime import datetime
from uuid import UUID

import structlog
from backend.services.command_bus_service.audit_repository import AuditLog, AuditRepository
from backend.services.command_bus_service.kill_switch import KillSwitch
from backend.services.command_bus_service.models import (
    C2LCommand,
    C2LCommandType,
    CommandReceipt,
    KillSwitchLayer,
)
from backend.services.command_bus_service.nats_publisher import NATSPublisher

logger = structlog.get_logger()


class C2LCommandExecutor:
    """Execute C2L commands with multi-layer kill switch."""

    def __init__(
        self,
        publisher: NATSPublisher,
        kill_switch: KillSwitch,
        audit_repo: AuditRepository,
    ) -> None:
        """Initialize executor."""
        self.publisher = publisher
        self.kill_switch = kill_switch
        self.audit_repo = audit_repo

    async def execute(self, command: C2LCommand) -> CommandReceipt:
        """Execute C2L command with multi-layer kill switch."""
        start_time = time.time()
        executed_layers: list[str] = []
        cascade_terminated: list[str] = []
        error: str | None = None

        try:
            logger.info(
                "command_execution_start",
                command_id=str(command.id),
                type=command.command_type,
                targets=command.target_agents,
            )

            for target_agent_id in command.target_agents:
                if command.command_type == C2LCommandType.MUTE:
                    # MUTE: Layer 1 only (graceful)
                    await self._execute_layer(
                        command.id,
                        target_agent_id,
                        KillSwitchLayer.SOFTWARE,
                        "mute_agent",
                        executed_layers,
                    )

                elif command.command_type == C2LCommandType.ISOLATE:
                    # ISOLATE: Layers 1 + 3 (graceful + network)
                    await self._execute_layer(
                        command.id,
                        target_agent_id,
                        KillSwitchLayer.SOFTWARE,
                        "revoke_credentials",
                        executed_layers,
                    )
                    await self._execute_layer(
                        command.id,
                        target_agent_id,
                        KillSwitchLayer.NETWORK,
                        "isolate_network",
                        executed_layers,
                    )

                elif command.command_type == C2LCommandType.TERMINATE:
                    # TERMINATE: All 3 layers + cascade
                    await self._execute_layer(
                        command.id,
                        target_agent_id,
                        KillSwitchLayer.SOFTWARE,
                        "graceful_shutdown",
                        executed_layers,
                    )
                    await self._execute_layer(
                        command.id,
                        target_agent_id,
                        KillSwitchLayer.CONTAINER,
                        "force_kill",
                        executed_layers,
                    )
                    await self._execute_layer(
                        command.id,
                        target_agent_id,
                        KillSwitchLayer.NETWORK,
                        "network_quarantine",
                        executed_layers,
                    )

                    # Cascade terminate sub-agents
                    sub_agents = await self._cascade_terminate(target_agent_id, command.id)
                    cascade_terminated.extend(sub_agents)

            execution_time_ms = int((time.time() - start_time) * 1000)

            receipt = CommandReceipt(
                command_id=command.id,
                status="COMPLETED",
                message=f"Command executed successfully. Layers: {len(executed_layers)}, Cascade: {len(cascade_terminated)}",
                timestamp=datetime.utcnow(),
            )

            logger.info(
                "command_execution_success",
                command_id=str(command.id),
                layers=len(executed_layers),
                cascade_count=len(cascade_terminated),
                duration_ms=execution_time_ms,
            )

            return receipt

        except Exception as e:
            error = str(e)
            logger.error(
                "command_execution_failed",
                command_id=str(command.id),
                error=error,
                exc_info=True,
            )

            return CommandReceipt(
                command_id=command.id,
                status="FAILED",
                message=f"Command execution failed: {error}",
                timestamp=datetime.utcnow(),
            )

    async def _execute_layer(
        self,
        command_id: UUID,
        target_agent_id: str,
        layer: KillSwitchLayer,
        action: str,
        executed_layers: list[str],
    ) -> None:
        """Execute single kill switch layer."""
        try:
            if layer == KillSwitchLayer.SOFTWARE:
                await self.kill_switch.graceful_shutdown(target_agent_id)
            elif layer == KillSwitchLayer.CONTAINER:
                await self.kill_switch.force_kill(target_agent_id)
            else:  # layer == KillSwitchLayer.NETWORK
                await self.kill_switch.network_quarantine(target_agent_id)

            executed_layers.append(layer.value)

            # Audit log
            audit = AuditLog(
                command_id=command_id,
                layer=layer.value,
                action=action,
                success=True,
                details={"agent_id": target_agent_id},
            )
            await self.audit_repo.save(audit)

            logger.info(
                "layer_executed",
                command_id=str(command_id),
                layer=layer.value,
                action=action,
                agent_id=target_agent_id,
            )

        except Exception as e:
            # Log failure but continue to next layer
            audit = AuditLog(
                command_id=command_id,
                layer=layer.value,
                action=action,
                success=False,
                details={"error": str(e), "agent_id": target_agent_id},
            )
            await self.audit_repo.save(audit)

            logger.warning(
                "layer_failed",
                command_id=str(command_id),
                layer=layer.value,
                error=str(e),
                agent_id=target_agent_id,
            )

    async def _cascade_terminate(self, agent_id: str, command_id: UUID) -> list[str]:
        """Recursively terminate sub-agents."""
        # Query DB for sub-agents (mocked for now)
        sub_agents = await self._get_sub_agents(agent_id)

        terminated = []
        for sub_agent_id in sub_agents:
            # Create cascade command
            cascade_command = C2LCommand(
                operator_id="cascade-termination",
                command_type=C2LCommandType.TERMINATE,
                target_agents=[sub_agent_id],
            )

            # Execute recursively
            result = await self.execute(cascade_command)
            if result.status == "COMPLETED":
                terminated.append(sub_agent_id)

        return terminated

    async def _get_sub_agents(self, agent_id: str) -> list[str]:
        """Get list of sub-agents for cascade termination."""
        # Mock: In production, query DB relationship graph
        return []
