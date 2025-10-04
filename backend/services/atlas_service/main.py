"""Atlas Service - Geospatial (GIS) Data Enrichment.

This service provides geospatial data enrichment for the Vertice project by
querying open data sources, primarily OpenStreetMap via the Overpass API.
It allows other services to retrieve information about Points of Interest (POIs)
and other geographic features.

Typical usage example:

  A client would make a POST request to the /query/ endpoint with an
  Overpass QL query in the request body.
"""

import httpx
from fastapi import FastAPI, HTTPException, Body
from pydantic import BaseModel
from datetime import datetime, timezone
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Atlas Service",
    description="Geospatial (GIS) data enrichment service for Vertice. Provides data on Points of Interest (POIs) from open sources.",
    version="1.0.0",
)

# Overpass API URL constant
OVERPASS_API_URL = "https://overpass-api.de/api/interpreter"


async def query_overpass_api(query: str) -> dict:
    """Executes a query against the Overpass API and returns the JSON result.

    This function sends a POST request with the given Overpass QL query string
    to the public Overpass API endpoint.

    Args:
        query (str): The Overpass QL query string to be executed.

    Returns:
        dict: The JSON response from the Overpass API as a dictionary.

    Raises:
        HTTPException: If there is an HTTP error (e.g., 4xx, 5xx) from the
            Overpass API, a connection error, or any other unexpected error
            during the process.
    """
    logger.info("Executing query on Overpass API...")
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(OVERPASS_API_URL, data=query)
            response.raise_for_status()  # Raise an exception for HTTP errors
            logger.info(f"Query executed successfully. Status: {response.status_code}")
            return response.json()
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error while querying Overpass API: {e.response.status_code} - {e.response.text}")
        raise HTTPException(status_code=e.response.status_code, detail=f"Error from Overpass API: {e.response.text}")
    except httpx.RequestError as e:
        logger.error(f"Connection error with Overpass API: {e}")
        raise HTTPException(status_code=503, detail=f"Could not connect to Overpass API: {e}")
    except Exception as e:
        logger.error(f"Unexpected error processing Overpass query: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal error while processing the query.")


@app.get("/", tags=["Health"])
async def read_root():
    """Provides a health check endpoint for the Atlas Service.

    Returns:
        dict: A dictionary containing the service status, version, data source,
            and the current UTC timestamp.
    """
    return {
        "status": "Atlas Service Online",
        "version": "1.0.0",
        "data_source": "OpenStreetMap via Overpass API",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@app.post("/query/", tags=["Overpass"])
async def execute_raw_query(query: str = Body(..., media_type="text/plain")):
    """Executes a raw Overpass QL query.

    This low-level endpoint is intended for development and testing purposes,
    allowing direct execution of Overpass QL queries.

    Args:
        query (str): The raw Overpass QL query string, sent in the request body.

    Returns:
        dict: The JSON response from the Overpass API.
    """
    return await query_overpass_api(query=query)