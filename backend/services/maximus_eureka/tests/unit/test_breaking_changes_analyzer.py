"""
Unit tests for Breaking Changes Analyzer.

Tests LLM-powered analysis of version diffs to detect breaking changes.
"""

import pytest
import json
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock

from llm.breaking_changes_analyzer import (
    BreakingChangesAnalyzer,
    BreakingChange,
    BreakingChangesReport,
    BreakingSeverity,
    AnalysisError,
    analyze_breaking_changes,
)


# Fixtures

@pytest.fixture
def mock_gemini_response():
    """Mock Gemini API response"""
    return Mock(
        text=json.dumps({
            "breaking_changes": [
                {
                    "severity": "CRITICAL",
                    "category": "API signature change",
                    "description": "Removed verify parameter default value",
                    "affected_apis": ["requests.get", "requests.post"],
                    "migration_steps": [
                        "Add verify=True explicitly to all requests calls",
                        "Review SSL certificate handling"
                    ],
                    "confidence": 0.95
                },
                {
                    "severity": "HIGH",
                    "category": "Behavior change",
                    "description": "Timeout now raises ConnectionError instead of Timeout",
                    "affected_apis": ["requests.request"],
                    "migration_steps": [
                        "Update exception handling to catch ConnectionError"
                    ],
                    "confidence": 0.85
                }
            ],
            "has_breaking_changes": True,
            "overall_risk": "HIGH",
            "estimated_migration_time": "2-4 hours",
            "reasoning": "Two significant breaking changes requiring code updates"
        })
    )


@pytest.fixture
def sample_diff():
    """Sample git diff content"""
    return """
diff --git a/requests/api.py b/requests/api.py
--- a/requests/api.py
+++ b/requests/api.py
@@ -45,7 +45,7 @@ def request(method, url, **kwargs):
-def get(url, params=None, **kwargs):
+def get(url, params=None, verify=True, **kwargs):
     kwargs.setdefault('allow_redirects', True)
-    return request('get', url, params=params, **kwargs)
+    return request('get', url, params=params, verify=verify, **kwargs)
"""


# Tests: Initialization

def test_analyzer_initialization():
    """Test analyzer can be initialized"""
    analyzer = BreakingChangesAnalyzer(api_key="test_key")
    
    assert analyzer.api_key == "test_key"
    assert analyzer.MODEL == "gemini-2.0-flash-exp"
    assert analyzer.TEMPERATURE == 0.1


def test_analyzer_initialization_no_key():
    """Test analyzer with no API key (uses env var)"""
    with patch.dict('os.environ', {'GEMINI_API_KEY': 'env_key'}):
        analyzer = BreakingChangesAnalyzer()
        # Should not raise, will use env var
        assert analyzer is not None


# Tests: analyze_diff

@pytest.mark.asyncio
async def test_analyze_diff_success(mock_gemini_response, sample_diff):
    """Test successful diff analysis"""
    analyzer = BreakingChangesAnalyzer(api_key="test_key")
    
    # Mock Gemini API call
    with patch.object(analyzer.model, 'generate_content', return_value=mock_gemini_response):
        report = await analyzer.analyze_diff(
            package="requests",
            from_version="2.28.0",
            to_version="2.31.0",
            diff_content=sample_diff
        )
    
    # Assertions
    assert report.package == "requests"
    assert report.from_version == "2.28.0"
    assert report.to_version == "2.31.0"
    assert report.has_breaking_changes is True
    assert len(report.breaking_changes) == 2
    assert report.overall_risk == BreakingSeverity.HIGH
    assert report.estimated_migration_time == "2-4 hours"
    assert report.critical_count == 1
    assert report.high_count == 1


@pytest.mark.asyncio
async def test_analyze_diff_no_breaking_changes(sample_diff):
    """Test diff with no breaking changes"""
    analyzer = BreakingChangesAnalyzer(api_key="test_key")
    
    # Mock response with no breaking changes
    mock_response = Mock(
        text=json.dumps({
            "breaking_changes": [],
            "has_breaking_changes": False,
            "overall_risk": "INFO",
            "estimated_migration_time": "< 1 hour",
            "reasoning": "Only internal changes, no public API affected"
        })
    )
    
    with patch.object(analyzer.model, 'generate_content', return_value=mock_response):
        report = await analyzer.analyze_diff(
            "safe-package", "1.0.0", "1.0.1", sample_diff
        )
    
    assert report.has_breaking_changes is False
    assert len(report.breaking_changes) == 0
    assert report.overall_risk == BreakingSeverity.INFO
    assert "✅ No breaking changes" in report.summary()


@pytest.mark.asyncio
async def test_analyze_diff_truncates_large_diff():
    """Test that large diffs are truncated"""
    analyzer = BreakingChangesAnalyzer(api_key="test_key")
    
    # Create huge diff
    large_diff = "+" + ("x" * 600_000)  # 600K chars
    
    mock_response = Mock(
        text=json.dumps({
            "breaking_changes": [],
            "has_breaking_changes": False,
            "overall_risk": "INFO",
            "estimated_migration_time": "< 1 hour"
        })
    )
    
    with patch.object(analyzer.model, 'generate_content', return_value=mock_response) as mock_gen:
        await analyzer.analyze_diff("pkg", "1.0", "2.0", large_diff)
        
        # Check that truncated diff was sent
        call_args = mock_gen.call_args[0][0]
        assert "[... diff truncated ...]" in call_args
        assert len(call_args) < len(large_diff)


@pytest.mark.asyncio
async def test_analyze_diff_llm_failure(sample_diff):
    """Test handling of LLM API failure"""
    analyzer = BreakingChangesAnalyzer(api_key="test_key")
    
    # Mock API failure
    with patch.object(analyzer.model, 'generate_content', side_effect=Exception("API Error")):
        with pytest.raises(AnalysisError, match="LLM analysis failed"):
            await analyzer.analyze_diff("pkg", "1.0", "2.0", sample_diff)


@pytest.mark.asyncio
async def test_analyze_diff_invalid_json_response(sample_diff):
    """Test handling of invalid JSON in LLM response"""
    analyzer = BreakingChangesAnalyzer(api_key="test_key")
    
    # Mock response with invalid JSON
    mock_response = Mock(text="Not valid JSON {{{")
    
    with patch.object(analyzer.model, 'generate_content', return_value=mock_response):
        with pytest.raises(AnalysisError):
            await analyzer.analyze_diff("pkg", "1.0", "2.0", sample_diff)


# Tests: BreakingChange model

def test_breaking_change_model():
    """Test BreakingChange dataclass"""
    change = BreakingChange(
        severity=BreakingSeverity.CRITICAL,
        category="API signature",
        description="Removed parameter",
        affected_apis=["func1", "func2"],
        migration_steps=["Step 1", "Step 2"],
        confidence=0.9
    )
    
    assert change.severity == BreakingSeverity.CRITICAL
    assert len(change.affected_apis) == 2
    assert change.confidence == 0.9


# Tests: BreakingChangesReport model

def test_report_critical_count():
    """Test critical_count property"""
    report = BreakingChangesReport(
        package="test",
        from_version="1.0",
        to_version="2.0",
        analyzed_at=datetime.now(),
        breaking_changes=[
            BreakingChange(
                severity=BreakingSeverity.CRITICAL,
                category="test",
                description="test",
                affected_apis=[],
                migration_steps=[],
                confidence=0.9
            ),
            BreakingChange(
                severity=BreakingSeverity.HIGH,
                category="test",
                description="test",
                affected_apis=[],
                migration_steps=[],
                confidence=0.8
            ),
            BreakingChange(
                severity=BreakingSeverity.CRITICAL,
                category="test",
                description="test",
                affected_apis=[],
                migration_steps=[],
                confidence=0.95
            ),
        ],
        has_breaking_changes=True,
        overall_risk=BreakingSeverity.CRITICAL,
        estimated_migration_time="1 day",
        llm_model="gemini-2.0-flash-exp",
        tokens_used=1000,
        cost_usd=0.05
    )
    
    assert report.critical_count == 2
    assert report.high_count == 1


def test_report_summary_with_breaking_changes():
    """Test summary generation with breaking changes"""
    report = BreakingChangesReport(
        package="test",
        from_version="1.0",
        to_version="2.0",
        analyzed_at=datetime.now(),
        breaking_changes=[
            BreakingChange(
                severity=BreakingSeverity.CRITICAL,
                category="test",
                description="test",
                affected_apis=[],
                migration_steps=[],
                confidence=0.9
            )
        ],
        has_breaking_changes=True,
        overall_risk=BreakingSeverity.HIGH,
        estimated_migration_time="2-4 hours",
        llm_model="gemini",
        tokens_used=500,
        cost_usd=0.02
    )
    
    summary = report.summary()
    assert "⚠️" in summary
    assert "1 breaking changes detected" in summary
    assert "Critical: 1" in summary
    assert "2-4 hours" in summary


def test_report_summary_no_breaking_changes():
    """Test summary generation without breaking changes"""
    report = BreakingChangesReport(
        package="test",
        from_version="1.0",
        to_version="1.0.1",
        analyzed_at=datetime.now(),
        breaking_changes=[],
        has_breaking_changes=False,
        overall_risk=BreakingSeverity.INFO,
        estimated_migration_time="< 1 hour",
        llm_model="gemini",
        tokens_used=300,
        cost_usd=0.01
    )
    
    summary = report.summary()
    assert "✅ No breaking changes" in summary
    assert "1.0 → 1.0.1" in summary


# Tests: Cost calculation

def test_calculate_cost():
    """Test cost calculation"""
    analyzer = BreakingChangesAnalyzer(api_key="test_key")
    
    # Free model currently
    cost = analyzer._calculate_cost(input_tokens=10000, output_tokens=2000)
    assert cost == 0.0


# Tests: Convenience function

@pytest.mark.asyncio
async def test_analyze_breaking_changes_convenience(mock_gemini_response, sample_diff):
    """Test convenience function"""
    with patch('llm.breaking_changes_analyzer.BreakingChangesAnalyzer') as MockAnalyzer:
        mock_instance = Mock()
        mock_instance.analyze_diff = AsyncMock(return_value=Mock(critical_count=1))
        MockAnalyzer.return_value = mock_instance
        
        report = await analyze_breaking_changes(
            "requests", "2.28.0", "2.31.0", sample_diff, api_key="test"
        )
        
        assert mock_instance.analyze_diff.called


# Tests: Edge cases

@pytest.mark.asyncio
async def test_analyze_diff_empty_diff():
    """Test analysis with empty diff"""
    analyzer = BreakingChangesAnalyzer(api_key="test_key")
    
    mock_response = Mock(
        text=json.dumps({
            "breaking_changes": [],
            "has_breaking_changes": False,
            "overall_risk": "INFO",
            "estimated_migration_time": "< 1 hour"
        })
    )
    
    with patch.object(analyzer.model, 'generate_content', return_value=mock_response):
        report = await analyzer.analyze_diff("pkg", "1.0", "1.0", "")
    
    assert report.has_breaking_changes is False


@pytest.mark.asyncio
async def test_analyze_diff_unicode_content(sample_diff):
    """Test diff with unicode characters"""
    analyzer = BreakingChangesAnalyzer(api_key="test_key")
    
    unicode_diff = sample_diff + "\n# Comment with émojis 🚀 and 中文"
    
    mock_response = Mock(
        text=json.dumps({
            "breaking_changes": [],
            "has_breaking_changes": False,
            "overall_risk": "INFO",
            "estimated_migration_time": "< 1 hour"
        })
    )
    
    with patch.object(analyzer.model, 'generate_content', return_value=mock_response):
        report = await analyzer.analyze_diff("pkg", "1.0", "2.0", unicode_diff)
        # Should not raise
        assert report is not None


# Tests: BreakingSeverity enum

def test_breaking_severity_enum():
    """Test BreakingSeverity enum values"""
    assert BreakingSeverity.CRITICAL.value == "critical"
    assert BreakingSeverity.HIGH.value == "high"
    assert BreakingSeverity.MEDIUM.value == "medium"
    assert BreakingSeverity.LOW.value == "low"
    assert BreakingSeverity.INFO.value == "info"


# Integration-like test (requires API key, skip by default)

@pytest.mark.skip(reason="Requires real Gemini API key and costs money")
@pytest.mark.asyncio
async def test_real_gemini_api_call():
    """Integration test with real Gemini API (skip by default)"""
    import os
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        pytest.skip("GEMINI_API_KEY not set")
    
    analyzer = BreakingChangesAnalyzer(api_key=api_key)
    
    simple_diff = """
diff --git a/test.py b/test.py
--- a/test.py
+++ b/test.py
@@ -1,3 +1,3 @@
-def hello(name):
+def hello(name, greeting="Hello"):
     pass
"""
    
    report = await analyzer.analyze_diff(
        "test-package", "1.0.0", "2.0.0", simple_diff
    )
    
    # Basic sanity checks
    assert report.package == "test-package"
    assert report.llm_model == analyzer.MODEL
    assert report.cost_usd >= 0
