"""
🛡️ Microsoft Sentinel Connector

Integração com Microsoft Sentinel usando Azure REST API.
Docs: https://learn.microsoft.com/en-us/rest/api/securityinsights/
"""

import httpx
from typing import List, Dict, Any, Optional
from .base import SOARConnector, Incident, Artifact, IncidentSeverity, IncidentStatus
from datetime import datetime


class SentinelConnector(SOARConnector):
    """
    Connector para Microsoft Sentinel
    """

    def __init__(
        self,
        base_url: str,
        api_key: str,
        subscription_id: str,
        resource_group: str,
        workspace_name: str,
    ):
        """
        Args:
            base_url: Azure Management API URL (https://management.azure.com)
            api_key: Azure Bearer token
            subscription_id: Azure subscription ID
            resource_group: Resource group do Sentinel
            workspace_name: Nome do workspace Sentinel
        """
        super().__init__(base_url, api_key)
        self.subscription_id = subscription_id
        self.resource_group = resource_group
        self.workspace_name = workspace_name

        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            timeout=30.0,
        )

        # Base path para Sentinel API
        self.sentinel_path = (
            f"/subscriptions/{subscription_id}"
            f"/resourceGroups/{resource_group}"
            f"/providers/Microsoft.OperationalInsights"
            f"/workspaces/{workspace_name}"
            f"/providers/Microsoft.SecurityInsights"
        )

    async def health_check(self) -> bool:
        """Verifica conectividade com Sentinel"""
        try:
            # Tenta listar incidentes como health check
            response = await self.client.get(
                f"{self.sentinel_path}/incidents",
                params={"api-version": "2023-02-01"}
            )
            return response.status_code == 200
        except Exception:
            return False

    async def create_incident(self, incident: Incident) -> str:
        """Cria incidente no Sentinel"""
        # Mapeia severidade
        severity_map = {
            IncidentSeverity.LOW: "Low",
            IncidentSeverity.MEDIUM: "Medium",
            IncidentSeverity.HIGH: "High",
            IncidentSeverity.CRITICAL: "High",  # Sentinel: Informational/Low/Medium/High
        }

        # Mapeia status
        status_map = {
            IncidentStatus.NEW: "New",
            IncidentStatus.IN_PROGRESS: "Active",
            IncidentStatus.RESOLVED: "Closed",
            IncidentStatus.CLOSED: "Closed",
        }

        # Gera GUID para incident
        import uuid
        incident_id = str(uuid.uuid4())

        payload = {
            "properties": {
                "title": incident.title,
                "description": incident.description,
                "severity": severity_map[incident.severity],
                "status": status_map[incident.status],
                "labels": [{"labelName": tag} for tag in incident.tags],
            }
        }

        try:
            response = await self.client.put(
                f"{self.sentinel_path}/incidents/{incident_id}",
                params={"api-version": "2023-02-01"},
                json=payload,
            )
            response.raise_for_status()

            return incident_id

        except httpx.HTTPStatusError as e:
            raise ValueError(f"Failed to create incident: {e.response.text}")

    async def get_incident(self, incident_id: str) -> Optional[Incident]:
        """Busca incidente por ID"""
        try:
            response = await self.client.get(
                f"{self.sentinel_path}/incidents/{incident_id}",
                params={"api-version": "2023-02-01"}
            )

            if response.status_code == 404:
                return None

            response.raise_for_status()
            data = response.json()
            props = data.get("properties", {})

            # Mapeia de volta
            severity_map = {
                "Low": IncidentSeverity.LOW,
                "Medium": IncidentSeverity.MEDIUM,
                "High": IncidentSeverity.HIGH,
            }

            status_map = {
                "New": IncidentStatus.NEW,
                "Active": IncidentStatus.IN_PROGRESS,
                "Closed": IncidentStatus.CLOSED,
            }

            tags = [label.get("labelName") for label in props.get("labels", [])]

            incident = Incident(
                id=data.get("name"),
                title=props.get("title", ""),
                description=props.get("description", ""),
                severity=severity_map.get(props.get("severity"), IncidentSeverity.MEDIUM),
                status=status_map.get(props.get("status"), IncidentStatus.NEW),
                tags=tags,
                created_at=datetime.fromisoformat(props.get("createdTimeUtc").replace("Z", "+00:00")) if props.get("createdTimeUtc") else None,
            )

            return incident

        except httpx.HTTPStatusError:
            return None

    async def update_incident(
        self,
        incident_id: str,
        updates: Dict[str, Any]
    ) -> bool:
        """Atualiza incidente"""
        # Sentinel usa PATCH
        payload = {"properties": updates}

        try:
            response = await self.client.patch(
                f"{self.sentinel_path}/incidents/{incident_id}",
                params={"api-version": "2023-02-01"},
                json=payload,
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
        """
        Adiciona artifact (entity) ao incidente

        Sentinel usa "entities" para artifacts
        """
        # Entities são automaticamente linkados via KQL queries
        # Para adicionar manualmente, usa-se comments com metadata

        comment_payload = {
            "properties": {
                "message": f"Artifact added: {artifact.type} = {artifact.value}",
            }
        }

        try:
            import uuid
            comment_id = str(uuid.uuid4())

            response = await self.client.put(
                f"{self.sentinel_path}/incidents/{incident_id}/comments/{comment_id}",
                params={"api-version": "2023-02-01"},
                json=comment_payload,
            )
            response.raise_for_status()
            return True
        except httpx.HTTPStatusError:
            return False

    async def execute_playbook(
        self,
        playbook_id: str,
        parameters: Dict[str, Any]
    ) -> str:
        """
        Executa Logic App (playbook) no Sentinel

        Sentinel usa Azure Logic Apps como playbooks
        """
        # Logic Apps são triggerados via webhook ou manualmente
        # Aqui simulamos trigger manual

        logic_app_path = (
            f"/subscriptions/{self.subscription_id}"
            f"/resourceGroups/{self.resource_group}"
            f"/providers/Microsoft.Logic/workflows/{playbook_id}/triggers/manual/run"
        )

        try:
            response = await self.client.post(
                logic_app_path,
                params={"api-version": "2016-06-01"},
                json=parameters,
            )
            response.raise_for_status()

            # Logic Apps retornam run URL
            run_url = response.headers.get("Location", "")
            return run_url

        except httpx.HTTPStatusError as e:
            raise ValueError(f"Failed to execute playbook: {e.response.text}")

    async def list_incidents(
        self,
        status: Optional[IncidentStatus] = None,
        severity: Optional[IncidentSeverity] = None,
        limit: int = 100
    ) -> List[Incident]:
        """Lista incidentes"""
        params = {
            "api-version": "2023-02-01",
            "$top": limit,
            "$orderby": "properties/createdTimeUtc desc",
        }

        # Filtros OData
        filters = []

        if status:
            status_map = {
                IncidentStatus.NEW: "New",
                IncidentStatus.IN_PROGRESS: "Active",
                IncidentStatus.CLOSED: "Closed",
            }
            filters.append(f"properties/status eq '{status_map[status]}'")

        if severity:
            severity_map = {
                IncidentSeverity.LOW: "Low",
                IncidentSeverity.MEDIUM: "Medium",
                IncidentSeverity.HIGH: "High",
                IncidentSeverity.CRITICAL: "High",
            }
            filters.append(f"properties/severity eq '{severity_map[severity]}'")

        if filters:
            params["$filter"] = " and ".join(filters)

        try:
            response = await self.client.get(
                f"{self.sentinel_path}/incidents",
                params=params,
            )
            response.raise_for_status()

            data = response.json()
            incident_data = data.get("value", [])

            incidents = []
            for item in incident_data:
                props = item.get("properties", {})

                severity_map = {
                    "Low": IncidentSeverity.LOW,
                    "Medium": IncidentSeverity.MEDIUM,
                    "High": IncidentSeverity.HIGH,
                }

                status_map = {
                    "New": IncidentStatus.NEW,
                    "Active": IncidentStatus.IN_PROGRESS,
                    "Closed": IncidentStatus.CLOSED,
                }

                tags = [label.get("labelName") for label in props.get("labels", [])]

                incident = Incident(
                    id=item.get("name"),
                    title=props.get("title", ""),
                    description=props.get("description", ""),
                    severity=severity_map.get(props.get("severity"), IncidentSeverity.MEDIUM),
                    status=status_map.get(props.get("status"), IncidentStatus.NEW),
                    tags=tags,
                )

                incidents.append(incident)

            return incidents

        except httpx.HTTPStatusError:
            return []

    async def close(self) -> None:
        """Fecha cliente HTTP"""
        await self.client.aclose()
