"""Maximus Core Service - Agent Templates Module.

This module provides a repository and management system for various agent
templates or personas that Maximus AI can adopt. These templates define specific
behaviors, communication styles, expertise domains, and operational constraints
for different tasks or user interactions.

By leveraging agent templates, Maximus can dynamically adapt its approach to
match the requirements of a given situation, ensuring more appropriate and
effective responses. This allows for flexible and context-aware AI behavior.
"""

from typing import Dict, Any, List, Optional


class AgentTemplates:
    """Manages a repository of agent templates or personas for Maximus AI.

    These templates define specific behaviors, communication styles, expertise domains,
    and operational constraints for different tasks or user interactions.
    """

    def __init__(self):
        """Initializes the AgentTemplates with a set of predefined templates."""
        self.templates: Dict[str, Dict[str, Any]] = {
            "default_assistant": {
                "name": "Default Assistant",
                "description": "A general-purpose helpful AI assistant.",
                "instructions": "You are a helpful AI assistant. Provide concise and accurate information.",
                "tone": "neutral",
                "expertise": ["general knowledge"]
            },
            "technical_expert": {
                "name": "Technical Expert",
                "description": "An AI specialized in technical problem-solving and explanations.",
                "instructions": "You are a technical expert. Provide detailed, accurate, and precise technical information. Use code examples where appropriate.",
                "tone": "formal and precise",
                "expertise": ["software engineering", "cloud computing", "AI/ML"]
            },
            "creative_writer": {
                "name": "Creative Writer",
                "description": "An AI skilled in generating creative content.",
                "instructions": "You are a creative writer. Generate imaginative and engaging content. Focus on storytelling and vivid descriptions.",
                "tone": "imaginative and engaging",
                "expertise": ["storytelling", "poetry", "marketing copy"]
            }
        }

    def get_template(self, template_name: str) -> Optional[Dict[str, Any]]:
        """Retrieves an agent template by its name.

        Args:
            template_name (str): The name of the template to retrieve.

        Returns:
            Optional[Dict[str, Any]]: The agent template dictionary, or None if not found.
        """
        return self.templates.get(template_name)

    def list_templates(self) -> List[Dict[str, Any]]:
        """Lists all available agent templates.

        Returns:
            List[Dict[str, Any]]: A list of all agent template dictionaries.
        """
        return list(self.templates.values())

    def add_template(self, template_name: str, template_data: Dict[str, Any]):
        """Adds a new agent template to the repository.

        Args:
            template_name (str): The name of the new template.
            template_data (Dict[str, Any]): The data defining the new template.
        
        Raises:
            ValueError: If a template with the given name already exists.
        """
        if template_name in self.templates:
            raise ValueError(f"Template '{template_name}' already exists.")
        self.templates[template_name] = template_data

    def update_template(self, template_name: str, template_data: Dict[str, Any]):
        """Updates an existing agent template.

        Args:
            template_name (str): The name of the template to update.
            template_data (Dict[str, Any]): The new data for the template.
        
        Raises:
            ValueError: If the template with the given name does not exist.
        """
        if template_name not in self.templates:
            raise ValueError(f"Template '{template_name}' does not exist.")
        self.templates[template_name].update(template_data)

    def delete_template(self, template_name: str):
        """Deletes an agent template from the repository.

        Args:
            template_name (str): The name of the template to delete.
        
        Raises:
            ValueError: If the template with the given name does not exist.
        """
        if template_name not in self.templates:
            raise ValueError(f"Template '{template_name}' does not exist.")
        del self.templates[template_name]
