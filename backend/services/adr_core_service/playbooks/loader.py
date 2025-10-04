"""Playbook Loader for loading and parsing YAML-based response playbooks.

This module provides the `PlaybookLoader` class, which is responsible for
finding, parsing, and validating playbook files from a specified directory.
It converts the YAML definitions into Pydantic models for use by the
Response Engine.

Typical usage example:

  loader = PlaybookLoader()
  playbooks = loader.load_all_playbooks()
  for playbook in playbooks:
      response_engine.register_playbook(playbook)
"""

import yaml
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

from ..models import (
    Playbook,
    PlaybookStep,
    PlaybookTrigger,
    ActionType,
    SeverityLevel
)

logger = logging.getLogger(__name__)


class PlaybookLoader:
    """Loads, parses, and validates YAML playbooks from a directory.

    This class handles the auto-discovery of playbook files (`.yml` or `.yaml`),
    parses their content, and validates them against the `Playbook` Pydantic
    model. It also supports hot-reloading of playbooks.

    Attributes:
        playbooks_dir (Path): The directory where playbook files are located.
        loaded_playbooks (Dict[str, Playbook]): A cache of successfully loaded
            playbooks, indexed by their ID.
    """

    def __init__(self, playbooks_dir: str = None):
        """Initializes the PlaybookLoader.

        Args:
            playbooks_dir (str, optional): The path to the playbooks directory.
                If not provided, it defaults to the same directory as this file.
        """
        if playbooks_dir is None:
            # Default to playbooks/ directory relative to this file
            current_file = Path(__file__).resolve()
            self.playbooks_dir = current_file.parent
        else:
            self.playbooks_dir = Path(playbooks_dir)

        self.loaded_playbooks: Dict[str, Playbook] = {}
        logger.info(f"PlaybookLoader initialized for directory: {self.playbooks_dir}")

    def load_all_playbooks(self) -> List[Playbook]:
        """Finds and loads all valid playbooks from the target directory.

        It scans the directory for `.yml` and `.yaml` files, attempts to load
        each one, and returns a list of valid `Playbook` objects.

        Returns:
            List[Playbook]: A list of successfully loaded and validated playbooks.
        """
        playbooks = []

        if not self.playbooks_dir.exists():
            logger.warning(f"Playbooks directory not found: {self.playbooks_dir}")
            return playbooks

        # Find all .yaml and .yml files
        yaml_files = list(self.playbooks_dir.glob("*.yaml"))
        yaml_files.extend(list(self.playbooks_dir.glob("*.yml")))

        logger.info(f"Found {len(yaml_files)} potential playbook files.")

        for yaml_file in yaml_files:
            try:
                playbook = self.load_playbook(yaml_file)
                if playbook:
                    playbooks.append(playbook)
                    self.loaded_playbooks[playbook.playbook_id] = playbook
                    logger.info(f"Successfully loaded playbook: {playbook.name}")
            except Exception as e:
                logger.error(f"Failed to load playbook from {yaml_file.name}: {e}")

        return playbooks

    def load_playbook(self, file_path: Path) -> Optional[Playbook]:
        """Loads and validates a single playbook from a YAML file.

        Args:
            file_path (Path): The path to the YAML playbook file.

        Returns:
            Optional[Playbook]: A `Playbook` object if loading and validation
                succeed, otherwise None.

        Raises:
            ValueError: If a required field is missing in the YAML file.
            yaml.YAMLError: If the file is not valid YAML.
        """
        try:
            with open(file_path, 'r') as f:
                data = yaml.safe_load(f)

            # Basic validation for required top-level fields
            required = ['playbook_id', 'name', 'steps', 'trigger_type', 'trigger_conditions']
            for field in required:
                if field not in data:
                    raise ValueError(f"Missing required field: '{field}'")

            # Parse steps into PlaybookStep models
            steps = []
            for step_data in data['steps']:
                step = PlaybookStep(
                    step_id=step_data['step_id'],
                    name=step_data['name'],
                    action_type=ActionType(step_data['action_type']),
                    order=step_data['order'],
                    parallel=step_data.get('parallel', False),
                    critical=step_data.get('critical', False),
                    timeout_seconds=step_data.get('timeout_seconds', 300),
                    retry_on_failure=step_data.get('retry_on_failure', True),
                    max_retries=step_data.get('max_retries', 3),
                    parameters=step_data.get('parameters', {}),
                    conditions=step_data.get('conditions', [])
                )
                steps.append(step)

            # Create the final Playbook object
            playbook = Playbook(
                playbook_id=data['playbook_id'],
                name=data['name'],
                description=data.get('description', ''),
                enabled=data.get('enabled', True),
                trigger_type=PlaybookTrigger(data['trigger_type']),
                trigger_conditions=data['trigger_conditions'],
                steps=steps,
                auto_execute=data.get('auto_execute', False),
                require_approval=data.get('require_approval', True),
                approval_timeout_minutes=data.get('approval_timeout_minutes', 30),
                severity_threshold=SeverityLevel(data.get('severity_threshold', 'medium')),
                author=data.get('author'),
                version=str(data.get('version', '1.0')),
                tags=data.get('tags', [])
            )

            return playbook

        except (yaml.YAMLError, ValueError, KeyError) as e:
            logger.error(f"Error parsing playbook file {file_path.name}: {e}")
            raise

    def get_playbook(self, playbook_id: str) -> Optional[Playbook]:
        """Retrieves a loaded playbook by its ID.

        Args:
            playbook_id (str): The ID of the playbook to retrieve.

        Returns:
            Optional[Playbook]: The `Playbook` object if found, otherwise None.
        """
        return self.loaded_playbooks.get(playbook_id)

    def reload_playbooks(self) -> int:
        """Clears the cache and reloads all playbooks from the directory.

        This method allows for hot-reloading of playbook configurations without
        restarting the service.

        Returns:
            int: The number of playbooks that were successfully reloaded.
        """
        self.loaded_playbooks.clear()
        playbooks = self.load_all_playbooks()
        return len(playbooks)

    def list_playbooks(self) -> List[Dict[str, Any]]:
        """Provides a summary list of all loaded playbooks.

        Returns:
            List[Dict[str, Any]]: A list of dictionaries, with each dictionary
                containing summary information about a playbook.
        """
        return [
            {
                'playbook_id': pb.playbook_id,
                'name': pb.name,
                'enabled': pb.enabled,
                'auto_execute': pb.auto_execute,
                'steps_count': len(pb.steps),
                'trigger_type': pb.trigger_type.value,
                'version': pb.version
            }
            for pb in self.loaded_playbooks.values()
        ]