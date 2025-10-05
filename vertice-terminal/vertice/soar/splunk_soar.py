"""
👻 Splunk SOAR (Phantom) Connector

Integração com Splunk SOAR usando REST API.
Docs: https://docs.splunk.com/Documentation/SOARonprem/latest/PlatformAPI
"""

import httpx
from typing import List, Dict, Any, Optional
from .base import SOARConnector, Incident, Artifact, IncidentSeverity, IncidentStatus
from datetime import datetime


class SplunkSOARConnector(SOARConnector):
    """
    Connector para Splunk SOAR (Phantom)
    """

    def __init__(self, base_url: str, api_key: str):
        """
        Args:
            base_url: URL do Splunk SOAR (ex: https://soar.company.com)
            api_key: API token do Splunk SOAR
        """
        super().__init__(base_url, api_key)
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={
                "ph-auth-token": self.api_key,
                "Content-Type": "application/json",
            },
            timeout=30.0,
        )

    async def health_check(self) -> bool:
        """Verifica conectividade"""
        try:
            response = await self.client.get("/rest/system_info")
            return response.status_code == 200
        except Exception:
            return False

    async def create_incident(self, incident: Incident) -> str:
        """
        Cria container (incidente) no Splunk SOAR

        Splunk SOAR chama incidentes de "containers"
        """
        # Mapeia severidade
        severity_map = {
            IncidentSeverity.LOW: "low",
            IncidentSeverity.MEDIUM: "medium",
            IncidentSeverity.HIGH: "high",
            IncidentSeverity.CRITICAL: "high",  # SOAR só tem low/medium/high
        }

        # Mapeia status
        status_map = {
            IncidentStatus.NEW: "new",
            IncidentStatus.IN_PROGRESS: "open",
            IncidentStatus.RESOLVED: "closed",
            IncidentStatus.CLOSED: "closed",
        }

        payload = {
            "name": incident.title,
            "description": incident.description,
            "severity": severity_map[incident.severity],
            "status": status_map[incident.status],
            "tags": incident.tags,
            "label": "incident",  # Splunk SOAR requer label
        }

        try:
            response = await self.client.post("/rest/container", json=payload)
            response.raise_for_status()

            result = response.json()
            container_id = str(result.get("id"))

            # Adiciona artifacts se houver
            for artifact in incident.artifacts:
                await self.add_artifact(container_id, artifact)

            return container_id

        except httpx.HTTPStatusError as e:
            raise ValueError(f"Failed to create incident: {e.response.text}")

    async def get_incident(self, incident_id: str) -> Optional[Incident]:
        """Busca container por ID"""
        try:
            response = await self.client.get(f"/rest/container/{incident_id}")

            if response.status_code == 404:
                return None

            response.raise_for_status()
            data = response.json()

            # Mapeia de volta para nosso modelo
            severity_map_reverse = {
                "low": IncidentSeverity.LOW,
                "medium": IncidentSeverity.MEDIUM,
                "high": IncidentSeverity.HIGH,
            }

            status_map_reverse = {
                "new": IncidentStatus.NEW,
                "open": IncidentStatus.IN_PROGRESS,
                "closed": IncidentStatus.CLOSED,
            }

            incident = Incident(
                id=str(data.get("id")),
                title=data.get("name", ""),
                description=data.get("description", ""),
                severity=severity_map_reverse.get(data.get("severity"), IncidentSeverity.MEDIUM),
                status=status_map_reverse.get(data.get("status"), IncidentStatus.NEW),
                tags=data.get("tags", []),
                created_at=datetime.fromisoformat(data.get("create_time")) if data.get("create_time") else None,
            )

            return incident

        except httpx.HTTPStatusError:
            return None

    async def update_incident(
        self,
        incident_id: str,
        updates: Dict[str, Any]
    ) -> bool:
        """Atualiza container"""
        try:
            response = await self.client.post(
                f"/rest/container/{incident_id}",
                json=updates
            )
            response.raise_for_status()
            return True
        except httpx.HTTPStatusError:
            return False

    async def add_artifact(
        self,
        incident_id: str,
        artifact: Artifact
    ) -> bool:
        """Adiciona artifact ao container"""
        payload = {
            "container_id": int(incident_id),
            "name": f"{artifact.type}: {artifact.value}",
            "cef": {
                artifact.type: artifact.value,
            },
            "label": "event",
            "type": artifact.type,
            "source_data_identifier": artifact.value,
        }

        if artifact.description:
            payload["description"] = artifact.description

        try:
            response = await self.client.post("/rest/artifact", json=payload)
            response.raise_for_status()
            return True
        except httpx.HTTPStatusError:
            return False

    async def execute_playbook(
        self,
        playbook_id: str,
        parameters: Dict[str, Any]
    ) -> str:
        """Executa playbook"""
        # Splunk SOAR usa run_id para playbooks
        payload = {
            "playbook_id": playbook_id,
            "scope": "all",
            "run": True,
            **parameters,
        }

        try:
            response = await self.client.post(
                f"/rest/playbook_run/{playbook_id}",
                json=payload
            )
            response.raise_for_status()

            result = response.json()
            run_id = str(result.get("playbook_run_id", ""))

            return run_id

        except httpx.HTTPStatusError as e:
            raise ValueError(f"Failed to execute playbook: {e.response.text}")

    async def list_incidents(
        self,
        status: Optional[IncidentStatus] = None,
        severity: Optional[IncidentSeverity] = None,
        limit: int = 100
    ) -> List[Incident]:
        """Lista containers"""
        params = {
            "page_size": limit,
            "sort": "create_time",
            "order": "desc",
        }

        # Filtros
        filter_parts = []

        if status:
            status_map = {
                IncidentStatus.NEW: "new",
                IncidentStatus.IN_PROGRESS: "open",
                IncidentStatus.CLOSED: "closed",
            }
            filter_parts.append(f'"status":"{status_map[status]}"')

        if severity:
            severity_map = {
                IncidentSeverity.LOW: "low",
                IncidentSeverity.MEDIUM: "medium",
                IncidentSeverity.HIGH: "high",
                IncidentSeverity.CRITICAL: "high",
            }
            filter_parts.append(f'"severity":"{severity_map[severity]}"')

        if filter_parts:
            params["_filter_"] = "{" + ",".join(filter_parts) + "}"

        try:
            response = await self.client.get("/rest/container", params=params)
            response.raise_for_status()

            data = response.json()
            containers = data.get("data", [])

            incidents = []
            for container in containers:
                # Mapeia para nosso modelo
                severity_map = {
                    "low": IncidentSeverity.LOW,
                    "medium": IncidentSeverity.MEDIUM,
                    "high": IncidentSeverity.HIGH,
                }

                status_map = {
                    "new": IncidentStatus.NEW,
                    "open": IncidentStatus.IN_PROGRESS,
                    "closed": IncidentStatus.CLOSED,
                }

                incident = Incident(
                    id=str(container.get("id")),
                    title=container.get("name", ""),
                    description=container.get("description", ""),
                    severity=severity_map.get(container.get("severity"), IncidentSeverity.MEDIUM),
                    status=status_map.get(container.get("status"), IncidentStatus.NEW),
                    tags=container.get("tags", []),
                )

                incidents.append(incident)

            return incidents

        except httpx.HTTPStatusError:
            return []

    async def close(self) -> None:
        """Fecha cliente HTTP"""
        await self.client.aclose()
