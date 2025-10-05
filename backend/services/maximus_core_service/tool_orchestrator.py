"""Maximus Core Service - Tool Orchestrator.

This module is responsible for dynamically selecting, invoking, and managing
the execution of various tools available to the Maximus AI system. It acts as
a central hub for tool interaction, enabling Maximus to extend its capabilities
beyond its internal knowledge base by interacting with external APIs and services.

The orchestrator interprets tool-use requests from the Reasoning Engine, validates
parameters, executes the appropriate tool, and returns the results, facilitating
a robust and extensible architecture.
"""

import asyncio
from typing import Dict, Any, List, Optional
from all_services_tools import AllServicesTools


class ToolOrchestrator:
    """Dynamically selects, invokes, and manages the execution of various tools.

    This class acts as a central hub for tool interaction, enabling Maximus to
    extend its capabilities by interacting with external APIs and services.
    """

    def __init__(self, gemini_client: Any):
        """Initializes the ToolOrchestrator with an AllServicesTools instance.

        Args:
            gemini_client (Any): An initialized Gemini client for tool interactions.
        """
        self.all_tools = AllServicesTools(gemini_client)

    async def execute_tools(self, tool_calls: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Executes a list of tool calls.

        Args:
            tool_calls (List[Dict[str, Any]]): A list of dictionaries, each representing a tool call.
                Each dictionary should have 'name' and 'args' keys.

        Returns:
            List[Dict[str, Any]]: A list of dictionaries, each containing the result of a tool execution.
        """
        results = []
        for tool_call in tool_calls:
            tool_name = tool_call.get("name")
            tool_args = tool_call.get("args", {})

            tool_info = self.all_tools.get_tool(tool_name)
            if not tool_info:
                results.append({"tool_name": tool_name, "error": f"Tool '{tool_name}' not found."})
                continue

            try:
                method = tool_info["method"]
                result = await method(**tool_args)
                results.append({"tool_name": tool_name, "output": result})
            except Exception as e:
                results.append({"tool_name": tool_name, "error": str(e)})
        return results

    def list_all_available_tools(self) -> List[Dict[str, Any]]:
        """Lists all tools registered with the orchestrator.

        Returns:
            List[Dict[str, Any]]: A list of dictionaries, each describing an available tool.
        """
        return self.all_tools.list_all_tools()

    def get_gemini_function_declarations(self) -> List[Dict[str, Any]]:
        """Generates Gemini-compatible function declarations for all available tools.

        Returns:
            List[Dict[str, Any]]: A list of function declarations in Gemini format.
        """
        all_tools = self.all_tools.list_all_tools()
        function_declarations = []

        for tool in all_tools:
            # Convert tool parameters to JSON schema format
            properties = {}
            required_params = []

            # Parse parameter descriptions into JSON schema
            if isinstance(tool.get("parameters"), dict):
                for param_name, param_desc in tool["parameters"].items():
                    properties[param_name] = {
                        "type": "string",  # Default type
                        "description": param_desc
                    }
                    # All parameters are considered optional by default
                    # unless explicitly marked as required

            function_declaration = {
                "name": tool["name"],
                "description": tool["description"],
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required_params  # Empty list means all params are optional
                }
            }

            function_declarations.append(function_declaration)

        return function_declarations