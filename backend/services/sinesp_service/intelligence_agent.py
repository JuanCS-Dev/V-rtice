"""Maximus Sinesp Service - Intelligence Agent.

This module implements the Intelligence Agent for the Maximus AI's Sinesp Service.
It is responsible for orchestrating queries to the Sinesp Cidadão API, processing
the retrieved public security data, and extracting relevant intelligence.

Key functionalities include:
- Formulating queries for vehicle license plates, chassis numbers, or other identifiers.
- Handling API interactions, including authentication and error handling.
- Parsing Sinesp API responses and normalizing data.
- Identifying key information and potential anomalies from public security records.
- Providing contextual information for investigations, situational awareness,
  and law enforcement support within the Maximus AI system.
"""

import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
import httpx

from models import VehicleInfo, SinespQuery
from config import get_settings
from llm_client import LLMClient
from prompt_templates import SINESP_ANALYSIS_PROMPT

settings = get_settings()


class IntelligenceAgent:
    """Orchestrates queries to the Sinesp Cidadão API, processes retrieved public
    security data, and extracts relevant intelligence.

    Formulates queries for vehicle license plates, chassis numbers, or other
    identifiers, handles API interactions, and parses Sinesp API responses.
    """

    def __init__(self, llm_client: LLMClient):
        """Initializes the IntelligenceAgent.

        Args:
            llm_client (LLMClient): An instance of the LLMClient for AI-driven analysis.
        """
        self.llm_client = llm_client
        self.api_url = settings.sinesp_api_url
        self.api_key = settings.sinesp_api_key
        self.query_history: List[Dict[str, Any]] = []
        self.last_query_time: Optional[datetime] = None
        self.current_status: str = "ready_for_queries"

    async def query_sinesp(self, query: SinespQuery) -> VehicleInfo:
        """Queries the Sinesp Cidadão API for vehicle information.

        Args:
            query (SinespQuery): The query object containing the identifier and type.

        Returns:
            VehicleInfo: Detailed information about the vehicle.
        
        Raises:
            httpx.HTTPStatusError: If the Sinesp API returns an error.
            ValueError: If the API key is missing.
        """
        if not self.api_key or self.api_key == "your_sinesp_api_key":
            raise ValueError("Sinesp API key is not configured.")

        print(f"[IntelligenceAgent] Querying Sinesp for {query.query_type}: {query.identifier}")
        
        # Simulate API call to Sinesp
        async with httpx.AsyncClient() as client:
            try:
                # In a real scenario, construct the actual Sinesp API request
                # For mock, we simulate a response
                await asyncio.sleep(0.5) # Simulate network latency

                if query.identifier == "ABC1234":
                    sinesp_response = {
                        "status": "success",
                        "plate": "ABC1234",
                        "model": "FIAT/UNO",
                        "color": "PRATA",
                        "year": 2010,
                        "city": "SAO PAULO",
                        "state": "SP",
                        "stolen": False
                    }
                elif query.identifier == "XYZ9876":
                    sinesp_response = {
                        "status": "success",
                        "plate": "XYZ9876",
                        "model": "VW/GOL",
                        "color": "PRETO",
                        "year": 2015,
                        "city": "RIO DE JANEIRO",
                        "state": "RJ",
                        "stolen": True
                    }
                else:
                    sinesp_response = {"status": "error", "message": "Vehicle not found."}

                if sinesp_response.get("status") == "error":
                    raise httpx.HTTPStatusError(f"Sinesp API error: {sinesp_response.get('message')}", request=httpx.Request("POST", self.api_url), response=httpx.Response(404))

                vehicle_info = VehicleInfo(**sinesp_response)
                self.query_history.append({"timestamp": datetime.now().isoformat(), "query": query.dict(), "result": vehicle_info.dict()})
                self.last_query_time = datetime.now()
                return vehicle_info

            except httpx.HTTPStatusError as e:
                print(f"[IntelligenceAgent] Sinesp API returned error: {e.response.status_code} - {e.response.text}")
                raise
            except httpx.RequestError as e:
                print(f"[IntelligenceAgent] Network error during Sinesp API call: {e}")
                raise HTTPException(status_code=503, detail=f"Could not connect to Sinesp API: {e}")

    async def analyze_vehicle_info(self, vehicle_info: VehicleInfo) -> Dict[str, Any]:
        """Analyzes vehicle information using an LLM to extract insights.

        Args:
            vehicle_info (VehicleInfo): The vehicle information to analyze.

        Returns:
            Dict[str, Any]: A dictionary containing AI-generated insights.
        """
        print(f"[IntelligenceAgent] Analyzing vehicle info for {vehicle_info.plate} with LLM.")
        
        prompt = SINESP_ANALYSIS_PROMPT.format(vehicle_info=vehicle_info.json())
        llm_response = await self.llm_client.generate_text(prompt)

        # Simulate parsing LLM response for structured insights
        insights = {
            "summary": llm_response[:100] + "...",
            "potential_risks": [],
            "recommendations": []
        }
        if vehicle_info.stolen:
            insights["potential_risks"].append("Vehicle reported stolen.")
            insights["recommendations"].append("Alert authorities immediately.")
        if vehicle_info.year < 2010:
            insights["recommendations"].append("Check for older vehicle vulnerabilities.")

        return insights

    async def get_status(self) -> Dict[str, Any]:
        """Retrieves the current operational status of the Intelligence Agent.

        Returns:
            Dict[str, Any]: A dictionary summarizing the agent's status.
        """
        return {
            "status": self.current_status,
            "total_queries": len(self.query_history),
            "last_query": self.last_query_time.isoformat() if self.last_query_time else "N/A"
        }