"""
FASE A - Simple tests for MIP infrastructure modules
Targets:
- audit_trail.py: 63.6% → 95%+ (4 missing lines)
- hitl_queue.py: 58.3% → 95%+ (5 missing lines)
- knowledge_base.py: 42.9% → 95%+ (8 missing lines)

Zero mocks - Padrão Pagani Absoluto
EM NOME DE JESUS!
"""

import pytest
from datetime import datetime
from motor_integridade_processual.infrastructure.audit_trail import AuditLogger
from motor_integridade_processual.infrastructure.hitl_queue import HITLQueue
from motor_integridade_processual.infrastructure.knowledge_base import KnowledgeBase


class TestAuditLogger:
    """Test audit_trail.py - AuditLogger class."""

    def test_init(self):
        """Test AuditLogger initialization."""
        logger = AuditLogger()
        assert logger is not None
        assert isinstance(logger.log, list)
        assert len(logger.log) == 0

    def test_log_decision_basic(self):
        """Test logging a decision with minimal verdict."""
        logger = AuditLogger()

        # Create minimal verdict-like object
        class MinimalVerdict:
            action_plan_id = "test-123"
            final_decision = type('obj', (object,), {'value': 'approve'})()
            aggregate_score = 0.85
            confidence = 0.9

        verdict = MinimalVerdict()
        logger.log_decision(verdict)

        assert len(logger.log) == 1
        entry = logger.log[0]
        assert entry["action_plan_id"] == "test-123"
        assert entry["decision"] == "approve"
        assert entry["score"] == 0.85
        assert entry["confidence"] == 0.9

    def test_log_multiple_decisions(self):
        """Test logging multiple decisions."""
        logger = AuditLogger()

        class Verdict:
            def __init__(self, action_id, score):
                self.action_plan_id = action_id
                self.final_decision = type('obj', (object,), {'value': 'approve'})()
                self.aggregate_score = score
                self.confidence = 0.9

        for i in range(3):
            logger.log_decision(Verdict(f"action-{i}", 0.8 + i * 0.05))

        assert len(logger.log) == 3
        assert logger.log[0]["action_plan_id"] == "action-0"
        assert logger.log[2]["score"] == 0.9

    def test_get_history(self):
        """Test retrieving audit history."""
        logger = AuditLogger()

        class Verdict:
            action_plan_id = "test-456"
            final_decision = type('obj', (object,), {'value': 'deny'})()
            aggregate_score = 0.3
            confidence = 0.95

        logger.log_decision(Verdict())

        history = logger.get_history()
        assert len(history) == 1
        assert history[0]["action_plan_id"] == "test-456"

        # Verify it's a copy
        history.clear()
        assert len(logger.log) == 1

    def test_get_history_empty(self):
        """Test getting history when empty."""
        logger = AuditLogger()
        history = logger.get_history()
        assert history == []

    def test_timestamp_format(self):
        """Test timestamp is ISO format."""
        logger = AuditLogger()

        class Verdict:
            action_plan_id = "test-789"
            final_decision = type('obj', (object,), {'value': 'approve'})()
            aggregate_score = 0.75
            confidence = 0.85

        logger.log_decision(Verdict())

        timestamp_str = logger.log[0]["timestamp"]
        # Should be parseable as ISO format
        parsed = datetime.fromisoformat(timestamp_str)
        assert isinstance(parsed, datetime)


class TestHITLQueue:
    """Test hitl_queue.py - HITLQueue class."""

    def test_init(self):
        """Test HITLQueue initialization."""
        queue = HITLQueue()
        assert queue is not None
        assert isinstance(queue.queue, list)
        assert len(queue.queue) == 0

    def test_add_to_queue_requires_review(self):
        """Test adding verdict that requires review."""
        queue = HITLQueue()

        class Verdict:
            requires_human_review = True
            action_plan_id = "review-123"

        verdict = Verdict()
        queue.add_to_queue(verdict)

        assert len(queue.queue) == 1
        assert queue.queue[0].action_plan_id == "review-123"

    def test_add_to_queue_no_review_needed(self):
        """Test verdict not requiring review is not added."""
        queue = HITLQueue()

        class Verdict:
            requires_human_review = False
            action_plan_id = "no-review"

        queue.add_to_queue(Verdict())
        assert len(queue.queue) == 0

    def test_get_next(self):
        """Test getting next case from queue."""
        queue = HITLQueue()

        class Verdict:
            requires_human_review = True
            action_plan_id = "case-1"

        queue.add_to_queue(Verdict())

        result = queue.get_next()
        assert result.action_plan_id == "case-1"
        assert len(queue.queue) == 0

    def test_get_next_empty(self):
        """Test get_next on empty queue."""
        queue = HITLQueue()
        result = queue.get_next()
        assert result is None

    def test_get_next_fifo_order(self):
        """Test FIFO ordering."""
        queue = HITLQueue()

        for i in range(3):
            class Verdict:
                requires_human_review = True
                action_plan_id = f"case-{i}"

            queue.add_to_queue(Verdict())

        assert queue.get_next().action_plan_id == "case-0"
        assert queue.get_next().action_plan_id == "case-1"
        assert queue.get_next().action_plan_id == "case-2"

    def test_queue_size(self):
        """Test queue_size method."""
        queue = HITLQueue()
        assert queue.queue_size() == 0

        class Verdict:
            requires_human_review = True
            action_plan_id = "test"

        queue.add_to_queue(Verdict())
        assert queue.queue_size() == 1

        queue.get_next()
        assert queue.queue_size() == 0


class TestKnowledgeBase:
    """Test knowledge_base.py - KnowledgeBase class."""

    def test_init(self):
        """Test KnowledgeBase initialization."""
        kb = KnowledgeBase()
        assert kb is not None
        assert isinstance(kb.precedents, list)
        assert isinstance(kb.principles, list)
        assert len(kb.precedents) == 0
        assert len(kb.principles) == 0

    def test_store_precedent(self):
        """Test storing a precedent."""
        kb = KnowledgeBase()
        precedent = {
            "case_id": "case-001",
            "decision": "approve",
            "reasoning": "Test reasoning"
        }

        kb.store_precedent(precedent)
        assert len(kb.precedents) == 1
        assert kb.precedents[0] == precedent

    def test_store_multiple_precedents(self):
        """Test storing multiple precedents."""
        kb = KnowledgeBase()
        for i in range(3):
            kb.store_precedent({"case_id": f"case-{i}"})

        assert len(kb.precedents) == 3

    def test_find_similar(self):
        """Test finding similar cases."""
        kb = KnowledgeBase()

        # Store 15 precedents
        for i in range(15):
            kb.store_precedent({
                "case_id": f"case-{i}",
                "type": "security" if i % 2 == 0 else "privacy"
            })

        # find_similar returns up to 10 cases
        results = kb.find_similar("security breach")
        assert len(results) <= 10
        assert isinstance(results, list)

    def test_find_similar_empty(self):
        """Test find_similar on empty knowledge base."""
        kb = KnowledgeBase()
        results = kb.find_similar("any query")
        assert results == []

    def test_get_principle(self):
        """Test retrieving a principle by name."""
        kb = KnowledgeBase()
        principle = {
            "name": "do_no_harm",
            "description": "First, do no harm"
        }

        kb.principles.append(principle)

        result = kb.get_principle("do_no_harm")
        assert result == principle
        assert result["description"] == "First, do no harm"

    def test_get_principle_not_found(self):
        """Test getting non-existent principle."""
        kb = KnowledgeBase()
        result = kb.get_principle("nonexistent")
        assert result is None

    def test_get_principle_multiple(self):
        """Test getting principle from multiple stored principles."""
        kb = KnowledgeBase()
        principles = [
            {"name": "transparency", "value": "be transparent"},
            {"name": "fairness", "value": "be fair"},
            {"name": "accountability", "value": "be accountable"}
        ]

        for p in principles:
            kb.principles.append(p)

        result = kb.get_principle("fairness")
        assert result["value"] == "be fair"

    def test_precedent_count(self):
        """Test counting precedents."""
        kb = KnowledgeBase()
        assert len(kb.precedents) == 0

        kb.store_precedent({"id": "1"})
        assert len(kb.precedents) == 1

        kb.store_precedent({"id": "2"})
        assert len(kb.precedents) == 2
