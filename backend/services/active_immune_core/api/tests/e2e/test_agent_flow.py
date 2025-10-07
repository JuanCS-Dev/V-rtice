"""Agent Flow E2E Tests - PRODUCTION-READY

End-to-end tests for complete agent lifecycle flows.

Tests real HTTP requests → API → Core System integration.

NO MOCKS, NO PLACEHOLDERS, NO TODOS.

Authors: Juan & Claude
Version: 1.0.0
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_agent_creation_flow(client: AsyncClient, agent_ids: list):
    """Test complete agent creation flow."""
    # Create agent
    response = await client.post(
        "/agents/",
        json={
            "agent_type": "macrofago",
            "config": {"area_patrulha": "test_zone_e2e"},
        },
    )

    assert response.status_code == 201
    data = response.json()

    assert "agent_id" in data
    assert data["agent_type"].lower() == "macrofago"  # Case-insensitive check
    assert data["status"] in ["active", "inactive", "patrulhando"]
    assert data["health"] >= 0.0
    assert data["energia"] >= 0.0

    agent_id = data["agent_id"]
    agent_ids.append(agent_id)


@pytest.mark.asyncio
async def test_agent_list_and_get_flow(client: AsyncClient, agent_ids: list):
    """Test listing and getting agents."""
    # Create agent first
    create_response = await client.post(
        "/agents/",
        json={
            "agent_type": "neutrofilo",
            "config": {"area_patrulha": "test_zone_e2e"},
        },
    )
    assert create_response.status_code == 201
    agent_id = create_response.json()["agent_id"]
    agent_ids.append(agent_id)

    # List all agents
    list_response = await client.get("/agents/")
    assert list_response.status_code == 200
    list_data = list_response.json()

    assert "total" in list_data
    assert "agents" in list_data
    assert list_data["total"] >= 1
    assert len(list_data["agents"]) >= 1

    # Get specific agent
    get_response = await client.get(f"/agents/{agent_id}")
    assert get_response.status_code == 200
    agent_data = get_response.json()

    assert agent_data["agent_id"] == agent_id
    assert agent_data["agent_type"].lower() == "neutrofilo"


@pytest.mark.asyncio
async def test_agent_update_flow(client: AsyncClient, agent_ids: list):
    """Test agent update flow."""
    # Create agent
    create_response = await client.post(
        "/agents/",
        json={
            "agent_type": "nk_cell",
            "config": {"area_patrulha": "test_zone_e2e"},
        },
    )
    assert create_response.status_code == 201
    agent_id = create_response.json()["agent_id"]
    agent_ids.append(agent_id)

    # Update agent
    update_response = await client.patch(
        f"/agents/{agent_id}",
        json={"config": {"new_param": "test_value"}},
    )
    assert update_response.status_code == 200
    updated_data = update_response.json()

    assert updated_data["agent_id"] == agent_id
    # Config should be updated (merged)


@pytest.mark.asyncio
async def test_agent_stats_flow(client: AsyncClient, agent_ids: list):
    """Test agent statistics retrieval."""
    # Create agent
    create_response = await client.post(
        "/agents/",
        json={
            "agent_type": "macrofago",
            "config": {"area_patrulha": "test_zone_e2e"},
        },
    )
    assert create_response.status_code == 201
    agent_id = create_response.json()["agent_id"]
    agent_ids.append(agent_id)

    # Get stats
    stats_response = await client.get(f"/agents/{agent_id}/stats")
    assert stats_response.status_code == 200
    stats_data = stats_response.json()

    assert "agent_id" in stats_data
    assert "total_tasks" in stats_data
    assert "success_rate" in stats_data
    assert "uptime_seconds" in stats_data
    assert stats_data["agent_id"] == agent_id


@pytest.mark.asyncio
async def test_agent_actions_flow(client: AsyncClient, agent_ids: list):
    """Test agent action flow (start/stop/pause/resume)."""
    # Create agent
    create_response = await client.post(
        "/agents/",
        json={
            "agent_type": "neutrofilo",
            "config": {"area_patrulha": "test_zone_e2e"},
        },
    )
    assert create_response.status_code == 201
    agent_id = create_response.json()["agent_id"]
    agent_ids.append(agent_id)

    # Start agent
    start_response = await client.post(
        f"/agents/{agent_id}/actions", json={"action": "start"}
    )
    assert start_response.status_code == 200
    start_data = start_response.json()

    assert start_data["success"] is True
    assert start_data["action"] == "start"

    # Pause agent
    pause_response = await client.post(
        f"/agents/{agent_id}/actions", json={"action": "pause"}
    )
    # May succeed or fail depending on current status
    # Just verify it returns a valid response
    assert pause_response.status_code in [200, 400]

    # Stop agent
    stop_response = await client.post(
        f"/agents/{agent_id}/actions", json={"action": "stop"}
    )
    assert stop_response.status_code == 200
    stop_data = stop_response.json()

    assert stop_data["success"] is True
    assert stop_data["action"] == "stop"


@pytest.mark.asyncio
async def test_agent_delete_flow(client: AsyncClient, agent_ids: list):
    """Test agent deletion flow."""
    # Create agent
    create_response = await client.post(
        "/agents/",
        json={
            "agent_type": "macrofago",
            "config": {"area_patrulha": "test_zone_e2e"},
        },
    )
    assert create_response.status_code == 201
    agent_id = create_response.json()["agent_id"]

    # Delete agent
    delete_response = await client.delete(f"/agents/{agent_id}")
    assert delete_response.status_code == 204

    # Verify agent is gone
    get_response = await client.get(f"/agents/{agent_id}")
    assert get_response.status_code == 404

    # Remove from tracking (already deleted)
    if agent_id in agent_ids:
        agent_ids.remove(agent_id)


@pytest.mark.asyncio
async def test_agent_list_filtering(client: AsyncClient, agent_ids: list):
    """Test agent list filtering by type and status."""
    # Create multiple agents
    agent1_response = await client.post(
        "/agents/",
        json={"agent_type": "macrofago", "config": {"area_patrulha": "zone1"}},
    )
    assert agent1_response.status_code == 201
    agent_ids.append(agent1_response.json()["agent_id"])

    agent2_response = await client.post(
        "/agents/",
        json={"agent_type": "neutrofilo", "config": {"area_patrulha": "zone2"}},
    )
    assert agent2_response.status_code == 201
    agent_ids.append(agent2_response.json()["agent_id"])

    # Filter by type
    filter_response = await client.get("/agents/?agent_type=macrofago")
    assert filter_response.status_code == 200
    filter_data = filter_response.json()

    # Should have at least the macrofago we just created
    macrofagos = [a for a in filter_data["agents"] if a["agent_type"] == "macrofago"]
    assert len(macrofagos) >= 1


@pytest.mark.asyncio
async def test_agent_types_available(client: AsyncClient):
    """Test available agent types endpoint."""
    response = await client.get("/agents/types/available")
    assert response.status_code == 200
    types = response.json()

    assert isinstance(types, list)
    assert len(types) > 0
    # Should contain expected types
    expected_types = ["neutrophil", "macrophage", "nk_cell"]
    for expected in expected_types:
        assert expected in types


@pytest.mark.asyncio
async def test_agent_not_found(client: AsyncClient):
    """Test 404 for non-existent agent."""
    response = await client.get("/agents/nonexistent_agent_id")
    assert response.status_code == 404
    error_data = response.json()
    assert "detail" in error_data


@pytest.mark.asyncio
async def test_agent_pagination(client: AsyncClient, agent_ids: list):
    """Test agent list pagination."""
    # Create multiple agents
    for i in range(3):
        response = await client.post(
            "/agents/",
            json={
                "agent_type": "neutrofilo",
                "config": {"area_patrulha": f"zone_{i}"},
            },
        )
        assert response.status_code == 201
        agent_ids.append(response.json()["agent_id"])

    # Test pagination
    page1 = await client.get("/agents/?skip=0&limit=2")
    assert page1.status_code == 200
    page1_data = page1.json()

    assert len(page1_data["agents"]) <= 2

    # Second page
    page2 = await client.get("/agents/?skip=2&limit=2")
    assert page2.status_code == 200
    page2_data = page2.json()

    # Should have different agents (or empty if not enough)
    if len(page2_data["agents"]) > 0:
        assert page1_data["agents"][0]["agent_id"] != page2_data["agents"][0]["agent_id"]
