"""
🔬 YARA Scanner - Malware detection com regras YARA

Integra com backend malware_analysis_service para scanning distribuído.
Suporta:
- Scan local com regras YARA
- Scan remoto via backend service
- Rule compilation e caching
- Match metadata extraction
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from pathlib import Path
import hashlib
import logging

logger = logging.getLogger(__name__)


@dataclass
class YARAMatch:
    """Match de regra YARA"""
    rule_name: str
    namespace: str
    strings: List[Dict[str, Any]] = field(default_factory=list)  # Matched strings
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class YARAScanner:
    """
    YARA Scanner com integração backend

    Features:
    - Local scanning com python-yara
    - Remote scanning via malware_analysis_service
    - Rule compilation e caching
    - Bulk scanning
    """

    def __init__(
        self,
        backend_url: Optional[str] = None,
        use_backend: bool = True,
    ):
        """
        Args:
            backend_url: URL do malware_analysis_service
            use_backend: Se True, usa backend para scanning (recomendado)
        """
        self.backend_url = backend_url or "http://localhost:8001"
        self.use_backend = use_backend

        # Regras compiladas (local mode)
        self.compiled_rules: Optional[Any] = None
        self.rules_source: Dict[str, str] = {}

        # Try import yara for local scanning
        self.yara_available = False
        try:
            import yara
            self.yara = yara
            self.yara_available = True
        except ImportError:
            logger.warning(
                "python-yara not installed. Install with: pip install yara-python\n"
                "Falling back to backend scanning only."
            )

    def load_rules(self, rules_path: Path) -> int:
        """
        Carrega regras YARA de arquivo ou diretório

        Args:
            rules_path: Path para .yar/.yara ou diretório

        Returns:
            Número de regras carregadas
        """
        if not self.yara_available:
            logger.warning("YARA not available locally, rules loaded for backend use only")
            return self._load_rules_for_backend(rules_path)

        rules_dict = {}

        if rules_path.is_file():
            rules_dict[rules_path.stem] = str(rules_path)
        else:
            # Diretório
            for rule_file in rules_path.glob("**/*.yar*"):
                namespace = rule_file.stem
                rules_dict[namespace] = str(rule_file)

        try:
            self.compiled_rules = self.yara.compile(filepaths=rules_dict)
            self.rules_source = rules_dict
            logger.info(f"Compiled {len(rules_dict)} YARA rules")
            return len(rules_dict)

        except Exception as e:
            logger.error(f"Failed to compile YARA rules: {e}")
            return 0

    def _load_rules_for_backend(self, rules_path: Path) -> int:
        """
        Carrega regras apenas para uso com backend

        Args:
            rules_path: Path das regras

        Returns:
            Número de regras carregadas
        """
        count = 0

        if rules_path.is_file():
            self.rules_source[rules_path.stem] = rules_path.read_text()
            count = 1
        else:
            for rule_file in rules_path.glob("**/*.yar*"):
                self.rules_source[rule_file.stem] = rule_file.read_text()
                count += 1

        return count

    def scan_file(self, file_path: Path) -> List[YARAMatch]:
        """
        Escaneia arquivo com regras YARA

        Args:
            file_path: Path do arquivo

        Returns:
            Lista de YARAMatch
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # Prioriza backend se disponível
        if self.use_backend:
            try:
                return self._scan_file_backend(file_path)
            except Exception as e:
                logger.warning(f"Backend scan failed, falling back to local: {e}")

        # Fallback para scan local
        if self.yara_available and self.compiled_rules:
            return self._scan_file_local(file_path)

        logger.error("No YARA scanning available (backend failed and local not available)")
        return []

    def _scan_file_local(self, file_path: Path) -> List[YARAMatch]:
        """
        Scan local com python-yara

        Args:
            file_path: Path do arquivo

        Returns:
            Lista de YARAMatch
        """
        if not self.compiled_rules:
            logger.warning("No YARA rules loaded")
            return []

        try:
            matches = self.compiled_rules.match(str(file_path))

            yara_matches = []
            for match in matches:
                # Extract matched strings
                strings = []
                for string_match in match.strings:
                    strings.append({
                        "identifier": string_match.identifier,
                        "instances": [
                            {
                                "offset": instance[0],
                                "matched_data": instance[2].decode("utf-8", errors="replace")
                            }
                            for instance in string_match.instances
                        ]
                    })

                yara_match = YARAMatch(
                    rule_name=match.rule,
                    namespace=match.namespace,
                    strings=strings,
                    tags=list(match.tags),
                    metadata=dict(match.meta),
                )

                yara_matches.append(yara_match)

            return yara_matches

        except Exception as e:
            logger.error(f"YARA scan failed: {e}")
            return []

    def _scan_file_backend(self, file_path: Path) -> List[YARAMatch]:
        """
        Scan via malware_analysis_service backend

        Args:
            file_path: Path do arquivo

        Returns:
            Lista de YARAMatch
        """
        import httpx

        # Calcula hash do arquivo
        file_hash = self._calculate_hash(file_path)

        # Upload e scan via backend
        with httpx.Client(timeout=60.0) as client:
            # 1. Upload file
            with open(file_path, "rb") as f:
                upload_response = client.post(
                    f"{self.backend_url}/api/malware/upload",
                    files={"file": (file_path.name, f, "application/octet-stream")},
                )
                upload_response.raise_for_status()

            # 2. Request YARA scan
            scan_response = client.post(
                f"{self.backend_url}/api/malware/yara-scan",
                json={
                    "file_hash": file_hash,
                    "file_path": str(file_path),
                }
            )
            scan_response.raise_for_status()

            result = scan_response.json()

            # Parse backend response
            matches = []
            for match_data in result.get("matches", []):
                matches.append(YARAMatch(
                    rule_name=match_data.get("rule_name"),
                    namespace=match_data.get("namespace", "default"),
                    strings=match_data.get("strings", []),
                    tags=match_data.get("tags", []),
                    metadata=match_data.get("metadata", {}),
                ))

            return matches

    def scan_memory(self, pid: int, endpoint_id: str = "local") -> List[YARAMatch]:
        """
        Escaneia memória de processo (via backend endpoint agent)

        Args:
            pid: Process ID
            endpoint_id: ID do endpoint

        Returns:
            Lista de YARAMatch
        """
        import httpx

        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(
                    f"{self.backend_url}/api/malware/memory-scan",
                    json={
                        "endpoint_id": endpoint_id,
                        "pid": pid,
                    }
                )
                response.raise_for_status()

                result = response.json()

                matches = []
                for match_data in result.get("matches", []):
                    matches.append(YARAMatch(
                        rule_name=match_data.get("rule_name"),
                        namespace=match_data.get("namespace", "default"),
                        strings=match_data.get("strings", []),
                        tags=match_data.get("tags", []),
                        metadata=match_data.get("metadata", {}),
                    ))

                return matches

        except Exception as e:
            logger.error(f"Memory scan failed: {e}")
            return []

    def bulk_scan(
        self,
        file_paths: List[Path],
        parallel: bool = True,
    ) -> Dict[str, List[YARAMatch]]:
        """
        Scan múltiplos arquivos (via backend para paralelização)

        Args:
            file_paths: Lista de paths
            parallel: Se True, usa backend para scan paralelo

        Returns:
            Dict {file_path: [matches]}
        """
        if parallel and self.use_backend:
            return self._bulk_scan_backend(file_paths)

        # Fallback: scan sequencial local
        results = {}
        for file_path in file_paths:
            try:
                matches = self.scan_file(file_path)
                results[str(file_path)] = matches
            except Exception as e:
                logger.error(f"Failed to scan {file_path}: {e}")
                results[str(file_path)] = []

        return results

    def _bulk_scan_backend(self, file_paths: List[Path]) -> Dict[str, List[YARAMatch]]:
        """
        Bulk scan via backend (paralelo)

        Args:
            file_paths: Lista de paths

        Returns:
            Dict {file_path: [matches]}
        """
        import httpx

        try:
            with httpx.Client(timeout=120.0) as client:
                # Calcula hashes
                files_data = []
                for file_path in file_paths:
                    files_data.append({
                        "path": str(file_path),
                        "hash": self._calculate_hash(file_path),
                    })

                # Bulk scan request
                response = client.post(
                    f"{self.backend_url}/api/malware/bulk-scan",
                    json={"files": files_data}
                )
                response.raise_for_status()

                result = response.json()

                # Parse results
                parsed_results = {}
                for file_path, match_data in result.get("results", {}).items():
                    matches = []
                    for match in match_data.get("matches", []):
                        matches.append(YARAMatch(
                            rule_name=match.get("rule_name"),
                            namespace=match.get("namespace", "default"),
                            strings=match.get("strings", []),
                            tags=match.get("tags", []),
                            metadata=match.get("metadata", {}),
                        ))
                    parsed_results[file_path] = matches

                return parsed_results

        except Exception as e:
            logger.error(f"Bulk scan failed: {e}")
            return {str(fp): [] for fp in file_paths}

    def _calculate_hash(self, file_path: Path, algorithm: str = "sha256") -> str:
        """
        Calcula hash de arquivo

        Args:
            file_path: Path do arquivo
            algorithm: Algoritmo (md5, sha1, sha256)

        Returns:
            Hash hex string
        """
        hasher = hashlib.new(algorithm)

        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                hasher.update(chunk)

        return hasher.hexdigest()

    def get_rule_info(self, rule_name: str) -> Optional[Dict[str, Any]]:
        """
        Retorna informações sobre regra YARA

        Args:
            rule_name: Nome da regra

        Returns:
            Dict com info da regra ou None
        """
        # TODO: Parse rule file to extract metadata
        # For now, retorna basic info

        for namespace, rule_path in self.rules_source.items():
            if namespace == rule_name or rule_name in rule_path:
                return {
                    "name": rule_name,
                    "namespace": namespace,
                    "path": rule_path if isinstance(rule_path, str) and "/" in rule_path else None,
                }

        return None
