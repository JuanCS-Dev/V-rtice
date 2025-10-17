"""Maximus Web Attack Service - OWASP ZAP Wrapper.

This module provides a wrapper for integrating the Maximus AI's Web Attack
Service with OWASP ZAP (Zed Attack Proxy). ZAP is a free, open-source
penetration testing tool for finding vulnerabilities in web applications.

This wrapper allows Maximus to programmatically initiate various types of ZAP
scans (e.g., spider, active scan, AJAX spider), configure scan policies,
handle authentication, and retrieve detailed vulnerability alerts. It is crucial
for automated web application security testing, continuous monitoring, and
identifying web-specific attack vectors.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional

from zapv2 import ZAPv2

from backend.services.web_attack_service.models import ScanType, Severity, ZAPAlert, ZAPScanRequest, ZAPScanResult

logger = logging.getLogger(__name__)


class ZAPWrapper:
    """
    OWASP ZAP API Wrapper

    Automation Framework:
    - Spider + Active scan
    - Custom scan policies
    - Alert de-duplication
    """

    def __init__(
        self,
        zap_api_url: str = "http://localhost:8080",
        zap_api_key: Optional[str] = None,
    ):
        """Inicializa o ZAPWrapper.

        Args:
            zap_api_url (str): A URL da API do ZAP.
            zap_api_key (Optional[str]): A chave da API do ZAP para autenticação.
        """
        self.zap = ZAPv2(apikey=zap_api_key, proxies={"http": zap_api_url, "https": zap_api_url})

    async def scan(self, request: ZAPScanRequest) -> ZAPScanResult:
        """
        Execute ZAP scan

        Args:
            request: ZAPScanRequest

        Returns:
            ZAPScanResult with alerts
        """
        scan_id = self._generate_scan_id()
        start_time = datetime.now()
        target_url = str(request.target_url)

        logger.info(f"[{scan_id}] Starting ZAP scan: {target_url}")

        # Create context
        context_id = await self._create_context(request)

        # Configure authentication
        if request.auth_method:
            await self._configure_auth(request, context_id)

        # Execute scan based on type
        if request.scan_type == ScanType.SPIDER:
            await self._spider_scan(target_url, request)
        elif request.scan_type == ScanType.AJAX_SPIDER:
            await self._ajax_spider_scan(target_url, request)
        elif request.scan_type == ScanType.ACTIVE:
            await self._spider_scan(target_url, request)  # Spider first
            await self._active_scan(target_url, request, context_id)
        else:
            await self._active_scan(target_url, request, context_id)

        # Get results
        alerts = await self._get_alerts(target_url)

        # Statistics
        urls_found = len(self.zap.core.urls(target_url))
        duration = (datetime.now() - start_time).total_seconds()

        return ZAPScanResult(
            scan_id=scan_id,
            target_url=target_url,
            scan_type=request.scan_type,
            alerts_count=len(alerts),
            alerts=alerts,
            urls_found=urls_found,
            scan_duration=duration,
            timestamp=datetime.now(),
        )

    async def _create_context(self, request: ZAPScanRequest) -> str:
        """Cria e configura um contexto ZAP para a varredura.

        Args:
            request (ZAPScanRequest): O objeto de requisição de varredura ZAP.

        Returns:
            str: O ID do contexto ZAP criado.
        """
        context_name = request.context_name or "default_context"

        # Create context
        context_id = await asyncio.to_thread(self.zap.context.new_context, contextname=context_name)

        # Include URLs
        if request.include_in_context:
            for pattern in request.include_in_context:
                await asyncio.to_thread(
                    self.zap.context.include_in_context,
                    contextname=context_name,
                    regex=pattern,
                )

        # Exclude URLs
        if request.exclude_from_context:
            for pattern in request.exclude_from_context:
                await asyncio.to_thread(
                    self.zap.context.exclude_from_context,
                    contextname=context_name,
                    regex=pattern,
                )

        return context_id

    async def _configure_auth(self, request: ZAPScanRequest, context_id: str):
        """Configura a autenticação para o ZAP com base nos detalhes da requisição.

        Args:
            request (ZAPScanRequest): O objeto de requisição de varredura ZAP.
            context_id (str): O ID do contexto ZAP.
        """
        if request.auth_method == "form" and request.login_url:
            await asyncio.to_thread(
                self.zap.authentication.set_authentication_method,
                contextid=context_id,
                authmethodname="formBasedAuthentication",
                authmethodconfigparams=f"loginUrl={request.login_url}",
            )

        # Set credentials
        if request.username and request.password:
            await asyncio.to_thread(self.zap.users.new_user, contextid=context_id, name="test_user")

            await asyncio.to_thread(
                self.zap.users.set_authentication_credentials,
                contextid=context_id,
                userid="1",
                authcredentialsconfigparams=f"username={request.username}&password={request.password}",
            )

    async def _spider_scan(self, target_url: str, request: ZAPScanRequest):
        """Executa uma varredura spider do ZAP no URL alvo.

        Args:
            target_url (str): O URL alvo para a varredura spider.
            request (ZAPScanRequest): O objeto de requisição de varredura ZAP.
        """
        logger.info(f"Starting spider on {target_url}")

        scan_id = await asyncio.to_thread(
            self.zap.spider.scan,
            url=target_url,
            maxchildren=request.max_children,
            recurse=request.recurse,
            subtreeonly=request.subtree_only,
        )

        # Wait for completion
        while int(self.zap.spider.status(scan_id)) < 100:
            await asyncio.sleep(2)

        logger.info("Spider scan complete")

    async def _ajax_spider_scan(self, target_url: str, request: ZAPScanRequest):
        """Executa uma varredura AJAX spider do ZAP no URL alvo.

        Args:
            target_url (str): O URL alvo para a varredura AJAX spider.
            request (ZAPScanRequest): O objeto de requisição de varredura ZAP.
        """
        logger.info(f"Starting AJAX spider on {target_url}")

        await asyncio.to_thread(self.zap.ajaxSpider.scan, url=target_url, inscope="true")

        # Wait for completion
        while self.zap.ajaxSpider.status == "running":
            await asyncio.sleep(2)

        logger.info("AJAX spider complete")

    async def _active_scan(self, target_url: str, request: ZAPScanRequest, context_id: str):
        """Executa uma varredura ativa do ZAP no URL alvo.

        Args:
            target_url (str): O URL alvo para a varredura ativa.
            request (ZAPScanRequest): O objeto de requisição de varredura ZAP.
            context_id (str): O ID do contexto ZAP.
        """
        logger.info(f"Starting active scan on {target_url}")

        # Configure policy
        policy_name = request.policy.policy_name
        await asyncio.to_thread(
            self.zap.ascan.set_policy_attack_strength,
            scanpolicyname=policy_name,
            attackstrength=request.policy.attack_strength,
        )

        await asyncio.to_thread(
            self.zap.ascan.set_policy_alert_threshold,
            scanpolicyname=policy_name,
            alertthreshold=request.policy.alert_threshold,
        )

        # Start scan
        scan_id = await asyncio.to_thread(
            self.zap.ascan.scan,
            url=target_url,
            scanpolicyname=policy_name,
            contextid=context_id,
        )

        # Wait for completion
        while int(self.zap.ascan.status(scan_id)) < 100:
            progress = self.zap.ascan.status(scan_id)
            logger.info(f"Active scan progress: {progress}%")
            await asyncio.sleep(5)

        logger.info("Active scan complete")

    async def _get_alerts(self, target_url: str) -> List[ZAPAlert]:
        """Obtém os alertas de varredura do ZAP para o URL alvo.

        Args:
            target_url (str): O URL alvo da varredura.

        Returns:
            List[ZAPAlert]: Uma lista de objetos ZAPAlert.
        """
        alerts_data = await asyncio.to_thread(self.zap.core.alerts, baseurl=target_url)

        alerts = []
        for alert_data in alerts_data:
            alert = self._parse_alert(alert_data)
            if alert:
                alerts.append(alert)

        return alerts

    def _parse_alert(self, alert_data: Dict) -> Optional[ZAPAlert]:
        """Analisa um dicionário de dados de alerta ZAP bruto em um objeto ZAPAlert.

        Args:
            alert_data (Dict): O dicionário de dados de alerta bruto do ZAP.

        Returns:
            Optional[ZAPAlert]: Um objeto ZAPAlert preenchido, ou None se a análise falhar.
        """
        try:
            risk_map = {
                "High": Severity.HIGH,
                "Medium": Severity.MEDIUM,
                "Low": Severity.LOW,
                "Informational": Severity.INFO,
            }

            return ZAPAlert(
                alert_id=int(alert_data.get("id", 0)),
                plugin_id=int(alert_data.get("pluginId", 0)),
                alert_name=alert_data.get("alert", "Unknown"),
                risk=risk_map.get(alert_data.get("risk", "Medium"), Severity.MEDIUM),
                confidence=alert_data.get("confidence", "Medium"),
                url=alert_data.get("url", ""),
                method=alert_data.get("method", "GET"),
                param=alert_data.get("param"),
                attack=alert_data.get("attack"),
                evidence=alert_data.get("evidence"),
                description=alert_data.get("description", ""),
                solution=alert_data.get("solution", ""),
                reference=alert_data.get("reference", ""),
                cwe_id=(int(alert_data.get("cweid", 0)) if alert_data.get("cweid") else None),
                wasc_id=(int(alert_data.get("wascid", 0)) if alert_data.get("wascid") else None),
                timestamp=datetime.now(),
            )

        except Exception as e:
            logger.warning(f"Failed to parse ZAP alert: {str(e)}")
            return None

    def _generate_scan_id(self) -> str:
        """Gera um ID de varredura único para identificar uma varredura ZAP.

        Returns:
            str: Um ID de varredura único formatado.
        """
        import uuid

        return f"zap_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
