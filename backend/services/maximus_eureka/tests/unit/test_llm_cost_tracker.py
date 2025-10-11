"""
Unit tests for LLM Cost Tracker.

Tests cost tracking, budget enforcement, and Prometheus metrics.
"""

import pytest
import tempfile
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import patch

from tracking.llm_cost_tracker import (
    LLMCostTracker,
    LLMModel,
    CostRecord,
    BudgetExceededError,
    get_cost_tracker,
)


# Fixtures

@pytest.fixture
def temp_storage():
    """Temporary storage for cost records"""
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        storage_path = Path(f.name)
    
    yield storage_path
    
    # Cleanup
    storage_path.unlink(missing_ok=True)


@pytest.fixture
def tracker(temp_storage):
    """Cost tracker with temp storage"""
    return LLMCostTracker(
        monthly_budget=50.0,
        storage_path=temp_storage,
        enable_throttling=False  # Disable for most tests
    )


# Tests: Initialization

def test_tracker_initialization(temp_storage):
    """Test tracker can be initialized"""
    tracker = LLMCostTracker(
        monthly_budget=100.0,
        storage_path=temp_storage
    )
    
    assert tracker.monthly_budget == 100.0
    assert tracker.storage_path == temp_storage
    assert len(tracker.records) == 0


def test_tracker_default_budget():
    """Test default budget from environment"""
    with patch.dict('os.environ', {'LLM_BUDGET_MONTHLY': '75.0'}):
        tracker = get_cost_tracker()
        assert tracker.monthly_budget == 75.0


# Tests: track_request

@pytest.mark.asyncio
async def test_track_request_claude(tracker):
    """Test tracking Claude request"""
    record = await tracker.track_request(
        model=LLMModel.CLAUDE_3_7_SONNET,
        strategy="code_patch_llm",
        input_tokens=1000,
        output_tokens=500,
        metadata={"apv_id": "apv_001"}
    )
    
    assert record.model == LLMModel.CLAUDE_3_7_SONNET
    assert record.strategy == "code_patch_llm"
    assert record.input_tokens == 1000
    assert record.output_tokens == 500
    assert record.cost_usd > 0  # Should have cost
    assert record.metadata["apv_id"] == "apv_001"


@pytest.mark.asyncio
async def test_track_request_gemini_free(tracker):
    """Test tracking Gemini Flash (free) request"""
    record = await tracker.track_request(
        model=LLMModel.GEMINI_2_0_FLASH,
        strategy="breaking_changes",
        input_tokens=5000,
        output_tokens=2000
    )
    
    assert record.cost_usd == 0.0  # Gemini Flash is free


@pytest.mark.asyncio
async def test_track_request_cost_calculation(tracker):
    """Test cost calculation accuracy"""
    # Claude 3.7 Sonnet: $0.003/1K input, $0.015/1K output
    record = await tracker.track_request(
        model=LLMModel.CLAUDE_3_7_SONNET,
        strategy="test",
        input_tokens=1000,
        output_tokens=1000
    )
    
    expected_cost = (1000 / 1000) * 0.003 + (1000 / 1000) * 0.015
    assert abs(record.cost_usd - expected_cost) < 0.0001


@pytest.mark.asyncio
async def test_track_request_creates_record(tracker):
    """Test record is stored"""
    await tracker.track_request(
        model=LLMModel.GPT_4_TURBO,
        strategy="test",
        input_tokens=100,
        output_tokens=50
    )
    
    assert len(tracker.records) == 1


@pytest.mark.asyncio
async def test_track_request_multiple(tracker):
    """Test tracking multiple requests"""
    for i in range(5):
        await tracker.track_request(
            model=LLMModel.CLAUDE_3_7_SONNET,
            strategy="test",
            input_tokens=100,
            output_tokens=50
        )
    
    assert len(tracker.records) == 5


# Tests: Budget enforcement

@pytest.mark.asyncio
async def test_budget_exceeded_error(temp_storage):
    """Test budget enforcement"""
    tracker = LLMCostTracker(
        monthly_budget=0.01,  # Very low budget
        storage_path=temp_storage,
        enable_throttling=True
    )
    
    # First request should succeed
    await tracker.track_request(
        model=LLMModel.CLAUDE_3_7_SONNET,
        strategy="test",
        input_tokens=1000,
        output_tokens=1000
    )
    
    # Second request should exceed budget
    with pytest.raises(BudgetExceededError, match="Monthly budget.*exceeded"):
        await tracker.track_request(
            model=LLMModel.CLAUDE_3_7_SONNET,
            strategy="test",
            input_tokens=1000,
            output_tokens=1000
        )


@pytest.mark.asyncio
async def test_throttling_disabled(temp_storage):
    """Test requests allowed when throttling disabled"""
    tracker = LLMCostTracker(
        monthly_budget=0.001,  # Very low
        storage_path=temp_storage,
        enable_throttling=False  # Disabled
    )
    
    # Should not raise even though budget exceeded
    await tracker.track_request(
        model=LLMModel.CLAUDE_3_7_SONNET,
        strategy="test",
        input_tokens=10000,
        output_tokens=10000
    )


# Tests: get_monthly_cost

@pytest.mark.asyncio
async def test_get_monthly_cost(tracker):
    """Test monthly cost calculation"""
    # Add some requests
    await tracker.track_request(
        model=LLMModel.CLAUDE_3_7_SONNET,
        strategy="test",
        input_tokens=1000,
        output_tokens=1000
    )
    await tracker.track_request(
        model=LLMModel.GPT_4_TURBO,
        strategy="test",
        input_tokens=500,
        output_tokens=500
    )
    
    monthly_cost = tracker.get_monthly_cost()
    assert monthly_cost > 0


@pytest.mark.asyncio
async def test_get_monthly_cost_different_month(tracker):
    """Test monthly cost for specific month"""
    # Add request this month
    await tracker.track_request(
        model=LLMModel.CLAUDE_3_7_SONNET,
        strategy="test",
        input_tokens=1000,
        output_tokens=1000
    )
    
    # Query last month (should be 0)
    last_month = datetime.now() - timedelta(days=35)
    cost = tracker.get_monthly_cost(last_month)
    assert cost == 0.0


# Tests: get_daily_cost

@pytest.mark.asyncio
async def test_get_daily_cost(tracker):
    """Test daily cost calculation"""
    await tracker.track_request(
        model=LLMModel.CLAUDE_3_7_SONNET,
        strategy="test",
        input_tokens=1000,
        output_tokens=1000
    )
    
    daily_cost = tracker.get_daily_cost()
    assert daily_cost > 0


# Tests: get_cost_by_strategy

@pytest.mark.asyncio
async def test_get_cost_by_strategy(tracker):
    """Test cost breakdown by strategy"""
    await tracker.track_request(
        model=LLMModel.CLAUDE_3_7_SONNET,
        strategy="code_patch",
        input_tokens=1000,
        output_tokens=1000
    )
    await tracker.track_request(
        model=LLMModel.CLAUDE_3_7_SONNET,
        strategy="breaking_changes",
        input_tokens=500,
        output_tokens=500
    )
    
    breakdown = tracker.get_cost_by_strategy()
    
    assert "code_patch" in breakdown
    assert "breaking_changes" in breakdown
    assert breakdown["code_patch"] > breakdown["breaking_changes"]  # More tokens


# Tests: get_cost_by_model

@pytest.mark.asyncio
async def test_get_cost_by_model(tracker):
    """Test cost breakdown by model"""
    await tracker.track_request(
        model=LLMModel.CLAUDE_3_7_SONNET,
        strategy="test",
        input_tokens=1000,
        output_tokens=1000
    )
    await tracker.track_request(
        model=LLMModel.GPT_4_TURBO,
        strategy="test",
        input_tokens=1000,
        output_tokens=1000
    )
    
    breakdown = tracker.get_cost_by_model()
    
    assert LLMModel.CLAUDE_3_7_SONNET.value in breakdown
    assert LLMModel.GPT_4_TURBO.value in breakdown
    # GPT-4 more expensive
    assert breakdown[LLMModel.GPT_4_TURBO.value] > breakdown[LLMModel.CLAUDE_3_7_SONNET.value]


# Tests: check_budget_status

@pytest.mark.asyncio
async def test_check_budget_status_ok(tracker):
    """Test budget status when OK"""
    await tracker.track_request(
        model=LLMModel.GEMINI_2_0_FLASH,  # Free
        strategy="test",
        input_tokens=1000,
        output_tokens=1000
    )
    
    status = tracker.check_budget_status()
    
    assert status["status"] == "ok"
    assert status["monthly_budget"] == 50.0
    assert status["percentage_used"] < 80


@pytest.mark.asyncio
async def test_check_budget_status_warning(temp_storage):
    """Test budget status at warning threshold"""
    tracker = LLMCostTracker(
        monthly_budget=0.02,  # Low budget
        storage_path=temp_storage,
        enable_throttling=False
    )
    
    # Add requests to reach 80%+
    await tracker.track_request(
        model=LLMModel.CLAUDE_3_7_SONNET,
        strategy="test",
        input_tokens=1000,
        output_tokens=1000
    )
    
    status = tracker.check_budget_status()
    
    assert status["status"] in ["warning", "exceeded"]


# Tests: generate_monthly_report

@pytest.mark.asyncio
async def test_generate_monthly_report(tracker):
    """Test monthly report generation"""
    await tracker.track_request(
        model=LLMModel.CLAUDE_3_7_SONNET,
        strategy="code_patch",
        input_tokens=1000,
        output_tokens=1000
    )
    await tracker.track_request(
        model=LLMModel.GPT_4_TURBO,
        strategy="breaking_changes",
        input_tokens=500,
        output_tokens=500
    )
    
    report = tracker.generate_monthly_report()
    
    assert "LLM COST REPORT" in report
    assert "BUDGET SUMMARY" in report
    assert "BY STRATEGY" in report
    assert "BY MODEL" in report
    assert "code_patch" in report
    assert "breaking_changes" in report


# Tests: Storage (save/load)

@pytest.mark.asyncio
async def test_save_and_load_records(temp_storage):
    """Test persisting records to storage"""
    # Create tracker and add records
    tracker1 = LLMCostTracker(
        monthly_budget=50.0,
        storage_path=temp_storage
    )
    
    await tracker1.track_request(
        model=LLMModel.CLAUDE_3_7_SONNET,
        strategy="test",
        input_tokens=1000,
        output_tokens=1000,
        metadata={"test": "data"}
    )
    
    # Create new tracker (should load records)
    tracker2 = LLMCostTracker(
        monthly_budget=50.0,
        storage_path=temp_storage
    )
    
    assert len(tracker2.records) == 1
    assert tracker2.records[0].metadata["test"] == "data"


def test_load_records_nonexistent_file(temp_storage):
    """Test loading when file doesn't exist"""
    # Remove file if exists
    temp_storage.unlink(missing_ok=True)
    
    tracker = LLMCostTracker(storage_path=temp_storage)
    
    assert len(tracker.records) == 0


# Tests: LLMModel enum

def test_llm_model_enum_values():
    """Test LLMModel enum values"""
    assert LLMModel.CLAUDE_3_7_SONNET.value == "claude-3-7-sonnet"
    assert LLMModel.GPT_4_TURBO.value == "gpt-4-turbo"
    assert LLMModel.GEMINI_2_0_FLASH.value == "gemini-2-0-flash-exp"


# Tests: CostRecord model

def test_cost_record_to_dict():
    """Test CostRecord to dictionary"""
    now = datetime.now()
    record = CostRecord(
        timestamp=now,
        model=LLMModel.CLAUDE_3_7_SONNET,
        strategy="test",
        input_tokens=100,
        output_tokens=50,
        cost_usd=0.01,
        metadata={"key": "value"}
    )
    
    data = record.to_dict()
    
    assert data["model"] == "claude-3-7-sonnet"
    assert data["strategy"] == "test"
    assert data["input_tokens"] == 100
    assert data["metadata"]["key"] == "value"


# Tests: Pricing accuracy

def test_pricing_claude():
    """Test Claude pricing is correct"""
    tracker = LLMCostTracker()
    
    # $0.003/1K input, $0.015/1K output
    cost = tracker._calculate_cost(
        LLMModel.CLAUDE_3_7_SONNET,
        input_tokens=1000,
        output_tokens=1000
    )
    
    expected = (1 * 0.003) + (1 * 0.015)
    assert abs(cost - expected) < 0.0001


def test_pricing_gpt4():
    """Test GPT-4 pricing is correct"""
    tracker = LLMCostTracker()
    
    # $0.01/1K input, $0.03/1K output
    cost = tracker._calculate_cost(
        LLMModel.GPT_4_TURBO,
        input_tokens=1000,
        output_tokens=1000
    )
    
    expected = (1 * 0.01) + (1 * 0.03)
    assert abs(cost - expected) < 0.0001


def test_pricing_gemini_free():
    """Test Gemini Flash is free"""
    tracker = LLMCostTracker()
    
    cost = tracker._calculate_cost(
        LLMModel.GEMINI_2_0_FLASH,
        input_tokens=10000,
        output_tokens=10000
    )
    
    assert cost == 0.0


# Tests: Convenience function

def test_get_cost_tracker_singleton():
    """Test get_cost_tracker returns singleton"""
    tracker1 = get_cost_tracker(monthly_budget=100.0)
    tracker2 = get_cost_tracker()
    
    assert tracker1 is tracker2  # Same instance


# Tests: Edge cases

@pytest.mark.asyncio
async def test_track_request_zero_tokens(tracker):
    """Test tracking with zero tokens"""
    record = await tracker.track_request(
        model=LLMModel.CLAUDE_3_7_SONNET,
        strategy="test",
        input_tokens=0,
        output_tokens=0
    )
    
    assert record.cost_usd == 0.0


@pytest.mark.asyncio
async def test_track_request_large_tokens(tracker):
    """Test tracking with large token counts"""
    record = await tracker.track_request(
        model=LLMModel.CLAUDE_3_7_SONNET,
        strategy="test",
        input_tokens=100000,
        output_tokens=50000
    )
    
    assert record.cost_usd > 1.0  # Should be significant cost
