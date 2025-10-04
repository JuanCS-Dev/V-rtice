"""
⚖️ Load Balancer - Distribui tasks entre endpoints do fleet

Responsável por:
- Seleção inteligente de endpoints
- Load balancing algorithms (round-robin, least-loaded, capability-based)
- Task queue management
- Performance tracking
"""

from typing import List, Dict, Any, Optional
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict
import logging

from .registry import EndpointRegistry, Endpoint, EndpointStatus
from .capability_detector import CapabilityDetector

logger = logging.getLogger(__name__)


class LoadBalancingStrategy(Enum):
    """Estratégias de load balancing."""

    ROUND_ROBIN = "round_robin"  # Rotação circular
    LEAST_LOADED = "least_loaded"  # Menos carregado
    CAPABILITY_BASED = "capability_based"  # Baseado em capabilities
    RANDOM = "random"  # Aleatório
    WEIGHTED = "weighted"  # Ponderado por performance


@dataclass
class TaskAssignment:
    """
    Atribuição de task a endpoint.

    Attributes:
        task_id: ID da task
        endpoint_id: ID do endpoint atribuído
        task_type: Tipo da task
        assigned_at: Quando foi atribuída
        priority: Prioridade (0-10)
        estimated_duration: Duração estimada em segundos
    """
    task_id: str
    endpoint_id: str
    task_type: str
    assigned_at: datetime = field(default_factory=datetime.now)
    priority: int = 5
    estimated_duration: float = 60.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EndpointLoad:
    """
    Load atual de um endpoint.

    Attributes:
        endpoint_id: ID do endpoint
        active_tasks: Tasks ativas atualmente
        completed_tasks: Total de tasks completadas
        failed_tasks: Total de tasks falhadas
        avg_task_duration: Duração média de tasks (segundos)
        current_load: Load atual (0-1, onde 1 = saturado)
    """
    endpoint_id: str
    active_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    avg_task_duration: float = 0.0
    current_load: float = 0.0
    last_updated: datetime = field(default_factory=datetime.now)


class LoadBalancer:
    """
    Load balancer para distribuição inteligente de tasks no fleet.

    Example:
        balancer = LoadBalancer(registry, strategy=LoadBalancingStrategy.LEAST_LOADED)

        # Assign task
        assignment = balancer.assign_task(
            task_id="scan-001",
            task_type="network_scan",
            required_capabilities=["nmap"]
        )

        # Mark completion
        balancer.complete_task(assignment.task_id, success=True, duration=45.2)
    """

    def __init__(
        self,
        registry: EndpointRegistry,
        strategy: LoadBalancingStrategy = LoadBalancingStrategy.LEAST_LOADED,
        max_tasks_per_endpoint: int = 5,
    ):
        """
        Initialize load balancer.

        Args:
            registry: Endpoint registry
            strategy: Load balancing strategy
            max_tasks_per_endpoint: Max concurrent tasks per endpoint
        """
        self.registry = registry
        self.strategy = strategy
        self.max_tasks_per_endpoint = max_tasks_per_endpoint

        # State tracking
        self._endpoint_loads: Dict[str, EndpointLoad] = defaultdict(
            lambda: EndpointLoad(endpoint_id="")
        )
        self._active_assignments: Dict[str, TaskAssignment] = {}
        self._round_robin_index = 0

        logger.info(
            f"LoadBalancer initialized (strategy={strategy.value}, "
            f"max_tasks={max_tasks_per_endpoint})"
        )

    def assign_task(
        self,
        task_id: str,
        task_type: str,
        required_capabilities: Optional[List[str]] = None,
        priority: int = 5,
        estimated_duration: float = 60.0,
        **metadata
    ) -> Optional[TaskAssignment]:
        """
        Assign task to best available endpoint.

        Args:
            task_id: Unique task ID
            task_type: Type of task
            required_capabilities: Required capabilities
            priority: Task priority (0-10, higher = more important)
            estimated_duration: Estimated duration in seconds
            **metadata: Additional task metadata

        Returns:
            TaskAssignment or None if no suitable endpoint

        Example:
            assignment = balancer.assign_task(
                task_id="hunt-001",
                task_type="threat_hunt",
                required_capabilities=["osquery"],
                priority=8
            )
        """
        logger.info(f"Assigning task {task_id} (type={task_type})")

        # Get available endpoints
        available = self._get_available_endpoints(required_capabilities)

        if not available:
            logger.warning(f"No available endpoints for task {task_id}")
            return None

        # Select endpoint based on strategy
        if self.strategy == LoadBalancingStrategy.ROUND_ROBIN:
            endpoint = self._select_round_robin(available)

        elif self.strategy == LoadBalancingStrategy.LEAST_LOADED:
            endpoint = self._select_least_loaded(available)

        elif self.strategy == LoadBalancingStrategy.CAPABILITY_BASED:
            endpoint = self._select_by_capability(available, required_capabilities or [])

        elif self.strategy == LoadBalancingStrategy.WEIGHTED:
            endpoint = self._select_weighted(available)

        else:  # RANDOM
            import random
            endpoint = random.choice(available)

        # Create assignment
        assignment = TaskAssignment(
            task_id=task_id,
            endpoint_id=endpoint.id,
            task_type=task_type,
            priority=priority,
            estimated_duration=estimated_duration,
            metadata=metadata
        )

        # Track assignment
        self._active_assignments[task_id] = assignment

        # Update endpoint load
        load = self._endpoint_loads[endpoint.id]
        load.endpoint_id = endpoint.id
        load.active_tasks += 1
        load.current_load = load.active_tasks / self.max_tasks_per_endpoint
        load.last_updated = datetime.now()

        logger.info(
            f"Task {task_id} assigned to {endpoint.hostname} "
            f"(load: {load.active_tasks}/{self.max_tasks_per_endpoint})"
        )

        return assignment

    def complete_task(
        self,
        task_id: str,
        success: bool = True,
        duration: Optional[float] = None,
    ) -> None:
        """
        Mark task as completed.

        Args:
            task_id: Task ID
            success: Whether task completed successfully
            duration: Actual duration in seconds

        Example:
            balancer.complete_task("scan-001", success=True, duration=42.5)
        """
        if task_id not in self._active_assignments:
            logger.warning(f"Task {task_id} not found in active assignments")
            return

        assignment = self._active_assignments.pop(task_id)
        load = self._endpoint_loads[assignment.endpoint_id]

        # Update load tracking
        load.active_tasks = max(0, load.active_tasks - 1)
        load.current_load = load.active_tasks / self.max_tasks_per_endpoint

        if success:
            load.completed_tasks += 1
        else:
            load.failed_tasks += 1

        # Update average duration
        if duration:
            total_tasks = load.completed_tasks + load.failed_tasks
            if total_tasks == 1:
                load.avg_task_duration = duration
            else:
                # Running average
                load.avg_task_duration = (
                    (load.avg_task_duration * (total_tasks - 1) + duration) / total_tasks
                )

        load.last_updated = datetime.now()

        logger.debug(
            f"Task {task_id} completed on {assignment.endpoint_id} "
            f"(success={success}, duration={duration}s)"
        )

    def cancel_task(self, task_id: str) -> None:
        """
        Cancel active task.

        Args:
            task_id: Task ID to cancel
        """
        if task_id in self._active_assignments:
            assignment = self._active_assignments.pop(task_id)

            # Reduce load
            load = self._endpoint_loads[assignment.endpoint_id]
            load.active_tasks = max(0, load.active_tasks - 1)
            load.current_load = load.active_tasks / self.max_tasks_per_endpoint
            load.last_updated = datetime.now()

            logger.info(f"Task {task_id} cancelled")

    def _get_available_endpoints(
        self,
        required_capabilities: Optional[List[str]] = None
    ) -> List[Endpoint]:
        """Get endpoints available for task assignment."""
        # Get all online endpoints
        endpoints = self.registry.list(status=EndpointStatus.ONLINE)

        available = []

        for endpoint in endpoints:
            # Check if under max load
            load = self._endpoint_loads[endpoint.id]
            if load.active_tasks >= self.max_tasks_per_endpoint:
                continue

            # Check capabilities if required
            if required_capabilities:
                can_execute = CapabilityDetector.can_execute_query(
                    endpoint.capabilities,
                    required_capabilities[0]  # Simplified
                )

                if not can_execute:
                    continue

            available.append(endpoint)

        return available

    def _select_round_robin(self, endpoints: List[Endpoint]) -> Endpoint:
        """Select endpoint using round-robin."""
        endpoint = endpoints[self._round_robin_index % len(endpoints)]
        self._round_robin_index += 1
        return endpoint

    def _select_least_loaded(self, endpoints: List[Endpoint]) -> Endpoint:
        """Select endpoint with least current load."""
        def get_load(endpoint: Endpoint) -> float:
            return self._endpoint_loads[endpoint.id].current_load

        return min(endpoints, key=get_load)

    def _select_by_capability(
        self,
        endpoints: List[Endpoint],
        capabilities: List[str]
    ) -> Endpoint:
        """Select endpoint best suited for required capabilities."""
        # Score each endpoint by capability match
        def score_endpoint(endpoint: Endpoint) -> int:
            score = 0

            # Check system commands
            sys_commands = endpoint.capabilities.get("system_commands", {})
            for cap in capabilities:
                if sys_commands.get(cap, False):
                    score += 1

            # Check security tools
            sec_tools = endpoint.capabilities.get("security_tools", {})
            for cap in capabilities:
                if sec_tools.get(cap, False):
                    score += 2  # Security tools worth more

            return score

        # Return endpoint with highest score, fallback to least loaded
        if capabilities:
            return max(endpoints, key=score_endpoint)
        else:
            return self._select_least_loaded(endpoints)

    def _select_weighted(self, endpoints: List[Endpoint]) -> Endpoint:
        """Select endpoint weighted by performance."""
        def get_weight(endpoint: Endpoint) -> float:
            load = self._endpoint_loads[endpoint.id]

            # Calculate success rate
            total = load.completed_tasks + load.failed_tasks
            success_rate = load.completed_tasks / total if total > 0 else 0.5

            # Weight = success_rate * (1 - current_load)
            return success_rate * (1.0 - load.current_load)

        return max(endpoints, key=get_weight)

    def get_load_stats(self) -> Dict[str, Any]:
        """
        Get load balancing statistics.

        Returns:
            Statistics dict

        Example:
            stats = balancer.get_load_stats()
            print(f"Active tasks: {stats['total_active_tasks']}")
        """
        total_active = sum(load.active_tasks for load in self._endpoint_loads.values())
        total_completed = sum(load.completed_tasks for load in self._endpoint_loads.values())
        total_failed = sum(load.failed_tasks for load in self._endpoint_loads.values())

        # Average load across endpoints
        loads = [load.current_load for load in self._endpoint_loads.values()]
        avg_load = sum(loads) / len(loads) if loads else 0.0

        # Most/least loaded endpoints
        if self._endpoint_loads:
            most_loaded = max(
                self._endpoint_loads.values(),
                key=lambda l: l.current_load
            )
            least_loaded = min(
                self._endpoint_loads.values(),
                key=lambda l: l.current_load
            )
        else:
            most_loaded = None
            least_loaded = None

        return {
            "total_active_tasks": total_active,
            "total_completed": total_completed,
            "total_failed": total_failed,
            "avg_load": round(avg_load, 2),
            "most_loaded_endpoint": most_loaded.endpoint_id if most_loaded else None,
            "least_loaded_endpoint": least_loaded.endpoint_id if least_loaded else None,
            "endpoints_tracked": len(self._endpoint_loads),
        }

    def get_endpoint_load(self, endpoint_id: str) -> Optional[EndpointLoad]:
        """
        Get current load for specific endpoint.

        Args:
            endpoint_id: Endpoint ID

        Returns:
            EndpointLoad or None
        """
        return self._endpoint_loads.get(endpoint_id)

    def rebalance(self) -> int:
        """
        Rebalance tasks across endpoints.

        Moves tasks from overloaded to underloaded endpoints.

        Returns:
            Number of tasks rebalanced

        Example:
            moved = balancer.rebalance()
            print(f"Rebalanced {moved} tasks")
        """
        # Find overloaded and underloaded endpoints
        overloaded = [
            (endpoint_id, load)
            for endpoint_id, load in self._endpoint_loads.items()
            if load.current_load > 0.8  # Over 80% capacity
        ]

        underloaded = [
            endpoint_id
            for endpoint_id, load in self._endpoint_loads.items()
            if load.current_load < 0.5  # Under 50% capacity
        ]

        if not overloaded or not underloaded:
            return 0

        moved_count = 0

        # Move tasks from overloaded to underloaded
        for overloaded_id, overloaded_load in overloaded:
            # Find tasks from this endpoint
            tasks_to_move = [
                (task_id, assignment)
                for task_id, assignment in self._active_assignments.items()
                if assignment.endpoint_id == overloaded_id
            ]

            # Move lowest priority tasks
            tasks_to_move.sort(key=lambda x: x[1].priority)

            for task_id, assignment in tasks_to_move[:1]:  # Move one at a time
                if underloaded:
                    new_endpoint_id = underloaded[0]

                    # Update assignment
                    assignment.endpoint_id = new_endpoint_id

                    # Update loads
                    overloaded_load.active_tasks -= 1
                    self._endpoint_loads[new_endpoint_id].active_tasks += 1

                    moved_count += 1
                    logger.info(f"Rebalanced task {task_id} to {new_endpoint_id}")

        return moved_count
