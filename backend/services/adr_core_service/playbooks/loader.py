"""
Playbook Loader - Load and parse YAML playbooks
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
    """
    Load and validate YAML playbooks

    Features:
    - Auto-discovery of .yaml files
    - Validation against schema
    - Hot-reload capability
    """

    def __init__(self, playbooks_dir: str = None):
        if playbooks_dir is None:
            # Default to playbooks/ directory
            current_file = Path(__file__).resolve()
            self.playbooks_dir = current_file.parent
        else:
            self.playbooks_dir = Path(playbooks_dir)

        self.loaded_playbooks: Dict[str, Playbook] = {}
        logger.info(f"PlaybookLoader initialized: {self.playbooks_dir}")

    def load_all_playbooks(self) -> List[Playbook]:
        """
        Load all playbooks from directory

        Returns:
            List of loaded playbook objects
        """
        playbooks = []

        if not self.playbooks_dir.exists():
            logger.warning(f"Playbooks directory not found: {self.playbooks_dir}")
            return playbooks

        # Find all .yaml files
        yaml_files = list(self.playbooks_dir.glob("*.yaml"))
        yaml_files.extend(list(self.playbooks_dir.glob("*.yml")))

        logger.info(f"Found {len(yaml_files)} playbook files")

        for yaml_file in yaml_files:
            try:
                playbook = self.load_playbook(yaml_file)
                if playbook:
                    playbooks.append(playbook)
                    self.loaded_playbooks[playbook.playbook_id] = playbook
                    logger.info(f"✅ Loaded playbook: {playbook.name}")
            except Exception as e:
                logger.error(f"❌ Failed to load {yaml_file.name}: {e}")

        return playbooks

    def load_playbook(self, file_path: Path) -> Optional[Playbook]:
        """
        Load single playbook from YAML file

        Args:
            file_path: Path to YAML file

        Returns:
            Playbook object or None if failed
        """
        try:
            with open(file_path, 'r') as f:
                data = yaml.safe_load(f)

            # Validate required fields
            required = ['playbook_id', 'name', 'steps', 'trigger_type', 'trigger_conditions']
            for field in required:
                if field not in data:
                    raise ValueError(f"Missing required field: {field}")

            # Parse steps
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

            # Create playbook
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
                version=data.get('version', '1.0'),
                tags=data.get('tags', [])
            )

            return playbook

        except Exception as e:
            logger.error(f"Error loading playbook from {file_path}: {e}")
            return None

    def get_playbook(self, playbook_id: str) -> Optional[Playbook]:
        """Get playbook by ID"""
        return self.loaded_playbooks.get(playbook_id)

    def reload_playbooks(self) -> int:
        """
        Reload all playbooks from disk

        Returns:
            Number of playbooks loaded
        """
        self.loaded_playbooks.clear()
        playbooks = self.load_all_playbooks()
        return len(playbooks)

    def list_playbooks(self) -> List[Dict[str, Any]]:
        """
        List all loaded playbooks (summary)

        Returns:
            List of playbook summaries
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
