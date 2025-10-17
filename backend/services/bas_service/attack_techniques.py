"""Maximus BAS Service - Attack Techniques.

This module defines and manages a repository of known cyberattack techniques
that can be simulated by the Breach and Attack Simulation (BAS) service.
These techniques are often mapped to frameworks like MITRE ATT&CK, providing
a standardized way to categorize and describe adversary behaviors.

Each technique includes metadata such as its ID, name, description, and potential
parameters, allowing the BAS service to orchestrate realistic and relevant
attack simulations. This module is crucial for building a comprehensive and
up-to-date library of offensive capabilities for Maximus AI.
"""

from typing import Any, Dict, List, Optional

from services.bas_service.models import AttackTechnique


class AttackTechniques:
    """Manages a repository of known cyberattack techniques for BAS simulations.

    Techniques are often mapped to frameworks like MITRE ATT&CK, providing a
    standardized way to categorize and describe adversary behaviors.
    """

    def __init__(self):
        """Initializes the AttackTechniques repository with predefined techniques."""
        self.techniques: Dict[str, AttackTechnique] = {
            "T1059": AttackTechnique(
                id="T1059",
                name="Command and Scripting Interpreter",
                description="Adversaries may abuse command and scripting interpreters to execute commands, scripts, or binaries.",
                parameters=["command", "target_process"],
            ),
            "T1003": AttackTechnique(
                id="T1003",
                name="OS Credential Dumping",
                description="Adversaries may attempt to dump credentials to obtain account access and privileges.",
                parameters=["target_os", "method"],
            ),
            "T1078": AttackTechnique(
                id="T1078",
                name="Valid Accounts",
                description="Adversaries may steal credentials or use legitimate credentials to operate within an environment.",
                parameters=["username", "password", "service"],
            ),
            "T1048": AttackTechnique(
                id="T1048",
                name="Exfiltration Over Alternative Protocol",
                description="Adversaries may exfiltrate data using a different protocol than the primary command and control protocol.",
                parameters=["data_to_exfiltrate", "protocol"],
            ),
        }
        print("[AttackTechniques] Loaded predefined attack techniques.")

    def get_technique(self, technique_id: str) -> Optional[AttackTechnique]:
        """Retrieves an attack technique by its ID.

        Args:
            technique_id (str): The ID of the technique (e.g., 'T1059').

        Returns:
            Optional[AttackTechnique]: The AttackTechnique object, or None if not found.
        """
        return self.techniques.get(technique_id)

    def list_all_techniques(self) -> List[AttackTechnique]:
        """Lists all available attack techniques.

        Returns:
            List[AttackTechnique]: A list of all AttackTechnique objects.
        """
        return list(self.techniques.values())

    def add_technique(self, technique: AttackTechnique):
        """Adds a new attack technique to the repository.

        Args:
            technique (AttackTechnique): The AttackTechnique object to add.

        Raises:
            ValueError: If a technique with the same ID already exists.
        """
        if technique.id in self.techniques:
            raise ValueError(f"Technique with ID {technique.id} already exists.")
        self.techniques[technique.id] = technique
        print(f"[AttackTechniques] Added new technique: {technique.id}")

    def update_technique(self, technique_id: str, updated_data: Dict[str, Any]):
        """Updates an existing attack technique.

        Args:
            technique_id (str): The ID of the technique to update.
            updated_data (Dict[str, Any]): A dictionary containing the updated fields.

        Raises:
            ValueError: If the technique with the given ID does not exist.
        """
        if technique_id not in self.techniques:
            raise ValueError(f"Technique with ID {technique_id} not found.")

        current_technique = self.techniques[technique_id]
        for key, value in updated_data.items():
            setattr(current_technique, key, value)
        print(f"[AttackTechniques] Updated technique: {technique_id}")
