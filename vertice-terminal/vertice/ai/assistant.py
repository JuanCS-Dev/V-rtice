"""
Maximus Assistant
==================

AI-powered assistant for workspace queries, vulnerability correlation,
and intelligent suggestions.

Capabilities:
- Natural language workspace queries
- CVE/ExploitDB correlation
- Context-aware next-step suggestions
- Automatic report generation
"""

import logging
import re
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class MaximusAssistant:
    """
    Intelligent assistant for security operations.

    Features:
    - NL queries: "show all web servers" → SQL
    - CVE correlation: Apache 2.4.41 → CVE-2021-44228
    - Smart suggestions: Analyze workspace → recommend next actions
    - Report generation: Workspace → PDF/HTML/Markdown
    """

    def __init__(self, workspace_manager=None):
        """
        Initialize Maximus Assistant.

        Args:
            workspace_manager: WorkspaceManager instance for data access
        """
        self.workspace_manager = workspace_manager
        self.query_parser = NaturalLanguageQueryParser()
        self.cve_correlator = CVECorrelator()
        self.suggestion_engine = SuggestionEngine()
        self.report_generator = ReportGenerator()

    def query_nl(self, question: str) -> Dict[str, Any]:
        """
        Execute natural language query on workspace.

        Args:
            question: Natural language question

        Returns:
            Query results dict with data and metadata

        Examples:
            >>> assistant.query_nl("show all web servers")
            {
                "question": "show all web servers",
                "parsed_query": {"type": "filter", "service": "http"},
                "results": [
                    {"ip": "10.10.1.5", "port": 80, "service": "http"},
                    {"ip": "10.10.1.6", "port": 443, "service": "https"}
                ],
                "count": 2
            }

            >>> assistant.query_nl("what hosts have critical vulns?")
            {
                "question": "what hosts have critical vulns?",
                "parsed_query": {"type": "filter", "severity": "critical"},
                "results": [
                    {"ip": "10.10.1.5", "vulnerabilities": 3},
                    {"ip": "10.10.1.10", "vulnerabilities": 1}
                ],
                "count": 2
            }
        """
        logger.info(f"Processing NL query: {question}")

        # Parse natural language to structured query
        parsed = self.query_parser.parse(question)

        if not parsed:
            return {
                "question": question,
                "error": "Could not understand question",
                "suggestions": [
                    "Try: 'show all web servers'",
                    "Try: 'what hosts have critical vulns?'",
                    "Try: 'find SSH with weak auth'"
                ]
            }

        # Execute query on workspace
        if self.workspace_manager:
            results = self._execute_query(parsed)
        else:
            # Mock results for testing
            results = []

        return {
            "question": question,
            "parsed_query": parsed,
            "results": results,
            "count": len(results)
        }

    def correlate_vulns(self, service: str, version: str) -> List[Dict[str, Any]]:
        """
        Auto-lookup CVE/ExploitDB for service version.

        Args:
            service: Service name (e.g., "Apache", "OpenSSH")
            version: Version string (e.g., "2.4.41", "8.2p1")

        Returns:
            List of CVEs and exploits

        Example:
            >>> assistant.correlate_vulns("Apache", "2.4.41")
            [
                {
                    "cve_id": "CVE-2021-44228",
                    "severity": "critical",
                    "description": "Apache Log4j RCE",
                    "exploits": [
                        {"source": "ExploitDB", "id": "50592"},
                        {"source": "Metasploit", "module": "exploit/multi/http/log4shell"}
                    ]
                }
            ]
        """
        logger.info(f"Correlating vulnerabilities for {service} {version}")

        # Use CVE correlator to find vulnerabilities
        vulnerabilities = self.cve_correlator.find_cves(service, version)

        return vulnerabilities

    def suggest_next_steps(self, context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Context-aware suggestions for next actions.

        Args:
            context: Workspace context (optional, will fetch if not provided)

        Returns:
            List of suggested actions with reasoning

        Example:
            >>> assistant.suggest_next_steps()
            [
                {
                    "action": "vcli scan nuclei 10.10.1.5 --severity critical",
                    "reason": "Found Apache 2.4.41 with known critical CVEs",
                    "priority": "high",
                    "estimated_time": "5 minutes"
                },
                {
                    "action": "vcli autopilot pentest 10.10.1.0/24 --depth full",
                    "reason": "Only 3/256 hosts scanned so far",
                    "priority": "medium",
                    "estimated_time": "30 minutes"
                }
            ]
        """
        logger.info("Generating context-aware suggestions")

        # Get workspace context if not provided
        if context is None and self.workspace_manager:
            context = self._get_workspace_context()
        elif context is None:
            context = {}

        # Use suggestion engine to generate recommendations
        suggestions = self.suggestion_engine.generate(context)

        return suggestions

    def generate_report(
        self,
        format: str = "markdown",
        include_sections: Optional[List[str]] = None
    ) -> str:
        """
        Generate report from workspace data.

        Args:
            format: Output format (markdown, html, pdf, json)
            include_sections: List of sections to include

        Returns:
            Formatted report string

        Example:
            >>> report = assistant.generate_report(format="markdown")
            >>> print(report)
            # Penetration Test Report
            ## Executive Summary
            - Hosts scanned: 5
            - Critical vulnerabilities: 3
            - High vulnerabilities: 7
            ...
        """
        logger.info(f"Generating {format} report")

        # Get workspace data
        if self.workspace_manager:
            data = self._get_workspace_data()
        else:
            data = {}

        # Generate report
        report = self.report_generator.generate(
            data=data,
            format=format,
            include_sections=include_sections
        )

        return report

    def _execute_query(self, parsed_query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Execute parsed query on workspace.

        Args:
            parsed_query: Structured query from parser

        Returns:
            Query results
        """
        query_type = parsed_query.get("type")

        if query_type == "filter":
            return self._execute_filter_query(parsed_query)
        elif query_type == "aggregate":
            return self._execute_aggregate_query(parsed_query)
        elif query_type == "search":
            return self._execute_search_query(parsed_query)
        else:
            return []

    def _execute_filter_query(self, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Execute filter-type query."""
        # TODO: Integrate with WorkspaceManager
        # For now, return mock data
        return []

    def _execute_aggregate_query(self, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Execute aggregate-type query."""
        # TODO: Integrate with WorkspaceManager
        return []

    def _execute_search_query(self, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Execute search-type query."""
        # TODO: Integrate with WorkspaceManager
        return []

    def _get_workspace_context(self) -> Dict[str, Any]:
        """Get current workspace context for suggestions."""
        if not self.workspace_manager:
            return {}

        # TODO: Integrate with WorkspaceManager
        # Get stats: hosts, vulns, services, etc.
        return {
            "total_hosts": 0,
            "scanned_hosts": 0,
            "total_vulns": 0,
            "critical_vulns": 0,
            "services": []
        }

    def _get_workspace_data(self) -> Dict[str, Any]:
        """Get all workspace data for reporting."""
        if not self.workspace_manager:
            return {}

        # TODO: Integrate with WorkspaceManager
        return {
            "hosts": [],
            "vulnerabilities": [],
            "services": [],
            "credentials": []
        }


class NaturalLanguageQueryParser:
    """
    Parses natural language questions into structured queries.

    Supports patterns like:
    - "show all web servers" → filter by service=http/https
    - "what hosts have critical vulns?" → filter by severity=critical
    - "find SSH with weak auth" → filter by service=ssh + auth_type=weak
    - "how many hosts are up?" → aggregate count
    """

    def __init__(self):
        """Initialize parser with query patterns."""
        self.patterns = self._build_patterns()

    def parse(self, question: str) -> Optional[Dict[str, Any]]:
        """
        Parse natural language question.

        Args:
            question: Natural language question

        Returns:
            Structured query dict or None if unparseable
        """
        question = question.lower().strip()

        # Try each pattern
        for pattern, handler in self.patterns:
            match = re.match(pattern, question)
            if match:
                return handler(match)

        return None

    def _build_patterns(self) -> List[tuple]:
        """Build regex patterns for query parsing."""
        return [
            # "show all web servers"
            (r"show all (web|http|https) servers?", self._parse_service_filter),

            # "show all SSH servers"
            (r"show all ssh servers?", lambda m: {
                "type": "filter",
                "service": "ssh"
            }),

            # "what hosts have critical vulns?"
            (r"what hosts have (critical|high|medium|low) vuln", self._parse_severity_filter),

            # "find SSH with weak auth"
            (r"find ssh with weak auth", lambda m: {
                "type": "filter",
                "service": "ssh",
                "weak_auth": True
            }),

            # "how many hosts are up?"
            (r"how many hosts", lambda m: {
                "type": "aggregate",
                "field": "hosts",
                "function": "count"
            }),

            # "list all vulnerabilities"
            (r"list all vuln", lambda m: {
                "type": "filter",
                "entity": "vulnerabilities"
            }),

            # "show hosts with port 22 open"
            (r"show hosts with port (\d+) open", self._parse_port_filter),
        ]

    def _parse_service_filter(self, match) -> Dict[str, Any]:
        """Parse service filter queries."""
        service_type = match.group(1)

        if service_type in ["web", "http", "https"]:
            return {
                "type": "filter",
                "service": ["http", "https"]
            }

        return {
            "type": "filter",
            "service": service_type
        }

    def _parse_severity_filter(self, match) -> Dict[str, Any]:
        """Parse severity filter queries."""
        severity = match.group(1)

        return {
            "type": "filter",
            "entity": "hosts",
            "has_vulns": True,
            "severity": severity
        }

    def _parse_port_filter(self, match) -> Dict[str, Any]:
        """Parse port filter queries."""
        port = int(match.group(1))

        return {
            "type": "filter",
            "entity": "hosts",
            "port": port,
            "port_state": "open"
        }


class CVECorrelator:
    """
    Correlates services/versions with CVEs and exploits.

    Data sources:
    - NVD (National Vulnerability Database)
    - ExploitDB
    - Metasploit modules
    """

    def __init__(self):
        """Initialize correlator."""
        # TODO: Load CVE database
        self.cve_db = {}

    def find_cves(self, service: str, version: str) -> List[Dict[str, Any]]:
        """
        Find CVEs for service version.

        Args:
            service: Service name
            version: Version string

        Returns:
            List of CVEs with exploits
        """
        # Mock data for demonstration
        # TODO: Integrate with real CVE database
        if "apache" in service.lower() and "2.4" in version:
            return [
                {
                    "cve_id": "CVE-2021-44228",
                    "severity": "critical",
                    "cvss": 10.0,
                    "description": "Apache Log4j Remote Code Execution",
                    "published": "2021-12-10",
                    "exploits": [
                        {
                            "source": "ExploitDB",
                            "id": "50592",
                            "title": "Apache Log4j 2.x - RCE",
                            "url": "https://www.exploit-db.com/exploits/50592"
                        },
                        {
                            "source": "Metasploit",
                            "module": "exploit/multi/http/log4shell_header_injection",
                            "rank": "excellent"
                        }
                    ]
                }
            ]

        return []


class SuggestionEngine:
    """
    Generates context-aware suggestions for next actions.

    Analyzes workspace state and recommends:
    - What to scan next
    - Which vulnerabilities to exploit
    - Security hardening steps
    """

    def generate(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate suggestions based on context.

        Args:
            context: Workspace context

        Returns:
            List of suggested actions
        """
        suggestions = []

        # Suggest deeper scanning if coverage is low
        total_hosts = context.get("total_hosts", 0)
        scanned_hosts = context.get("scanned_hosts", 0)

        if total_hosts > 0 and scanned_hosts < total_hosts * 0.5:
            suggestions.append({
                "action": "vcli autopilot pentest <network> --depth full",
                "reason": f"Only {scanned_hosts}/{total_hosts} hosts scanned",
                "priority": "medium",
                "estimated_time": "30 minutes"
            })

        # Suggest vulnerability scanning if critical CVEs found
        critical_vulns = context.get("critical_vulns", 0)

        if critical_vulns > 0:
            suggestions.append({
                "action": "vcli scan nuclei <targets> --severity critical",
                "reason": f"Found {critical_vulns} critical vulnerabilities",
                "priority": "high",
                "estimated_time": "10 minutes"
            })

        # Suggest SIEM integration if many findings
        total_vulns = context.get("total_vulns", 0)

        if total_vulns > 10:
            suggestions.append({
                "action": "vcli siem connectors sync elasticsearch --workspace <workspace>",
                "reason": f"Forward {total_vulns} findings to SIEM for correlation",
                "priority": "low",
                "estimated_time": "2 minutes"
            })

        return suggestions


class ReportGenerator:
    """
    Generates reports in multiple formats.

    Supported formats:
    - Markdown
    - HTML
    - PDF (via markdown → HTML → PDF)
    - JSON
    """

    def generate(
        self,
        data: Dict[str, Any],
        format: str = "markdown",
        include_sections: Optional[List[str]] = None
    ) -> str:
        """
        Generate report.

        Args:
            data: Workspace data
            format: Output format
            include_sections: Sections to include

        Returns:
            Formatted report
        """
        if format == "markdown":
            return self._generate_markdown(data, include_sections)
        elif format == "html":
            return self._generate_html(data, include_sections)
        elif format == "json":
            return self._generate_json(data, include_sections)
        else:
            raise ValueError(f"Unsupported format: {format}")

    def _generate_markdown(
        self,
        data: Dict[str, Any],
        include_sections: Optional[List[str]]
    ) -> str:
        """Generate Markdown report."""
        report = []

        # Title
        report.append("# Penetration Test Report")
        report.append(f"\n**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        # Executive Summary
        if not include_sections or "summary" in include_sections:
            report.append("## Executive Summary\n")
            report.append(f"- **Hosts scanned**: {len(data.get('hosts', []))}")
            report.append(f"- **Vulnerabilities found**: {len(data.get('vulnerabilities', []))}")
            report.append(f"- **Services identified**: {len(data.get('services', []))}\n")

        # Findings by Severity
        if not include_sections or "findings" in include_sections:
            report.append("## Findings by Severity\n")
            vulns = data.get('vulnerabilities', [])

            # Group by severity
            by_severity = {}
            for vuln in vulns:
                severity = vuln.get('severity', 'unknown')
                by_severity.setdefault(severity, []).append(vuln)

            for severity in ['critical', 'high', 'medium', 'low', 'info']:
                count = len(by_severity.get(severity, []))
                report.append(f"- **{severity.capitalize()}**: {count}")

        # Recommendations
        if not include_sections or "recommendations" in include_sections:
            report.append("\n## Recommendations\n")
            report.append("1. Patch critical vulnerabilities immediately")
            report.append("2. Implement network segmentation")
            report.append("3. Enable logging and monitoring")

        return "\n".join(report)

    def _generate_html(
        self,
        data: Dict[str, Any],
        include_sections: Optional[List[str]]
    ) -> str:
        """Generate HTML report."""
        # Convert markdown to HTML
        markdown = self._generate_markdown(data, include_sections)

        # Process markdown for HTML (cannot use backslashes in f-string)
        content = markdown.replace('#', 'h').replace('\n', '<br>')

        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Penetration Test Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        h1 {{ color: #333; }}
        h2 {{ color: #666; border-bottom: 2px solid #ddd; padding-bottom: 10px; }}
    </style>
</head>
<body>
    {content}
</body>
</html>
"""

        return html

    def _generate_json(
        self,
        data: Dict[str, Any],
        include_sections: Optional[List[str]]
    ) -> str:
        """Generate JSON report."""
        import json

        report_data = {
            "generated_at": datetime.now().isoformat(),
            "hosts": data.get("hosts", []),
            "vulnerabilities": data.get("vulnerabilities", []),
            "services": data.get("services", [])
        }

        return json.dumps(report_data, indent=2)
