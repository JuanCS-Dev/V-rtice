"""
Slack Notification Plugin
=========================

Send real-time notifications to Slack channels.

Installation:
    pip install slack-sdk

Configuration:
    ~/.vertice/config.yaml:
        plugins:
          slack:
            webhook_url: https://hooks.slack.com/services/YOUR/WEBHOOK/URL
            notify_on_critical: true
            notify_on_scan_complete: true

Usage:
    vcli plugin enable slack

    # Notifications sent automatically
    vcli scan nmap 10.10.1.0/24
    # → Slack notification when scan completes

Author: example@vertice.dev
License: MIT
"""

from typing import Dict, Any
import logging
import requests

from vertice.plugins import BasePlugin, hook, HookPriority

logger = logging.getLogger(__name__)


class SlackNotificationPlugin(BasePlugin):
    """
    Slack notification integration.

    Hooks into:
    - on_vulnerability_found: Alert on critical vulns
    - on_scan_complete: Scan completion notifications
    - on_project_created: Project tracking
    """

    # Metadata
    name = "slack"
    version = "1.0.0"
    author = "vertice-community"
    description = "Send notifications to Slack"
    homepage = "https://github.com/vertice-plugins/slack"
    dependencies = []  # Using requests (already available)
    vertice_min_version = "1.0.0"

    def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize Slack webhook."""
        super().initialize(config)

        self.webhook_url = config.get("webhook_url")

        if not self.webhook_url:
            raise ValueError("Slack plugin requires 'webhook_url' in config")

        self.notify_on_critical = config.get("notify_on_critical", True)
        self.notify_on_scan_complete = config.get("notify_on_scan_complete", True)

        logger.info("Slack notification plugin initialized")

    def _send_message(self, message: str, color: str = "good") -> bool:
        """
        Send message to Slack.

        Args:
            message: Message text
            color: Attachment color (good, warning, danger)

        Returns:
            True if sent successfully
        """
        try:
            payload = {
                "attachments": [
                    {
                        "color": color,
                        "text": message,
                        "footer": "Vértice CLI",
                    }
                ]
            }

            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=10
            )

            response.raise_for_status()

            logger.debug(f"Slack message sent: {message[:50]}...")

            return True

        except Exception as e:
            logger.error(f"Failed to send Slack message: {e}")
            return False

    @hook("on_vulnerability_found", priority=HookPriority.HIGH)
    def alert_critical_vuln(self, context):
        """
        Alert on critical vulnerabilities.

        Args:
            context: HookContext with vulnerability data
        """
        if not self.notify_on_critical:
            return

        vuln = context.data.get("vulnerability")

        if not vuln:
            return

        severity = getattr(vuln, "severity", "unknown")

        if severity != "critical":
            return

        # Send alert
        cve_id = getattr(vuln, "cve_id", "Unknown")
        title = getattr(vuln, "title", "Unknown Vulnerability")

        message = (
            f"🚨 *Critical Vulnerability Found*\n"
            f"• CVE: {cve_id}\n"
            f"• Title: {title}\n"
            f"• Severity: CRITICAL"
        )

        self._send_message(message, color="danger")

        logger.info(f"Slack alert sent for {cve_id}")

    @hook("on_scan_complete", priority=HookPriority.LOW)
    def notify_scan_complete(self, context):
        """
        Notify when scan completes.

        Args:
            context: HookContext with scan results
        """
        if not self.notify_on_scan_complete:
            return

        scan_result = context.data.get("scan_result")

        if not scan_result:
            return

        # Extract summary
        target = getattr(scan_result, "target", "Unknown")
        hosts_found = getattr(scan_result, "hosts_found", 0)

        message = (
            f"✅ *Scan Complete*\n"
            f"• Target: {target}\n"
            f"• Hosts Found: {hosts_found}"
        )

        self._send_message(message, color="good")

        logger.info("Slack notification sent for scan completion")

    @hook("on_project_created")
    def track_project(self, context):
        """
        Track project creation.

        Args:
            context: HookContext with project data
        """
        project = context.data.get("project")

        if not project:
            return

        project_name = getattr(project, "name", "Unknown")
        scope = getattr(project, "scope", "N/A")

        message = (
            f"📁 *New Project Created*\n"
            f"• Name: {project_name}\n"
            f"• Scope: {scope}"
        )

        self._send_message(message, color="#439FE0")

        logger.info(f"Slack notification sent for project: {project_name}")
