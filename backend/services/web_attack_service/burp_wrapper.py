# ============================================================================
# BURP SUITE PRO WRAPPER - Montoya API Integration
# AI-Powered Web Security Scanning
# ============================================================================

import asyncio
import base64
import logging
from datetime import datetime
from typing import Dict, List, Optional

import httpx

from services.web_attack_service.models import (
    BurpScanRequest,
    BurpScanResult,
    BurpVulnerability,
    Severity,
)

logger = logging.getLogger(__name__)


class BurpSuiteWrapper:
    """
    Burp Suite Professional API Wrapper

    Montoya API Integration:
    - REST API for scan control
    - AI-powered payload generation
    - Intelligent vulnerability analysis
    """

    def __init__(
        self,
        burp_api_url: str = "http://localhost:1337",
        burp_api_key: Optional[str] = None,
    ):
        self.burp_api_url = burp_api_url.rstrip("/")
        self.burp_api_key = burp_api_key
        self.headers = {"Content-Type": "application/json"}
        if burp_api_key:
            self.headers["X-API-Key"] = burp_api_key

    async def scan(self, request: BurpScanRequest, ai_copilot=None) -> BurpScanResult:
        """
        Execute Burp Suite scan

        Args:
            request: BurpScanRequest
            ai_copilot: Optional AI Co-Pilot for enhanced analysis

        Returns:
            BurpScanResult with findings
        """
        scan_id = self._generate_scan_id()
        start_time = datetime.now()

        logger.info(f"[{scan_id}] Starting Burp Suite scan: {request.target_url}")

        async with httpx.AsyncClient(timeout=600.0) as client:
            # Create scan task
            task_id = await self._create_scan_task(client, request)

            # Wait for completion
            await self._wait_for_scan(client, task_id)

            # Get results
            findings = await self._get_scan_results(client, task_id)

            # AI enhancement
            if ai_copilot and request.enable_ai_copilot:
                findings = await self._enhance_with_ai(findings, ai_copilot)

            # Get statistics
            stats = await self._get_scan_stats(client, task_id)

            duration = (datetime.now() - start_time).total_seconds()

            return BurpScanResult(
                scan_id=scan_id,
                target_url=str(request.target_url),
                scan_type=request.config.scan_type,
                vulnerabilities_found=len(findings),
                findings=findings,
                requests_made=stats.get("requests", 0),
                pages_crawled=stats.get("pages", 0),
                scan_duration=duration,
                timestamp=datetime.now(),
            )

    async def _create_scan_task(self, client: httpx.AsyncClient, request: BurpScanRequest) -> str:
        """Create Burp scan task via API"""
        payload = {
            "scan_configurations": [
                {
                    "type": request.config.scan_type.value,
                    "name": f"Scan {request.target_url}",
                }
            ],
            "urls": [str(request.target_url)],
            "scope": {"include": [{"rule": str(request.target_url), "type": "SimpleScopeDef"}]},
        }

        # Authentication
        if request.auth_type == "basic" and request.auth_credentials:
            user = request.auth_credentials.get("username")
            password = request.auth_credentials.get("password")
            auth_header = base64.b64encode(f"{user}:{password}".encode()).decode()
            payload["application_logins"] = [{"type": "basic", "username": user, "password": password}]

        response = await client.post(f"{self.burp_api_url}/v0.1/scan", headers=self.headers, json=payload)

        if response.status_code != 201:
            raise RuntimeError(f"Burp scan creation failed: {response.text}")

        return response.headers.get("Location", "").split("/")[-1]

    async def _wait_for_scan(self, client: httpx.AsyncClient, task_id: str, poll_interval: int = 5):
        """Wait for scan completion"""
        while True:
            response = await client.get(f"{self.burp_api_url}/v0.1/scan/{task_id}", headers=self.headers)

            if response.status_code != 200:
                raise RuntimeError(f"Failed to get scan status: {response.text}")

            status = response.json()
            scan_status = status.get("scan_status")

            logger.info(f"Scan {task_id} status: {scan_status}")

            if scan_status in ["succeeded", "failed"]:
                break

            await asyncio.sleep(poll_interval)

    async def _get_scan_results(self, client: httpx.AsyncClient, task_id: str) -> List[BurpVulnerability]:
        """Retrieve scan results"""
        response = await client.get(f"{self.burp_api_url}/v0.1/scan/{task_id}", headers=self.headers)

        if response.status_code != 200:
            raise RuntimeError(f"Failed to get scan results: {response.text}")

        data = response.json()
        issues = data.get("issue_events", [])

        vulnerabilities = []
        for issue in issues:
            vuln = self._parse_issue(issue)
            if vuln:
                vulnerabilities.append(vuln)

        return vulnerabilities

    def _parse_issue(self, issue: Dict) -> Optional[BurpVulnerability]:
        """Parse Burp issue into vulnerability model"""
        try:
            severity_map = {
                "high": Severity.HIGH,
                "medium": Severity.MEDIUM,
                "low": Severity.LOW,
                "information": Severity.INFO,
            }

            return BurpVulnerability(
                issue_type=issue.get("type_index", 0),
                issue_name=issue.get("issue_type", "Unknown"),
                severity=severity_map.get(issue.get("severity", "medium").lower(), Severity.MEDIUM),
                confidence=issue.get("confidence", "tentative"),
                url=issue.get("origin", ""),
                path=issue.get("path", ""),
                method=issue.get("method", "GET"),
                parameter=issue.get("issue_detail", {}).get("insertion_point"),
                request=(
                    base64.b64decode(issue.get("request", "")).decode("utf-8", errors="ignore")
                    if issue.get("request")
                    else ""
                ),
                response=(
                    base64.b64decode(issue.get("response", "")).decode("utf-8", errors="ignore")
                    if issue.get("response")
                    else ""
                ),
                evidence=issue.get("evidence"),
                timestamp=datetime.now(),
            )

        except Exception as e:
            logger.warning(f"Failed to parse Burp issue: {str(e)}")
            return None

    async def _enhance_with_ai(self, findings: List[BurpVulnerability], ai_copilot) -> List[BurpVulnerability]:
        """Enhance findings with AI analysis"""
        for finding in findings:
            try:
                # Prepare context
                context = {
                    "vulnerability": finding.issue_name,
                    "url": finding.url,
                    "parameter": finding.parameter,
                    "evidence": finding.evidence,
                }

                # Get AI analysis
                analysis_text = await ai_copilot.analyze_vulnerability_context(
                    http_request={"url": finding.url, "method": finding.method},
                    http_response={"body": finding.response[:500]},
                    suspected_vuln=finding.issue_type,
                )

                finding.ai_analysis = {"analysis": analysis_text}
                finding.ai_recommendations = self._extract_recommendations(analysis_text)

            except Exception as e:
                logger.warning(f"AI enhancement failed for finding: {str(e)}")

        return findings

    def _extract_recommendations(self, analysis_text: str) -> List[str]:
        """Extract recommendations from AI analysis"""
        recommendations = []
        lines = analysis_text.split("\n")

        for line in lines:
            if any(keyword in line.lower() for keyword in ["recommend", "should", "fix"]):
                cleaned = line.strip("- *#").strip()
                if len(cleaned) > 20:
                    recommendations.append(cleaned)

        return recommendations[:3]

    async def _get_scan_stats(self, client: httpx.AsyncClient, task_id: str) -> Dict:
        """Get scan statistics"""
        response = await client.get(f"{self.burp_api_url}/v0.1/scan/{task_id}", headers=self.headers)

        if response.status_code != 200:
            return {"requests": 0, "pages": 0}

        data = response.json()
        scan_metrics = data.get("scan_metrics", {})

        return {
            "requests": scan_metrics.get("requests_made", 0),
            "pages": scan_metrics.get("crawled_pages", 0),
        }

    def _generate_scan_id(self) -> str:
        """Generate unique scan ID"""
        import uuid

        return f"burp_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
