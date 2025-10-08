"""Maximus OSINT Service - Email Analyzer.

This module implements the Email Analyzer for the Maximus AI's OSINT Service.
It is responsible for extracting, validating, and analyzing email addresses
found within collected OSINT data. This includes identifying patterns, domains,
and potential associations.

Key functionalities include:
- Extracting email addresses from text content using regular expressions.
- Validating email address formats.
- Identifying associated domains and potential organizational affiliations.
- Providing insights into the prevalence and context of discovered email addresses.

This analyzer is crucial for building profiles of individuals or organizations,
tracking communication patterns, and enriching threat intelligence related to
phishing campaigns or credential harvesting.
"""

import re
from datetime import datetime
from typing import Any, Dict, List, Optional


class EmailAnalyzer:
    """Extracts, validates, and analyzes email addresses found within collected OSINT data.

    Identifies patterns, domains, and potential associations, and provides insights
    into the prevalence and context of discovered email addresses.
    """

    def __init__(self):
        """Initializes the EmailAnalyzer with an email regex pattern."""
        self.email_pattern = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
        self.analysis_history: List[Dict[str, Any]] = []
        self.last_analysis_time: Optional[datetime] = None

    def analyze_text(self, text: str) -> Dict[str, Any]:
        """Extracts and analyzes email addresses from a given text.

        Args:
            text (str): The text content to analyze.

        Returns:
            Dict[str, Any]: A dictionary containing the extracted emails and their analysis.
        """
        print(f"[EmailAnalyzer] Analyzing text for email addresses (length: {len(text)})...")
        extracted_emails = self.email_pattern.findall(text)

        domains: Dict[str, int] = {}
        for email in extracted_emails:
            domain = email.split("@")[-1]
            domains[domain] = domains.get(domain, 0) + 1

        analysis_result = {
            "timestamp": datetime.now().isoformat(),
            "extracted_emails": list(set(extracted_emails)),  # Unique emails
            "email_count": len(extracted_emails),
            "domains_found": domains,
            "potential_phishing_indicators": (True if any("phish" in email for email in extracted_emails) else False),
        }
        self.analysis_history.append(analysis_result)
        self.last_analysis_time = datetime.now()

        return analysis_result

    def validate_email(self, email: str) -> bool:
        """Validates the format of an email address.

        Args:
            email (str): The email address to validate.

        Returns:
            bool: True if the email format is valid, False otherwise.
        """
        return bool(self.email_pattern.fullmatch(email))

    def get_status(self) -> Dict[str, Any]:
        """Retrieves the current operational status of the Email Analyzer.

        Returns:
            Dict[str, Any]: A dictionary summarizing the Analyzer's status.
        """
        return {
            "status": "active",
            "total_analyses": len(self.analysis_history),
            "last_analysis": (self.last_analysis_time.isoformat() if self.last_analysis_time else "N/A"),
        }
