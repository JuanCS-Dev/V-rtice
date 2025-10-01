"""
IP Intelligence Connector - Enriquece detecções com dados reais de IP
================================================

Conecta ADR Core com IP Intelligence Service (porta 8000)
Adiciona contexto geográfico, ISP, ASN, reputation a ameaças detectadas.
"""

import httpx
import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class IPIntelligenceConnector:
    """
    Conector para IP Intelligence Service

    Enriquece ameaças detectadas com:
    - Geolocalização (país, cidade, coordenadas)
    - ISP e ASN
    - Reputation score
    - Threat level
    - Open ports
    - PTR records
    """

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=10.0)
        self.cache = {}  # Cache simples para evitar consultas duplicadas

    async def analyze_ip(self, ip: str) -> Optional[Dict[str, Any]]:
        """
        Analisa IP usando serviço de IP Intelligence

        Args:
            ip: Endereço IP a ser analisado

        Returns:
            Dados enriquecidos do IP ou None se falhar
        """
        # Verifica cache primeiro
        if ip in self.cache:
            logger.debug(f"Cache hit for IP: {ip}")
            return self.cache[ip]

        try:
            response = await self.client.post(
                f"{self.base_url}/api/ip/analyze",
                json={"ip": ip}
            )

            if response.status_code == 200:
                data = response.json()

                # Formata dados para ADR
                enriched = {
                    'ip': data.get('ip'),
                    'source': data.get('source'),  # 'cache' ou 'live'
                    'timestamp': data.get('timestamp'),

                    # Geolocation
                    'geolocation': {
                        'country': data.get('geolocation', {}).get('country'),
                        'region': data.get('geolocation', {}).get('regionName'),
                        'city': data.get('geolocation', {}).get('city'),
                        'lat': data.get('geolocation', {}).get('lat'),
                        'lon': data.get('geolocation', {}).get('lon'),
                        'isp': data.get('geolocation', {}).get('isp'),
                        'asn': data.get('geolocation', {}).get('as', '').split(' ')[0] if data.get('geolocation', {}).get('as') else None,
                    },

                    # Reputation
                    'reputation': {
                        'score': data.get('reputation', {}).get('score', 0),
                        'threat_level': data.get('reputation', {}).get('threat_level', 'unknown'),
                        'categories': data.get('reputation', {}).get('categories', []),
                    },

                    # Network
                    'ptr_record': data.get('ptr_record'),
                    'open_ports': data.get('open_ports', []),

                    # Metadata
                    'enriched_at': datetime.utcnow().isoformat(),
                    'enriched_by': 'ip_intelligence_service'
                }

                # Cache resultado
                self.cache[ip] = enriched

                logger.info(f"✅ IP {ip} enriched: {enriched['geolocation']['city']}, {enriched['geolocation']['country']}")

                return enriched
            else:
                logger.warning(f"IP Intelligence Service returned {response.status_code} for {ip}")
                return None

        except httpx.RequestError as e:
            logger.error(f"Failed to connect to IP Intelligence Service: {e}")
            return None
        except Exception as e:
            logger.error(f"Error enriching IP {ip}: {e}")
            return None

    async def enrich_threat_with_ip_context(self, threat: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enriquece uma ameaça detectada com contexto de IP Intelligence

        Args:
            threat: Objeto de ameaça do ADR

        Returns:
            Ameaça enriquecida com dados de IP
        """
        # Extrai IPs da ameaça
        ips_to_analyze = []

        # IP da fonte
        source = threat.get('source', '')
        if self._is_valid_ip(source):
            ips_to_analyze.append(source)

        # IPs nos indicadores
        for indicator in threat.get('indicators', []):
            potential_ip = self._extract_ip_from_indicator(indicator)
            if potential_ip and potential_ip not in ips_to_analyze:
                ips_to_analyze.append(potential_ip)

        # Analisa cada IP
        enriched_ips = {}
        for ip in ips_to_analyze:
            ip_data = await self.analyze_ip(ip)
            if ip_data:
                enriched_ips[ip] = ip_data

        # Adiciona ao threat
        threat['enriched_context'] = threat.get('enriched_context', {})
        threat['enriched_context']['ip_intelligence'] = enriched_ips

        # Atualiza threat_score baseado em reputation
        if enriched_ips:
            # Pega o pior score de reputation
            reputation_scores = [
                ip_data['reputation']['score']
                for ip_data in enriched_ips.values()
            ]
            if reputation_scores:
                worst_score = max(reputation_scores)

                # Ajusta threat_score original
                original_score = threat.get('threat_score', 0)
                adjusted_score = int((original_score + worst_score) / 2)

                threat['threat_score_original'] = original_score
                threat['threat_score'] = adjusted_score
                threat['threat_score_adjusted_by'] = 'ip_reputation'

                logger.info(f"🎯 Threat score adjusted: {original_score} → {adjusted_score} based on IP reputation")

        return threat

    def _is_valid_ip(self, text: str) -> bool:
        """Verifica se texto é um IP válido"""
        import re
        ipv4_pattern = r'^(?:\d{1,3}\.){3}\d{1,3}$'
        return bool(re.match(ipv4_pattern, text))

    def _extract_ip_from_indicator(self, indicator: str) -> Optional[str]:
        """Extrai IP de um indicador (ex: 'Destination: 1.2.3.4')"""
        import re
        ipv4_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
        match = re.search(ipv4_pattern, indicator)
        return match.group(0) if match else None

    async def get_my_ip(self) -> Optional[str]:
        """Detecta IP público do servidor ADR"""
        try:
            response = await self.client.get(f"{self.base_url}/api/ip/my-ip")
            if response.status_code == 200:
                data = response.json()
                return data.get('detected_ip')
        except Exception as e:
            logger.error(f"Failed to get my IP: {e}")
        return None

    async def close(self):
        """Fecha conexão HTTP"""
        await self.client.aclose()
