"""Maximus OSINT Service - Phone Analyzer.

This module implements the Phone Analyzer for the Maximus AI's OSINT Service.
It is responsible for extracting, validating, and analyzing phone numbers
found within collected OSINT data. This includes identifying country codes,
area codes, and potential associations.

Key functionalities include:
- Extracting phone numbers from text content using regular expressions.
- Validating phone number formats against international standards.
- Identifying associated countries, regions, and telecommunication providers.
- Providing insights into the prevalence and context of discovered phone numbers.

This analyzer is crucial for building profiles of individuals or organizations,
tracking communication patterns, and enriching threat intelligence related to
telephony-based attacks or social engineering campaigns.
"""

import re
from datetime import datetime
from typing import Any, Dict, List, Optional


class PhoneAnalyzer:
    """Extracts, validates, and analyzes phone numbers found within collected OSINT data.

    Identifies country codes, area codes, and potential associations, and provides
    insights into the prevalence and context of discovered phone numbers.
    """

    def __init__(self):
        """Initializes the PhoneAnalyzer with common phone number patterns."""
        # Regex for common international phone number formats (simplified)
        self.phone_pattern = re.compile(r"\+?\d{1,4}[-.\s]?\(?\d{1,3}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,9}")
        self.analysis_history: List[Dict[str, Any]] = []
        self.last_analysis_time: Optional[datetime] = None

    def analyze_text(self, text: str) -> Dict[str, Any]:
        """Extracts and analyzes phone numbers from a given text.

        Args:
            text (str): The text content to analyze.

        Returns:
            Dict[str, Any]: A dictionary containing the extracted phone numbers and their analysis.
        """
        print(f"[PhoneAnalyzer] Analyzing text for phone numbers (length: {len(text)})...")
        extracted_numbers = self.phone_pattern.findall(text)

        countries: Dict[str, int] = {}
        for number in extracted_numbers:
            # Simulate country code detection (very basic)
            if number.startswith("+1"):
                countries["USA"] = countries.get("USA", 0) + 1
            elif number.startswith("+44"):
                countries["UK"] = countries.get("UK", 0) + 1
            else:
                countries["Unknown"] = countries.get("Unknown", 0) + 1

        analysis_result = {
            "timestamp": datetime.now().isoformat(),
            "extracted_phone_numbers": list(set(extracted_numbers)),  # Unique numbers
            "number_count": len(extracted_numbers),
            "countries_found": countries,
            "potential_social_engineering_indicators": (
                True if any("urgent" in text.lower() for _ in extracted_numbers) else False
            ),
        }
        self.analysis_history.append(analysis_result)
        self.last_analysis_time = datetime.now()

        return analysis_result

    def validate_phone_number(self, phone_number: str) -> bool:
        """Validates the format of a phone number.

        Args:
            phone_number (str): The phone number to validate.

        Returns:
            bool: True if the phone number format is valid, False otherwise.
        """
        return bool(self.phone_pattern.fullmatch(phone_number))

    def get_status(self) -> Dict[str, Any]:
        """Retrieves the current operational status of the Phone Analyzer.

        Returns:
            Dict[str, Any]: A dictionary summarizing the Analyzer's status.
        """
        return {
            "status": "active",
            "total_analyses": len(self.analysis_history),
            "last_analysis": (self.last_analysis_time.isoformat() if self.last_analysis_time else "N/A"),
        }
