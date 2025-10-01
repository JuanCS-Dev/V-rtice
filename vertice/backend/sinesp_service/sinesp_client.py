import httpx
import json
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type

from .config import settings


class SinespAPIError(Exception):
    """Custom exception for Sinesp API errors."""

    def __init__(
        self, message: str, status_code: int = None, response_text: str = None
    ):
        super().__init__(message)
        self.status_code = status_code
        self.response_text = response_text


class SinespAPIClient:
    def __init__(self):
        self.base_url = settings.SINESP_API_BASE_URL
        self.headers = {
            "User-Agent": "SinespCidadao / 5.0.0",  # Consider moving this to settings if it changes
            "Content-Type": "application/json; charset=utf-8",
            "Host": "wdapi2.sinesp.gov.br",  # Consider moving this to settings if it changes
        }
        self.timeout = 15.0  # Consider moving this to settings

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_fixed(2),
        retry=retry_if_exception_type(httpx.RequestError),
        reraise=True,
    )
    async def _post(self, endpoint: str, payload: dict) -> dict:
        """Internal method to handle POST requests to Sinesp API with retries."""
        url = f"{self.base_url}{endpoint}"
        logger.debug(
            f"Making POST request to Sinesp API: {url} with payload: {payload}"
        )
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    headers=self.headers,
                    data=json.dumps(payload),
                    timeout=self.timeout,
                )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as exc:
            logger.error(
                f"Sinesp API HTTP error: {exc.response.status_code} - {exc.response.text}"
            )
            # Here we can parse Sinesp's specific error messages if they exist
            raise SinespAPIError(
                f"Sinesp API returned an error: {exc.response.status_code}",
                status_code=exc.response.status_code,
                response_text=exc.response.text,
            ) from exc
        except httpx.RequestError as exc:
            logger.error(f"Sinesp API request error: {exc}")
            raise SinespAPIError(f"Could not connect to Sinesp API: {exc}") from exc
        except Exception as exc:
            logger.error(f"An unexpected error occurred during Sinesp API call: {exc}")
            raise SinespAPIError(f"An unexpected error occurred: {exc}") from exc

    async def get_vehicle_data(
        self, plate: str, latitude: float = -16.328, longitude: float = -48.953
    ) -> dict:
        """Fetches vehicle data from Sinesp API."""
        endpoint = "/v2/consultar-placa"  # This should ideally be part of settings or a constant
        payload = {"latitude": latitude, "longitude": longitude, "placa": plate}
        return await self._post(endpoint, payload)
