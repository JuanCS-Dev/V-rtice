"""
Docker Image Scanner.

Discovers dependencies and packages within Docker images using:
- docker image inspect (image metadata)
- docker run + package manager queries (pip freeze, npm list, etc.)
- Dockerfile parsing (base images, installed packages)
- Trivy scanning (comprehensive vulnerability data)
"""

import json
import logging
import re
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class DockerPackage(BaseModel):
    """Package discovered in Docker image."""

    name: str
    version: str
    ecosystem: str  # "pypi", "npm", "apt", "apk", etc.
    layer_id: Optional[str] = None
    source: str = "docker"  # "dockerfile", "image_inspect", "trivy", "runtime"


class DockerImageInfo(BaseModel):
    """Docker image metadata."""

    image_id: str
    repo_tags: List[str] = Field(default_factory=list)
    base_image: Optional[str] = None
    created: str
    size: int
    os: str
    architecture: str


class DockerScanner:
    """
    Scanner for Docker images.

    Strategies:
    1. docker image inspect: Image metadata
    2. Dockerfile parsing: Base images and RUN commands
    3. Trivy scan: Comprehensive vulnerability scanning
    4. Runtime package extraction: Run container and query package managers
    """

    def __init__(self, image_name: str):
        """
        Initialize Docker scanner.

        Args:
            image_name: Docker image name (e.g., "myapp:latest", "python:3.11-slim")
        """
        self.image_name = image_name
        logger.info(f"DockerScanner initialized for: {self.image_name}")

    def scan(self) -> Tuple[DockerImageInfo, List[DockerPackage]]:
        """
        Scan Docker image for metadata and packages.

        Returns:
            Tuple of (DockerImageInfo, List[DockerPackage])

        Raises:
            RuntimeError: If Docker is not available or image doesn't exist
        """
        # Get image metadata
        image_info = self._inspect_image()

        packages: Dict[str, DockerPackage] = {}

        # Strategy 1: Trivy scan (most comprehensive)
        try:
            trivy_packages = self._scan_with_trivy()
            for pkg in trivy_packages:
                key = f"{pkg.ecosystem}:{pkg.name}@{pkg.version}"
                if key not in packages:
                    packages[key] = pkg

            logger.info(f"Trivy: Found {len(trivy_packages)} packages")
        except Exception as e:
            logger.warning(f"Trivy scan failed: {e}")

        # Strategy 2: Runtime package extraction
        try:
            runtime_packages = self._extract_runtime_packages()
            for pkg in runtime_packages:
                key = f"{pkg.ecosystem}:{pkg.name}@{pkg.version}"
                if key not in packages:
                    packages[key] = pkg

            logger.info(f"Runtime: Found {len(runtime_packages)} packages")
        except Exception as e:
            logger.warning(f"Runtime package extraction failed: {e}")

        # Strategy 3: Dockerfile parsing
        try:
            dockerfile_packages = self._parse_dockerfile()
            for pkg in dockerfile_packages:
                key = f"{pkg.ecosystem}:{pkg.name}@{pkg.version}"
                if key not in packages:
                    packages[key] = pkg

            logger.info(f"Dockerfile: Found {len(dockerfile_packages)} packages")
        except Exception as e:
            logger.debug(f"Dockerfile parsing failed: {e}")

        result = list(packages.values())
        logger.info(f"✅ Docker scan complete: {len(result)} unique packages discovered")
        return image_info, result

    def _inspect_image(self) -> DockerImageInfo:
        """
        Inspect Docker image metadata.

        Returns:
            DockerImageInfo instance

        Raises:
            RuntimeError: If docker inspect fails
        """
        try:
            result = subprocess.run(
                ["docker", "image", "inspect", self.image_name],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode != 0:
                raise RuntimeError(f"docker inspect failed: {result.stderr}")

            data = json.loads(result.stdout)

            if not data:
                raise RuntimeError(f"Image {self.image_name} not found")

            image_data = data[0]

            # Extract base image from Config.Image or history
            base_image = None
            if "Config" in image_data and "Image" in image_data["Config"]:
                base_image = image_data["Config"]["Image"]

            return DockerImageInfo(
                image_id=image_data["Id"],
                repo_tags=image_data.get("RepoTags", []),
                base_image=base_image,
                created=image_data["Created"],
                size=image_data["Size"],
                os=image_data.get("Os", "unknown"),
                architecture=image_data.get("Architecture", "unknown"),
            )

        except FileNotFoundError:
            raise RuntimeError("docker not found. Install Docker from https://docker.com/")
        except subprocess.TimeoutExpired:
            raise RuntimeError("docker inspect timed out after 30s")
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Failed to parse docker inspect JSON: {e}")

    def _scan_with_trivy(self) -> List[DockerPackage]:
        """
        Scan image using Trivy vulnerability scanner.

        Returns:
            List of DockerPackage instances

        Raises:
            RuntimeError: If Trivy is not available or fails
        """
        try:
            result = subprocess.run(
                [
                    "trivy",
                    "image",
                    "--format", "json",
                    "--quiet",
                    self.image_name,
                ],
                capture_output=True,
                text=True,
                timeout=300,  # Trivy can take time on first run
            )

            if result.returncode != 0:
                raise RuntimeError(f"trivy scan failed: {result.stderr}")

            data = json.loads(result.stdout)

            packages = []

            for result_item in data.get("Results", []):
                target = result_item.get("Target", "")
                package_type = result_item.get("Type", "")

                # Map Trivy package types to ecosystems
                ecosystem_map = {
                    "pip": "pypi",
                    "npm": "npm",
                    "yarn": "npm",
                    "bundler": "rubygems",
                    "composer": "composer",
                    "cargo": "cargo",
                    "gomod": "go",
                    "maven": "maven",
                    "gradle": "maven",
                    "apk": "apk",
                    "dpkg": "apt",
                    "rpm": "rpm",
                }

                ecosystem = ecosystem_map.get(package_type.lower(), package_type.lower())

                for pkg in result_item.get("Packages", []):
                    name = pkg.get("Name", "")
                    version = pkg.get("Version", "unknown")
                    layer_id = pkg.get("Layer", {}).get("Digest", None)

                    if name:
                        packages.append(
                            DockerPackage(
                                name=name,
                                version=version,
                                ecosystem=ecosystem,
                                layer_id=layer_id,
                                source="trivy",
                            )
                        )

            return packages

        except FileNotFoundError:
            raise RuntimeError(
                "trivy not found. Install with: https://aquasecurity.github.io/trivy/"
            )
        except subprocess.TimeoutExpired:
            raise RuntimeError("trivy scan timed out after 300s")
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Failed to parse trivy JSON: {e}")

    def _extract_runtime_packages(self) -> List[DockerPackage]:
        """
        Extract packages by running container and querying package managers.

        Returns:
            List of DockerPackage instances

        Raises:
            RuntimeError: If container execution fails
        """
        packages = []

        # Try Python packages
        try:
            python_packages = self._run_command_in_container("pip freeze")
            for line in python_packages.splitlines():
                if "==" in line:
                    name, version = line.split("==", 1)
                    packages.append(
                        DockerPackage(
                            name=name.strip().lower(),
                            version=version.strip(),
                            ecosystem="pypi",
                            source="runtime",
                        )
                    )
        except Exception as e:
            logger.debug(f"Failed to extract Python packages: {e}")

        # Try npm packages
        try:
            npm_output = self._run_command_in_container("npm list --json --depth=0")
            npm_data = json.loads(npm_output)
            for name, info in npm_data.get("dependencies", {}).items():
                version = info.get("version", "unknown")
                packages.append(
                    DockerPackage(
                        name=name,
                        version=version,
                        ecosystem="npm",
                        source="runtime",
                    )
                )
        except Exception as e:
            logger.debug(f"Failed to extract npm packages: {e}")

        # Try apt packages (Debian/Ubuntu)
        try:
            apt_output = self._run_command_in_container("dpkg-query -W -f='${Package}=${Version}\\n'")
            for line in apt_output.splitlines():
                if "=" in line:
                    name, version = line.split("=", 1)
                    packages.append(
                        DockerPackage(
                            name=name.strip(),
                            version=version.strip(),
                            ecosystem="apt",
                            source="runtime",
                        )
                    )
        except Exception as e:
            logger.debug(f"Failed to extract apt packages: {e}")

        # Try apk packages (Alpine)
        try:
            apk_output = self._run_command_in_container("apk info -v")
            for line in apk_output.splitlines():
                # Alpine format: package-name-version
                match = re.match(r"^(.+)-(\d+.*)$", line)
                if match:
                    name, version = match.groups()
                    packages.append(
                        DockerPackage(
                            name=name.strip(),
                            version=version.strip(),
                            ecosystem="apk",
                            source="runtime",
                        )
                    )
        except Exception as e:
            logger.debug(f"Failed to extract apk packages: {e}")

        return packages

    def _run_command_in_container(self, command: str) -> str:
        """
        Run command inside Docker container.

        Args:
            command: Shell command to execute

        Returns:
            Command output

        Raises:
            RuntimeError: If command execution fails
        """
        result = subprocess.run(
            [
                "docker", "run", "--rm",
                "--entrypoint", "sh",
                self.image_name,
                "-c", command,
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )

        if result.returncode != 0:
            raise RuntimeError(f"Command failed: {result.stderr}")

        return result.stdout

    def _parse_dockerfile(self) -> List[DockerPackage]:
        """
        Parse Dockerfile for installed packages.

        Returns:
            List of DockerPackage instances

        Raises:
            FileNotFoundError: If Dockerfile doesn't exist
        """
        # Try to find Dockerfile in common locations
        possible_dockerfiles = [
            Path.cwd() / "Dockerfile",
            Path.cwd() / "docker" / "Dockerfile",
            Path.cwd() / "build" / "Dockerfile",
        ]

        dockerfile_path = None
        for path in possible_dockerfiles:
            if path.exists():
                dockerfile_path = path
                break

        if not dockerfile_path:
            raise FileNotFoundError("Dockerfile not found")

        with open(dockerfile_path, "r", encoding="utf-8") as f:
            content = f.read()

        packages = []

        # Parse RUN commands for package installations
        run_commands = re.findall(r"^RUN\s+(.+)$", content, re.MULTILINE | re.IGNORECASE)

        for cmd in run_commands:
            # pip install
            pip_matches = re.findall(r"pip\s+install\s+([^\s&|;]+)", cmd)
            for match in pip_matches:
                # Remove version specifiers
                name = re.sub(r"[<>=!~].*", "", match).strip()
                if name:
                    packages.append(
                        DockerPackage(
                            name=name.lower(),
                            version="latest",
                            ecosystem="pypi",
                            source="dockerfile",
                        )
                    )

            # npm install
            npm_matches = re.findall(r"npm\s+install\s+([^\s&|;]+)", cmd)
            for match in npm_matches:
                # Remove version specifiers
                name = re.sub(r"@[\d.]+", "", match).strip()
                if name and name not in ["-g", "--global", "--save", "--save-dev"]:
                    packages.append(
                        DockerPackage(
                            name=name,
                            version="latest",
                            ecosystem="npm",
                            source="dockerfile",
                        )
                    )

            # apt-get install (Debian/Ubuntu)
            apt_matches = re.findall(r"apt-get\s+install.*?\s+([a-z0-9][a-z0-9\-]+)", cmd)
            for match in apt_matches:
                if match not in ["-y", "--yes", "--no-install-recommends"]:
                    packages.append(
                        DockerPackage(
                            name=match,
                            version="latest",
                            ecosystem="apt",
                            source="dockerfile",
                        )
                    )

            # apk add (Alpine)
            apk_matches = re.findall(r"apk\s+add.*?\s+([a-z0-9][a-z0-9\-]+)", cmd)
            for match in apk_matches:
                if match not in ["--no-cache", "--virtual"]:
                    packages.append(
                        DockerPackage(
                            name=match,
                            version="latest",
                            ecosystem="apk",
                            source="dockerfile",
                        )
                    )

        return packages

    def get_image_layers(self) -> List[dict]:
        """
        Get Docker image layers.

        Returns:
            List of layer dictionaries with ID and command

        Raises:
            RuntimeError: If docker history fails
        """
        try:
            result = subprocess.run(
                ["docker", "history", "--no-trunc", "--format", "{{json .}}", self.image_name],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode != 0:
                raise RuntimeError(f"docker history failed: {result.stderr}")

            layers = []
            for line in result.stdout.splitlines():
                if line.strip():
                    layer = json.loads(line)
                    layers.append(layer)

            return layers

        except subprocess.TimeoutExpired:
            raise RuntimeError("docker history timed out after 30s")
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Failed to parse docker history JSON: {e}")
