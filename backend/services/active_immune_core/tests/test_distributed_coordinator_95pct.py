"""Distributed Coordinator - Surgical Tests for 95%+ Coverage

Targets uncovered edge cases and error paths to achieve 95%+ coverage.

Coverage targets (28 missing statements):
- Line 80: AgentNode.__hash__()
- Line 113: DistributedTask.is_timeout() when not assigned
- Lines 295-300: Unregister agent with assigned tasks
- Lines 333, 353: Update non-existent agent
- Line 393: check_agent_health() skip dead agents
- Lines 473-474: elect_leader() when election in progress
- Line 527: get_leader() when no leader exists
- Line 593: assign_tasks() with empty queue
- Line 602: assign_tasks() with invalid task
- Lines 668, 705: complete/fail non-existent task
- Lines 747, 750-752: check_task_timeouts() max retries
- Lines 812-813, 823-824: cast_vote() error paths
- Lines 847, 851: tally_votes() error paths

NO MOCKS, NO PLACEHOLDERS, NO TODOS - PRODUCTION-READY.

Authors: Juan & Claude
Version: 1.0.0
"""

import time
from datetime import datetime, timedelta

import pytest

from agents.distributed_coordinator import (
    AgentNode,
    AgentRole,
    DistributedCoordinator,
    DistributedTask,
    TaskStatus,
    VoteDecision,
    VoteProposal,
)


# ==================== FIXTURES ====================


@pytest.fixture
def coordinator() -> DistributedCoordinator:
    """Create coordinator with fast timeouts for testing"""
    return DistributedCoordinator(
        heartbeat_interval=1,
        heartbeat_timeout=5,
        election_timeout=5,
        task_timeout=10,
        enable_auto_recovery=True,
    )


# ==================== MODEL TESTS ====================


class TestAgentNodeHash:
    """Test AgentNode.__hash__() for set operations (line 80)"""

    def test_agent_node_hash_for_set_operations(self):
        """Test AgentNode can be used in sets via __hash__"""
        # ARRANGE: Create agents
        agent1 = AgentNode(id="agent_1", priority=10)
        agent2 = AgentNode(id="agent_2", priority=20)
        agent3 = AgentNode(id="agent_3", priority=30)

        # ACT: Create set and verify hash works
        agent_set = {agent1, agent2, agent3}

        # ASSERT: Hash function returns integers for all agents
        assert all(isinstance(hash(a), int) for a in agent_set)
        assert len(agent_set) == 3
        # Verify hash is based on ID
        assert hash(agent1) == hash(agent1.id)


class TestDistributedTaskTimeout:
    """Test DistributedTask.is_timeout() edge cases (line 113)"""

    def test_task_timeout_when_not_assigned(self):
        """Test is_timeout() returns False when task not yet assigned"""
        # ARRANGE: Create task without assignment
        task = DistributedTask(
            task_type="test",
            payload={"data": "test"},
            timeout_seconds=10,
        )
        assert task.assigned_at is None

        # ACT: Check timeout
        result = task.is_timeout()

        # ASSERT: Not timed out (not assigned yet)
        assert result is False


# ==================== AGENT MANAGEMENT EDGE CASES ====================


class TestUnregisterAgentWithTasks:
    """Test unregister_agent() with assigned tasks (lines 295-300)"""

    def test_unregister_agent_reassigns_tasks(self, coordinator: DistributedCoordinator):
        """Test unregistering agent moves its assigned tasks back to queue"""
        # ARRANGE: Register agents and assign task
        coordinator.register_agent("agent_1", capabilities={"capability_a"})
        coordinator.register_agent("agent_2", capabilities={"capability_a"})

        task_id = coordinator.submit_task(
            "test_task",
            {"data": "test"},
            required_capabilities={"capability_a"},
        )

        # Assign task to agent_1
        coordinator.assign_tasks()
        task = coordinator.get_task(task_id)
        assert task.assigned_to == "agent_1"
        assert task.status == TaskStatus.ASSIGNED

        # ACT: Unregister agent_1 (who has assigned task)
        result = coordinator.unregister_agent("agent_1")

        # ASSERT: Task returned to queue
        assert result is True
        task = coordinator.get_task(task_id)
        assert task.status == TaskStatus.PENDING
        assert task.assigned_to is None
        assert task.assigned_at is None
        assert task_id in coordinator._task_queue


class TestUpdateAgentNotFound:
    """Test update methods with non-existent agent (lines 333, 353)"""

    def test_update_health_agent_not_found(self, coordinator: DistributedCoordinator):
        """Test update_agent_health() returns False for non-existent agent"""
        # ACT: Update health of non-existent agent
        result = coordinator.update_agent_health("non_existent", 0.8)

        # ASSERT: Returns False
        assert result is False

    def test_update_load_agent_not_found(self, coordinator: DistributedCoordinator):
        """Test update_agent_load() returns False for non-existent agent"""
        # ACT: Update load of non-existent agent
        result = coordinator.update_agent_load("non_existent", 0.5)

        # ASSERT: Returns False
        assert result is False


class TestCheckHealthSkipDeadAgents:
    """Test check_agent_health() skips already-dead agents (line 393)"""

    def test_check_health_skips_already_dead_agents(self, coordinator: DistributedCoordinator):
        """Test check_agent_health() continues when agent already marked dead"""
        # ARRANGE: Register agent and mark as dead
        coordinator.register_agent("agent_1")
        agent = coordinator.get_agent("agent_1")
        agent.is_alive = False
        agent.last_heartbeat = datetime.now() - timedelta(seconds=100)

        initial_failures = coordinator._failures_detected

        # ACT: Check health
        failed = coordinator.check_agent_health()

        # ASSERT: Already-dead agent not counted again
        assert len(failed) == 0
        assert coordinator._failures_detected == initial_failures


# ==================== LEADER ELECTION EDGE CASES ====================


class TestElectionInProgress:
    """Test elect_leader() when election already in progress (lines 473-474)"""

    def test_elect_leader_already_in_progress(self, coordinator: DistributedCoordinator):
        """Test elect_leader() returns early when election already running"""
        # ARRANGE: Register agents and manually set election flag
        coordinator.register_agent("agent_1", priority=10)
        coordinator.register_agent("agent_2", priority=20)

        # Simulate election in progress
        coordinator._election_in_progress = True
        coordinator._leader_id = "agent_1"

        initial_elections = coordinator._elections_total

        # ACT: Try to start new election
        result = coordinator.elect_leader()

        # ASSERT: Returns current leader without new election
        assert result == "agent_1"
        assert coordinator._elections_total == initial_elections  # No new election


class TestGetLeaderWhenNone:
    """Test get_leader() when no leader exists (line 527)"""

    def test_get_leader_returns_none_when_no_leader(self, coordinator: DistributedCoordinator):
        """Test get_leader() returns None when no leader elected"""
        # ARRANGE: Coordinator with no leader
        assert coordinator._leader_id is None

        # ACT: Get leader
        result = coordinator.get_leader()

        # ASSERT: Returns None
        assert result is None


# ==================== TASK ASSIGNMENT EDGE CASES ====================


class TestAssignTasksEmptyQueue:
    """Test assign_tasks() with empty queue (line 593)"""

    def test_assign_tasks_with_empty_queue(self, coordinator: DistributedCoordinator):
        """Test assign_tasks() returns 0 when queue is empty"""
        # ARRANGE: Coordinator with agents but no tasks
        coordinator.register_agent("agent_1", capabilities={"test"})
        assert len(coordinator._task_queue) == 0

        # ACT: Assign tasks
        result = coordinator.assign_tasks()

        # ASSERT: Returns 0
        assert result == 0


class TestAssignTasksInvalidTask:
    """Test assign_tasks() with invalid task in queue (line 602)"""

    def test_assign_tasks_skips_invalid_task(self, coordinator: DistributedCoordinator):
        """Test assign_tasks() continues when task not found or not pending"""
        # ARRANGE: Register agent
        coordinator.register_agent("agent_1", capabilities={"test"})

        # Add non-existent task ID to queue
        coordinator._task_queue.append("non_existent_task_id")

        # ACT: Assign tasks
        result = coordinator.assign_tasks()

        # ASSERT: Skips invalid task, returns 0
        assert result == 0


# ==================== TASK COMPLETION EDGE CASES ====================


class TestCompleteTaskNotFound:
    """Test complete_task() with non-existent task (line 668)"""

    def test_complete_task_not_found(self, coordinator: DistributedCoordinator):
        """Test complete_task() returns False for non-existent task"""
        # ACT: Complete non-existent task
        result = coordinator.complete_task("non_existent_task_id")

        # ASSERT: Returns False
        assert result is False


class TestFailTaskNotFound:
    """Test fail_task() with non-existent task (line 705)"""

    def test_fail_task_not_found(self, coordinator: DistributedCoordinator):
        """Test fail_task() returns False for non-existent task"""
        # ACT: Fail non-existent task
        result = coordinator.fail_task("non_existent_task_id", "error")

        # ASSERT: Returns False
        assert result is False


# ==================== TASK TIMEOUT EDGE CASES ====================


class TestTaskTimeoutMaxRetries:
    """Test check_task_timeouts() with max retries (lines 747, 750-752)"""

    def test_task_timeout_reassigns_within_retries(self, coordinator: DistributedCoordinator):
        """Test check_task_timeouts() reassigns task when retries available"""
        # ARRANGE: Create task with timeout in past
        coordinator.register_agent("agent_1", capabilities={"test"})

        task_id = coordinator.submit_task(
            "test_task",
            {"data": "test"},
            required_capabilities={"test"},
            timeout_seconds=1,
        )

        # Assign task
        coordinator.assign_tasks()
        task = coordinator.get_task(task_id)

        # Simulate timeout by backdating assignment
        task.assigned_at = datetime.now() - timedelta(seconds=5)
        task.retries = 2  # Still has 1 retry left (max=3)

        # ACT: Check timeouts
        timed_out = coordinator.check_task_timeouts()

        # ASSERT: Task reassigned (line 747)
        assert task_id in timed_out
        assert task.status == TaskStatus.PENDING
        assert task.retries == 3
        assert task_id in coordinator._task_queue

    def test_task_timeout_fails_when_max_retries_exceeded(
        self, coordinator: DistributedCoordinator
    ):
        """Test check_task_timeouts() fails task when max retries exceeded"""
        # ARRANGE: Create task with max retries already used
        coordinator.register_agent("agent_1", capabilities={"test"})

        task_id = coordinator.submit_task(
            "test_task",
            {"data": "test"},
            required_capabilities={"test"},
            timeout_seconds=1,
        )

        # Assign task
        coordinator.assign_tasks()
        task = coordinator.get_task(task_id)

        # Simulate timeout and max retries
        task.assigned_at = datetime.now() - timedelta(seconds=5)
        task.retries = 3  # Max retries reached

        initial_failed = coordinator._tasks_failed

        # ACT: Check timeouts
        timed_out = coordinator.check_task_timeouts()

        # ASSERT: Task failed (lines 750-752)
        assert task.status == TaskStatus.FAILED
        assert "Max retries exceeded" in task.error
        assert coordinator._tasks_failed == initial_failed + 1
        assert task_id not in timed_out  # Not in timed_out list (failed instead)


# ==================== VOTING EDGE CASES ====================


class TestCastVoteProposalNotFound:
    """Test cast_vote() when proposal not found (lines 812-813)"""

    def test_cast_vote_proposal_not_found(self, coordinator: DistributedCoordinator):
        """Test cast_vote() returns False for non-existent proposal"""
        # ARRANGE: Register agent
        coordinator.register_agent("agent_1")

        # ACT: Vote on non-existent proposal
        result = coordinator.cast_vote(
            "non_existent_proposal",
            "agent_1",
            VoteDecision.APPROVE,
        )

        # ASSERT: Returns False
        assert result is False


class TestCastVoteProposalTimedOut:
    """Test cast_vote() when proposal timed out (lines 823-824)"""

    def test_cast_vote_proposal_timed_out(self, coordinator: DistributedCoordinator):
        """Test cast_vote() returns False when proposal has timed out"""
        # ARRANGE: Register agent and create proposal
        coordinator.register_agent("agent_1")

        proposal_id = coordinator.propose_vote(
            "test_proposal",
            {"data": "test"},
            "agent_1",
            timeout_seconds=1,
        )

        # Simulate timeout by backdating proposal
        proposal = coordinator.get_proposal(proposal_id)
        proposal.created_at = datetime.now() - timedelta(seconds=5)

        # ACT: Try to vote on timed-out proposal
        result = coordinator.cast_vote(
            proposal_id,
            "agent_1",
            VoteDecision.APPROVE,
        )

        # ASSERT: Returns False
        assert result is False


class TestTallyVotesProposalNotFound:
    """Test tally_votes() when proposal not found (line 847)"""

    def test_tally_votes_proposal_not_found(self, coordinator: DistributedCoordinator):
        """Test tally_votes() returns None for non-existent proposal"""
        # ACT: Tally votes for non-existent proposal
        result = coordinator.tally_votes("non_existent_proposal")

        # ASSERT: Returns None
        assert result is None


class TestTallyVotesNoAliveAgents:
    """Test tally_votes() when no alive agents (line 851)"""

    def test_tally_votes_no_alive_agents(self, coordinator: DistributedCoordinator):
        """Test tally_votes() returns error when no alive agents"""
        # ARRANGE: Register agent and create proposal
        coordinator.register_agent("agent_1")

        proposal_id = coordinator.propose_vote(
            "test_proposal",
            {"data": "test"},
            "agent_1",
        )

        # Kill all agents
        for agent in coordinator._agents.values():
            agent.is_alive = False

        # ACT: Tally votes with no alive agents
        result = coordinator.tally_votes(proposal_id)

        # ASSERT: Returns error
        assert result is not None
        quorum_reached, details = result
        assert quorum_reached is False
        assert "error" in details
        assert details["error"] == "No alive agents"


# ==================== INTEGRATION TESTS ====================


class TestEdgeCaseIntegration:
    """Integration tests for edge case scenarios"""

    def test_election_tie_breaking_by_agent_id(self, coordinator: DistributedCoordinator):
        """Test leader election tie-breaking uses lexicographic agent ID"""
        # ARRANGE: Register agents with identical scores
        coordinator.register_agent("zebra", priority=10, health_score=1.0)
        coordinator.register_agent("alpha", priority=10, health_score=1.0)
        coordinator.register_agent("beta", priority=10, health_score=1.0)

        # Both have same priority and health, so score is identical

        # ACT: Elect leader
        leader_id = coordinator.elect_leader()

        # ASSERT: "alpha" wins (lexicographically first)
        assert leader_id == "alpha"
        assert coordinator.get_agent("alpha").role == AgentRole.LEADER

    def test_task_reassignment_cascade_on_multiple_failures(
        self, coordinator: DistributedCoordinator
    ):
        """Test cascading task reassignment when multiple agents fail"""
        # ARRANGE: Register multiple agents
        coordinator.register_agent("agent_1", capabilities={"skill_a"})
        coordinator.register_agent("agent_2", capabilities={"skill_a"})
        coordinator.register_agent("agent_3", capabilities={"skill_a"})

        # Submit and assign tasks
        task_id_1 = coordinator.submit_task("task_1", {}, {"skill_a"})
        task_id_2 = coordinator.submit_task("task_2", {}, {"skill_a"})

        coordinator.assign_tasks()

        # Get initial assignments
        task_1 = coordinator.get_task(task_id_1)
        task_2 = coordinator.get_task(task_id_2)

        initial_agent_1 = task_1.assigned_to
        initial_agent_2 = task_2.assigned_to

        # ACT: Simulate agent failures by timeout
        for agent in coordinator._agents.values():
            agent.last_heartbeat = datetime.now() - timedelta(seconds=100)

        failed_agents = coordinator.check_agent_health()

        # ASSERT: All agents failed, tasks reassigned
        assert len(failed_agents) == 3
        assert task_1.status == TaskStatus.PENDING
        assert task_2.status == TaskStatus.PENDING
        assert task_1.retries == 1
        assert task_2.retries == 1
        assert coordinator._recoveries_performed == 3

    def test_consensus_with_mixed_votes_and_quorum(
        self, coordinator: DistributedCoordinator
    ):
        """Test consensus voting with mixed votes requiring exact quorum"""
        # ARRANGE: Register 5 agents
        for i in range(5):
            coordinator.register_agent(f"agent_{i}")

        # Create proposal with 60% quorum requirement
        proposal_id = coordinator.propose_vote(
            "critical_decision",
            {"action": "upgrade"},
            "agent_0",
            required_quorum=0.6,
        )

        # ACT: Cast exactly 3 votes (60% of 5)
        coordinator.cast_vote(proposal_id, "agent_0", VoteDecision.APPROVE)
        coordinator.cast_vote(proposal_id, "agent_1", VoteDecision.APPROVE)
        coordinator.cast_vote(proposal_id, "agent_2", VoteDecision.REJECT)

        # Tally votes
        quorum_reached, details = coordinator.tally_votes(proposal_id)

        # ASSERT: Quorum reached (3/5 = 60%), approved (2 approve > 1 reject)
        assert quorum_reached is True
        assert details["approved"] is True
        assert details["approve"] == 2
        assert details["reject"] == 1
        assert details["actual_quorum"] == 0.6
