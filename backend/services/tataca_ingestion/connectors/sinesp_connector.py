"""Tatacá Ingestion - SINESP Connector.

Connector for fetching data from SINESP (Sistema Nacional de Informações
de Segurança Pública) service.
"""

from datetime import datetime
import logging
from typing import Any, Dict, List, Optional

from config import get_settings
import httpx
from models import DataSource, Ocorrencia, SinespVehicleResponse, Veiculo

logger = logging.getLogger(__name__)
settings = get_settings()


class SinespConnector:
    """
    Connector for SINESP service.

    Fetches vehicle and occurrence data from the SINESP API.
    """

    def __init__(self, base_url: Optional[str] = None):
        """
        Initialize SINESP connector.

        Args:
            base_url: SINESP service base URL (defaults to settings)
        """
        self.base_url = base_url or settings.SINESP_SERVICE_URL
        self.timeout = 30.0
        self._client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self):
        """Async context manager entry."""
        self._client = httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._client:
            await self._client.aclose()

    async def fetch_vehicle_by_plate(self, placa: str) -> Optional[Veiculo]:
        """
        Fetch vehicle data by license plate.

        Args:
            placa: License plate number

        Returns:
            Veiculo entity if found, None otherwise
        """
        try:
            if not self._client:
                raise RuntimeError(
                    "Connector not initialized. Use async context manager."
                )

            logger.info(f"Fetching vehicle data for plate: {placa}")

            response = await self._client.get(f"/veiculos/{placa}")
            response.raise_for_status()

            data = response.json()

            # Convert SINESP response to Veiculo entity
            sinesp_vehicle = SinespVehicleResponse(**data)
            veiculo = sinesp_vehicle.to_veiculo()

            logger.info(f"Successfully fetched vehicle: {placa}")
            return veiculo

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.warning(f"Vehicle not found: {placa}")
                return None
            logger.error(f"HTTP error fetching vehicle {placa}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error fetching vehicle {placa}: {e}", exc_info=True)
            raise

    async def fetch_vehicles_batch(self, placas: List[str]) -> List[Veiculo]:
        """
        Fetch multiple vehicles in batch.

        Args:
            placas: List of license plates

        Returns:
            List of Veiculo entities
        """
        veiculos = []

        for placa in placas:
            try:
                veiculo = await self.fetch_vehicle_by_plate(placa)
                if veiculo:
                    veiculos.append(veiculo)
            except Exception as e:
                logger.error(f"Error fetching vehicle {placa} in batch: {e}")
                continue  # Continue with next vehicle

        logger.info(f"Fetched {len(veiculos)} vehicles out of {len(placas)} plates")
        return veiculos

    async def fetch_occurrences(
        self, filters: Optional[Dict[str, Any]] = None
    ) -> List[Ocorrencia]:
        """
        Fetch occurrences (criminal reports) from SINESP.

        Args:
            filters: Query filters (tipo, cidade, data_inicio, data_fim, etc)

        Returns:
            List of Ocorrencia entities
        """
        try:
            if not self._client:
                raise RuntimeError(
                    "Connector not initialized. Use async context manager."
                )

            filters = filters or {}
            logger.info(f"Fetching occurrences with filters: {filters}")

            # Build query parameters
            params = {}
            if "tipo" in filters:
                params["tipo"] = filters["tipo"]
            if "cidade" in filters:
                params["cidade"] = filters["cidade"]
            if "data_inicio" in filters:
                params["data_inicio"] = filters["data_inicio"]
            if "data_fim" in filters:
                params["data_fim"] = filters["data_fim"]

            response = await self._client.get("/ocorrencias", params=params)
            response.raise_for_status()

            data = response.json()

            # Convert to Ocorrencia entities
            ocorrencias = []
            for item in data.get("items", []):
                try:
                    ocorrencia = Ocorrencia(
                        numero_bo=item.get("numero_bo"),
                        tipo=item.get("tipo"),
                        data_hora=datetime.fromisoformat(item.get("data_hora")),
                        descricao=item.get("descricao"),
                        local_logradouro=item.get("local", {}).get("logradouro"),
                        local_bairro=item.get("local", {}).get("bairro"),
                        local_cidade=item.get("local", {}).get("cidade"),
                        local_estado=item.get("local", {}).get("estado"),
                        delegacia=item.get("delegacia"),
                        status=item.get("status"),
                        metadata={
                            "source": DataSource.SINESP,
                            "fetched_at": datetime.utcnow().isoformat(),
                        },
                    )
                    ocorrencias.append(ocorrencia)
                except Exception as e:
                    logger.error(f"Error parsing occurrence: {e}")
                    continue

            logger.info(f"Fetched {len(ocorrencias)} occurrences")
            return ocorrencias

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching occurrences: {e}")
            raise
        except Exception as e:
            logger.error(f"Error fetching occurrences: {e}", exc_info=True)
            raise

    async def fetch_occurrence_types(self) -> List[str]:
        """
        Fetch available occurrence types from SINESP.

        Returns:
            List of occurrence type names
        """
        try:
            if not self._client:
                raise RuntimeError(
                    "Connector not initialized. Use async context manager."
                )

            response = await self._client.get("/ocorrencias/tipos")
            response.raise_for_status()

            data = response.json()
            tipos = [item.get("tipo") for item in data.get("tipos", [])]

            logger.info(f"Fetched {len(tipos)} occurrence types")
            return tipos

        except Exception as e:
            logger.error(f"Error fetching occurrence types: {e}", exc_info=True)
            return []

    async def health_check(self) -> bool:
        """
        Check SINESP service health.

        Returns:
            True if service is healthy, False otherwise
        """
        try:
            if not self._client:
                # Create temporary client for health check
                async with httpx.AsyncClient(
                    base_url=self.base_url, timeout=5.0
                ) as client:
                    response = await client.get("/health")
                    return response.status_code == 200
            else:
                response = await self._client.get("/health")
                return response.status_code == 200

        except Exception as e:
            logger.error(f"SINESP health check failed: {e}")
            return False
