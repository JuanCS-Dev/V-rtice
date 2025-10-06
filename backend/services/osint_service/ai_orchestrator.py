"""Maximus OSINT Service - AI Orchestrator.

This module implements the AI Orchestrator for the Maximus AI's OSINT Service.
It is responsible for coordinating the various stages of an OSINT investigation,
from data collection (scraping) to analysis and report generation.

Key functionalities include:
- Receiving high-level OSINT queries and breaking them down into sub-tasks.
- Distributing data collection tasks to specialized scrapers.
- Routing collected data to appropriate analyzers for processing.
- Managing the workflow of OSINT investigations and aggregating results.
- Providing a unified interface for initiating and monitoring complex OSINT operations.

This orchestrator is crucial for enabling Maximus AI to conduct efficient and
comprehensive OSINT investigations, transforming raw open-source information
into actionable intelligence.
"""

import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional
import uuid

from ai_processor import AIProcessor
from analyzers.email_analyzer import EmailAnalyzer
from analyzers.image_analyzer import ImageAnalyzer
from analyzers.pattern_detector import PatternDetector
from analyzers.phone_analyzer import PhoneAnalyzer
from report_generator import ReportGenerator
from scrapers.discord_bot import DiscordBotScraper
from scrapers.social_scraper import SocialMediaScraper
from scrapers.username_hunter import UsernameHunter


class AIOrchestrator:
    """Coordinates the various stages of an OSINT investigation, from data collection
    (scraping) to analysis and report generation.

    Distributes data collection tasks to specialized scrapers and routes collected
    data to appropriate analyzers for processing.
    """

    def __init__(self):
        """Initializes the AIOrchestrator with instances of scrapers, analyzers, and other components."""
        self.social_scraper = SocialMediaScraper()
        self.username_hunter = UsernameHunter()
        self.discord_scraper = DiscordBotScraper()
        self.email_analyzer = EmailAnalyzer()
        self.phone_analyzer = PhoneAnalyzer()
        self.image_analyzer = ImageAnalyzer()
        self.pattern_detector = PatternDetector()
        self.report_generator = ReportGenerator()
        self.ai_processor = AIProcessor()

        self.active_investigations: Dict[str, Dict[str, Any]] = {}
        print("[AIOrchestrator] Initialized OSINT AI Orchestrator.")

    async def start_investigation(
        self,
        query: str,
        investigation_type: str,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Starts a new OSINT investigation.

        Args:
            query (str): The primary query for the investigation (e.g., username, email, domain).
            investigation_type (str): The type of investigation (e.g., 'person_recon', 'domain_analysis').
            parameters (Optional[Dict[str, Any]]): Additional parameters for the investigation.

        Returns:
            Dict[str, Any]: A dictionary containing the investigation ID and initial status.
        """
        investigation_id = str(uuid.uuid4())
        print(
            f"[AIOrchestrator] Starting investigation {investigation_id}: {investigation_type} for {query}"
        )

        self.active_investigations[investigation_id] = {
            "id": investigation_id,
            "query": query,
            "type": investigation_type,
            "status": "running",
            "progress": 0.0,
            "start_time": datetime.now().isoformat(),
            "results": {},
            "parameters": parameters or {},
        }

        # Run the investigation workflow in a background task
        asyncio.create_task(
            self._run_investigation_workflow(
                investigation_id, query, investigation_type, parameters
            )
        )

        return {
            "investigation_id": investigation_id,
            "status": "initiated",
            "timestamp": datetime.now().isoformat(),
        }

    async def _run_investigation_workflow(
        self,
        investigation_id: str,
        query: str,
        investigation_type: str,
        parameters: Optional[Dict[str, Any]],
    ):
        """Executes the multi-step OSINT investigation workflow.

        Args:
            investigation_id (str): The ID of the investigation.
            query (str): The primary query.
            investigation_type (str): The type of investigation.
            parameters (Optional[Dict[str, Any]]): Additional parameters.
        """
        investigation = self.active_investigations[investigation_id]
        all_collected_data: List[Dict[str, Any]] = []

        try:
            # Step 1: Data Collection (Scraping)
            investigation["progress"] = 0.2
            investigation["current_step"] = "Collecting data"
            print(f"[AIOrchestrator] {investigation_id}: Collecting data...")

            if investigation_type == "person_recon":
                social_data = await self.social_scraper.scrape_profile(query)
                all_collected_data.append(
                    {"source": "social_media", "data": social_data}
                )
                username_data = await self.username_hunter.hunt_username(query)
                all_collected_data.append(
                    {"source": "username_hunter", "data": username_data}
                )
            elif investigation_type == "domain_analysis":
                # Simulate domain-specific scraping
                all_collected_data.append(
                    {
                        "source": "domain_whois",
                        "data": {"domain": query, "registrant": "mock_registrant"},
                    }
                )

            # Step 2: AI Processing (LLM for initial synthesis)
            investigation["progress"] = 0.5
            investigation["current_step"] = "AI Processing"
            print(f"[AIOrchestrator] {investigation_id}: AI Processing...")
            ai_summary = await self.ai_processor.process_raw_data(
                all_collected_data, query
            )
            all_collected_data.append({"source": "ai_summary", "data": ai_summary})

            # Step 3: Data Analysis
            investigation["progress"] = 0.7
            investigation["current_step"] = "Analyzing data"
            print(f"[AIOrchestrator] {investigation_id}: Analyzing data...")
            analysis_results: Dict[str, Any] = {}
            for data_entry in all_collected_data:
                if data_entry["source"] == "social_media":
                    analysis_results["email_found"] = self.email_analyzer.analyze_text(
                        str(data_entry["data"])
                    )
                    analysis_results["phone_found"] = self.phone_analyzer.analyze_text(
                        str(data_entry["data"])
                    )
                # Add more analysis based on data types

            # Step 4: Report Generation
            investigation["progress"] = 0.9
            investigation["current_step"] = "Generating report"
            print(f"[AIOrchestrator] {investigation_id}: Generating report...")
            final_report = await self.report_generator.generate_report(
                query, investigation_type, all_collected_data, analysis_results
            )

            investigation["results"] = final_report
            investigation["status"] = "completed"
            investigation["progress"] = 1.0
            print(
                f"[AIOrchestrator] Investigation {investigation_id} completed successfully."
            )

        except Exception as e:
            investigation["status"] = "failed"
            investigation["error"] = str(e)
            print(f"[AIOrchestrator] Investigation {investigation_id} failed: {e}")

    def get_investigation_status(
        self, investigation_id: str
    ) -> Optional[Dict[str, Any]]:
        """Retrieves the current status of an OSINT investigation.

        Args:
            investigation_id (str): The ID of the investigation.

        Returns:
            Optional[Dict[str, Any]]: A dictionary containing the investigation status, or None if not found.
        """
        return self.active_investigations.get(investigation_id)

    def list_active_investigations(self) -> List[Dict[str, Any]]:
        """Lists all currently active OSINT investigations.

        Returns:
            List[Dict[str, Any]]: A list of active investigation status dictionaries.
        """
        return [
            inv
            for inv in self.active_investigations.values()
            if inv["status"] == "running"
        ]
