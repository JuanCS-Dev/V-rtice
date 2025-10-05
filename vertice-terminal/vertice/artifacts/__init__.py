"""
📚 Artifact Library - Pre-built VeQL queries

Artifacts são queries VeQL pre-configuradas para threat hunting comum.
"""

import yaml
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class Artifact:
    """Representa um artifact VeQL"""
    name: str
    description: str
    query: str
    author: str
    version: str
    tags: List[str]
    severity: str
    output_fields: List[str]
    remediation: List[str]

    @classmethod
    def from_yaml(cls, yaml_path: Path) -> "Artifact":
        """Carrega artifact de arquivo YAML"""
        with open(yaml_path, "r") as f:
            data = yaml.safe_load(f)

        return cls(
            name=data["name"],
            description=data["description"],
            query=data["query"].strip(),
            author=data.get("author", "Unknown"),
            version=data.get("version", "1.0.0"),
            tags=data.get("tags", []),
            severity=data.get("severity", "medium"),
            output_fields=data.get("output_fields", []),
            remediation=data.get("remediation", []),
        )


class ArtifactLibrary:
    """
    Biblioteca de artifacts VeQL
    """

    def __init__(self, artifacts_dir: Optional[Path] = None):
        """
        Args:
            artifacts_dir: Diretório com arquivos .yaml de artifacts
        """
        if artifacts_dir is None:
            # Default: diretório artifacts no módulo
            artifacts_dir = Path(__file__).parent

        self.artifacts_dir = artifacts_dir
        self._artifacts: Dict[str, Artifact] = {}
        self._load_all()

    def _load_all(self) -> None:
        """Carrega todos os artifacts do diretório"""
        for yaml_file in self.artifacts_dir.glob("*.yaml"):
            try:
                artifact = Artifact.from_yaml(yaml_file)
                # Nome do arquivo (sem extensão) é o ID
                artifact_id = yaml_file.stem
                self._artifacts[artifact_id] = artifact
            except Exception as e:
                print(f"Warning: Failed to load artifact {yaml_file}: {e}")

    def get(self, artifact_id: str) -> Optional[Artifact]:
        """
        Busca artifact por ID

        Args:
            artifact_id: ID do artifact (ex: suspicious_network)

        Returns:
            Artifact ou None
        """
        return self._artifacts.get(artifact_id)

    def list(self, tag: Optional[str] = None) -> List[Artifact]:
        """
        Lista artifacts disponíveis

        Args:
            tag: Filtrar por tag

        Returns:
            Lista de artifacts
        """
        artifacts = list(self._artifacts.values())

        if tag:
            artifacts = [a for a in artifacts if tag in a.tags]

        return artifacts

    def search(self, query: str) -> List[Artifact]:
        """
        Busca artifacts por nome ou descrição

        Args:
            query: Termo de busca

        Returns:
            Lista de artifacts que correspondem
        """
        query_lower = query.lower()
        results = []

        for artifact in self._artifacts.values():
            if (query_lower in artifact.name.lower() or
                query_lower in artifact.description.lower()):
                results.append(artifact)

        return results


# Global library instance
_library = None


def get_library() -> ArtifactLibrary:
    """Retorna instância global da biblioteca"""
    global _library
    if _library is None:
        _library = ArtifactLibrary()
    return _library


__all__ = ["Artifact", "ArtifactLibrary", "get_library"]
