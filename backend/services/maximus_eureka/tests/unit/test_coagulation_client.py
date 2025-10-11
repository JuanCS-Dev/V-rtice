"""
Unit tests for Coagulation Client.

Tests WAF rule creation and management via RTE Service integration.
Uses respx for HTTP mocking (httpx-compatible).
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock
import respx
import httpx

from integrations.coagulation_client import (
    CoagulationClient,
    CoagulationRule,
    AttackVectorType,
    CoagulationError,
    create_waf_rule_for_apv,
)


# Fixtures

@pytest.fixture
def mock_rte_response():
    """Mock successful RTE API response"""
    return {
        "rule_id": "rule_12345",
        "status": "active",
        "message": "Rule created successfully"
    }


@pytest.fixture
def sample_apv():
    """Mock APV object"""
    apv = Mock()
    apv.apv_id = "apv_001"
    apv.cve_id = "CVE-2024-TEST"
    apv.cwe_ids = ["CWE-89"]
    return apv


# Tests: Initialization

def test_client_initialization():
    """Test client can be initialized"""
    client = CoagulationClient(rte_url="http://test:8002")
    
    assert client.rte_url == "http://test:8002"
    assert client.timeout == 10
    assert client.max_retries == 3


def test_client_initialization_strips_trailing_slash():
    """Test URL trailing slash is stripped"""
    client = CoagulationClient(rte_url="http://test:8002/")
    
    assert client.rte_url == "http://test:8002"


# Tests: create_temporary_rule

@pytest.mark.asyncio
@respx.mock
async def test_create_temporary_rule_success(mock_rte_response):
    """Test successful rule creation"""
    client = CoagulationClient(rte_url="http://test:8002")
    
    # Mock RTE API
    respx.post("http://test:8002/api/v1/rules").mock(
        return_value=httpx.Response(200, json=mock_rte_response)
    )
    
    rule = await client.create_temporary_rule(
        apv_id="apv_001",
        cve_id="CVE-2024-TEST",
        attack_vector=AttackVectorType.SQL_INJECTION,
        duration=timedelta(hours=24)
    )
    
    # Assertions
    assert rule.rule_id == "rule_12345"
    assert rule.apv_id == "apv_001"
    assert rule.cve_id == "CVE-2024-TEST"
    assert rule.attack_vector == AttackVectorType.SQL_INJECTION
    assert rule.active is True
    assert rule.ttl_seconds == 86400  # 24 hours


@pytest.mark.asyncio
@respx.mock
async def test_create_temporary_rule_with_custom_pattern(mock_rte_response):
    """Test rule creation with custom pattern"""
    client = CoagulationClient(rte_url="http://test:8002")
    
    respx.post("http://test:8002/api/v1/rules").mock(
        return_value=httpx.Response(200, json=mock_rte_response)
    )
    
    rule = await client.create_temporary_rule(
        apv_id="apv_001",
        cve_id="CVE-2024-TEST",
        attack_vector=AttackVectorType.GENERIC,
        custom_pattern=r"custom_regex_pattern"
    )
    
    assert rule.pattern == r"custom_regex_pattern"


@pytest.mark.asyncio
async def test_create_temporary_rule_no_template_no_pattern():
    """Test error when no template and no custom pattern"""
    client = CoagulationClient()
    
    with pytest.raises(CoagulationError, match="No template"):
        await client.create_temporary_rule(
            apv_id="apv_001",
            cve_id="CVE-2024-TEST",
            attack_vector=AttackVectorType.GENERIC  # No template
        )


@pytest.mark.asyncio
@respx.mock
async def test_create_temporary_rule_rte_api_error():
    """Test handling of RTE API error"""
    client = CoagulationClient(rte_url="http://test:8002")
    
    respx.post("http://test:8002/api/v1/rules").mock(
        return_value=httpx.Response(500, text="Internal Error")
    )
    
    with pytest.raises(CoagulationError, match="Failed to create rule"):
        await client.create_temporary_rule(
            apv_id="apv_001",
            cve_id="CVE-2024-TEST",
            attack_vector=AttackVectorType.SQL_INJECTION
        )


@pytest.mark.asyncio
@respx.mock
async def test_create_temporary_rule_network_error():
    """Test handling of network error"""
    client = CoagulationClient(rte_url="http://test:8002")
    
    respx.post("http://test:8002/api/v1/rules").mock(
        side_effect=httpx.ConnectError("Connection refused")
    )
    
    with pytest.raises(CoagulationError, match="Rule creation failed"):
        await client.create_temporary_rule(
            apv_id="apv_001",
            cve_id="CVE-2024-TEST",
            attack_vector=AttackVectorType.XSS
        )


# Tests: expire_rule

@pytest.mark.asyncio
@respx.mock
async def test_expire_rule_success():
    """Test successful rule expiration"""
    client = CoagulationClient(rte_url="http://test:8002")
    
    respx.delete("http://test:8002/api/v1/rules/rule_12345").mock(
        return_value=httpx.Response(204)
    )
    
    result = await client.expire_rule("rule_12345")
    
    assert result is True


@pytest.mark.asyncio
@respx.mock
async def test_expire_rule_not_found():
    """Test expiring non-existent rule"""
    client = CoagulationClient(rte_url="http://test:8002")
    
    respx.delete("http://test:8002/api/v1/rules/rule_nonexistent").mock(
        return_value=httpx.Response(404)
    )
    
    result = await client.expire_rule("rule_nonexistent")
    
    assert result is False  # Should return False, not raise


@pytest.mark.asyncio
@respx.mock
async def test_expire_rule_api_error():
    """Test expiration API error"""
    client = CoagulationClient(rte_url="http://test:8002")
    
    respx.delete("http://test:8002/api/v1/rules/rule_12345").mock(
        return_value=httpx.Response(500)
    )
    
    with pytest.raises(CoagulationError, match="Expiration failed"):
        await client.expire_rule("rule_12345")


# Tests: get_rule_status

@pytest.mark.asyncio
@respx.mock
async def test_get_rule_status_success():
    """Test getting rule status"""
    client = CoagulationClient(rte_url="http://test:8002")
    
    status_data = {
        "rule_id": "rule_12345",
        "status": "active",
        "blocks_count": 42,
        "expires_at": "2024-01-02T00:00:00"
    }
    
    respx.get("http://test:8002/api/v1/rules/rule_12345").mock(
        return_value=httpx.Response(200, json=status_data)
    )
    
    status = await client.get_rule_status("rule_12345")
    
    assert status["rule_id"] == "rule_12345"
    assert status["blocks_count"] == 42


@pytest.mark.asyncio
@respx.mock
async def test_get_rule_status_not_found():
    """Test status of non-existent rule"""
    client = CoagulationClient(rte_url="http://test:8002")
    
    respx.get("http://test:8002/api/v1/rules/rule_nonexistent").mock(
        return_value=httpx.Response(404)
    )
    
    with pytest.raises(CoagulationError, match="not found"):
        await client.get_rule_status("rule_nonexistent")


# Tests: list_active_rules

@pytest.mark.asyncio
@respx.mock
async def test_list_active_rules():
    """Test listing active rules"""
    client = CoagulationClient(rte_url="http://test:8002")
    
    rules_data = {
        "rules": [
            {"rule_id": "rule_1", "status": "active"},
            {"rule_id": "rule_2", "status": "active"}
        ]
    }
    
    respx.get("http://test:8002/api/v1/rules").mock(
        return_value=httpx.Response(200, json=rules_data)
    )
    
    rules = await client.list_active_rules()
    
    assert len(rules) == 2
    assert rules[0]["rule_id"] == "rule_1"


@pytest.mark.asyncio
@respx.mock
async def test_list_active_rules_with_apv_filter():
    """Test listing rules filtered by APV"""
    client = CoagulationClient(rte_url="http://test:8002")
    
    rules_data = {"rules": [{"rule_id": "rule_1", "apv_id": "apv_001"}]}
    
    respx.get("http://test:8002/api/v1/rules", params={"apv_id": "apv_001"}).mock(
        return_value=httpx.Response(200, json=rules_data)
    )
    
    rules = await client.list_active_rules(apv_id="apv_001")
    
    assert len(rules) == 1


# Tests: health_check

@pytest.mark.asyncio
@respx.mock
async def test_health_check_healthy():
    """Test health check when service is healthy"""
    client = CoagulationClient(rte_url="http://test:8002")
    
    respx.get("http://test:8002/health").mock(
        return_value=httpx.Response(200)
    )
    
    healthy = await client.health_check()
    
    assert healthy is True


@pytest.mark.asyncio
@respx.mock
async def test_health_check_unhealthy():
    """Test health check when service is down"""
    client = CoagulationClient(rte_url="http://test:8002")
    
    respx.get("http://test:8002/health").mock(
        side_effect=httpx.ConnectError("Connection refused")
    )
    
    healthy = await client.health_check()
    
    assert healthy is False


# Tests: detect_attack_vector_from_cwe

def test_detect_attack_vector_sql_injection():
    """Test CWE-89 maps to SQL Injection"""
    vector = CoagulationClient.detect_attack_vector_from_cwe("CWE-89")
    assert vector == AttackVectorType.SQL_INJECTION


def test_detect_attack_vector_xss():
    """Test CWE-79 maps to XSS"""
    vector = CoagulationClient.detect_attack_vector_from_cwe("CWE-79")
    assert vector == AttackVectorType.XSS


def test_detect_attack_vector_command_injection():
    """Test CWE-78 maps to Command Injection"""
    vector = CoagulationClient.detect_attack_vector_from_cwe("CWE-78")
    assert vector == AttackVectorType.COMMAND_INJECTION


def test_detect_attack_vector_unknown_cwe():
    """Test unknown CWE maps to GENERIC"""
    vector = CoagulationClient.detect_attack_vector_from_cwe("CWE-9999")
    assert vector == AttackVectorType.GENERIC


# Tests: CoagulationRule model

def test_coagulation_rule_to_dict():
    """Test rule to dictionary conversion"""
    now = datetime.now()
    rule = CoagulationRule(
        rule_id="rule_123",
        apv_id="apv_001",
        cve_id="CVE-2024-TEST",
        attack_vector=AttackVectorType.SQL_INJECTION,
        pattern=r"pattern",
        action="block",
        ttl_seconds=86400,
        created_at=now,
        expires_at=now + timedelta(hours=24),
        active=True
    )
    
    data = rule.to_dict()
    
    assert data["rule_id"] == "rule_123"
    assert data["attack_vector"] == "sql_injection"
    assert data["active"] is True


# Tests: AttackVectorType enum

def test_attack_vector_enum_values():
    """Test AttackVectorType enum values"""
    assert AttackVectorType.SQL_INJECTION.value == "sql_injection"
    assert AttackVectorType.XSS.value == "xss"
    assert AttackVectorType.COMMAND_INJECTION.value == "command_injection"


# Tests: RULE_TEMPLATES

def test_rule_templates_coverage():
    """Test rule templates exist for common vectors"""
    client = CoagulationClient()
    
    # Check key templates exist
    assert AttackVectorType.SQL_INJECTION in client.RULE_TEMPLATES
    assert AttackVectorType.XSS in client.RULE_TEMPLATES
    assert AttackVectorType.COMMAND_INJECTION in client.RULE_TEMPLATES
    assert AttackVectorType.PATH_TRAVERSAL in client.RULE_TEMPLATES
    assert AttackVectorType.SSRF in client.RULE_TEMPLATES


def test_rule_template_structure():
    """Test rule templates have required fields"""
    client = CoagulationClient()
    
    for vector, template in client.RULE_TEMPLATES.items():
        assert "pattern" in template
        assert "action" in template
        assert "description" in template
        assert isinstance(template["pattern"], str)
        assert template["action"] in ["block", "alert", "log"]


# Tests: Convenience function

@pytest.mark.asyncio
@respx.mock
async def test_create_waf_rule_for_apv(sample_apv, mock_rte_response):
    """Test convenience function"""
    respx.post("http://test:8002/api/v1/rules").mock(
        return_value=httpx.Response(200, json=mock_rte_response)
    )
    
    rule = await create_waf_rule_for_apv(sample_apv, rte_url="http://test:8002")
    
    assert rule.apv_id == "apv_001"
    assert rule.cve_id == "CVE-2024-TEST"
    assert rule.attack_vector == AttackVectorType.SQL_INJECTION  # From CWE-89


# Tests: Edge cases

@pytest.mark.asyncio
@respx.mock
async def test_create_rule_with_zero_duration(mock_rte_response):
    """Test creating rule with minimal duration"""
    client = CoagulationClient(rte_url="http://test:8002")
    
    respx.post("http://test:8002/api/v1/rules").mock(
        return_value=httpx.Response(200, json=mock_rte_response)
    )
    
    rule = await client.create_temporary_rule(
        apv_id="apv_001",
        cve_id="CVE-2024-TEST",
        attack_vector=AttackVectorType.SQL_INJECTION,
        duration=timedelta(seconds=1)
    )
    
    assert rule.ttl_seconds == 1


@pytest.mark.asyncio
@respx.mock
async def test_create_rule_with_very_long_duration(mock_rte_response):
    """Test creating rule with long duration"""
    client = CoagulationClient(rte_url="http://test:8002")
    
    respx.post("http://test:8002/api/v1/rules").mock(
        return_value=httpx.Response(200, json=mock_rte_response)
    )
    
    rule = await client.create_temporary_rule(
        apv_id="apv_001",
        cve_id="CVE-2024-TEST",
        attack_vector=AttackVectorType.SQL_INJECTION,
        duration=timedelta(days=365)
    )
    
    assert rule.ttl_seconds == 365 * 86400
