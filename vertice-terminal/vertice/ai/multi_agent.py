"""
Multi-Agent Orchestration System
=================================

Coordinates multiple specialized AI agents working together to solve
complex security problems through collaboration and task decomposition.

Features:
- Specialized agent creation and registration
- Task decomposition and delegation
- Inter-agent communication
- Consensus building
- Load balancing across agents

Examples:
    orchestrator = MultiAgentOrchestrator()

    # Register specialized agents
    orchestrator.register_agent(
        agent_id="threat_analyzer",
        specialization="Threat analysis and IOC correlation",
        capabilities=["analyze_threat", "correlate_iocs"]
    )

    # Execute multi-agent task
    result = orchestrator.execute_collaborative_task(
        task="Investigate APT campaign",
        context={...}
    )
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Callable
from enum import Enum
import logging
from datetime import datetime
from collections import defaultdict

logger = logging.getLogger(__name__)


class AgentRole(Enum):
    """Predefined agent roles."""

    COORDINATOR = "coordinator"  # Coordinates other agents
    ANALYST = "analyst"  # Data analysis specialist
    HUNTER = "hunter"  # Threat hunting specialist
    RESPONDER = "responder"  # Incident response specialist
    INVESTIGATOR = "investigator"  # Deep investigation specialist
    ENRICHER = "enricher"  # Data enrichment specialist
    STRATEGIST = "strategist"  # Strategic planning
    VALIDATOR = "validator"  # Validation and QA


class TaskPriority(Enum):
    """Task priority levels."""

    CRITICAL = "critical"
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"


class TaskStatus(Enum):
    """Task execution statuses."""

    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Agent:
    """
    Specialized AI agent.

    Attributes:
        agent_id: Unique agent identifier
        role: Agent's role
        specialization: Description of specialty
        capabilities: List of capabilities
        max_concurrent_tasks: Maximum parallel tasks
        performance_score: Historical performance (0-1)
    """
    agent_id: str
    role: AgentRole
    specialization: str
    capabilities: List[str]
    max_concurrent_tasks: int = 3
    performance_score: float = 0.8
    current_tasks: int = 0
    total_tasks_completed: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    registered_at: datetime = field(default_factory=datetime.now)


@dataclass
class Task:
    """
    Task to be executed by agent(s).

    Attributes:
        task_id: Unique task identifier
        description: Natural language task description
        priority: Task priority
        required_capabilities: Capabilities needed
        context: Task context data
        assigned_agent: Agent assigned to task
        status: Current task status
        result: Task result when completed
    """
    task_id: str
    description: str
    priority: TaskPriority
    required_capabilities: List[str]
    context: Dict[str, Any]
    assigned_agent: Optional[str] = None
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[Dict[str, Any]] = None
    dependencies: List[str] = field(default_factory=list)  # Task IDs this depends on
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


@dataclass
class CollaborationResult:
    """
    Result of multi-agent collaboration.

    Attributes:
        task_description: Original task
        final_result: Aggregated result
        agent_contributions: Individual agent contributions
        consensus_score: Agreement level among agents (0-1)
        execution_time_seconds: Total execution time
    """
    task_description: str
    final_result: Dict[str, Any]
    agent_contributions: Dict[str, Dict[str, Any]]  # agent_id → contribution
    consensus_score: float
    execution_time_seconds: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    completed_at: datetime = field(default_factory=datetime.now)


class MultiAgentOrchestrator:
    """
    Multi-agent orchestration and coordination system.

    Manages multiple specialized agents, decomposes complex tasks,
    and coordinates collaborative execution.

    Example:
        orchestrator = MultiAgentOrchestrator()

        # Register agents
        orchestrator.register_agent(
            agent_id="hunter1",
            role=AgentRole.HUNTER,
            specialization="Network threat hunting",
            capabilities=["analyze_netflow", "detect_lateral_movement"]
        )

        orchestrator.register_agent(
            agent_id="analyst1",
            role=AgentRole.ANALYST,
            specialization="Log analysis",
            capabilities=["parse_logs", "correlate_events"]
        )

        # Execute collaborative task
        result = orchestrator.execute_collaborative_task(
            task="Investigate suspicious lateral movement",
            context={"source_ip": "10.0.0.5", "dest_ips": [...]}
        )
    """

    def __init__(self):
        """Initialize multi-agent orchestrator."""
        self._agents: Dict[str, Agent] = {}
        self._tasks: Dict[str, Task] = {}
        self._task_counter = 0

        # Performance tracking
        self._agent_performance: Dict[str, List[float]] = defaultdict(list)

        logger.info("MultiAgentOrchestrator initialized")

    def register_agent(
        self,
        agent_id: str,
        role: AgentRole,
        specialization: str,
        capabilities: List[str],
        max_concurrent_tasks: int = 3,
        **metadata
    ) -> Agent:
        """
        Register specialized agent.

        Args:
            agent_id: Unique agent ID
            role: Agent role
            specialization: Specialty description
            capabilities: List of capabilities
            max_concurrent_tasks: Max parallel tasks
            **metadata: Additional agent metadata

        Returns:
            Registered Agent

        Example:
            agent = orchestrator.register_agent(
                agent_id="threat_hunter_01",
                role=AgentRole.HUNTER,
                specialization="APT detection",
                capabilities=["hunt_apt", "analyze_ttps"]
            )
        """
        agent = Agent(
            agent_id=agent_id,
            role=role,
            specialization=specialization,
            capabilities=capabilities,
            max_concurrent_tasks=max_concurrent_tasks,
            metadata=metadata
        )

        self._agents[agent_id] = agent

        logger.info(
            f"Agent registered: {agent_id} ({role.value}) - {len(capabilities)} capabilities"
        )

        return agent

    def create_task(
        self,
        description: str,
        required_capabilities: List[str],
        context: Dict[str, Any],
        priority: TaskPriority = TaskPriority.NORMAL,
        dependencies: Optional[List[str]] = None,
    ) -> Task:
        """
        Create task for agent execution.

        Args:
            description: Task description
            required_capabilities: Capabilities needed
            context: Task context
            priority: Task priority
            dependencies: Task IDs this depends on

        Returns:
            Created Task

        Example:
            task = orchestrator.create_task(
                description="Analyze suspicious process execution",
                required_capabilities=["process_analysis", "memory_forensics"],
                context={"process_id": 1234, "host": "workstation-05"},
                priority=TaskPriority.HIGH
            )
        """
        self._task_counter += 1
        task_id = f"task_{self._task_counter:04d}"

        task = Task(
            task_id=task_id,
            description=description,
            priority=priority,
            required_capabilities=required_capabilities,
            context=context,
            dependencies=dependencies or []
        )

        self._tasks[task_id] = task

        logger.debug(
            f"Task created: {task_id} - {description[:50]}... "
            f"(priority={priority.value})"
        )

        return task

    def assign_task(self, task: Task) -> Optional[Agent]:
        """
        Assign task to best available agent.

        Uses capability matching, load balancing, and performance scores.

        Args:
            task: Task to assign

        Returns:
            Assigned Agent or None if no suitable agent

        Example:
            agent = orchestrator.assign_task(task)
            if agent:
                print(f"Task assigned to {agent.agent_id}")
        """
        # Find agents with required capabilities
        capable_agents = []

        for agent in self._agents.values():
            # Check if agent has all required capabilities
            if all(cap in agent.capabilities for cap in task.required_capabilities):
                # Check if agent has capacity
                if agent.current_tasks < agent.max_concurrent_tasks:
                    capable_agents.append(agent)

        if not capable_agents:
            logger.warning(
                f"No capable agent found for task {task.task_id} "
                f"(requires: {task.required_capabilities})"
            )
            return None

        # Select best agent based on performance and load
        def agent_score(agent: Agent) -> float:
            # Higher is better
            load_factor = 1.0 - (agent.current_tasks / agent.max_concurrent_tasks)
            return agent.performance_score * 0.7 + load_factor * 0.3

        best_agent = max(capable_agents, key=agent_score)

        # Assign task
        task.assigned_agent = best_agent.agent_id
        task.status = TaskStatus.ASSIGNED
        best_agent.current_tasks += 1

        logger.info(
            f"Task {task.task_id} assigned to {best_agent.agent_id} "
            f"(load: {best_agent.current_tasks}/{best_agent.max_concurrent_tasks})"
        )

        return best_agent

    def execute_task(self, task: Task) -> Dict[str, Any]:
        """
        Execute task (simulated).

        In production, this would delegate to actual agent implementation.

        Args:
            task: Task to execute

        Returns:
            Task result

        Example:
            result = orchestrator.execute_task(task)
        """
        if not task.assigned_agent:
            raise ValueError(f"Task {task.task_id} not assigned to agent")

        agent = self._agents[task.assigned_agent]

        logger.info(
            f"Executing task {task.task_id} with agent {agent.agent_id}"
        )

        task.status = TaskStatus.IN_PROGRESS
        task.started_at = datetime.now()

        # Simulated execution (in production, would call real agent)
        result = {
            "task_id": task.task_id,
            "agent_id": agent.agent_id,
            "description": task.description,
            "status": "completed",
            "findings": f"Analysis completed by {agent.role.value}",
            "confidence": agent.performance_score,
            "context_analyzed": list(task.context.keys()),
        }

        # Update task
        task.status = TaskStatus.COMPLETED
        task.result = result
        task.completed_at = datetime.now()

        # Update agent
        agent.current_tasks -= 1
        agent.total_tasks_completed += 1

        # Track performance (simulated success)
        self._agent_performance[agent.agent_id].append(0.85)

        logger.info(
            f"Task {task.task_id} completed by {agent.agent_id}"
        )

        return result

    def execute_collaborative_task(
        self,
        task: str,
        context: Dict[str, Any],
        num_agents: int = 3,
        priority: TaskPriority = TaskPriority.HIGH,
    ) -> CollaborationResult:
        """
        Execute task with multiple agents collaboratively.

        Decomposes task, assigns to multiple agents, and aggregates results.

        Args:
            task: Task description
            context: Task context
            num_agents: Number of agents to involve
            priority: Task priority

        Returns:
            CollaborationResult with aggregated findings

        Example:
            result = orchestrator.execute_collaborative_task(
                task="Investigate APT campaign targeting organization",
                context={"iocs": [...], "timeline": [...], "affected_hosts": [...]},
                num_agents=4
            )

            print(f"Consensus: {result.consensus_score:.0%}")
            for agent_id, contribution in result.agent_contributions.items():
                print(f"{agent_id}: {contribution}")
        """
        start_time = datetime.now()

        logger.info(
            f"Starting collaborative task with {num_agents} agents: {task[:60]}..."
        )

        # Decompose into subtasks (simplified - in production would use AI)
        subtasks = self._decompose_task(task, context, num_agents)

        # Assign and execute subtasks
        agent_contributions = {}

        for subtask_desc, subtask_context, required_caps in subtasks:
            subtask = self.create_task(
                description=subtask_desc,
                required_capabilities=required_caps,
                context=subtask_context,
                priority=priority
            )

            agent = self.assign_task(subtask)

            if agent:
                result = self.execute_task(subtask)
                agent_contributions[agent.agent_id] = result

        # Aggregate results and build consensus
        final_result, consensus = self._aggregate_results(agent_contributions)

        execution_time = (datetime.now() - start_time).total_seconds()

        collaboration_result = CollaborationResult(
            task_description=task,
            final_result=final_result,
            agent_contributions=agent_contributions,
            consensus_score=consensus,
            execution_time_seconds=execution_time,
            metadata={"num_agents": len(agent_contributions)}
        )

        logger.info(
            f"Collaborative task complete: {len(agent_contributions)} agents, "
            f"consensus={consensus:.0%}, time={execution_time:.1f}s"
        )

        return collaboration_result

    def _decompose_task(
        self,
        task: str,
        context: Dict[str, Any],
        num_subtasks: int
    ) -> List[tuple]:
        """
        Decompose complex task into subtasks.

        In production, would use AI to intelligently decompose.

        Returns:
            List of (description, context, required_capabilities) tuples
        """
        # Simplified decomposition (production would be more sophisticated)
        subtasks = []

        if "investigate" in task.lower():
            subtasks.append((
                "Analyze initial indicators and timeline",
                context,
                ["log_analysis", "timeline_analysis"]
            ))

            subtasks.append((
                "Correlate with threat intelligence",
                context,
                ["threat_intel", "ioc_correlation"]
            ))

            subtasks.append((
                "Assess impact and scope",
                context,
                ["impact_analysis", "scope_assessment"]
            ))

        elif "hunt" in task.lower():
            subtasks.append((
                "Formulate hunt hypothesis",
                context,
                ["hypothesis_generation"]
            ))

            subtasks.append((
                "Execute hunt across environment",
                context,
                ["hunt_execution", "data_analysis"]
            ))

        else:
            # Generic decomposition
            for i in range(min(num_subtasks, 3)):
                subtasks.append((
                    f"Analyze aspect {i+1} of problem",
                    context,
                    ["analysis", "investigation"]
                ))

        return subtasks[:num_subtasks]

    def _aggregate_results(
        self,
        agent_contributions: Dict[str, Dict[str, Any]]
    ) -> tuple:
        """
        Aggregate agent results and calculate consensus.

        Returns:
            (final_result dict, consensus_score float)
        """
        if not agent_contributions:
            return {}, 0.0

        # Aggregate findings
        all_findings = []
        all_confidences = []

        for contribution in agent_contributions.values():
            all_findings.append(contribution.get("findings", ""))
            all_confidences.append(contribution.get("confidence", 0.5))

        # Calculate consensus (simplified - production would be more sophisticated)
        avg_confidence = sum(all_confidences) / len(all_confidences)
        confidence_variance = sum((c - avg_confidence) ** 2 for c in all_confidences) / len(all_confidences)

        # High consensus = low variance in confidence scores
        consensus_score = max(0.0, 1.0 - confidence_variance)

        final_result = {
            "aggregated_findings": all_findings,
            "average_confidence": avg_confidence,
            "consensus_level": "high" if consensus_score > 0.8 else "medium" if consensus_score > 0.5 else "low",
            "num_agents": len(agent_contributions),
        }

        return final_result, consensus_score

    def get_agent_stats(self, agent_id: str) -> Dict[str, Any]:
        """
        Get agent performance statistics.

        Args:
            agent_id: Agent ID

        Returns:
            Stats dict

        Example:
            stats = orchestrator.get_agent_stats("hunter1")
            print(f"Completed: {stats['tasks_completed']}")
        """
        if agent_id not in self._agents:
            raise ValueError(f"Agent not found: {agent_id}")

        agent = self._agents[agent_id]
        performance_history = self._agent_performance.get(agent_id, [])

        return {
            "agent_id": agent.agent_id,
            "role": agent.role.value,
            "specialization": agent.specialization,
            "capabilities": agent.capabilities,
            "tasks_completed": agent.total_tasks_completed,
            "current_load": agent.current_tasks,
            "max_concurrent": agent.max_concurrent_tasks,
            "performance_score": agent.performance_score,
            "avg_recent_performance": sum(performance_history[-10:]) / len(performance_history[-10:]) if performance_history else 0.0,
        }

    def get_orchestrator_stats(self) -> Dict[str, Any]:
        """
        Get orchestrator statistics.

        Returns:
            Stats dict

        Example:
            stats = orchestrator.get_orchestrator_stats()
            print(f"Total agents: {stats['total_agents']}")
        """
        return {
            "total_agents": len(self._agents),
            "total_tasks": len(self._tasks),
            "completed_tasks": sum(1 for t in self._tasks.values() if t.status == TaskStatus.COMPLETED),
            "pending_tasks": sum(1 for t in self._tasks.values() if t.status == TaskStatus.PENDING),
            "in_progress_tasks": sum(1 for t in self._tasks.values() if t.status == TaskStatus.IN_PROGRESS),
            "total_agent_capacity": sum(a.max_concurrent_tasks for a in self._agents.values()),
            "current_load": sum(a.current_tasks for a in self._agents.values()),
        }
