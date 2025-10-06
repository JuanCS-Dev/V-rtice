"""Maximus OSINT Service - Report Generator.

This module implements the Report Generator for the Maximus AI's OSINT Service.
It is responsible for compiling and formatting the results of an OSINT
investigation into a comprehensive and human-readable report.

Key functionalities include:
- Aggregating data from various scrapers and analyzers.
- Structuring the information logically and clearly.
- Highlighting key findings, insights, and actionable intelligence.
- Generating reports in various formats (e.g., PDF, Markdown, JSON).

This generator is crucial for presenting the complex output of OSINT
investigations in an accessible manner, enabling human analysts and other
Maximus AI services to quickly grasp the intelligence and make informed decisions.
"""

import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional


class ReportGenerator:
    """Compiles and formats the results of an OSINT investigation into a comprehensive
    and human-readable report.

    Aggregates data from various scrapers and analyzers, structures the information
    logically and clearly, and highlights key findings, insights, and actionable intelligence.
    """

    def __init__(self):
        """Initializes the ReportGenerator."""
        self.generated_reports: List[Dict[str, Any]] = []
        self.last_report_time: Optional[datetime] = None

    async def generate_report(
        self,
        query: str,
        investigation_type: str,
        collected_data: List[Dict[str, Any]],
        analysis_results: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Generates a comprehensive OSINT report.

        Args:
            query (str): The original query for the investigation.
            investigation_type (str): The type of investigation.
            collected_data (List[Dict[str, Any]]): Raw data collected by scrapers.
            analysis_results (Dict[str, Any]): Results from various analyzers.

        Returns:
            Dict[str, Any]: A dictionary representing the generated report.
        """
        print(
            f"[ReportGenerator] Generating report for query: {query} (type: {investigation_type})..."
        )
        await asyncio.sleep(0.5)  # Simulate report generation time

        report_content = f"# OSINT Investigation Report\n\n"
        report_content += f"## Query: {query}\n"
        report_content += f"## Investigation Type: {investigation_type}\n\n"
        report_content += f"### Summary of Findings\n"
        report_content += f"- AI Processed Summary: {analysis_results.get('ai_summary', {}).get('synthesized_summary', 'N/A')}\n"
        report_content += f"- Extracted Emails: {analysis_results.get('email_found', {}).get('extracted_emails', [])}\n"
        report_content += f"- Extracted Phone Numbers: {analysis_results.get('phone_found', {}).get('extracted_phone_numbers', [])}\n"
        report_content += f"- Detected Patterns: {analysis_results.get('patterns_detected', {}).get('detected_patterns', [])}\n\n"

        report_content += f"### Raw Collected Data ({len(collected_data)} entries)\n"
        for entry in collected_data:
            report_content += f"- Source: {entry.get('source')}, Data: {str(entry.get('data'))[:100]}...\n"

        final_report = {
            "timestamp": datetime.now().isoformat(),
            "query": query,
            "investigation_type": investigation_type,
            "report_summary": report_content[:500] + "...",  # Truncate for summary
            "full_report_content": report_content,
            "key_findings": analysis_results,
        }
        self.generated_reports.append(final_report)
        self.last_report_time = datetime.now()

        return final_report

    async def get_status(self) -> Dict[str, Any]:
        """Retrieves the current operational status of the Report Generator.

        Returns:
            Dict[str, Any]: A dictionary summarizing the Generator's status.
        """
        return {
            "status": "active",
            "total_reports_generated": len(self.generated_reports),
            "last_report": (
                self.last_report_time.isoformat() if self.last_report_time else "N/A"
            ),
        }
