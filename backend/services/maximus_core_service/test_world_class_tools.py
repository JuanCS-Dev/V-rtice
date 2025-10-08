"""Maximus Core Service - Test World Class Tools.

This module contains unit tests for the 'World Class Tools' integration within
the Maximus AI system. It ensures that the advanced tools and external APIs
integrated into Maximus function as expected, providing reliable and accurate
results for complex tasks.

These tests cover various aspects of tool invocation, parameter passing,
response parsing, and error handling, validating the robustness of the tool
orchestration mechanism.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest
from tools_world_class import WorldClassTools


@pytest.fixture
def mock_gemini_client():
    """Fixture to provide a mocked GeminiClient instance."""
    mock = AsyncMock()
    mock.generate_content.return_value = MagicMock(text="Mocked Gemini response")
    return mock


@pytest.fixture
def world_class_tools(mock_gemini_client):
    """Fixture to provide a WorldClassTools instance with a mocked GeminiClient."""
    return WorldClassTools(gemini_client=mock_gemini_client)


@pytest.mark.asyncio
async def test_execute_tool_success(world_class_tools, mock_gemini_client):
    """Tests successful execution of a world-class tool."""
    tool_name = "search_web"
    tool_args = {"query": "latest AI research"}
    expected_response = "Mocked Gemini response"

    result = await world_class_tools.execute_tool(tool_name, tool_args)

    mock_gemini_client.generate_content.assert_called_once()
    assert result == expected_response


@pytest.mark.asyncio
async def test_execute_tool_unsupported_tool(world_class_tools):
    """Tests execution of an unsupported tool."""
    tool_name = "unsupported_tool"
    tool_args = {"param": "value"}

    with pytest.raises(ValueError, match=f"Unsupported tool: {tool_name}"):
        await world_class_tools.execute_tool(tool_name, tool_args)


@pytest.mark.asyncio
async def test_execute_tool_missing_args(world_class_tools):
    """Tests execution of a tool with missing arguments."""
    tool_name = "search_web"
    tool_args = {}  # Missing 'query'

    with pytest.raises(ValueError, match="Missing required argument 'query' for tool 'search_web'"):
        await world_class_tools.execute_tool(tool_name, tool_args)


@pytest.mark.asyncio
async def test_execute_tool_api_error(world_class_tools, mock_gemini_client):
    """Tests error handling when the underlying API call fails."""
    tool_name = "search_web"
    tool_args = {"query": "error test"}
    mock_gemini_client.generate_content.side_effect = Exception("API Error")

    with pytest.raises(Exception, match="API Error"):
        await world_class_tools.execute_tool(tool_name, tool_args)


@pytest.mark.asyncio
async def test_list_available_tools(world_class_tools):
    """Tests listing of available tools."""
    tools = world_class_tools.list_available_tools()
    assert isinstance(tools, list)
    assert "search_web" in [t["name"] for t in tools]
    assert "get_current_weather" in [t["name"] for t in tools]


@pytest.mark.asyncio
async def test_get_current_weather_success(world_class_tools, mock_gemini_client):
    """Tests successful execution of the get_current_weather tool."""
    tool_name = "get_current_weather"
    tool_args = {"location": "London", "unit": "celsius"}
    expected_response = "Mocked Gemini response"

    result = await world_class_tools.execute_tool(tool_name, tool_args)

    mock_gemini_client.generate_content.assert_called_once()
    assert result == expected_response


@pytest.mark.asyncio
async def test_get_current_weather_missing_location(world_class_tools):
    """Tests get_current_weather with missing location argument."""
    tool_name = "get_current_weather"
    tool_args = {"unit": "fahrenheit"}

    with pytest.raises(
        ValueError,
        match="Missing required argument 'location' for tool 'get_current_weather'",
    ):
        await world_class_tools.execute_tool(tool_name, tool_args)
