"""Automated wound healing (SOAR playbook execution)."""

from __future__ import annotations

import asyncio
import logging
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx
import yaml

from ..config import TegumentarSettings, get_settings

logger = logging.getLogger(__name__)


class WoundHealingError(RuntimeError):
    pass


class WoundHealingOrchestrator:
    """Executes biomimetic wound healing playbooks."""

    def __init__(self, settings: Optional[TegumentarSettings] = None):
        self._settings = settings or get_settings()
        self._client = httpx.AsyncClient(timeout=30.0)

    async def shutdown(self) -> None:
        await self._client.aclose()

    async def execute(self, playbook_name: str, context: Dict[str, Any]) -> None:
        path = Path(self._settings.soar_playbooks_path) / f"{playbook_name}.yaml"
        if not path.exists():
            raise FileNotFoundError(f"Playbook {playbook_name} not found at {path}")

        with path.open("r", encoding="utf-8") as handle:
            doc = yaml.safe_load(handle)

        for phase in doc.get("phases", []):
            name = phase.get("name", "unknown")
            logger.info("Starting wound healing phase %s", name)
            for step in phase.get("steps", []):
                await self._execute_step(step, context)
            logger.info("Completed phase %s", name)

    async def _execute_step(self, step: Dict[str, Any], context: Dict[str, Any]) -> None:
        step_type = step.get("type")
        if step_type == "command":
            await self._run_command(step["command"], step.get("timeout", 60))
        elif step_type == "http":
            await self._run_http(step, context)
        elif step_type == "sleep":
            await asyncio.sleep(step.get("seconds", 1))
        else:
            raise WoundHealingError(f"Unsupported step type: {step_type}")

    async def _run_command(self, command: List[str], timeout: int) -> None:
        logger.debug("Executing wound healing command: %s", " ".join(command))
        try:
            proc = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        except asyncio.TimeoutError as exc:
            raise WoundHealingError(f"Command {' '.join(command)} timed out") from exc

        if proc.returncode != 0:
            raise WoundHealingError(
                f"Command {' '.join(command)} failed (rc={proc.returncode}): {stderr.decode().strip()}"
            )
        if stdout:
            logger.debug(stdout.decode().strip())

    async def _run_http(self, step: Dict[str, Any], context: Dict[str, Any]) -> None:
        method = step.get("method", "post").lower()
        url = step["url"].format(**context)
        data = step.get("body", {})
        headers = step.get("headers")
        logger.debug("Executing wound healing HTTP %s %s", method.upper(), url)
        response = await self._client.request(method, url, json=data, headers=headers)
        response.raise_for_status()


__all__ = ["WoundHealingOrchestrator", "WoundHealingError"]
