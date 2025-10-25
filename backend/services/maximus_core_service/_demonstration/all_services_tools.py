"""Maximus Core Service - All Services Tools.

This module serves as a centralized registry and dispatcher for all available
tools and services within the Maximus AI ecosystem. It aggregates tools from
various categories (e.g., world-class tools, offensive arsenal, advanced tools)
and provides a unified interface for the Tool Orchestrator to discover and
invoke them.

This centralization simplifies tool management, enhances discoverability, and
ensures that Maximus can dynamically access and utilize its full range of
capabilities.
"""

from typing import Any, Dict, List, Optional

from advanced_tools import AdvancedTools
from distributed_organism_tools import DistributedOrganismTools
from enhanced_cognition_tools import EnhancedCognitionTools
from immune_enhancement_tools import ImmuneEnhancementTools
from offensive_arsenal_tools import OffensiveArsenalTools
from _demonstration.tools_world_class import WorldClassTools


class AllServicesTools:
    """Aggregates and manages all available tools and services within Maximus.

    This class provides a unified interface to access and execute tools from
    different categories, such as world-class tools, offensive arsenal, and
    advanced tools.
    """

    def __init__(self, gemini_client: Any):
        """Initializes AllServicesTools with instances of various tool categories.

        Args:
            gemini_client (Any): An initialized Gemini client for tool interactions.
        """
        self.world_class_tools = WorldClassTools(gemini_client)
        self.offensive_arsenal_tools = OffensiveArsenalTools(gemini_client)
        self.advanced_tools = AdvancedTools(gemini_client)
        self.enhanced_cognition_tools = EnhancedCognitionTools(gemini_client)
        self.immune_enhancement_tools = ImmuneEnhancementTools(gemini_client)
        self.distributed_organism_tools = DistributedOrganismTools(gemini_client)

        self.all_tools: Dict[str, Any] = {}
        self._register_tools()

    def _register_tools(self):
        """Registers all tools from different categories into a single dictionary."""
        # Register WorldClassTools
        for tool_info in self.world_class_tools.list_available_tools():
            self.all_tools[tool_info["name"]] = {
                "instance": self.world_class_tools,
                "method": getattr(self.world_class_tools, tool_info["method_name"]),
                "description": tool_info["description"],
                "parameters": tool_info["parameters"],
            }

        # Register OffensiveArsenalTools
        for tool_info in self.offensive_arsenal_tools.list_available_tools():
            self.all_tools[tool_info["name"]] = {
                "instance": self.offensive_arsenal_tools,
                "method": getattr(
                    self.offensive_arsenal_tools, tool_info["method_name"]
                ),
                "description": tool_info["description"],
                "parameters": tool_info["parameters"],
            }

        # Register AdvancedTools
        for tool_info in self.advanced_tools.list_available_tools():
            self.all_tools[tool_info["name"]] = {
                "instance": self.advanced_tools,
                "method": getattr(self.advanced_tools, tool_info["method_name"]),
                "description": tool_info["description"],
                "parameters": tool_info["parameters"],
            }

        # Register EnhancedCognitionTools (FASE 8)
        for tool_info in self.enhanced_cognition_tools.list_available_tools():
            self.all_tools[tool_info["name"]] = {
                "instance": self.enhanced_cognition_tools,
                "method": getattr(
                    self.enhanced_cognition_tools, tool_info["method_name"]
                ),
                "description": tool_info["description"],
                "parameters": tool_info["parameters"],
            }

        # Register ImmuneEnhancementTools (FASE 9)
        for tool_info in self.immune_enhancement_tools.list_available_tools():
            self.all_tools[tool_info["name"]] = {
                "instance": self.immune_enhancement_tools,
                "method": getattr(
                    self.immune_enhancement_tools, tool_info["method_name"]
                ),
                "description": tool_info["description"],
                "parameters": tool_info["parameters"],
            }

        # Register DistributedOrganismTools (FASE 10)
        for tool_info in self.distributed_organism_tools.list_available_tools():
            self.all_tools[tool_info["name"]] = {
                "instance": self.distributed_organism_tools,
                "method": getattr(
                    self.distributed_organism_tools, tool_info["method_name"]
                ),
                "description": tool_info["description"],
                "parameters": tool_info["parameters"],
            }

    def get_tool(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """Retrieves a registered tool by its name.

        Args:
            tool_name (str): The name of the tool to retrieve.

        Returns:
            Optional[Dict[str, Any]]: A dictionary containing tool information (instance, method, description, parameters), or None if the tool is not found.
        """
        return self.all_tools.get(tool_name)

    def list_all_tools(self) -> List[Dict[str, Any]]:
        """Lists all available tools with their descriptions and parameters.

        Returns:
            List[Dict[str, Any]]: A list of dictionaries, each describing an available tool.
        """
        return [
            {
                "name": name,
                "description": tool_info["description"],
                "parameters": tool_info["parameters"],
            }
            for name, tool_info in self.all_tools.items()
        ]
