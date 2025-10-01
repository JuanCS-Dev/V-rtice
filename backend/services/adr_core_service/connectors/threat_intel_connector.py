"""
Threat Intelligence Connector - Enriquece detecções com threat intel
=====================================================================

Conecta ADR Core com Threat Intel Service (porta 8013)
Adiciona contexto de ameaças conhecidas, malware families, IOCs.
"""

import httpx
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)


class ThreatIntelConnector:
    """
    Conector para Threat Intelligence Service

    Enriquece ameaças com:
    - Threat score agregado (offline engine + APIs externas)
    - Malware family identification
    - IOC correlation
    - Reputation (clean, suspicious, malicious)
    - Recommendations de resposta
    """

    def __init__(self, base_url: str = "http://localhost:8013"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=15.0)
        self.cache = {}

    async def check_threat(
        self,
        target: str,
        target_type: str = "auto"
    ) -> Optional[Dict[str, Any]]:
        """
        Verifica ameaça usando Threat Intel Service

        Args:
            target: IP, domain, hash, ou URL
            target_type: 'auto', 'ip', 'domain', 'hash', 'url'

        Returns:
            Dados de threat intelligence ou None
        """
        cache_key = f"{target}:{target_type}"

        if cache_key in self.cache:
            logger.debug(f"Cache hit for threat: {target}")
            return self.cache[cache_key]

        try:
            response = await self.client.post(
                f"{self.base_url}/api/threat-intel/check",
                json={
                    "target": target,
                    "target_type": target_type
                }
            )

            if response.status_code == 200:
                data = response.json()

                enriched = {
                    'target': data.get('target'),
                    'target_type': data.get('target_type'),

                    # Threat Assessment
                    'threat_score': data.get('threat_score', 0),
                    'is_malicious': data.get('is_malicious', False),
                    'confidence': data.get('confidence', 'low'),
                    'reputation': data.get('reputation', 'unknown'),

                    # Categories & TTPs
                    'categories': data.get('categories', []),
                    'mitre_tactics': self._extract_mitre_tactics(data),

                    # Sources
                    'sources': data.get('sources', {}),
                    'sources_available': [
                        source for source, info in data.get('sources', {}).items()
                        if info.get('available')
                    ],

                    # Recommendations
                    'recommendations': data.get('recommendations', []),

                    # Timeline
                    'first_seen': data.get('first_seen'),
                    'last_seen': data.get('last_seen'),

                    # Metadata
                    'enriched_at': datetime.utcnow().isoformat(),
                    'enriched_by': 'threat_intel_service'
                }

                self.cache[cache_key] = enriched

                logger.info(
                    f"🎯 Threat intel for {target}: "
                    f"Score={enriched['threat_score']}, "
                    f"Malicious={enriched['is_malicious']}, "
                    f"Reputation={enriched['reputation']}"
                )

                return enriched
            else:
                logger.warning(f"Threat Intel Service returned {response.status_code} for {target}")
                return None

        except httpx.RequestError as e:
            logger.error(f"Failed to connect to Threat Intel Service: {e}")
            return None
        except Exception as e:
            logger.error(f"Error checking threat {target}: {e}")
            return None

    async def enrich_threat_with_intel(self, threat: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enriquece ameaça com threat intelligence

        Args:
            threat: Objeto de ameaça do ADR

        Returns:
            Ameaça enriquecida com threat intel
        """
        # Determina targets para análise
        targets_to_check = []

        # Source (IP, domain, hash)
        source = threat.get('source', '')
        if source:
            targets_to_check.append({
                'target': source,
                'type': self._detect_target_type(source)
            })

        # Indicadores
        for indicator in threat.get('indicators', []):
            extracted = self._extract_target_from_indicator(indicator)
            if extracted and extracted not in [t['target'] for t in targets_to_check]:
                targets_to_check.append(extracted)

        # Raw data (pode conter hashes, URLs, etc)
        raw_data = threat.get('raw_data', {})
        if raw_data.get('file_hash'):
            targets_to_check.append({
                'target': raw_data['file_hash'],
                'type': 'hash'
            })

        # Verifica cada target
        intel_results = {}
        for item in targets_to_check:
            intel = await self.check_threat(item['target'], item['type'])
            if intel:
                intel_results[item['target']] = intel

        # Adiciona ao threat
        threat['enriched_context'] = threat.get('enriched_context', {})
        threat['enriched_context']['threat_intelligence'] = intel_results

        # Ajusta threat_score baseado em threat intel
        if intel_results:
            # Pega o pior threat score
            threat_scores = [
                intel_data['threat_score']
                for intel_data in intel_results.values()
            ]

            if threat_scores:
                worst_intel_score = max(threat_scores)

                original_score = threat.get('threat_score', 0)

                # Weighted average (60% threat intel, 40% original detection)
                adjusted_score = int(worst_intel_score * 0.6 + original_score * 0.4)

                threat['threat_score_original'] = original_score
                threat['threat_score'] = adjusted_score
                threat['threat_score_adjusted_by'] = 'threat_intelligence'

                # Atualiza severity baseado no novo score
                threat['severity'] = self._calculate_severity(adjusted_score)

                logger.info(
                    f"🎯 Threat score adjusted: {original_score} → {adjusted_score} "
                    f"based on threat intelligence"
                )

                # Adiciona recommendations agregadas
                all_recommendations = []
                for intel_data in intel_results.values():
                    all_recommendations.extend(intel_data.get('recommendations', []))

                threat['recommendations'] = list(set(all_recommendations))

        return threat

    def _detect_target_type(self, target: str) -> str:
        """Auto-detecta tipo do target"""
        import re

        # IP
        if re.match(r'^(?:\d{1,3}\.){3}\d{1,3}$', target):
            return 'ip'

        # Hash
        if re.match(r'^[a-fA-F0-9]{32}$', target):
            return 'md5'
        if re.match(r'^[a-fA-F0-9]{40}$', target):
            return 'sha1'
        if re.match(r'^[a-fA-F0-9]{64}$', target):
            return 'sha256'

        # URL
        if target.startswith(('http://', 'https://')):
            return 'url'

        # Domain
        if re.match(r'^[a-zA-Z0-9][a-zA-Z0-9-]{0,61}[a-zA-Z0-9]?(\.[a-zA-Z]{2,})+$', target):
            return 'domain'

        return 'auto'

    def _extract_target_from_indicator(self, indicator: str) -> Optional[Dict[str, str]]:
        """Extrai target de um indicador"""
        import re

        # Tenta extrair IP
        ip_match = re.search(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', indicator)
        if ip_match:
            return {'target': ip_match.group(0), 'type': 'ip'}

        # Tenta extrair domain
        domain_match = re.search(r'\b[a-zA-Z0-9][a-zA-Z0-9-]{0,61}[a-zA-Z0-9]?\.[a-zA-Z]{2,}\b', indicator)
        if domain_match:
            return {'target': domain_match.group(0), 'type': 'domain'}

        # Tenta extrair hash
        hash_match = re.search(r'\b[a-fA-F0-9]{32,64}\b', indicator)
        if hash_match:
            hash_val = hash_match.group(0)
            hash_type = 'md5' if len(hash_val) == 32 else 'sha256'
            return {'target': hash_val, 'type': hash_type}

        return None

    def _extract_mitre_tactics(self, data: Dict[str, Any]) -> List[str]:
        """Extrai táticas MITRE ATT&CK das categorias"""
        # Mapping de categorias para MITRE tactics
        category_to_mitre = {
            'malware': ['TA0002'],  # Execution
            'botnet': ['TA0011'],   # Command and Control
            'phishing': ['TA0001'], # Initial Access
            'ransomware': ['TA0040'], # Impact
            'trojan': ['TA0002', 'TA0011'],
            'backdoor': ['TA0003', 'TA0011'], # Persistence, C2
        }

        categories = data.get('categories', [])
        tactics = set()

        for cat in categories:
            cat_lower = cat.lower()
            for key, mitre_ids in category_to_mitre.items():
                if key in cat_lower:
                    tactics.update(mitre_ids)

        return list(tactics)

    def _calculate_severity(self, threat_score: int) -> str:
        """Calcula severity baseado no threat score"""
        if threat_score >= 80:
            return 'critical'
        elif threat_score >= 60:
            return 'high'
        elif threat_score >= 40:
            return 'medium'
        else:
            return 'low'

    async def close(self):
        """Fecha conexão HTTP"""
        await self.client.aclose()
