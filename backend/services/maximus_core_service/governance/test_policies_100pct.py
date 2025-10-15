"""
Policies Module - 100% Coverage Test Suite

Tests specifically targeting uncovered lines in policies.py to achieve 100% coverage.
Missing lines: 367, 376, 380, 384, 389, 405-414, 418

Author: Claude Code + JuanCS-Dev
Date: 2025-10-14
"""

from datetime import datetime, timedelta

import pytest

from .base import PolicyType
from .policies import PolicyRegistry

# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def policy_registry():
    """Create policy registry."""
    return PolicyRegistry()


# ============================================================================
# ERROR PATH TESTS (Lines 367, 389, 405)
# ============================================================================


class TestPolicyRegistryErrorPaths:
    """Test error handling paths in PolicyRegistry."""

    def test_get_policy_invalid_type_raises_error(self, policy_registry):
        """Test get_policy with invalid type raises ValueError (line 367)."""
        # Create a fake policy type that doesn't exist
        with pytest.raises(ValueError, match="not found in registry"):
            # Remove a policy to trigger error
            del policy_registry.policies[PolicyType.ETHICAL_USE]
            policy_registry.get_policy(PolicyType.ETHICAL_USE)

    def test_approve_policy_invalid_type_raises_error(self, policy_registry):
        """Test approve_policy with invalid type raises ValueError (line 389)."""
        # Remove policy first
        del policy_registry.policies[PolicyType.DATA_PRIVACY]

        with pytest.raises(ValueError, match="not found"):
            policy_registry.approve_policy(PolicyType.DATA_PRIVACY, "dec-123")

    def test_update_policy_version_invalid_type_raises_error(self, policy_registry):
        """Test update_policy_version with invalid type raises ValueError (line 405)."""
        # Remove policy first
        del policy_registry.policies[PolicyType.RED_TEAMING]

        with pytest.raises(ValueError, match="not found"):
            policy_registry.update_policy_version(
                policy_type=PolicyType.RED_TEAMING,
                new_version="2.0",
                updated_rules=["New rule"],
                description="Updated policy",
            )


# ============================================================================
# UNCOVERED METHOD TESTS (Lines 376, 380, 384, 405-414, 418)
# ============================================================================


class TestPolicyRegistryUntestedMethods:
    """Test previously untested methods in PolicyRegistry."""

    def test_get_all_policies(self, policy_registry):
        """Test get_all_policies returns all policies (line 372)."""
        all_policies = policy_registry.get_all_policies()

        # Should return all 5 policies
        assert len(all_policies) == 5
        assert all(isinstance(p, type(all_policies[0])) for p in all_policies)

    def test_get_policies_by_scope_all(self, policy_registry):
        """Test get_policies_by_scope with 'all' scope (line 376)."""
        policies = policy_registry.get_policies_by_scope("all")

        # All policies with scope="all" should be included
        assert len(policies) > 0

    def test_get_policies_by_scope_specific(self, policy_registry):
        """Test get_policies_by_scope with specific scope (line 376)."""
        # Red teaming policy has specific scope
        policies = policy_registry.get_policies_by_scope("c2_orchestration_service")

        # Should find red teaming policy
        assert any(p.policy_type == PolicyType.RED_TEAMING for p in policies)

    def test_get_policies_requiring_review(self, policy_registry):
        """Test get_policies_requiring_review (line 380)."""
        # Make a policy due for review
        policy = policy_registry.get_policy(PolicyType.ETHICAL_USE)
        policy.next_review_date = datetime.utcnow() - timedelta(days=1)  # Past due

        policies_due = policy_registry.get_policies_requiring_review()

        # Should include the overdue policy
        assert any(p.policy_type == PolicyType.ETHICAL_USE for p in policies_due)

    def test_get_unapproved_policies(self, policy_registry):
        """Test get_unapproved_policies (line 384)."""
        # All policies start unapproved
        unapproved = policy_registry.get_unapproved_policies()

        assert len(unapproved) == 5  # All 5 policies should be unapproved

        # Approve one
        policy_registry.approve_policy(PolicyType.ETHICAL_USE, "dec-001")

        unapproved = policy_registry.get_unapproved_policies()

        assert len(unapproved) == 4  # Now only 4 unapproved

    def test_update_policy_version_complete(self, policy_registry):
        """Test update_policy_version updates all fields (lines 405-414)."""
        new_rules = [
            "RULE-EU-001-v2: Updated rule",
            "RULE-EU-002-v2: Another updated rule",
        ]
        new_description = "Updated version 2.0 of Ethical Use Policy"

        policy_registry.update_policy_version(
            policy_type=PolicyType.ETHICAL_USE,
            new_version="2.0",
            updated_rules=new_rules,
            description=new_description,
        )

        policy = policy_registry.get_policy(PolicyType.ETHICAL_USE)

        # Verify all fields updated (lines 409-414)
        assert policy.version == "2.0"
        assert policy.rules == new_rules
        assert policy.description == new_description
        assert policy.last_review_date is not None
        assert policy.next_review_date is not None
        assert policy.approved_by_erb is False  # Requires re-approval

    def test_get_policy_summary(self, policy_registry):
        """Test get_policy_summary returns complete summary (line 418)."""
        # Approve some policies
        policy_registry.approve_policy(PolicyType.ETHICAL_USE, "dec-001")
        policy_registry.approve_policy(PolicyType.DATA_PRIVACY, "dec-002")

        summary = policy_registry.get_policy_summary()

        # Verify all summary fields (line 418-432)
        assert summary["total_policies"] == 5
        assert summary["approved_policies"] == 2
        assert summary["pending_approval"] == 3
        assert "due_for_review" in summary
        assert "policies" in summary

        # Verify policies dict structure
        assert PolicyType.ETHICAL_USE.value in summary["policies"]
        policy_info = summary["policies"][PolicyType.ETHICAL_USE.value]
        assert "version" in policy_info
        assert "approved" in policy_info
        assert "enforcement_level" in policy_info
        assert "total_rules" in policy_info
        assert "days_until_review" in policy_info


# ============================================================================
# INTEGRATION TESTS
# ============================================================================


class TestPolicyRegistryIntegration:
    """Integration tests for complete PolicyRegistry workflows."""

    def test_complete_policy_lifecycle(self, policy_registry):
        """Test complete lifecycle: create, review, approve, update."""
        policy_type = PolicyType.WHISTLEBLOWER

        # 1. Get initial policy
        policy = policy_registry.get_policy(policy_type)
        assert not policy.approved_by_erb

        # 2. Check it's in unapproved list
        unapproved = policy_registry.get_unapproved_policies()
        assert any(p.policy_type == policy_type for p in unapproved)

        # 3. Approve policy
        policy_registry.approve_policy(policy_type, "erb-decision-123")
        policy = policy_registry.get_policy(policy_type)
        assert policy.approved_by_erb
        assert policy.erb_decision_id == "erb-decision-123"

        # 4. Update policy version
        policy_registry.update_policy_version(
            policy_type=policy_type,
            new_version="2.0",
            updated_rules=["RULE-WB-NEW: New whistleblower rule"],
            description="Updated whistleblower policy v2.0",
        )

        # 5. Verify approval was reset
        policy = policy_registry.get_policy(policy_type)
        assert policy.version == "2.0"
        assert not policy.approved_by_erb  # Needs re-approval

    def test_policy_scope_filtering(self, policy_registry):
        """Test scope-based policy filtering."""
        # Get policies for general scope
        all_scope = policy_registry.get_policies_by_scope("maximus")
        assert len(all_scope) > 0  # Should have policies with scope="all"

        # Get policies for red team scope
        red_team_scope = policy_registry.get_policies_by_scope("offensive_gateway")
        assert any(p.policy_type == PolicyType.RED_TEAMING for p in red_team_scope)

        # Get policies for specific scope
        specific = policy_registry.get_policies_by_scope("c2_orchestration_service")
        assert len(specific) > 0

    def test_policy_review_tracking(self, policy_registry):
        """Test policy review date tracking."""
        # Make policy due for review
        policy = policy_registry.get_policy(PolicyType.DATA_PRIVACY)
        policy.next_review_date = datetime.utcnow() - timedelta(days=10)

        # Check it appears in review list
        due_for_review = policy_registry.get_policies_requiring_review()
        assert any(p.policy_type == PolicyType.DATA_PRIVACY for p in due_for_review)

        # Approve it (updates review dates)
        policy_registry.approve_policy(PolicyType.DATA_PRIVACY, "dec-review")

        # Should no longer be due (new next_review_date set)
        policy = policy_registry.get_policy(PolicyType.DATA_PRIVACY)
        assert policy.next_review_date > datetime.utcnow()


# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
