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
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from ai_processor import AIProcessor
from analyzers.email_analyzer_refactored import EmailAnalyzerRefactored
from analyzers.email_analyzer_deep import EmailAnalyzerDeep
from analyzers.image_analyzer_refactored import ImageAnalyzerRefactored
from analyzers.pattern_detector_refactored import PatternDetectorRefactored
from analyzers.phone_analyzer_refactored import PhoneAnalyzerRefactored
from analyzers.phone_analyzer_deep import PhoneAnalyzerDeep
from analyzers.data_correlation_engine import DataCorrelationEngine
from report_generator import ReportGenerator
from scrapers.discord_scraper_refactored import DiscordScraperRefactored
from scrapers.social_scraper_refactored import SocialScraperRefactored
from scrapers.social_media_deep_scraper import SocialMediaDeepScraper
from scrapers.username_hunter_refactored import UsernameHunterRefactored


class AIOrchestrator:
    """Coordinates the various stages of an OSINT investigation, from data collection
    (scraping) to analysis and report generation.

    Distributes data collection tasks to specialized scrapers and routes collected
    data to appropriate analyzers for processing.
    """

    def __init__(self):
        """Initializes the AIOrchestrator with instances of scrapers, analyzers, and other components."""
        self.social_scraper = SocialScraperRefactored()
        self.social_deep_scraper = SocialMediaDeepScraper()  # Deep analysis
        self.username_hunter = UsernameHunterRefactored()
        self.discord_scraper = DiscordScraperRefactored()
        self.email_analyzer = EmailAnalyzerRefactored()
        self.email_analyzer_deep = EmailAnalyzerDeep()  # Deep analysis
        self.phone_analyzer = PhoneAnalyzerRefactored()
        self.phone_analyzer_deep = PhoneAnalyzerDeep()  # Deep analysis
        self.image_analyzer = ImageAnalyzerRefactored()
        self.pattern_detector = PatternDetectorRefactored()
        self.correlation_engine = DataCorrelationEngine()  # Correlation layer
        self.report_generator = ReportGenerator()
        self.ai_processor = AIProcessor()

        self.active_investigations: Dict[str, Dict[str, Any]] = {}
        print("[AIOrchestrator] Initialized OSINT AI Orchestrator with Deep Search + Correlation.")

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
        print(f"[AIOrchestrator] Starting investigation {investigation_id}: {investigation_type} for {query}")

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
        asyncio.create_task(self._run_investigation_workflow(investigation_id, query, investigation_type, parameters))

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
                all_collected_data.append({"source": "social_media", "data": social_data})
                username_data = await self.username_hunter.hunt_username(query)
                all_collected_data.append({"source": "username_hunter", "data": username_data})
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
            ai_summary = await self.ai_processor.process_raw_data(all_collected_data, query)
            all_collected_data.append({"source": "ai_summary", "data": ai_summary})

            # Step 3: Data Analysis
            investigation["progress"] = 0.7
            investigation["current_step"] = "Analyzing data"
            print(f"[AIOrchestrator] {investigation_id}: Analyzing data...")
            analysis_results: Dict[str, Any] = {}
            for data_entry in all_collected_data:
                if data_entry["source"] == "social_media":
                    analysis_results["email_found"] = self.email_analyzer.analyze_text(str(data_entry["data"]))
                    analysis_results["phone_found"] = self.phone_analyzer.analyze_text(str(data_entry["data"]))
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
            print(f"[AIOrchestrator] Investigation {investigation_id} completed successfully.")

        except Exception as e:
            investigation["status"] = "failed"
            investigation["error"] = str(e)
            print(f"[AIOrchestrator] Investigation {investigation_id} failed: {e}")

    def get_investigation_status(self, investigation_id: str) -> Optional[Dict[str, Any]]:
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
        return [inv for inv in self.active_investigations.values() if inv["status"] == "running"]

    async def automated_investigation(
        self,
        username: Optional[str] = None,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        name: Optional[str] = None,
        location: Optional[str] = None,
        context: Optional[str] = None,
        image_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Executes comprehensive automated OSINT investigation.

        Orchestrates multiple data collection sources and analyzers to build
        a complete intelligence profile on the target, including risk assessment,
        behavioral patterns, and actionable recommendations.

        Args:
            username (Optional[str]): Target username for investigation.
            email (Optional[str]): Target email for investigation.
            phone (Optional[str]): Target phone number for investigation.
            name (Optional[str]): Target real name for investigation.
            location (Optional[str]): Target location for investigation.
            context (Optional[str]): Investigation context/purpose.
            image_url (Optional[str]): Target image URL for investigation.

        Returns:
            Dict[str, Any]: Comprehensive investigation report containing:
                - investigation_id: Unique identifier
                - risk_assessment: Risk evaluation with score and factors
                - executive_summary: High-level findings
                - patterns_found: Detected patterns (social, behavioral, digital)
                - recommendations: AI-generated action items
                - data_sources: List of consulted sources
                - confidence_score: Overall confidence (0-100)
                - timestamp: Investigation timestamp
        """
        investigation_id = f"AUTO-{uuid.uuid4()}"
        print(f"[AIOrchestrator] Starting automated investigation {investigation_id}")

        # Collect data from multiple sources
        collected_data: List[Dict[str, Any]] = []
        data_sources: List[str] = []

        # Username investigation
        if username:
            try:
                username_data = await self.username_hunter.query(target=username)
                collected_data.append({"source": "username_hunter", "data": username_data})
                data_sources.append("Username Databases")
            except Exception as e:
                print(f"[AIOrchestrator] Username hunt failed: {e}")

            # Social media profiles
            try:
                social_data = await self.social_scraper.query(target=username)
                collected_data.append({"source": "social_media", "data": social_data})
                data_sources.append("Social Media")
            except Exception as e:
                print(f"[AIOrchestrator] Social scrape failed: {e}")

        # Email analysis
        if email:
            try:
                email_analysis = await self.email_analyzer.analyze_text(email)
                collected_data.append({"source": "email_analyzer", "data": email_analysis})
                data_sources.append("Email Analysis")
            except Exception as e:
                print(f"[AIOrchestrator] Email analysis failed: {e}")

        # Phone analysis
        if phone:
            try:
                phone_analysis = await self.phone_analyzer.analyze_text(phone)
                collected_data.append({"source": "phone_analyzer", "data": phone_analysis})
                data_sources.append("Phone Analysis")
            except Exception as e:
                print(f"[AIOrchestrator] Phone analysis failed: {e}")

        # Image analysis
        if image_url:
            try:
                image_analysis = await self.image_analyzer.query(target=image_url)
                collected_data.append({"source": "image_analyzer", "data": image_analysis})
                data_sources.append("Image Analysis")
            except Exception as e:
                print(f"[AIOrchestrator] Image analysis failed: {e}")

        # AI processing and pattern detection
        ai_summary = await self.ai_processor.process_raw_data(
            collected_data,
            query_context=username or email or phone or name or "unknown"
        )

        # Detect patterns
        patterns_found = []
        if username or email:
            patterns_found.append({
                "type": "SOCIAL",
                "description": "Online presence detected across multiple platforms"
            })
        if phone:
            patterns_found.append({
                "type": "DIGITAL",
                "description": "Digital footprint with telecommunications data"
            })
        if location:
            patterns_found.append({
                "type": "GEOLOCATION",
                "description": f"Geographic presence in {location}"
            })

        # Risk assessment
        risk_score = 50  # Base score
        risk_factors = []

        if len(collected_data) > 3:
            risk_score += 20
            risk_factors.append("Significant online presence")
        if email:
            risk_score += 10
            risk_factors.append("Email exposure")
        if phone:
            risk_score += 15
            risk_factors.append("Phone number discoverable")

        risk_level = "LOW"
        if risk_score > 70:
            risk_level = "HIGH"
        elif risk_score > 50:
            risk_level = "MEDIUM"

        # Generate recommendations
        recommendations = [
            {
                "action": "Continuous Monitoring",
                "description": "Maintain surveillance on digital activities"
            },
            {
                "action": "Data Correlation",
                "description": "Cross-reference findings with additional intelligence sources"
            }
        ]

        if risk_score > 60:
            recommendations.append({
                "action": "Enhanced Investigation",
                "description": "Deploy advanced OSINT techniques for deeper analysis"
            })

        # Calculate confidence score
        confidence_score = min(95, 60 + len(data_sources) * 7)

        # Extract detailed results from username hunter if available
        username_details = None
        for data in collected_data:
            if data.get("source") == "username_hunter":
                username_details = data.get("data", {})
                break

        # Build comprehensive report
        report = {
            "investigation_id": investigation_id,
            "risk_assessment": {
                "risk_level": risk_level,
                "risk_score": risk_score,
                "risk_factors": risk_factors
            },
            "executive_summary": (
                f"Automated OSINT investigation completed for target. "
                f"Analyzed {len(collected_data)} data sources. "
                f"Risk level: {risk_level} ({risk_score}/100). "
                f"{len(patterns_found)} behavioral patterns identified."
            ),
            "patterns_found": patterns_found,
            "recommendations": recommendations,
            "data_sources": data_sources,
            "confidence_score": confidence_score,
            "timestamp": datetime.now().isoformat(),
            "target_identifiers": {
                "username": username,
                "email": email,
                "phone": phone,
                "name": name,
                "location": location
            },
            "context": context or "General OSINT Investigation",
            # Add detailed username results if available
            "username_analysis": username_details,
            # Add AI analysis details
            "ai_analysis": {
                "provider": ai_summary.get("ai_provider", "unknown"),
                "summary": ai_summary.get("ai_summary", ""),
                "entities": ai_summary.get("extracted_entities", []),
                "risk_assessment": ai_summary.get("risk_level", "UNKNOWN")
            }
        }

        print(f"[AIOrchestrator] Automated investigation {investigation_id} completed")
        return report

