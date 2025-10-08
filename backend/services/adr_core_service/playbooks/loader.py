"""Maximus ADR Core Service - Playbook Loader.

This module is responsible for loading, parsing, and validating Automated
Detection and Response (ADR) playbook definitions. Playbooks are typically
defined in a structured format (e.g., YAML, JSON) and outline the steps and
logic for responding to various security incidents.

The Playbook Loader ensures that playbooks are correctly formatted, adhere to
predefined schemas, and are available for the Response Engine to execute.
It supports dynamic loading and updating of playbooks, allowing for agile
adaptation to evolving threat landscapes.
"""

import os
from typing import Dict, List, Optional

import yaml  # Assuming PyYAML is installed for YAML parsing

from models.schemas import Playbook
from utils.logger import setup_logger

logger = setup_logger(__name__)


class PlaybookLoader:
    """Loads, parses, and validates Automated Detection and Response (ADR) playbook definitions.

    Ensures that playbooks are correctly formatted, adhere to predefined schemas,
    and are available for the Response Engine to execute.
    """

    def __init__(self):
        """Initializes the PlaybookLoader."""
        self.playbooks: Dict[str, Playbook] = {}
        logger.info("[PlaybookLoader] Initialized Playbook Loader.")

    async def load_playbooks(self, directory_path: str):
        """Loads all playbook definitions from a specified directory.

        Args:
            directory_path (str): The path to the directory containing playbook YAML/JSON files.

        Raises:
            FileNotFoundError: If the directory_path does not exist.
            ValueError: If a playbook file is malformed or invalid.
        """
        if not os.path.isdir(directory_path):
            raise FileNotFoundError(f"Playbook directory not found: {directory_path}")

        logger.info(f"[PlaybookLoader] Loading playbooks from: {directory_path}")
        for filename in os.listdir(directory_path):
            if filename.endswith(".yaml") or filename.endswith(".yml") or filename.endswith(".json"):
                filepath = os.path.join(directory_path, filename)
                try:
                    with open(filepath, "r") as f:
                        if filename.endswith(".json"):
                            import json

                            data = json.load(f)
                        else:
                            data = yaml.safe_load(f)

                    playbook = Playbook(**data)  # Validate with Pydantic schema
                    self.playbooks[playbook.id] = playbook
                    logger.info(f"[PlaybookLoader] Loaded playbook: {playbook.id}")
                except Exception as e:
                    logger.error(f"[PlaybookLoader] Error loading playbook {filename}: {e}")
                    raise ValueError(f"Malformed or invalid playbook file: {filename} - {e}")
        logger.info(f"[PlaybookLoader] Finished loading {len(self.playbooks)} playbooks.")

    def get_playbook(self, playbook_id: str) -> Optional[Playbook]:
        """Retrieves a specific playbook by its ID.

        Args:
            playbook_id (str): The ID of the playbook to retrieve.

        Returns:
            Optional[Playbook]: The Playbook object, or None if not found.
        """
        return self.playbooks.get(playbook_id)

    def get_playbook_for_incident(self, incident_id: str) -> Optional[Playbook]:
        """Retrieves a playbook suitable for a given incident (simplified logic).

        Args:
            incident_id (str): The ID of the incident.

        Returns:
            Optional[Playbook]: A suitable Playbook object, or None if no match.
        """
        # Simplified logic: In a real system, this would involve matching incident
        # characteristics (type, severity, affected assets) to playbook triggers.
        logger.info(f"[PlaybookLoader] Attempting to find playbook for incident: {incident_id}")
        for playbook in self.playbooks.values():
            # Example: if playbook name contains a keyword from incident_id
            if "malware" in incident_id.lower() and "malware" in playbook.id.lower():
                return playbook
            if "phishing" in incident_id.lower() and "phishing" in playbook.id.lower():
                return playbook
        return None

    def get_all_playbooks(self) -> List[Playbook]:
        """Returns a list of all loaded playbooks.

        Returns:
            List[Playbook]: A list of all Playbook objects.
        """
        return list(self.playbooks.values())
