"""
Tests for MAXIMUS Tool Adapter.

Validates integration between offensive tools and
MAXIMUS biomimetic intelligence system.
"""
import pytest
from datetime import datetime
from unittest.mock import Mock, AsyncMock

from .maximus_adapter import (
    MAXIMUSToolAdapter,
    MAXIMUSToolContext,
    OperationMode,
    EnhancedToolResult,
    EthicalContext
)
from .base import OffensiveTool, ToolResult, ToolMetadata
from .exceptions import OffensiveToolError


class MockTool(OffensiveTool):
    """Mock offensive tool for testing."""
    
    def __init__(self):
        super().__init__(name="mock_tool", category="test")
        self.execution_count = 0
    
    async def execute(self, **kwargs) -> ToolResult:
        """Mock execution."""
        self.execution_count += 1
        
        return ToolResult(
            success=True,
            data={"test": "data"},
            message="Mock execution successful",
            metadata=ToolMetadata(
                tool_name=self.name,
                execution_time=0.1,
                success_rate=1.0,
                confidence_score=0.9
            )
        )
    
    async def validate(self) -> bool:
        """Mock validation."""
        return True


@pytest.fixture
def mock_tool():
    """Create mock tool."""
    return MockTool()


@pytest.fixture
def mock_consciousness():
    """Create mock consciousness component."""
    consciousness = Mock()
    consciousness.get_state = AsyncMock(return_value={
        "phi_proxy": 0.85,
        "coherence": 0.92
    })
    return consciousness


@pytest.fixture
def defensive_context():
    """Create defensive operation context."""
    return MAXIMUSToolContext(
        operation_mode=OperationMode.DEFENSIVE,
        ethical_context=EthicalContext(
            operation_type="defensive",
            risk_level="low"
        ),
        human_oversight_required=False
    )


@pytest.fixture
def testing_context():
    """Create testing operation context."""
    return MAXIMUSToolContext(
        operation_mode=OperationMode.TESTING,
        ethical_context=EthicalContext(
            operation_type="testing",
            risk_level="medium"
        ),
        authorization_token="test-auth-token",
        human_oversight_required=True
    )


class TestMAXIMUSToolContext:
    """Test MAXIMUS tool context."""
    
    def test_defensive_context_validation(self, defensive_context):
        """Defensive context should always validate."""
        assert defensive_context.validate() is True
    
    def test_testing_context_with_auth(self, testing_context):
        """Testing context with auth should validate."""
        assert testing_context.validate() is True
    
    def test_testing_context_without_auth(self):
        """Testing context without auth should not validate."""
        context = MAXIMUSToolContext(
            operation_mode=OperationMode.TESTING,
            ethical_context=EthicalContext(
                operation_type="testing",
                risk_level="medium"
            ),
            authorization_token=None
        )
        
        assert context.validate() is False
    
    def test_intelligence_context(self):
        """Intelligence gathering context validation."""
        context = MAXIMUSToolContext(
            operation_mode=OperationMode.INTELLIGENCE,
            ethical_context=EthicalContext(
                operation_type="intelligence",
                risk_level="low"
            )
        )
        
        # Should require auth for non-defensive
        assert context.validate() is False


class TestMAXIMUSToolAdapter:
    """Test MAXIMUS tool adapter."""
    
    @pytest.mark.asyncio
    async def test_adapter_initialization(self, mock_tool):
        """Test adapter initialization."""
        adapter = MAXIMUSToolAdapter(mock_tool)
        
        assert adapter.tool == mock_tool
        assert adapter.consciousness is None
        assert len(adapter._execution_history) == 0
        assert adapter._ethical_violations == 0
    
    @pytest.mark.asyncio
    async def test_defensive_execution(
        self,
        mock_tool,
        defensive_context
    ):
        """Test defensive operation execution."""
        adapter = MAXIMUSToolAdapter(mock_tool)
        
        result = await adapter.execute_with_maximus(
            defensive_context,
            test_param="value"
        )
        
        assert isinstance(result, EnhancedToolResult)
        assert result.success is True
        assert result.ethical_score == 1.0
        assert mock_tool.execution_count == 1
        assert len(adapter._execution_history) == 1
    
    @pytest.mark.asyncio
    async def test_testing_execution_with_auth(
        self,
        mock_tool,
        testing_context
    ):
        """Test testing operation with authorization."""
        adapter = MAXIMUSToolAdapter(mock_tool)
        
        result = await adapter.execute_with_maximus(
            testing_context,
            test_param="value"
        )
        
        assert result.success is True
        assert result.ethical_score > 0.8
        assert result.ethical_score < 1.0
        assert len(adapter._execution_history) == 1
    
    @pytest.mark.asyncio
    async def test_testing_execution_without_auth(
        self,
        mock_tool
    ):
        """Test testing operation without authorization."""
        adapter = MAXIMUSToolAdapter(mock_tool)
        
        context = MAXIMUSToolContext(
            operation_mode=OperationMode.TESTING,
            ethical_context=EthicalContext(
                operation_type="testing",
                risk_level="medium"
            ),
            authorization_token=None
        )
        
        with pytest.raises(OffensiveToolError) as exc_info:
            await adapter.execute_with_maximus(context)
        
        assert "authorization required" in str(exc_info.value).lower()
        assert adapter._ethical_violations == 0  # No execution, no violation
    
    @pytest.mark.asyncio
    async def test_ethical_preflight_defensive(
        self,
        mock_tool,
        defensive_context
    ):
        """Test ethical preflight for defensive ops."""
        adapter = MAXIMUSToolAdapter(mock_tool)
        
        decision = await adapter._ethical_preflight(
            defensive_context,
            {}
        )
        
        assert decision.approved is True
        assert decision.score == 1.0
        assert "defensive" in decision.rationale.lower()
    
    @pytest.mark.asyncio
    async def test_ethical_preflight_intelligence(
        self,
        mock_tool
    ):
        """Test ethical preflight for intelligence ops."""
        adapter = MAXIMUSToolAdapter(mock_tool)
        
        context = MAXIMUSToolContext(
            operation_mode=OperationMode.INTELLIGENCE,
            ethical_context=EthicalContext(
                operation_type="intelligence",
                risk_level="low"
            )
        )
        
        decision = await adapter._ethical_preflight(context, {})
        
        assert decision.approved is True
        assert decision.score >= 0.9
    
    @pytest.mark.asyncio
    async def test_threat_prediction_basic(
        self,
        mock_tool,
        defensive_context
    ):
        """Test basic threat prediction."""
        adapter = MAXIMUSToolAdapter(mock_tool)
        
        prediction = await adapter._predict_threats(
            defensive_context,
            {}
        )
        
        assert "likelihood" in prediction
        assert "severity" in prediction
        assert "indicators" in prediction
        assert isinstance(prediction["indicators"], list)
    
    @pytest.mark.asyncio
    async def test_threat_prediction_with_consciousness(
        self,
        mock_tool,
        mock_consciousness
    ):
        """Test threat prediction with consciousness."""
        adapter = MAXIMUSToolAdapter(
            mock_tool,
            mock_consciousness
        )
        
        context = MAXIMUSToolContext(
            operation_mode=OperationMode.DEFENSIVE,
            ethical_context=EthicalContext(
                operation_type="defensive",
                risk_level="low"
            ),
            consciousness_state={"phi_proxy": 0.85}
        )
        
        prediction = await adapter._predict_threats(context, {})
        
        # Higher phi should increase likelihood
        assert prediction["likelihood"] > 0.5
        assert prediction.get("confidence") == "high"
    
    @pytest.mark.asyncio
    async def test_result_enhancement(
        self,
        mock_tool,
        defensive_context
    ):
        """Test result enhancement."""
        adapter = MAXIMUSToolAdapter(mock_tool)
        
        base_result = ToolResult(
            success=True,
            data={"test": "data"},
            message="Test",
            metadata=ToolMetadata(
                tool_name="test",
                execution_time=0.1,
                success_rate=1.0,
                confidence_score=0.9
            )
        )
        
        enhanced = await adapter._enhance_result(
            base_result,
            defensive_context,
            {"likelihood": 0.6, "severity": "medium"},
            datetime.utcnow()
        )
        
        assert isinstance(enhanced, EnhancedToolResult)
        assert enhanced.success is True
        assert hasattr(enhanced, 'ethical_score')
        assert hasattr(enhanced, 'threat_indicators')
        assert hasattr(enhanced, 'recommended_actions')
    
    @pytest.mark.asyncio
    async def test_ethical_score_calculation(
        self,
        mock_tool,
        defensive_context
    ):
        """Test ethical score calculation."""
        adapter = MAXIMUSToolAdapter(mock_tool)
        
        result = ToolResult(
            success=True,
            data={},
            message="Test",
            metadata=ToolMetadata(
                tool_name="test",
                execution_time=0.1,
                success_rate=1.0,
                confidence_score=0.9
            )
        )
        
        score = await adapter._calculate_ethical_score(
            result,
            defensive_context
        )
        
        assert 0.0 <= score <= 1.0
        assert score == 1.0  # Defensive should be 1.0
    
    @pytest.mark.asyncio
    async def test_ethical_score_with_testing_mode(
        self,
        mock_tool,
        testing_context
    ):
        """Test ethical score for testing mode."""
        adapter = MAXIMUSToolAdapter(mock_tool)
        
        result = ToolResult(
            success=True,
            data={},
            message="Test",
            metadata=ToolMetadata(
                tool_name="test",
                execution_time=0.1,
                success_rate=1.0,
                confidence_score=0.9
            )
        )
        
        score = await adapter._calculate_ethical_score(
            result,
            testing_context
        )
        
        assert score < 1.0  # Testing should have reduced score
        assert score >= 0.8
    
    @pytest.mark.asyncio
    async def test_execution_stats_empty(self, mock_tool):
        """Test execution stats with no history."""
        adapter = MAXIMUSToolAdapter(mock_tool)
        
        stats = adapter.get_execution_stats()
        
        assert stats["total_executions"] == 0
        assert stats["success_rate"] == 0.0
        assert stats["ethical_violations"] == 0
    
    @pytest.mark.asyncio
    async def test_execution_stats_with_history(
        self,
        mock_tool,
        defensive_context
    ):
        """Test execution stats with history."""
        adapter = MAXIMUSToolAdapter(mock_tool)
        
        # Execute multiple times
        for _ in range(3):
            await adapter.execute_with_maximus(defensive_context)
        
        stats = adapter.get_execution_stats()
        
        assert stats["total_executions"] == 3
        assert stats["success_rate"] == 1.0
        assert stats["average_ethical_score"] == 1.0
        assert OperationMode.DEFENSIVE.value in stats["modes_used"]
    
    @pytest.mark.asyncio
    async def test_tool_execution_failure(
        self,
        defensive_context
    ):
        """Test handling of tool execution failure."""
        class FailingTool(OffensiveTool):
            def __init__(self):
                super().__init__(name="failing_tool", category="test")
            
            async def execute(self, **kwargs):
                raise Exception("Tool execution failed")
            
            async def validate(self):
                return True
        
        adapter = MAXIMUSToolAdapter(FailingTool())
        
        with pytest.raises(Exception) as exc_info:
            await adapter.execute_with_maximus(defensive_context)
        
        assert "Tool execution failed" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_consciousness_integration(
        self,
        mock_tool,
        mock_consciousness,
        defensive_context
    ):
        """Test consciousness integration."""
        defensive_context.consciousness_state = {"phi_proxy": 0.85}
        
        adapter = MAXIMUSToolAdapter(
            mock_tool,
            mock_consciousness
        )
        
        result = await adapter.execute_with_maximus(defensive_context)
        
        assert result.consciousness_contribution == 0.85
    
    @pytest.mark.asyncio
    async def test_multiple_mode_execution(
        self,
        mock_tool
    ):
        """Test execution in multiple modes."""
        adapter = MAXIMUSToolAdapter(mock_tool)
        
        # Defensive
        defensive_ctx = MAXIMUSToolContext(
            operation_mode=OperationMode.DEFENSIVE,
            ethical_context=EthicalContext(
                operation_type="defensive",
                risk_level="low"
            )
        )
        await adapter.execute_with_maximus(defensive_ctx)
        
        # Intelligence with auth
        intel_ctx = MAXIMUSToolContext(
            operation_mode=OperationMode.INTELLIGENCE,
            ethical_context=EthicalContext(
                operation_type="intelligence",
                risk_level="low"
            ),
            authorization_token="test-token"  # Add auth token
        )
        await adapter.execute_with_maximus(intel_ctx)
        
        stats = adapter.get_execution_stats()
        
        assert len(stats["modes_used"]) == 2
        assert OperationMode.DEFENSIVE.value in stats["modes_used"]
        assert OperationMode.INTELLIGENCE.value in stats["modes_used"]
