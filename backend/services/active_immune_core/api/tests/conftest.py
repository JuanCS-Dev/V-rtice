"""Test Configuration and Fixtures - PRODUCTION-READY

Shared fixtures and configuration for test suite.

NO MOCKS, NO PLACEHOLDERS, NO TODOS.

Authors: Juan & Claude
Version: 1.0.0
"""

import pytest
from fastapi.testclient import TestClient
from typing import Dict, Generator
from prometheus_client import REGISTRY

from api.main import create_app


@pytest.fixture(scope="function")
def app():
    """
    Create FastAPI app for testing.

    Scope: function (fresh app for each test)
    """
    return create_app()


@pytest.fixture(scope="function")
def client(app) -> Generator[TestClient, None, None]:
    """
    Create test client.

    Yields:
        TestClient instance
    """
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="function", autouse=True)
def clean_prometheus():
    """
    Clean Prometheus registry before each test.

    This fixture runs automatically for every test.
    """
    # Clean Prometheus registry to avoid duplicated metrics
    collectors = list(REGISTRY._collector_to_names.keys())
    for collector in collectors:
        try:
            REGISTRY.unregister(collector)
        except Exception:
            pass  # Collector already unregistered

    yield

    # Clean Prometheus registry again
    collectors = list(REGISTRY._collector_to_names.keys())
    for collector in collectors:
        try:
            REGISTRY.unregister(collector)
        except Exception:
            pass


@pytest.fixture
def sample_agent_data() -> Dict:
    """
    Sample agent creation data.

    Returns:
        Agent creation payload
    """
    return {
        "agent_type": "neutrophil",
        "config": {
            "area_patrulha": "test_zone_unit"
        }
    }


@pytest.fixture
def sample_task_data() -> Dict:
    """
    Sample task creation data.

    Returns:
        Task creation payload
    """
    return {
        "task_type": "detection",
        "priority": 7,
        "target": "192.168.1.100",
        "parameters": {
            "scan_type": "full",
            "timeout": 300,
        },
        "timeout": 600.0,
    }


@pytest.fixture
def sample_consensus_proposal() -> Dict:
    """
    Sample consensus proposal data.

    Returns:
        Consensus proposal payload
    """
    return {
        "proposal_type": "policy_change",
        "proposal_data": {
            "policy_key": "detection_threshold",
            "new_value": 0.9,
            "reason": "Reduce false positives",
        },
        "proposer_id": "agent_neutrophil_001",
        "timeout": 30.0,
    }


@pytest.fixture
def created_agent(client: TestClient, sample_agent_data: Dict) -> Dict:
    """
    Create a test agent and return its data.

    Args:
        client: Test client
        sample_agent_data: Agent creation data

    Returns:
        Created agent data
    """
    response = client.post("/agents/", json=sample_agent_data)
    assert response.status_code == 201
    return response.json()


@pytest.fixture
def created_task(client: TestClient, sample_task_data: Dict) -> Dict:
    """
    Create a test task and return its data.

    Args:
        client: Test client
        sample_task_data: Task creation data

    Returns:
        Created task data
    """
    response = client.post("/coordination/tasks", json=sample_task_data)
    assert response.status_code == 201
    return response.json()


@pytest.fixture
def multiple_agents(client: TestClient) -> list[Dict]:
    """
    Create multiple test agents.

    Args:
        client: Test client

    Returns:
        List of created agents
    """
    agent_types = ["neutrophil", "macrophage", "nk_cell"]
    agents = []

    for agent_type in agent_types:
        response = client.post(
            "/agents/",
            json={
                "agent_type": agent_type,
                "config": {"area_patrulha": f"test_zone_{agent_type}"}
            }
        )
        assert response.status_code == 201
        agents.append(response.json())

    return agents


@pytest.fixture
def multiple_tasks(client: TestClient) -> list[Dict]:
    """
    Create multiple test tasks.

    Args:
        client: Test client

    Returns:
        List of created tasks
    """
    task_types = ["detection", "neutralization", "analysis"]
    tasks = []

    for task_type in task_types:
        response = client.post(
            "/coordination/tasks",
            json={
                "task_type": task_type,
                "priority": 5,
                "target": f"target_{task_type}",
            }
        )
        assert response.status_code == 201
        tasks.append(response.json())

    return tasks
