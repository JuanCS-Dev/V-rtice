"""
Comprehensive unit tests for main.py (FastAPI service).

Target: 95%+ coverage for all FastAPI endpoints and lifecycle.

Strategy:
- Direct async function testing (avoid TestClient/httpx version issues)
- Mock all analyzer dependencies
- Test success paths and error conditions
- HTTPException propagation

SAGA dos 95%+ - Service #6: system_architect_service
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime


# ========================================================================
# Test: Health Check Endpoint
# ========================================================================

@pytest.mark.asyncio
async def test_health_check_all_initialized():
    """
    SCENARIO: health_check() called when all analyzers initialized
    EXPECTED: Returns healthy status with all analyzers=True
    """
    import main

    # Set all global analyzers
    main._scanner = Mock()
    main._integration_analyzer = Mock()
    main._redundancy_detector = Mock()
    main._deployment_optimizer = Mock()
    main._report_generator = Mock()

    result = await main.health_check()

    assert result["status"] == "healthy"
    assert result["service"] == "system_architect_service"
    assert result["version"] == "1.0.0"
    assert "timestamp" in result
    assert result["analyzers"]["scanner"] is True
    assert result["analyzers"]["integration_analyzer"] is True
    assert result["analyzers"]["redundancy_detector"] is True
    assert result["analyzers"]["deployment_optimizer"] is True
    assert result["analyzers"]["report_generator"] is True


@pytest.mark.asyncio
async def test_health_check_not_initialized():
    """
    SCENARIO: health_check() when analyzers not initialized
    EXPECTED: Returns healthy status with analyzers=False
    """
    import main

    # Clear all global analyzers
    main._scanner = None
    main._integration_analyzer = None
    main._redundancy_detector = None
    main._deployment_optimizer = None
    main._report_generator = None

    result = await main.health_check()

    assert result["status"] == "healthy"
    assert result["analyzers"]["scanner"] is False
    assert result["analyzers"]["integration_analyzer"] is False
    assert result["analyzers"]["redundancy_detector"] is False
    assert result["analyzers"]["deployment_optimizer"] is False
    assert result["analyzers"]["report_generator"] is False


# ========================================================================
# Test: Full System Analysis Endpoint
# ========================================================================

@pytest.mark.asyncio
async def test_analyze_full_system_success():
    """
    SCENARIO: analyze_full_system() succeeds with all analyzers working
    EXPECTED: Returns AnalysisResponse with complete summary
    """
    import main
    from main import AnalysisRequest

    # Mock scanner
    mock_scanner = AsyncMock()
    mock_scanner.scan.return_value = {
        "total_services": 89,
        "subsystems": {
            "consciousness": ["maximus_core", "digital_thalamus"],
            "immune": ["immunis_t_cell", "adaptive_immunity"],
            "infrastructure": ["kafka", "redis", "postgres"]
        },
        "health_summary": {"coverage_percentage": 92.5},
        "ports": {"8080": "api_gateway", "9092": "kafka"},
        "networks": ["vertice_net"],
        "volumes": ["postgres_data"]
    }

    # Mock integration analyzer
    mock_integration = AsyncMock()
    mock_integration.analyze.return_value = {
        "total_integration_points": 45,
        "kafka": {"total_topics": 12},
        "redis": {"total_patterns": 5},
        "http": {"total_dependencies": 28}
    }

    # Mock redundancy detector
    mock_redundancy = AsyncMock()
    mock_redundancy.detect.return_value = {
        "redundant_services": [
            {"group": "osint", "services": ["google_osint", "sinesp_osint", "ip_intelligence"], "count": 3}
        ],
        "total_opportunities": 1
    }

    # Mock deployment optimizer
    mock_optimizer = AsyncMock()
    mock_optimizer.optimize.return_value = {
        "readiness_score": 85,
        "gaps": [
            {"type": "kubernetes_operators", "priority": "MEDIUM", "description": "No custom operators"},
            {"type": "service_mesh", "priority": "MEDIUM", "description": "No Istio"}
        ],
        "recommendations": [
            {"title": "Deploy Istio", "priority": "HIGH", "description": "Add service mesh"},
            {"title": "Implement GitOps", "priority": "MEDIUM", "description": "Deploy FluxCD"}
        ]
    }

    # Mock report generator
    mock_report_gen = AsyncMock()
    mock_report_gen.generate_all.return_value = {
        "json": "/tmp/system_architect_reports/VERTICE_ANALYSIS_20251023_120000.json",
        "markdown": "/tmp/system_architect_reports/VERTICE_ANALYSIS_20251023_120000.md",
        "html": "/tmp/system_architect_reports/VERTICE_ANALYSIS_20251023_120000.html"
    }

    # Inject mocks into main module
    main._scanner = mock_scanner
    main._integration_analyzer = mock_integration
    main._redundancy_detector = mock_redundancy
    main._deployment_optimizer = mock_optimizer
    main._report_generator = mock_report_gen

    # Execute
    request = AnalysisRequest(include_recommendations=True, generate_graphs=True)
    response = await main.analyze_full_system(request)

    # Assertions
    assert response.status == "success"
    assert response.timestamp  # timestamp is populated
    assert response.summary["total_services"] == 89
    assert response.summary["subsystems"] == 3
    assert response.summary["integration_points"] == 45
    assert response.summary["redundancies_found"] == 1
    assert response.summary["optimization_opportunities"] == 2
    assert response.summary["deployment_readiness_score"] == 85
    assert response.summary["critical_gaps"] == 0
    assert response.report_id.startswith("VERTICE_ANALYSIS_")
    assert response.report_url.endswith(".html")

    # Verify all analyzers were called
    mock_scanner.scan.assert_called_once()
    mock_integration.analyze.assert_called_once()
    mock_redundancy.detect.assert_called_once()
    mock_optimizer.optimize.assert_called_once()
    mock_report_gen.generate_all.assert_called_once()


@pytest.mark.asyncio
async def test_analyze_full_system_service_not_initialized():
    """
    SCENARIO: analyze_full_system() called when service not initialized
    EXPECTED: Raises HTTPException with 503 status
    """
    import main
    from fastapi import HTTPException
    from main import AnalysisRequest

    # Clear analyzers
    main._scanner = None
    main._report_generator = None

    request = AnalysisRequest()

    with pytest.raises(HTTPException) as exc_info:
        await main.analyze_full_system(request)

    assert exc_info.value.status_code == 503
    assert "not initialized" in exc_info.value.detail


@pytest.mark.asyncio
async def test_analyze_full_system_scanner_fails():
    """
    SCENARIO: analyze_full_system() when scanner.scan() raises exception
    EXPECTED: Raises HTTPException with 500 status and error message
    """
    import main
    from fastapi import HTTPException
    from main import AnalysisRequest

    # Mock scanner that fails
    mock_scanner = AsyncMock()
    mock_scanner.scan.side_effect = Exception("Docker compose file not found")

    mock_report_gen = Mock()

    main._scanner = mock_scanner
    main._integration_analyzer = AsyncMock()
    main._redundancy_detector = AsyncMock()
    main._deployment_optimizer = AsyncMock()
    main._report_generator = mock_report_gen

    request = AnalysisRequest()

    with pytest.raises(HTTPException) as exc_info:
        await main.analyze_full_system(request)

    assert exc_info.value.status_code == 500
    assert "Analysis failed" in exc_info.value.detail
    assert "Docker compose file not found" in exc_info.value.detail


@pytest.mark.asyncio
async def test_analyze_full_system_with_critical_gaps():
    """
    SCENARIO: Analysis finds CRITICAL priority gaps
    EXPECTED: Summary includes critical_gaps count
    """
    import main
    from main import AnalysisRequest

    mock_scanner = AsyncMock()
    mock_scanner.scan.return_value = {
        "total_services": 50,
        "subsystems": {"consciousness": ["service1"]},
        "health_summary": {"coverage_percentage": 50},
        "ports": {},
        "networks": [],
        "volumes": []
    }

    mock_integration = AsyncMock()
    mock_integration.analyze.return_value = {"total_integration_points": 10}

    mock_redundancy = AsyncMock()
    mock_redundancy.detect.return_value = {"redundant_services": [], "total_opportunities": 0}

    mock_optimizer = AsyncMock()
    mock_optimizer.optimize.return_value = {
        "readiness_score": 40,
        "gaps": [
            {"type": "security", "priority": "CRITICAL", "description": "No TLS"},
            {"type": "backup", "priority": "CRITICAL", "description": "No backups"},
            {"type": "monitoring", "priority": "HIGH", "description": "Limited monitoring"}
        ],
        "recommendations": []
    }

    mock_report_gen = AsyncMock()
    mock_report_gen.generate_all.return_value = {"html": "/tmp/report.html"}

    main._scanner = mock_scanner
    main._integration_analyzer = mock_integration
    main._redundancy_detector = mock_redundancy
    main._deployment_optimizer = mock_optimizer
    main._report_generator = mock_report_gen

    request = AnalysisRequest(generate_graphs=False)
    response = await main.analyze_full_system(request)

    assert response.summary["critical_gaps"] == 2  # Two CRITICAL gaps
    assert response.summary["deployment_readiness_score"] == 40


# ========================================================================
# Test: Subsystem Analysis Endpoint
# ========================================================================

@pytest.mark.asyncio
async def test_analyze_subsystem_success():
    """
    SCENARIO: analyze_subsystem() for existing subsystem (e.g., consciousness)
    EXPECTED: Returns subsystem-specific analysis
    """
    import main
    from main import AnalysisRequest

    mock_scanner = AsyncMock()
    mock_scanner.scan.return_value = {
        "services": {
            "maximus_core": {"name": "maximus_core", "subsystem": "consciousness"},
            "digital_thalamus": {"name": "digital_thalamus", "subsystem": "consciousness"}
        },
        "health_summary": {"coverage_percentage": 95.0}
    }

    mock_report_gen = AsyncMock()
    mock_report_gen.generate_subsystem_report.return_value = {
        "json": "/tmp/CONSCIOUSNESS_ANALYSIS.json",
        "markdown": "/tmp/CONSCIOUSNESS_ANALYSIS.md",
        "html": "/tmp/CONSCIOUSNESS_ANALYSIS.html"
    }

    main._scanner = mock_scanner
    main._report_generator = mock_report_gen

    request = AnalysisRequest(subsystem="consciousness")
    response = await main.analyze_subsystem(request)

    assert response.status == "success"
    assert response.summary["subsystem"] == "consciousness"
    assert response.summary["total_services"] == 2
    assert response.summary["health_status"]["coverage_percentage"] == 95.0
    assert "CONSCIOUSNESS_ANALYSIS_" in response.report_id
    assert response.report_url.endswith(".html")

    # Verify scanner called with subsystem_filter
    mock_scanner.scan.assert_called_once_with(subsystem_filter="consciousness")
    mock_report_gen.generate_subsystem_report.assert_called_once()


@pytest.mark.asyncio
async def test_analyze_subsystem_no_subsystem_provided():
    """
    SCENARIO: analyze_subsystem() without subsystem name
    EXPECTED: Raises HTTPException 400 (Bad Request)
    """
    import main
    from fastapi import HTTPException
    from main import AnalysisRequest

    main._scanner = Mock()
    main._report_generator = Mock()

    request = AnalysisRequest(subsystem=None)

    with pytest.raises(HTTPException) as exc_info:
        await main.analyze_subsystem(request)

    assert exc_info.value.status_code == 400
    assert "Subsystem name required" in exc_info.value.detail


@pytest.mark.asyncio
async def test_analyze_subsystem_not_found():
    """
    SCENARIO: analyze_subsystem() for non-existent subsystem
    EXPECTED: Raises HTTPException 404 (Not Found)
    """
    import main
    from fastapi import HTTPException
    from main import AnalysisRequest

    mock_scanner = AsyncMock()
    mock_scanner.scan.return_value = {"services": {}}  # Empty services

    main._scanner = mock_scanner
    main._report_generator = Mock()

    request = AnalysisRequest(subsystem="nonexistent_subsystem")

    with pytest.raises(HTTPException) as exc_info:
        await main.analyze_subsystem(request)

    assert exc_info.value.status_code == 404
    assert "not found" in exc_info.value.detail.lower()


@pytest.mark.asyncio
async def test_analyze_subsystem_service_not_initialized():
    """
    SCENARIO: analyze_subsystem() when service not initialized
    EXPECTED: Raises HTTPException 503
    """
    import main
    from fastapi import HTTPException
    from main import AnalysisRequest

    main._scanner = None
    main._report_generator = None

    request = AnalysisRequest(subsystem="consciousness")

    with pytest.raises(HTTPException) as exc_info:
        await main.analyze_subsystem(request)

    assert exc_info.value.status_code == 503
    assert "not initialized" in exc_info.value.detail


@pytest.mark.asyncio
async def test_analyze_subsystem_generic_error():
    """
    SCENARIO: analyze_subsystem() encounters unexpected error
    EXPECTED: Raises HTTPException 500
    """
    import main
    from fastapi import HTTPException
    from main import AnalysisRequest

    mock_scanner = AsyncMock()
    mock_scanner.scan.side_effect = Exception("Database connection failed")

    main._scanner = mock_scanner
    main._report_generator = Mock()

    request = AnalysisRequest(subsystem="immune")

    with pytest.raises(HTTPException) as exc_info:
        await main.analyze_subsystem(request)

    assert exc_info.value.status_code == 500
    assert "Analysis failed" in exc_info.value.detail


# ========================================================================
# Test: Latest Report Endpoint
# ========================================================================

@pytest.mark.asyncio
async def test_get_latest_report_success():
    """
    SCENARIO: get_latest_report() when reports exist
    EXPECTED: Returns most recent report metadata
    """
    import main

    mock_report_gen = AsyncMock()
    mock_report_gen.get_latest_report.return_value = {
        "report_id": "VERTICE_ANALYSIS_20251023_150000",
        "path": "/tmp/reports/VERTICE_ANALYSIS_20251023_150000.json",
        "generated_at": "2025-10-23T15:00:00Z",
        "summary": {
            "total_services": 89,
            "readiness_score": 85
        }
    }

    main._report_generator = mock_report_gen

    result = await main.get_latest_report()

    assert result["report_id"] == "VERTICE_ANALYSIS_20251023_150000"
    assert result["summary"]["total_services"] == 89
    assert result["summary"]["readiness_score"] == 85
    mock_report_gen.get_latest_report.assert_called_once()


@pytest.mark.asyncio
async def test_get_latest_report_no_reports():
    """
    SCENARIO: get_latest_report() when no reports exist
    EXPECTED: Raises HTTPException 404
    """
    import main
    from fastapi import HTTPException

    mock_report_gen = AsyncMock()
    mock_report_gen.get_latest_report.return_value = {}  # Empty dict = no reports

    main._report_generator = mock_report_gen

    with pytest.raises(HTTPException) as exc_info:
        await main.get_latest_report()

    assert exc_info.value.status_code == 404
    assert "No reports found" in exc_info.value.detail


@pytest.mark.asyncio
async def test_get_latest_report_service_not_initialized():
    """
    SCENARIO: get_latest_report() when report_generator not initialized
    EXPECTED: Raises HTTPException 503
    """
    import main
    from fastapi import HTTPException

    main._report_generator = None

    with pytest.raises(HTTPException) as exc_info:
        await main.get_latest_report()

    assert exc_info.value.status_code == 503
    assert "not initialized" in exc_info.value.detail


@pytest.mark.asyncio
async def test_get_latest_report_unexpected_error():
    """
    SCENARIO: get_latest_report() encounters filesystem error
    EXPECTED: Raises HTTPException 500
    """
    import main
    from fastapi import HTTPException

    mock_report_gen = AsyncMock()
    mock_report_gen.get_latest_report.side_effect = Exception("Permission denied")

    main._report_generator = mock_report_gen

    with pytest.raises(HTTPException) as exc_info:
        await main.get_latest_report()

    assert exc_info.value.status_code == 500
    assert "Permission denied" in exc_info.value.detail


# ========================================================================
# Test: Gaps Endpoint
# ========================================================================

@pytest.mark.asyncio
async def test_get_gaps_success():
    """
    SCENARIO: get_gaps() when gaps exist
    EXPECTED: Returns list of architectural gaps
    """
    import main

    mock_optimizer = AsyncMock()
    mock_optimizer.get_gaps.return_value = [
        {"type": "kubernetes_operators", "priority": "MEDIUM", "description": "No custom operators"},
        {"type": "service_mesh", "priority": "HIGH", "description": "No Istio"}
    ]

    main._deployment_optimizer = mock_optimizer

    result = await main.get_gaps()

    assert result["status"] == "success"
    assert "timestamp" in result
    assert len(result["gaps"]) == 2
    assert result["gaps"][0]["type"] == "kubernetes_operators"
    assert result["gaps"][1]["type"] == "service_mesh"
    mock_optimizer.get_gaps.assert_called_once()


@pytest.mark.asyncio
async def test_get_gaps_service_not_initialized():
    """
    SCENARIO: get_gaps() when deployment_optimizer not initialized
    EXPECTED: Raises HTTPException 503
    """
    import main
    from fastapi import HTTPException

    main._deployment_optimizer = None

    with pytest.raises(HTTPException) as exc_info:
        await main.get_gaps()

    assert exc_info.value.status_code == 503
    assert "not initialized" in exc_info.value.detail


@pytest.mark.asyncio
async def test_get_gaps_error():
    """
    SCENARIO: get_gaps() encounters error
    EXPECTED: Raises HTTPException 500
    """
    import main
    from fastapi import HTTPException

    mock_optimizer = AsyncMock()
    mock_optimizer.get_gaps.side_effect = Exception("Analysis failed")

    main._deployment_optimizer = mock_optimizer

    with pytest.raises(HTTPException) as exc_info:
        await main.get_gaps()

    assert exc_info.value.status_code == 500
    assert "Analysis failed" in exc_info.value.detail


# ========================================================================
# Test: Redundancies Endpoint
# ========================================================================

@pytest.mark.asyncio
async def test_get_redundancies_success():
    """
    SCENARIO: get_redundancies() finds redundant services
    EXPECTED: Returns redundancy analysis
    """
    import main

    mock_detector = AsyncMock()
    mock_detector.detect.return_value = {
        "redundant_services": [
            {"group": "osint", "services": ["google_osint", "sinesp_osint"], "count": 2}
        ],
        "total_opportunities": 1,
        "estimated_savings": {
            "services_reduced": 1,
            "estimated_memory_savings_gb": 0.5
        }
    }

    main._redundancy_detector = mock_detector

    result = await main.get_redundancies()

    assert result["status"] == "success"
    assert "timestamp" in result
    assert result["redundancies"]["total_opportunities"] == 1
    assert len(result["redundancies"]["redundant_services"]) == 1
    mock_detector.detect.assert_called_once()


@pytest.mark.asyncio
async def test_get_redundancies_service_not_initialized():
    """
    SCENARIO: get_redundancies() when redundancy_detector not initialized
    EXPECTED: Raises HTTPException 503
    """
    import main
    from fastapi import HTTPException

    main._redundancy_detector = None

    with pytest.raises(HTTPException) as exc_info:
        await main.get_redundancies()

    assert exc_info.value.status_code == 503
    assert "not initialized" in exc_info.value.detail


@pytest.mark.asyncio
async def test_get_redundancies_error():
    """
    SCENARIO: get_redundancies() encounters error
    EXPECTED: Raises HTTPException 500
    """
    import main
    from fastapi import HTTPException

    mock_detector = AsyncMock()
    mock_detector.detect.side_effect = Exception("Service scan failed")

    main._redundancy_detector = mock_detector

    with pytest.raises(HTTPException) as exc_info:
        await main.get_redundancies()

    assert exc_info.value.status_code == 500
    assert "Service scan failed" in exc_info.value.detail


# ========================================================================
# Test: Metrics Endpoint
# ========================================================================

@pytest.mark.asyncio
async def test_get_metrics_success():
    """
    SCENARIO: get_metrics() returns system metrics
    EXPECTED: Returns comprehensive metrics dictionary
    """
    import main

    mock_scanner = AsyncMock()
    mock_scanner.scan.return_value = {
        "total_services": 89,
        "subsystems": {
            "consciousness": ["service1", "service2"],
            "immune": ["service3"],
            "infrastructure": ["kafka", "redis", "postgres"]
        },
        "ports": {"8080": "api_gateway", "9092": "kafka", "6379": "redis"},
        "networks": ["vertice_net", "immune_net"],
        "volumes": ["postgres_data", "kafka_data"]
    }

    main._scanner = mock_scanner

    result = await main.get_metrics()

    assert result["status"] == "success"
    assert "timestamp" in result
    assert result["metrics"]["total_services"] == 89
    assert result["metrics"]["subsystems"] == 3
    assert result["metrics"]["ports_allocated"] == 3
    assert result["metrics"]["networks"] == 2
    assert result["metrics"]["volumes"] == 2
    mock_scanner.scan.assert_called_once()


@pytest.mark.asyncio
async def test_get_metrics_service_not_initialized():
    """
    SCENARIO: get_metrics() when scanner not initialized
    EXPECTED: Raises HTTPException 503
    """
    import main
    from fastapi import HTTPException

    main._scanner = None

    with pytest.raises(HTTPException) as exc_info:
        await main.get_metrics()

    assert exc_info.value.status_code == 503
    assert "not initialized" in exc_info.value.detail


@pytest.mark.asyncio
async def test_get_metrics_error():
    """
    SCENARIO: get_metrics() encounters scanning error
    EXPECTED: Raises HTTPException 500
    """
    import main
    from fastapi import HTTPException

    mock_scanner = AsyncMock()
    mock_scanner.scan.side_effect = Exception("File not found")

    main._scanner = mock_scanner

    with pytest.raises(HTTPException) as exc_info:
        await main.get_metrics()

    assert exc_info.value.status_code == 500
    assert "File not found" in exc_info.value.detail


# ========================================================================
# Test: Startup Event
# ========================================================================

@pytest.mark.asyncio
@patch('main.ArchitectureScanner')
@patch('main.IntegrationAnalyzer')
@patch('main.RedundancyDetector')
@patch('main.DeploymentOptimizer')
@patch('main.ReportGenerator')
async def test_startup_event_success(
    mock_report_class,
    mock_optimizer_class,
    mock_redundancy_class,
    mock_integration_class,
    mock_scanner_class
):
    """
    SCENARIO: startup_event() initializes all services
    EXPECTED: All global analyzers are created
    """
    import main

    # Mock class constructors
    mock_scanner_instance = Mock()
    mock_integration_instance = Mock()
    mock_redundancy_instance = Mock()
    mock_optimizer_instance = Mock()
    mock_report_instance = Mock()

    mock_scanner_class.return_value = mock_scanner_instance
    mock_integration_class.return_value = mock_integration_instance
    mock_redundancy_class.return_value = mock_redundancy_instance
    mock_optimizer_class.return_value = mock_optimizer_instance
    mock_report_class.return_value = mock_report_instance

    # Execute startup
    await main.startup_event()

    # Verify all analyzers were created
    assert main._scanner is mock_scanner_instance
    assert main._integration_analyzer is mock_integration_instance
    assert main._redundancy_detector is mock_redundancy_instance
    assert main._deployment_optimizer is mock_optimizer_instance
    assert main._report_generator is mock_report_instance

    # Verify constructors called with correct arguments
    mock_scanner_class.assert_called_once()
    mock_integration_class.assert_called_once_with(scanner=mock_scanner_instance)
    mock_redundancy_class.assert_called_once_with(scanner=mock_scanner_instance)
    mock_optimizer_class.assert_called_once_with(scanner=mock_scanner_instance)
    mock_report_class.assert_called_once()


# ========================================================================
# Test: Pydantic Models
# ========================================================================

def test_analysis_request_model_defaults():
    """
    SCENARIO: AnalysisRequest created with no parameters
    EXPECTED: Default values applied
    """
    from main import AnalysisRequest

    request = AnalysisRequest()

    assert request.subsystem is None
    assert request.include_recommendations is True
    assert request.generate_graphs is True


def test_analysis_request_model_custom_values():
    """
    SCENARIO: AnalysisRequest created with custom parameters
    EXPECTED: Custom values set correctly
    """
    from main import AnalysisRequest

    request = AnalysisRequest(
        subsystem="consciousness",
        include_recommendations=False,
        generate_graphs=False
    )

    assert request.subsystem == "consciousness"
    assert request.include_recommendations is False
    assert request.generate_graphs is False


def test_analysis_response_model():
    """
    SCENARIO: AnalysisResponse created with required fields
    EXPECTED: Model validates correctly
    """
    from main import AnalysisResponse

    response = AnalysisResponse(
        status="success",
        timestamp="2025-10-23T12:00:00Z",
        summary={"total_services": 89},
        report_id="TEST_REPORT_001",
        report_url="/tmp/report.html"
    )

    assert response.status == "success"
    assert response.timestamp == "2025-10-23T12:00:00Z"
    assert response.summary["total_services"] == 89
    assert response.report_id == "TEST_REPORT_001"
    assert response.report_url == "/tmp/report.html"


def test_analysis_response_model_optional_url():
    """
    SCENARIO: AnalysisResponse without report_url
    EXPECTED: report_url defaults to None
    """
    from main import AnalysisResponse

    response = AnalysisResponse(
        status="success",
        timestamp="2025-10-23T12:00:00Z",
        summary={},
        report_id="TEST_002"
    )

    assert response.report_url is None


# ========================================================================
# Coverage Summary
# ========================================================================

"""
COVERAGE TARGET: 95%+

Covered:
✅ health_check() - All paths
✅ analyze_full_system() - Success, errors, critical gaps
✅ analyze_subsystem() - Success, not found, errors
✅ get_latest_report() - Success, no reports, errors
✅ get_gaps() - Success, errors
✅ get_redundancies() - Success, errors
✅ get_metrics() - Success, errors
✅ startup_event() - Full initialization
✅ Pydantic models - AnalysisRequest, AnalysisResponse

Not Covered (untestable):
- if __name__ == "__main__" block (lines 341-347)
- app = FastAPI(...) instantiation (lines 40-44)

Expected Coverage: 95%+
Total Tests: 29 comprehensive tests
"""
