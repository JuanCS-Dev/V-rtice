"""Restoration Engine - Final 1% Coverage (99% → 100%)

Target: Line 214 in restoration.py
"""

import pytest
from coagulation.restoration import RestorationEngine, HealthCheck


class TestIdentifyUnhealthyReason:
    """Target: Line 214 - _identify_unhealthy_reason with no failed checks"""
    
    def test_identify_reason_no_failed_checks(self):
        """Line 214: Return 'Unknown' when no checks failed"""
        engine = RestorationEngine()
        
        # All checks passed
        checks = [
            HealthCheck(check_name="test1", passed=True, details="OK"),
            HealthCheck(check_name="test2", passed=True, details="OK"),
        ]
        
        reason = engine._identify_unhealthy_reason(checks)
        
        # Line 214: return "Unknown"
        assert reason == "Unknown"
    
    def test_identify_reason_with_failed_checks(self):
        """Contrast: With failed checks, line 215 executes"""
        engine = RestorationEngine()
        
        checks = [
            HealthCheck(check_name="test1", passed=False, details="Failed"),
            HealthCheck(check_name="test2", passed=True, details="OK"),
        ]
        
        reason = engine._identify_unhealthy_reason(checks)
        
        assert "test1" in reason
