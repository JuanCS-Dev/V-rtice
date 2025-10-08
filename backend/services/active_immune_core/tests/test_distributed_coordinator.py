"""Distributed Coordinator Tests - PRODUCTION-READY

Comprehensive test suite for DistributedCoordinator with 45+ tests covering:
- Agent management
- Leader election (Bully algorithm)
- Task assignment and load balancing
- Consensus voting and quorum
- Fault tolerance and recovery
- Metrics and monitoring

NO MOCKS - Real coordination logic tested.
"""

from datetime import datetime, timedelta

import pytest

from active_immune_core.agents.distributed_coordinator import (
    AgentRole,
    DistributedCoordinator,
    TaskStatus,
    VoteDecision,
)

# ==================== FIXTURES ====================


@pytest.fixture
def coordinator():
    """Create basic coordinator"""
    return DistributedCoordinator(
        heartbeat_interval=10,
        heartbeat_timeout=30,
        election_timeout=15,
        task_timeout=300,
        enable_auto_recovery=True,
    )


@pytest.fixture
def coordinator_with_agents(coordinator):
    """Create coordinator with 3 registered agents"""
    coordinator.register_agent("agent_1", capabilities={"phagocytosis"}, priority=10)
    coordinator.register_agent("agent_2", capabilities={"antigen_presentation"}, priority=5)
    coordinator.register_agent("agent_3", capabilities={"phagocytosis", "cytokine_secretion"}, priority=8)
    return coordinator


# ==================== INITIALIZATION TESTS ====================


@pytest.mark.asyncio
class TestDistributedCoordinatorInitialization:
    """Test coordinator initialization"""

    async def test_coordinator_creation(self, coordinator):
        """Test basic coordinator creation"""
        assert coordinator.heartbeat_interval == 10
        assert coordinator.heartbeat_timeout == 30
        assert coordinator.election_timeout == 15
        assert coordinator.task_timeout == 300
        assert coordinator.enable_auto_recovery is True
        assert len(coordinator._agents) == 0
        assert coordinator._leader_id is None

    async def test_coordinator_custom_parameters(self):
        """Test coordinator with custom parameters"""
        coord = DistributedCoordinator(
            heartbeat_interval=5,
            heartbeat_timeout=15,
            election_timeout=10,
            task_timeout=120,
            enable_auto_recovery=False,
        )

        assert coord.heartbeat_interval == 5
        assert coord.heartbeat_timeout == 15
        assert coord.election_timeout == 10
        assert coord.task_timeout == 120
        assert coord.enable_auto_recovery is False


# ==================== AGENT MANAGEMENT TESTS ====================


@pytest.mark.asyncio
class TestAgentManagement:
    """Test agent registration and management"""

    async def test_register_agent(self, coordinator):
        """Test registering single agent"""
        node = coordinator.register_agent(
            "agent_1",
            capabilities={"phagocytosis"},
            priority=10,
            health_score=0.9,
        )

        assert node.id == "agent_1"
        assert node.role == AgentRole.FOLLOWER
        assert node.priority == 10
        assert node.capabilities == {"phagocytosis"}
        assert node.health_score == 0.9
        assert node.is_alive is True
        assert "agent_1" in coordinator._agents

    async def test_register_multiple_agents(self, coordinator):
        """Test registering multiple agents"""
        coordinator.register_agent("agent_1", priority=10)
        coordinator.register_agent("agent_2", priority=5)
        coordinator.register_agent("agent_3", priority=8)

        assert len(coordinator._agents) == 3

    async def test_register_duplicate_agent(self, coordinator):
        """Test registering duplicate agent (should return existing)"""
        node1 = coordinator.register_agent("agent_1", priority=10)
        node2 = coordinator.register_agent("agent_1", priority=5)

        assert node1 is node2
        assert node1.priority == 10  # Original priority preserved

    async def test_get_agent(self, coordinator_with_agents):
        """Test retrieving agent by ID"""
        agent = coordinator_with_agents.get_agent("agent_1")

        assert agent is not None
        assert agent.id == "agent_1"
        assert agent.priority == 10

    async def test_get_agent_not_found(self, coordinator):
        """Test retrieving non-existent agent"""
        agent = coordinator.get_agent("non_existent")

        assert agent is None

    async def test_get_all_agents(self, coordinator_with_agents):
        """Test retrieving all agents"""
        agents = coordinator_with_agents.get_all_agents()

        assert len(agents) == 3
        agent_ids = {a.id for a in agents}
        assert agent_ids == {"agent_1", "agent_2", "agent_3"}

    async def test_get_alive_agents(self, coordinator_with_agents):
        """Test retrieving alive agents only"""
        # Mark one agent as dead
        agent = coordinator_with_agents.get_agent("agent_2")
        agent.is_alive = False

        alive = coordinator_with_agents.get_alive_agents()

        assert len(alive) == 2
        assert all(a.is_alive for a in alive)

    async def test_unregister_agent(self, coordinator_with_agents):
        """Test unregistering agent"""
        result = coordinator_with_agents.unregister_agent("agent_2")

        assert result is True
        assert len(coordinator_with_agents._agents) == 2
        assert "agent_2" not in coordinator_with_agents._agents

    async def test_unregister_agent_not_found(self, coordinator):
        """Test unregistering non-existent agent"""
        result = coordinator.unregister_agent("non_existent")

        assert result is False


# ==================== HEARTBEAT & HEALTH TESTS ====================


@pytest.mark.asyncio
class TestHeartbeatHealth:
    """Test heartbeat and health monitoring"""

    async def test_heartbeat(self, coordinator_with_agents):
        """Test recording heartbeat"""
        result = coordinator_with_agents.heartbeat("agent_1")

        assert result is True

        agent = coordinator_with_agents.get_agent("agent_1")
        # Heartbeat should be recent
        elapsed = (datetime.now() - agent.last_heartbeat).total_seconds()
        assert elapsed < 1.0

    async def test_heartbeat_invalid_agent(self, coordinator):
        """Test heartbeat for non-existent agent"""
        result = coordinator.heartbeat("non_existent")

        assert result is False

    async def test_update_agent_health(self, coordinator_with_agents):
        """Test updating agent health score"""
        result = coordinator_with_agents.update_agent_health("agent_1", 0.7)

        assert result is True

        agent = coordinator_with_agents.get_agent("agent_1")
        assert agent.health_score == 0.7

    async def test_update_agent_load(self, coordinator_with_agents):
        """Test updating agent load"""
        result = coordinator_with_agents.update_agent_load("agent_1", 0.5)

        assert result is True

        agent = coordinator_with_agents.get_agent("agent_1")
        assert agent.current_load == 0.5

    async def test_check_agent_health_timeout(self, coordinator_with_agents):
        """Test agent timeout detection"""
        # Set agent heartbeat to past
        agent = coordinator_with_agents.get_agent("agent_1")
        agent.last_heartbeat = datetime.now() - timedelta(seconds=35)

        failed = coordinator_with_agents.check_agent_health()

        assert "agent_1" in failed
        agent_after = coordinator_with_agents.get_agent("agent_1")
        assert agent_after.is_alive is False

    async def test_check_agent_health_no_timeout(self, coordinator_with_agents):
        """Test no timeout when heartbeat recent"""
        # Send recent heartbeat
        coordinator_with_agents.heartbeat("agent_1")

        failed = coordinator_with_agents.check_agent_health()

        assert len(failed) == 0


# ==================== LEADER ELECTION TESTS ====================


@pytest.mark.asyncio
class TestLeaderElection:
    """Test leader election (Bully algorithm)"""

    async def test_elect_leader_basic(self, coordinator_with_agents):
        """Test basic leader election"""
        leader_id = coordinator_with_agents.elect_leader()

        assert leader_id is not None
        assert leader_id == "agent_1"  # Highest priority (10)

        leader = coordinator_with_agents.get_leader()
        assert leader.id == "agent_1"
        assert leader.role == AgentRole.LEADER

    async def test_elect_leader_with_health_scores(self, coordinator):
        """Test leader election considers health scores"""
        coordinator.register_agent("agent_1", priority=10, health_score=0.5)
        coordinator.register_agent("agent_2", priority=8, health_score=1.0)

        leader_id = coordinator.elect_leader()

        # agent_1: score = 10 + 0.5 - 0.0 = 10.5
        # agent_2: score = 8 + 1.0 - 0.0 = 9.0
        # agent_1 wins
        assert leader_id == "agent_1"

    async def test_elect_leader_with_load(self, coordinator):
        """Test leader election considers load"""
        coordinator.register_agent("agent_1", priority=10)
        coordinator.register_agent("agent_2", priority=10)

        # Set agent_1 to high load
        coordinator.update_agent_load("agent_1", 0.8)

        leader_id = coordinator.elect_leader()

        # agent_1: score = 10 + 1.0 - 0.8 = 10.2
        # agent_2: score = 10 + 1.0 - 0.0 = 11.0
        # agent_2 wins
        assert leader_id == "agent_2"

    async def test_elect_leader_empty_coordinator(self, coordinator):
        """Test election with no agents"""
        leader_id = coordinator.elect_leader()

        assert leader_id is None

    async def test_elect_leader_all_dead(self, coordinator_with_agents):
        """Test election when all agents dead"""
        for agent in coordinator_with_agents.get_all_agents():
            agent.is_alive = False

        leader_id = coordinator_with_agents.elect_leader()

        assert leader_id is None

    async def test_is_leader(self, coordinator_with_agents):
        """Test checking if agent is leader"""
        coordinator_with_agents.elect_leader()

        assert coordinator_with_agents.is_leader("agent_1") is True
        assert coordinator_with_agents.is_leader("agent_2") is False


# ==================== TASK MANAGEMENT TESTS ====================


@pytest.mark.asyncio
class TestTaskManagement:
    """Test task submission and management"""

    async def test_submit_task_basic(self, coordinator):
        """Test basic task submission"""
        task_id = coordinator.submit_task(
            "phagocytosis",
            {"target": "malware"},
            required_capabilities={"phagocytosis"},
            priority=7,
        )

        assert task_id is not None
        assert task_id in coordinator._tasks

        task = coordinator.get_task(task_id)
        assert task.task_type == "phagocytosis"
        assert task.payload == {"target": "malware"}
        assert task.required_capabilities == {"phagocytosis"}
        assert task.priority == 7
        assert task.status == TaskStatus.PENDING

    async def test_submit_multiple_tasks(self, coordinator):
        """Test submitting multiple tasks"""
        task_id1 = coordinator.submit_task("task1", {})
        task_id2 = coordinator.submit_task("task2", {})
        task_id3 = coordinator.submit_task("task3", {})

        assert len(coordinator._tasks) == 3
        assert len(coordinator._task_queue) == 3

    async def test_task_queue_priority_ordering(self, coordinator):
        """Test task queue maintains priority order"""
        coordinator.submit_task("low", {}, priority=3)
        coordinator.submit_task("high", {}, priority=9)
        coordinator.submit_task("medium", {}, priority=5)

        # Queue should be sorted by priority (descending)
        priorities = [coordinator._tasks[tid].priority for tid in coordinator._task_queue]
        assert priorities == [9, 5, 3]

    async def test_get_task(self, coordinator):
        """Test retrieving task by ID"""
        task_id = coordinator.submit_task("test", {})

        task = coordinator.get_task(task_id)

        assert task is not None
        assert task.id == task_id

    async def test_get_task_not_found(self, coordinator):
        """Test retrieving non-existent task"""
        task = coordinator.get_task("non_existent")

        assert task is None

    async def test_complete_task(self, coordinator):
        """Test completing task"""
        task_id = coordinator.submit_task("test", {})
        task = coordinator.get_task(task_id)
        task.status = TaskStatus.ASSIGNED
        task.assigned_to = "agent_1"

        # Register agent first
        coordinator.register_agent("agent_1")

        result = coordinator.complete_task(task_id, result={"status": "success"})

        assert result is True

        task_after = coordinator.get_task(task_id)
        assert task_after.status == TaskStatus.COMPLETED
        assert task_after.result == {"status": "success"}
        assert task_after.completed_at is not None

    async def test_complete_task_invalid_status(self, coordinator):
        """Test completing task with wrong status"""
        task_id = coordinator.submit_task("test", {})
        # Task is PENDING, cannot complete

        result = coordinator.complete_task(task_id)

        assert result is False

    async def test_fail_task(self, coordinator):
        """Test failing task"""
        task_id = coordinator.submit_task("test", {})
        task = coordinator.get_task(task_id)
        task.status = TaskStatus.ASSIGNED
        task.assigned_to = "agent_1"

        # Register agent
        coordinator.register_agent("agent_1")

        result = coordinator.fail_task(task_id, "Test error")

        assert result is True

        task_after = coordinator.get_task(task_id)
        assert task_after.status == TaskStatus.FAILED
        assert task_after.error == "Test error"

    async def test_get_agent_tasks(self, coordinator):
        """Test retrieving tasks assigned to agent"""
        coordinator.register_agent("agent_1")

        task_id1 = coordinator.submit_task("task1", {})
        task_id2 = coordinator.submit_task("task2", {})

        task1 = coordinator.get_task(task_id1)
        task1.assigned_to = "agent_1"
        task1.status = TaskStatus.ASSIGNED

        task2 = coordinator.get_task(task_id2)
        task2.assigned_to = "agent_1"
        task2.status = TaskStatus.ASSIGNED

        agent_tasks = coordinator.get_agent_tasks("agent_1")

        assert len(agent_tasks) == 2

    async def test_task_timeout_detection(self, coordinator):
        """Test detecting timed-out tasks"""
        task_id = coordinator.submit_task("test", {}, timeout_seconds=1)

        task = coordinator.get_task(task_id)
        task.status = TaskStatus.ASSIGNED
        task.assigned_to = "agent_1"
        task.assigned_at = datetime.now() - timedelta(seconds=2)

        timed_out = coordinator.check_task_timeouts()

        assert task_id in timed_out

        task_after = coordinator.get_task(task_id)
        assert task_after.status == TaskStatus.PENDING
        assert task_after.retries == 1


# ==================== TASK ASSIGNMENT TESTS ====================


@pytest.mark.asyncio
class TestTaskAssignment:
    """Test task assignment and load balancing"""

    async def test_assign_tasks_capability_match(self, coordinator_with_agents):
        """Test task assignment based on capabilities"""
        # Submit task requiring phagocytosis
        task_id = coordinator_with_agents.submit_task(
            "phagocytosis_task",
            {"target": "bacteria"},
            required_capabilities={"phagocytosis"},
        )

        assigned = coordinator_with_agents.assign_tasks()

        assert assigned == 1

        task = coordinator_with_agents.get_task(task_id)
        assert task.status == TaskStatus.ASSIGNED
        # Should be assigned to agent_1 or agent_3 (both have phagocytosis)
        assert task.assigned_to in ["agent_1", "agent_3"]

    async def test_assign_tasks_no_capable_agent(self, coordinator_with_agents):
        """Test task assignment when no capable agent"""
        # Submit task requiring capability nobody has
        task_id = coordinator_with_agents.submit_task(
            "unknown_task",
            {},
            required_capabilities={"unknown_capability"},
        )

        assigned = coordinator_with_agents.assign_tasks()

        assert assigned == 0

        task = coordinator_with_agents.get_task(task_id)
        assert task.status == TaskStatus.PENDING  # Still pending

    async def test_assign_tasks_load_balancing(self, coordinator):
        """Test tasks assigned to least loaded agent"""
        coordinator.register_agent("agent_1", capabilities={"work"})
        coordinator.register_agent("agent_2", capabilities={"work"})

        # Set agent_1 to high load
        coordinator.update_agent_load("agent_1", 0.8)

        task_id = coordinator.submit_task("task", {}, required_capabilities={"work"})

        coordinator.assign_tasks()

        task = coordinator.get_task(task_id)
        # Should be assigned to agent_2 (lower load)
        assert task.assigned_to == "agent_2"

    async def test_assign_multiple_tasks(self, coordinator_with_agents):
        """Test assigning multiple tasks"""
        # Submit 3 tasks, all requiring phagocytosis
        for i in range(3):
            coordinator_with_agents.submit_task(
                f"task_{i}",
                {},
                required_capabilities={"phagocytosis"},
            )

        assigned = coordinator_with_agents.assign_tasks()

        # Should assign all 3 tasks (agent_1 and agent_3 have phagocytosis)
        assert assigned == 3


# ==================== CONSENSUS & VOTING TESTS ====================


@pytest.mark.asyncio
class TestConsensusVoting:
    """Test consensus voting and quorum"""

    async def test_propose_vote(self, coordinator):
        """Test creating vote proposal"""
        proposal_id = coordinator.propose_vote(
            "config_change",
            {"setting": "value"},
            "agent_1",
            required_quorum=0.5,
        )

        assert proposal_id is not None
        assert proposal_id in coordinator._proposals

        proposal = coordinator.get_proposal(proposal_id)
        assert proposal.proposal_type == "config_change"
        assert proposal.data == {"setting": "value"}
        assert proposal.proposer_id == "agent_1"
        assert proposal.required_quorum == 0.5

    async def test_cast_vote(self, coordinator_with_agents):
        """Test casting vote on proposal"""
        proposal_id = coordinator_with_agents.propose_vote(
            "test",
            {},
            "agent_1",
        )

        result = coordinator_with_agents.cast_vote(proposal_id, "agent_1", VoteDecision.APPROVE)

        assert result is True

        proposal = coordinator_with_agents.get_proposal(proposal_id)
        assert proposal.votes["agent_1"] == VoteDecision.APPROVE

    async def test_cast_vote_invalid_agent(self, coordinator_with_agents):
        """Test casting vote with invalid agent"""
        proposal_id = coordinator_with_agents.propose_vote(
            "test",
            {},
            "agent_1",
        )

        result = coordinator_with_agents.cast_vote(proposal_id, "non_existent", VoteDecision.APPROVE)

        assert result is False

    async def test_cast_vote_dead_agent(self, coordinator_with_agents):
        """Test dead agent cannot vote"""
        agent = coordinator_with_agents.get_agent("agent_1")
        agent.is_alive = False

        proposal_id = coordinator_with_agents.propose_vote(
            "test",
            {},
            "agent_2",
        )

        result = coordinator_with_agents.cast_vote(proposal_id, "agent_1", VoteDecision.APPROVE)

        assert result is False

    async def test_tally_votes_approved(self, coordinator_with_agents):
        """Test vote tallying - approved"""
        proposal_id = coordinator_with_agents.propose_vote(
            "test",
            {},
            "agent_1",
            required_quorum=0.5,
        )

        # 3 agents, need 2 votes for quorum
        coordinator_with_agents.cast_vote(proposal_id, "agent_1", VoteDecision.APPROVE)
        coordinator_with_agents.cast_vote(proposal_id, "agent_2", VoteDecision.APPROVE)

        quorum_reached, details = coordinator_with_agents.tally_votes(proposal_id)

        assert quorum_reached is True
        assert details["approved"] is True
        assert details["approve"] == 2
        assert details["reject"] == 0

    async def test_tally_votes_rejected(self, coordinator_with_agents):
        """Test vote tallying - rejected"""
        proposal_id = coordinator_with_agents.propose_vote(
            "test",
            {},
            "agent_1",
            required_quorum=0.5,
        )

        # 2 reject votes
        coordinator_with_agents.cast_vote(proposal_id, "agent_1", VoteDecision.REJECT)
        coordinator_with_agents.cast_vote(proposal_id, "agent_2", VoteDecision.REJECT)

        quorum_reached, details = coordinator_with_agents.tally_votes(proposal_id)

        assert quorum_reached is True
        assert details["approved"] is False  # Rejected
        assert details["reject"] == 2

    async def test_tally_votes_no_quorum(self, coordinator_with_agents):
        """Test vote tallying - no quorum"""
        proposal_id = coordinator_with_agents.propose_vote(
            "test",
            {},
            "agent_1",
            required_quorum=0.8,  # Need 80% votes (3 out of 3)
        )

        # Only 1 vote (33%)
        coordinator_with_agents.cast_vote(proposal_id, "agent_1", VoteDecision.APPROVE)

        quorum_reached, details = coordinator_with_agents.tally_votes(proposal_id)

        assert quorum_reached is False
        assert details["quorum_reached"] is False

    async def test_vote_counts(self, coordinator_with_agents):
        """Test vote count calculation"""
        proposal_id = coordinator_with_agents.propose_vote(
            "test",
            {},
            "agent_1",
        )

        coordinator_with_agents.cast_vote(proposal_id, "agent_1", VoteDecision.APPROVE)
        coordinator_with_agents.cast_vote(proposal_id, "agent_2", VoteDecision.REJECT)
        coordinator_with_agents.cast_vote(proposal_id, "agent_3", VoteDecision.ABSTAIN)

        proposal = coordinator_with_agents.get_proposal(proposal_id)
        approve, reject, abstain = proposal.get_vote_counts()

        assert approve == 1
        assert reject == 1
        assert abstain == 1


# ==================== FAULT TOLERANCE TESTS ====================


@pytest.mark.asyncio
class TestFaultTolerance:
    """Test fault tolerance and recovery"""

    async def test_auto_recovery_reassigns_tasks(self, coordinator_with_agents):
        """Test auto-recovery reassigns tasks from failed agent"""
        # Assign task to agent_1
        task_id = coordinator_with_agents.submit_task(
            "test",
            {},
            required_capabilities={"phagocytosis"},
        )
        coordinator_with_agents.assign_tasks()

        task = coordinator_with_agents.get_task(task_id)
        failed_agent = task.assigned_to

        # Simulate agent failure
        agent = coordinator_with_agents.get_agent(failed_agent)
        agent.last_heartbeat = datetime.now() - timedelta(seconds=35)

        # Check health (triggers recovery)
        coordinator_with_agents.check_agent_health()

        # Task should be back in pending state
        task_after = coordinator_with_agents.get_task(task_id)
        assert task_after.status == TaskStatus.PENDING
        assert task_after.assigned_to is None

    async def test_leader_failure_triggers_reelection(self, coordinator_with_agents):
        """Test leader failure triggers re-election"""
        # Elect leader
        leader_id = coordinator_with_agents.elect_leader()

        # Simulate leader failure
        leader = coordinator_with_agents.get_agent(leader_id)
        leader.last_heartbeat = datetime.now() - timedelta(seconds=35)

        # Check health
        coordinator_with_agents.check_agent_health()

        # Leader should be cleared
        assert coordinator_with_agents._leader_id is None

    async def test_unregister_leader_triggers_reelection(self, coordinator_with_agents):
        """Test unregistering leader clears leader ID"""
        # Elect leader
        leader_id = coordinator_with_agents.elect_leader()

        # Unregister leader
        coordinator_with_agents.unregister_agent(leader_id)

        # Leader should be None
        assert coordinator_with_agents._leader_id is None

    async def test_task_max_retries_exceeded(self, coordinator_with_agents):
        """Test task fails after max retries"""
        task_id = coordinator_with_agents.submit_task(
            "test",
            {},
            required_capabilities={"phagocytosis"},
        )

        task = coordinator_with_agents.get_task(task_id)
        task.retries = 3  # At max
        task.status = TaskStatus.ASSIGNED
        task.assigned_to = "agent_1"

        # Simulate agent failure
        agent = coordinator_with_agents.get_agent("agent_1")
        agent.last_heartbeat = datetime.now() - timedelta(seconds=35)

        # Trigger recovery
        coordinator_with_agents.check_agent_health()

        # Task should be FAILED (max retries exceeded)
        task_after = coordinator_with_agents.get_task(task_id)
        assert task_after.status == TaskStatus.FAILED
        assert "Max retries" in task_after.error

    async def test_recovery_metrics(self, coordinator_with_agents):
        """Test recovery increments metrics"""
        # Assign task
        task_id = coordinator_with_agents.submit_task(
            "test",
            {},
            required_capabilities={"phagocytosis"},
        )
        coordinator_with_agents.assign_tasks()

        task = coordinator_with_agents.get_task(task_id)
        failed_agent = task.assigned_to

        # Simulate failure
        agent = coordinator_with_agents.get_agent(failed_agent)
        agent.last_heartbeat = datetime.now() - timedelta(seconds=35)

        # Trigger recovery
        coordinator_with_agents.check_agent_health()

        metrics = coordinator_with_agents.get_coordinator_metrics()
        assert metrics["failures_detected"] == 1
        assert metrics["recoveries_performed"] == 1


# ==================== METRICS TESTS ====================


@pytest.mark.asyncio
class TestMetrics:
    """Test metrics collection"""

    async def test_get_coordinator_metrics(self, coordinator_with_agents):
        """Test retrieving comprehensive metrics"""
        # Elect leader
        coordinator_with_agents.elect_leader()

        # Submit some tasks
        coordinator_with_agents.submit_task("task1", {})
        coordinator_with_agents.submit_task("task2", {})

        metrics = coordinator_with_agents.get_coordinator_metrics()

        assert metrics["agents_total"] == 3
        assert metrics["agents_alive"] == 3
        assert metrics["has_leader"] is True
        assert metrics["leader_id"] is not None
        assert metrics["tasks_total"] == 2
        assert metrics["tasks_pending"] == 2

    async def test_metrics_averages(self, coordinator):
        """Test average health and load calculation"""
        coordinator.register_agent("agent_1", health_score=0.8)
        coordinator.register_agent("agent_2", health_score=1.0)

        coordinator.update_agent_load("agent_1", 0.4)
        coordinator.update_agent_load("agent_2", 0.6)

        metrics = coordinator.get_coordinator_metrics()

        assert metrics["average_health"] == 0.9  # (0.8 + 1.0) / 2
        assert metrics["average_load"] == 0.5  # (0.4 + 0.6) / 2

    async def test_repr(self, coordinator_with_agents):
        """Test string representation"""
        coordinator_with_agents.elect_leader()

        repr_str = repr(coordinator_with_agents)

        assert "DistributedCoordinator" in repr_str
        assert "agents=3/3" in repr_str


# ==================== INTEGRATION TESTS ====================


@pytest.mark.asyncio
class TestDistributedCoordinatorIntegration:
    """Test full integration scenarios"""

    async def test_full_workflow(self, coordinator):
        """Test complete workflow: register -> elect -> submit -> assign"""
        # 1. Register agents
        coordinator.register_agent("agent_1", capabilities={"work"}, priority=10)
        coordinator.register_agent("agent_2", capabilities={"work"}, priority=5)

        # 2. Elect leader
        leader_id = coordinator.elect_leader()
        assert leader_id == "agent_1"

        # 3. Submit tasks
        task_id1 = coordinator.submit_task("task1", {}, required_capabilities={"work"})
        task_id2 = coordinator.submit_task("task2", {}, required_capabilities={"work"})

        # 4. Assign tasks
        assigned = coordinator.assign_tasks()
        assert assigned == 2

        # 5. Complete tasks
        coordinator.complete_task(task_id1, result={"status": "done"})
        coordinator.complete_task(task_id2, result={"status": "done"})

        # Verify final state
        metrics = coordinator.get_coordinator_metrics()
        assert metrics["tasks_completed"] == 2
        assert metrics["tasks_pending"] == 0

    async def test_consensus_decision_workflow(self, coordinator_with_agents):
        """Test consensus decision workflow"""
        # 1. Propose vote
        proposal_id = coordinator_with_agents.propose_vote(
            "system_upgrade",
            {"version": "2.0"},
            "agent_1",
            required_quorum=0.66,  # Need 2/3 votes
        )

        # 2. Agents vote
        coordinator_with_agents.cast_vote(proposal_id, "agent_1", VoteDecision.APPROVE)
        coordinator_with_agents.cast_vote(proposal_id, "agent_2", VoteDecision.APPROVE)

        # 3. Tally votes
        quorum_reached, details = coordinator_with_agents.tally_votes(proposal_id)

        assert quorum_reached is True
        assert details["approved"] is True
        assert details["approve"] == 2

    async def test_fault_recovery_workflow(self, coordinator_with_agents):
        """Test full fault recovery workflow"""
        # 1. Elect leader
        leader_id = coordinator_with_agents.elect_leader()

        # 2. Submit and assign tasks
        task_id = coordinator_with_agents.submit_task(
            "critical_task",
            {},
            required_capabilities={"phagocytosis"},
        )
        coordinator_with_agents.assign_tasks()

        task = coordinator_with_agents.get_task(task_id)
        failed_agent = task.assigned_to

        # 3. Simulate agent failure
        agent = coordinator_with_agents.get_agent(failed_agent)
        agent.last_heartbeat = datetime.now() - timedelta(seconds=35)

        # 4. Detect failure and recover
        failed = coordinator_with_agents.check_agent_health()
        assert failed_agent in failed

        # 5. Verify task reassignment
        task_after = coordinator_with_agents.get_task(task_id)
        assert task_after.status == TaskStatus.PENDING
        assert task_after.retries == 1

        # 6. Re-assign task to healthy agent
        assigned = coordinator_with_agents.assign_tasks()
        assert assigned == 1

        task_final = coordinator_with_agents.get_task(task_id)
        assert task_final.assigned_to != failed_agent  # Different agent
