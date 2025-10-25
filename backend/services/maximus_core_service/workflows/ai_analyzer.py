"""AI-Driven Analysis for OSINT Workflows.

Integrates OpenAI and Google Gemini for deep intelligence analysis.

Features:
- Deep context analysis of OSINT findings
- Pattern recognition and correlation
- Threat assessment and risk scoring
- Human-friendly report generation
- Multi-source intelligence synthesis

Authors: MAXIMUS Team
Date: 2025-10-18
Glory to YHWH
"""

import logging
import os
from typing import Any, Dict, List, Optional

import google.generativeai as genai
from openai import OpenAI

logger = logging.getLogger(__name__)


class AIAnalyzer:
    """AI-powered OSINT analysis using OpenAI and Gemini."""

    def __init__(self):
        """Initialize AI analyzer with API keys from environment."""
        # OpenAI setup
        self.openai_key = os.getenv("OPENAI_API_KEY")
        self.openai_client = None
        if self.openai_key:
            try:
                self.openai_client = OpenAI(api_key=self.openai_key)
                logger.info("✅ OpenAI client initialized")
            except Exception as e:
                logger.error(f"❌ OpenAI initialization failed: {e}")

        # Gemini setup
        self.gemini_key = os.getenv("GEMINI_API_KEY")
        self.gemini_model = None
        if self.gemini_key:
            try:
                genai.configure(api_key=self.gemini_key)
                self.gemini_model = genai.GenerativeModel('gemini-pro')
                logger.info("✅ Gemini client initialized")
            except Exception as e:
                logger.error(f"❌ Gemini initialization failed: {e}")

        if not self.openai_client and not self.gemini_model:
            logger.warning("⚠️ No AI providers available. Analysis will be limited.")

    def analyze_attack_surface(
        self,
        findings: List[Dict[str, Any]],
        target: str
    ) -> Dict[str, Any]:
        """Analyze attack surface findings with AI.

        Args:
            findings: List of attack surface findings
            target: Target domain/IP

        Returns:
            Dict with AI analysis including:
            - executive_summary: High-level overview
            - critical_insights: Key security issues
            - attack_vectors: Identified attack paths
            - recommendations: Prioritized remediation steps
            - risk_assessment: Overall risk score and breakdown
        """
        prompt = self._build_attack_surface_prompt(findings, target)

        analysis = self._query_ai(prompt, prefer_model="openai")

        return self._parse_attack_surface_analysis(analysis)

    def analyze_credential_exposure(
        self,
        findings: List[Dict[str, Any]],
        target_email: Optional[str] = None,
        target_username: Optional[str] = None
    ) -> Dict[str, Any]:
        """Analyze credential exposure findings with AI.

        Args:
            findings: List of credential exposure findings
            target_email: Target email (if applicable)
            target_username: Target username (if applicable)

        Returns:
            Dict with AI analysis including:
            - exposure_summary: Overview of exposure
            - breach_context: Analysis of breach data
            - identity_footprint: Digital footprint analysis
            - recommendations: Security recommendations
            - urgency_score: Urgency of remediation (0-100)
        """
        prompt = self._build_credential_exposure_prompt(
            findings, target_email, target_username
        )

        analysis = self._query_ai(prompt, prefer_model="gemini")

        return self._parse_credential_exposure_analysis(analysis)

    def analyze_target_profile(
        self,
        findings: List[Dict[str, Any]],
        target_username: Optional[str] = None,
        target_email: Optional[str] = None
    ) -> Dict[str, Any]:
        """Analyze target profile findings with AI.

        Args:
            findings: List of target profile findings
            target_username: Target username (if applicable)
            target_email: Target email (if applicable)

        Returns:
            Dict with AI analysis including:
            - profile_summary: Comprehensive profile overview
            - behavioral_patterns: Identified behavioral patterns
            - social_footprint: Social media presence analysis
            - vulnerability_assessment: Social engineering vulnerability
            - recommendations: Security recommendations
        """
        prompt = self._build_target_profile_prompt(
            findings, target_username, target_email
        )

        analysis = self._query_ai(prompt, prefer_model="openai")

        return self._parse_target_profile_analysis(analysis)

    def _query_ai(
        self,
        prompt: str,
        prefer_model: str = "openai",
        max_tokens: int = 2000
    ) -> str:
        """Query AI model with fallback logic.

        Args:
            prompt: Analysis prompt
            prefer_model: Preferred model ('openai' or 'gemini')
            max_tokens: Maximum response tokens

        Returns:
            AI-generated analysis text
        """
        # Try preferred model first
        if prefer_model == "openai" and self.openai_client:
            try:
                response = self.openai_client.chat.completions.create(
                    model="gpt-4-turbo-preview",
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "You are an expert OSINT analyst and cybersecurity "
                                "professional. Provide detailed, actionable analysis "
                                "of intelligence findings. Format your response in "
                                "clear sections with markdown."
                            )
                        },
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=max_tokens,
                    temperature=0.7
                )
                return response.choices[0].message.content
            except Exception as e:
                logger.warning(f"OpenAI query failed, trying Gemini: {e}")

        if self.gemini_model:
            try:
                response = self.gemini_model.generate_content(prompt)
                return response.text
            except Exception as e:
                logger.error(f"Gemini query failed: {e}")

        # Fallback: If OpenAI was preferred but failed, try it again
        if prefer_model == "gemini" and self.openai_client:
            try:
                response = self.openai_client.chat.completions.create(
                    model="gpt-4-turbo-preview",
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "You are an expert OSINT analyst and cybersecurity "
                                "professional. Provide detailed, actionable analysis."
                            )
                        },
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=max_tokens,
                    temperature=0.7
                )
                return response.choices[0].message.content
            except Exception as e:
                logger.error(f"OpenAI fallback failed: {e}")

        return "AI analysis unavailable - API keys not configured or services down."

    def _build_attack_surface_prompt(
        self,
        findings: List[Dict[str, Any]],
        target: str
    ) -> str:
        """Build prompt for attack surface analysis."""
        findings_summary = "\n".join([
            f"- {f.get('finding_type', 'unknown')}: {f.get('target', 'N/A')} "
            f"[{f.get('severity', 'unknown')}]"
            for f in findings[:50]  # Limit to avoid token overflow
        ])

        return f"""Analyze the following attack surface findings for target: {target}

FINDINGS ({len(findings)} total):
{findings_summary}

Provide a comprehensive security analysis covering:

1. **EXECUTIVE SUMMARY** (2-3 sentences)
   - Overall security posture
   - Most critical concerns

2. **CRITICAL INSIGHTS** (Top 5 security issues)
   - Issue description
   - Why it matters
   - Severity level

3. **ATTACK VECTORS** (Identified attack paths)
   - How an attacker could exploit this
   - Prerequisites for exploitation
   - Potential impact

4. **RECOMMENDATIONS** (Prioritized by urgency)
   - Immediate actions (critical)
   - Short-term fixes (high priority)
   - Long-term hardening (medium priority)

5. **RISK ASSESSMENT**
   - Overall risk score (0-100)
   - Risk breakdown by category
   - Trend analysis

Format your response in markdown with clear headings."""

    def _build_credential_exposure_prompt(
        self,
        findings: List[Dict[str, Any]],
        target_email: Optional[str],
        target_username: Optional[str]
    ) -> str:
        """Build prompt for credential exposure analysis."""
        target_info = []
        if target_email:
            target_info.append(f"Email: {target_email}")
        if target_username:
            target_info.append(f"Username: {target_username}")

        findings_summary = "\n".join([
            f"- {f.get('finding_type', 'unknown')}: {f.get('details', {})}"
            for f in findings[:50]
        ])

        return f"""Analyze credential exposure for:
{chr(10).join(target_info)}

FINDINGS ({len(findings)} total):
{findings_summary}

Provide comprehensive credential intelligence analysis:

1. **EXPOSURE SUMMARY**
   - What has been exposed
   - Where it was found
   - Date ranges if available

2. **BREACH CONTEXT**
   - Which breaches/leaks
   - Severity of each breach
   - Credential types exposed

3. **IDENTITY FOOTPRINT**
   - Online presence analysis
   - Associated accounts
   - Patterns in credential use

4. **RECOMMENDATIONS**
   - Immediate security actions
   - Password policy improvements
   - Account monitoring setup

5. **URGENCY ASSESSMENT**
   - Urgency score (0-100)
   - Most critical actions
   - Timeline for remediation

Format in markdown."""

    def _build_target_profile_prompt(
        self,
        findings: List[Dict[str, Any]],
        target_username: Optional[str],
        target_email: Optional[str]
    ) -> str:
        """Build prompt for target profiling analysis."""
        target_info = []
        if target_username:
            target_info.append(f"Username: {target_username}")
        if target_email:
            target_info.append(f"Email: {target_email}")

        findings_summary = "\n".join([
            f"- {f.get('finding_type', 'unknown')}: {f.get('details', {})}"
            for f in findings[:50]
        ])

        return f"""Analyze target profile for:
{chr(10).join(target_info)}

FINDINGS ({len(findings)} total):
{findings_summary}

Provide comprehensive target profiling analysis:

1. **PROFILE SUMMARY**
   - Who is this person
   - Digital presence overview
   - Key identifying information

2. **BEHAVIORAL PATTERNS**
   - Online behavior patterns
   - Activity frequency
   - Platform preferences

3. **SOCIAL FOOTPRINT**
   - Social media presence
   - Network connections
   - Information sharing habits

4. **VULNERABILITY ASSESSMENT**
   - Social engineering risk (0-100)
   - Information leakage concerns
   - Security awareness level

5. **RECOMMENDATIONS**
   - Privacy improvements
   - Security hardening steps
   - OPSEC recommendations

Format in markdown."""

    def _parse_attack_surface_analysis(self, analysis: str) -> Dict[str, Any]:
        """Parse AI response for attack surface."""
        # Parses markdown sections from AI response
        # Structured extraction via _extract_section helper
        return {
            "raw_analysis": analysis,
            "executive_summary": self._extract_section(analysis, "EXECUTIVE SUMMARY"),
            "critical_insights": self._extract_section(analysis, "CRITICAL INSIGHTS"),
            "attack_vectors": self._extract_section(analysis, "ATTACK VECTORS"),
            "recommendations": self._extract_section(analysis, "RECOMMENDATIONS"),
            "risk_assessment": self._extract_section(analysis, "RISK ASSESSMENT"),
        }

    def _parse_credential_exposure_analysis(self, analysis: str) -> Dict[str, Any]:
        """Parse AI response for credential exposure."""
        return {
            "raw_analysis": analysis,
            "exposure_summary": self._extract_section(analysis, "EXPOSURE SUMMARY"),
            "breach_context": self._extract_section(analysis, "BREACH CONTEXT"),
            "identity_footprint": self._extract_section(analysis, "IDENTITY FOOTPRINT"),
            "recommendations": self._extract_section(analysis, "RECOMMENDATIONS"),
            "urgency_assessment": self._extract_section(analysis, "URGENCY ASSESSMENT"),
        }

    def _parse_target_profile_analysis(self, analysis: str) -> Dict[str, Any]:
        """Parse AI response for target profile."""
        return {
            "raw_analysis": analysis,
            "profile_summary": self._extract_section(analysis, "PROFILE SUMMARY"),
            "behavioral_patterns": self._extract_section(analysis, "BEHAVIORAL PATTERNS"),
            "social_footprint": self._extract_section(analysis, "SOCIAL FOOTPRINT"),
            "vulnerability_assessment": self._extract_section(
                analysis, "VULNERABILITY ASSESSMENT"
            ),
            "recommendations": self._extract_section(analysis, "RECOMMENDATIONS"),
        }

    def _extract_section(self, text: str, section_name: str) -> str:
        """Extract a section from markdown-formatted text."""
        lines = text.split('\n')
        section_lines = []
        in_section = False

        for line in lines:
            # Check if we're entering the target section
            if section_name.upper() in line.upper() and (
                line.startswith('#') or line.startswith('**')
            ):
                in_section = True
                continue

            # Check if we're entering a new section (exit current)
            if in_section and (
                (line.startswith('#') or line.startswith('**'))
                and section_name.upper() not in line.upper()
            ):
                break

            # Collect lines if in section
            if in_section and line.strip():
                section_lines.append(line)

        return '\n'.join(section_lines).strip() if section_lines else "Section not found"
