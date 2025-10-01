from loguru import logger
from .sinesp_client import SinespAPIClient, SinespAPIError


class InvalidPlateError(Exception):
    """Custom exception for invalid plate format."""

    pass


class SinespService:
    def __init__(self, sinesp_api_client: SinespAPIClient):
        self.sinesp_api_client = sinesp_api_client

    async def get_vehicle_data(self, plate: str) -> dict:
        """
        Retrieves vehicle data from Sinesp.
        Handles plate formatting and specific Sinesp API interactions.
        """
        if not plate or len(plate) != 7 or not plate.isalnum():
            logger.warning(f"Attempted to query with invalid plate format: {plate}")
            raise InvalidPlateError(
                "Invalid plate format. Plate must be 7 alphanumeric characters."
            )

        formatted_plate = plate.upper()
        logger.info(f"Fetching vehicle data for formatted plate: {formatted_plate}")

        try:
            # Default latitude and longitude for Sinesp queries
            # These could also come from settings or be passed as arguments if dynamic
            latitude = -16.328
            longitude = -48.953
            data = await self.sinesp_api_client.get_vehicle_data(
                plate=formatted_plate, latitude=latitude, longitude=longitude
            )
            logger.info(
                f"Successfully retrieved Sinesp data for plate: {formatted_plate}"
            )
            return data
        except SinespAPIError as e:
            logger.error(f"Error from Sinesp API for plate {formatted_plate}: {e}")
            raise  # Re-raise the SinespAPIError for main.py to handle
        except Exception as e:
            logger.error(
                f"An unexpected error occurred in SinespService for plate {formatted_plate}: {e}"
            )
            raise  # Re-raise any other unexpected exceptions
