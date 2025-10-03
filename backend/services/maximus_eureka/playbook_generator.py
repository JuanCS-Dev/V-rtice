"""
Playbook Generator - MAXIMUS EUREKA Automated Response Playbook Creation
=========================================================================

Gera playbooks de resposta customizados baseados em:
- IOCs extraídos
- Padrões maliciosos detectados
- Família de malware identificada
- MITRE ATT&CK techniques

Output: Playbooks YAML prontos para uso no ADR Core Service
"""

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from pattern_detector import PatternMatch, PatternCategory
from ioc_extractor import IOC, IOCType

logger = logging.getLogger(__name__)


class PlaybookSeverity(str, Enum):
    """Severidade do playbook"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class PlaybookAction:
    """Ação individual de um playbook"""
    name: str
    action_type: str  # block_ip, quarantine_file, isolate_host, etc.
    parameters: Dict[str, Any]
    require_approval: bool = False
    description: str = ""
    timeout_seconds: int = 30


@dataclass
class Playbook:
    """Representa um playbook de resposta"""
    playbook_id: str
    name: str
    description: str
    severity: PlaybookSeverity
    triggers: List[str]  # Condições que ativam o playbook
    actions: List[PlaybookAction]
    auto_execute: bool = False
    created_at: datetime = None
    mitre_techniques: List[str] = None
    tags: List[str] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.mitre_techniques is None:
            self.mitre_techniques = []
        if self.tags is None:
            self.tags = []

    def to_yaml(self) -> str:
        """Exporta playbook para formato YAML (compatível com ADR Core)"""
        yaml_content = f"""# Auto-generated playbook by MAXIMUS EUREKA
# Generated: {self.created_at.isoformat()}

playbook_id: {self.playbook_id}
name: "{self.name}"
description: "{self.description}"

metadata:
  severity: {self.severity.value}
  auto_execute: {'true' if self.auto_execute else 'false'}
  require_approval: {'true' if any(a.require_approval for a in self.actions) else 'false'}
  generated_by: "MAXIMUS EUREKA"
  mitre_techniques: {self.mitre_techniques if self.mitre_techniques else []}
  tags: {self.tags if self.tags else []}

triggers:
"""
        for trigger in self.triggers:
            yaml_content += f"  - {trigger}\n"

        yaml_content += "\nactions:\n"
        for i, action in enumerate(self.actions, 1):
            yaml_content += f"""  - name: "{action.name}"
    type: {action.action_type}
    description: "{action.description}"
    require_approval: {'true' if action.require_approval else 'false'}
    timeout_seconds: {action.timeout_seconds}
    parameters:
"""
            for key, value in action.parameters.items():
                if isinstance(value, str):
                    yaml_content += f'      {key}: "{value}"\n'
                else:
                    yaml_content += f'      {key}: {value}\n'

        return yaml_content


class PlaybookGenerator:
    """
    Gerador automático de playbooks de resposta

    Features:
    - Gera playbooks baseados em análise de malware
    - Templates pré-definidos para ameaças comuns
    - Customização baseada em IOCs/padrões
    - Export YAML compatível com ADR Core
    - MITRE ATT&CK mapping automático
    """

    def __init__(self):
        self.generated_playbooks: List[Playbook] = []

    def generate_from_analysis(
        self,
        patterns: List[PatternMatch],
        iocs: List[IOC],
        malware_family: Optional[str] = None
    ) -> Playbook:
        """
        Gera playbook customizado baseado em análise de malware

        Args:
            patterns: Padrões maliciosos detectados
            iocs: IOCs extraídos
            malware_family: Família de malware (se identificada)

        Returns:
            Playbook customizado
        """
        logger.info("📋 Gerando playbook de resposta customizado...")

        # Determina severidade baseada nos padrões
        severity = self._calculate_severity(patterns)

        # Extrai MITRE techniques dos padrões
        mitre_techniques = list(set(
            p.pattern.mitre_technique
            for p in patterns
            if p.pattern.mitre_technique
        ))

        # Gera ações baseadas em IOCs e padrões
        actions = []

        # 1. Ações de bloqueio de rede (IPs/Domains)
        actions.extend(self._generate_network_blocking_actions(iocs))

        # 2. Ações de quarentena de arquivos
        actions.extend(self._generate_file_quarantine_actions(patterns))

        # 3. Ações de isolamento de host (se crítico)
        if severity == PlaybookSeverity.CRITICAL:
            actions.extend(self._generate_host_isolation_actions())

        # 4. Ações de coleta de evidências
        actions.extend(self._generate_evidence_collection_actions(iocs))

        # 5. Ações de alerta
        actions.extend(self._generate_alert_actions(severity, malware_family))

        # 6. Ações de logging
        actions.append(PlaybookAction(
            name="log_incident",
            action_type="log",
            parameters={
                "message": f"Playbook executed for {malware_family or 'unknown'} malware",
                "level": "info"
            },
            description="Log incident details"
        ))

        # Cria triggers
        triggers = self._generate_triggers(patterns, iocs, malware_family)

        # Cria playbook
        playbook_id = f"eureka_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        playbook_name = f"Response to {malware_family or 'Unknown Malware'}"

        playbook = Playbook(
            playbook_id=playbook_id,
            name=playbook_name,
            description=f"Auto-generated response playbook for detected malware. "
                       f"Detected {len(patterns)} malicious patterns and {len(iocs)} IOCs.",
            severity=severity,
            triggers=triggers,
            actions=actions,
            auto_execute=(severity != PlaybookSeverity.CRITICAL),  # Não auto-exec se crítico
            mitre_techniques=mitre_techniques,
            tags=self._generate_tags(patterns, malware_family)
        ))

        self.generated_playbooks.append(playbook)
        logger.info(f"✅ Playbook gerado: {playbook_id} com {len(actions)} ações")

        return playbook

    def _calculate_severity(self, patterns: List[PatternMatch]) -> PlaybookSeverity:
        """Calcula severidade baseada nos padrões detectados"""
        if not patterns:
            return PlaybookSeverity.LOW

        # Conta padrões por severidade
        critical_count = sum(1 for p in patterns if p.pattern.severity.value == "critical")
        high_count = sum(1 for p in patterns if p.pattern.severity.value == "high")

        if critical_count >= 3 or (critical_count >= 1 and high_count >= 3):
            return PlaybookSeverity.CRITICAL
        elif critical_count >= 1 or high_count >= 2:
            return PlaybookSeverity.HIGH
        elif high_count >= 1:
            return PlaybookSeverity.MEDIUM
        else:
            return PlaybookSeverity.LOW

    def _generate_network_blocking_actions(self, iocs: List[IOC]) -> List[PlaybookAction]:
        """Gera ações de bloqueio de rede"""
        actions = []

        # Bloqueia IPs maliciosos
        ips = [ioc.value for ioc in iocs if ioc.ioc_type in [IOCType.IPV4, IOCType.IPV6]]
        for ip in ips[:10]:  # Limita a 10 para não sobrecarregar
            actions.append(PlaybookAction(
                name=f"block_ip_{ip.replace('.', '_')}",
                action_type="block_ip",
                parameters={
                    "ip_address": ip,
                    "direction": "both",  # inbound + outbound
                    "duration_minutes": 1440  # 24h
                },
                require_approval=False,
                description=f"Block malicious IP {ip} from IOC extraction",
                timeout_seconds=10
            ))

        # Bloqueia domains maliciosos
        domains = [ioc.value for ioc in iocs if ioc.ioc_type == IOCType.DOMAIN]
        for domain in domains[:10]:
            actions.append(PlaybookAction(
                name=f"block_domain_{domain.replace('.', '_')}",
                action_type="block_domain",
                parameters={
                    "domain": domain,
                    "dns_block": True
                },
                require_approval=False,
                description=f"Block malicious domain {domain}",
                timeout_seconds=10
            ))

        return actions

    def _generate_file_quarantine_actions(self, patterns: List[PatternMatch]) -> List[PlaybookAction]:
        """Gera ações de quarentena de arquivos"""
        actions = []

        # Se detectou malware, quarentena o arquivo
        if any(p.pattern.category in [PatternCategory.SHELLCODE, PatternCategory.CRYPTO] for p in patterns):
            actions.append(PlaybookAction(
                name="quarantine_malicious_file",
                action_type="quarantine_file",
                parameters={
                    "file_path": "{{detected_file_path}}",  # Template var
                    "quarantine_dir": "/var/quarantine/maximus",
                    "create_backup": True
                },
                require_approval=True,  # Requer aprovação
                description="Quarantine detected malicious file",
                timeout_seconds=30
            ))

        return actions

    def _generate_host_isolation_actions(self) -> List[PlaybookAction]:
        """Gera ações de isolamento de host"""
        return [
            PlaybookAction(
                name="isolate_infected_host",
                action_type="isolate_host",
                parameters={
                    "host_id": "{{infected_host_id}}",
                    "isolation_type": "network",  # network, full
                    "allow_management": True  # Permite acesso de gerenciamento
                },
                require_approval=True,  # SEMPRE requer aprovação
                description="Isolate infected host from network",
                timeout_seconds=60
            )
        ]

    def _generate_evidence_collection_actions(self, iocs: List[IOC]) -> List[PlaybookAction]:
        """Gera ações de coleta de evidências"""
        actions = []

        # Coleta memory dump se detectou shellcode/process injection
        actions.append(PlaybookAction(
            name="collect_memory_dump",
            action_type="collect_evidence",
            parameters={
                "evidence_type": "memory_dump",
                "target_process": "{{suspicious_process}}",
                "output_dir": "/var/evidence/maximus"
            },
            require_approval=False,
            description="Collect memory dump for forensic analysis",
            timeout_seconds=120
        ))

        # Coleta network capture
        if any(ioc.ioc_type in [IOCType.IPV4, IOCType.URL] for ioc in iocs):
            actions.append(PlaybookAction(
                name="capture_network_traffic",
                action_type="collect_evidence",
                parameters={
                    "evidence_type": "pcap",
                    "duration_seconds": 300,  # 5 min
                    "output_dir": "/var/evidence/maximus"
                },
                require_approval=False,
                description="Capture network traffic for analysis",
                timeout_seconds=310
            ))

        return actions

    def _generate_alert_actions(
        self,
        severity: PlaybookSeverity,
        malware_family: Optional[str]
    ) -> List[PlaybookAction]:
        """Gera ações de alertas"""
        alert_level = {
            PlaybookSeverity.CRITICAL: "critical",
            PlaybookSeverity.HIGH: "high",
            PlaybookSeverity.MEDIUM: "medium",
            PlaybookSeverity.LOW: "low"
        }[severity]

        return [
            PlaybookAction(
                name="send_security_alert",
                action_type="alert",
                parameters={
                    "level": alert_level,
                    "title": f"Malware Detected: {malware_family or 'Unknown'}",
                    "message": f"MAXIMUS EUREKA detected malicious activity. Automated response playbook executed.",
                    "channels": ["email", "slack", "siem"]
                },
                require_approval=False,
                description="Send security alert to SOC team",
                timeout_seconds=10
            )
        ]

    def _generate_triggers(
        self,
        patterns: List[PatternMatch],
        iocs: List[IOC],
        malware_family: Optional[str]
    ) -> List[str]:
        """Gera triggers do playbook"""
        triggers = []

        # Trigger por categoria de padrão
        categories = set(p.pattern.category.value for p in patterns)
        for cat in categories:
            triggers.append(f"pattern_category == '{cat}'")

        # Trigger por família de malware
        if malware_family:
            triggers.append(f"malware_family == '{malware_family}'")

        # Trigger por severidade
        severity = self._calculate_severity(patterns)
        triggers.append(f"severity >= '{severity.value}'")

        return triggers

    def _generate_tags(
        self,
        patterns: List[PatternMatch],
        malware_family: Optional[str]
    ) -> List[str]:
        """Gera tags para o playbook"""
        tags = ["auto_generated", "eureka"]

        if malware_family:
            tags.append(f"family_{malware_family.lower()}")

        # Tags por categoria de padrão
        categories = set(p.pattern.category.value for p in patterns)
        tags.extend(categories)

        return list(set(tags))  # Remove duplicatas

    def generate_template_playbook(self, template_name: str) -> Optional[Playbook]:
        """
        Gera playbook a partir de template pré-definido

        Templates disponíveis:
        - ransomware_response
        - c2_communication
        - data_exfiltration
        - privilege_escalation
        """
        logger.info(f"📋 Gerando playbook do template: {template_name}")

        if template_name == "ransomware_response":
            return self._template_ransomware()
        elif template_name == "c2_communication":
            return self._template_c2()
        elif template_name == "data_exfiltration":
            return self._template_exfiltration()
        elif template_name == "privilege_escalation":
            return self._template_privesc()
        else:
            logger.error(f"❌ Template desconhecido: {template_name}")
            return None

    def _template_ransomware(self) -> Playbook:
        """Template para resposta a ransomware"""
        return Playbook(
            playbook_id="template_ransomware",
            name="Ransomware Detection Response",
            description="Automated response to ransomware detection",
            severity=PlaybookSeverity.CRITICAL,
            triggers=["pattern_category == 'crypto'", "threat_type == 'ransomware'"],
            actions=[
                PlaybookAction("isolate_host", "isolate_host", {"isolation_type": "full"}, True, "Isolate infected host"),
                PlaybookAction("kill_process", "kill_process", {"process_name": "{{malicious_process}}"}, True, "Terminate malicious process"),
                PlaybookAction("quarantine_file", "quarantine_file", {"file_path": "{{ransomware_binary}}"}, True, "Quarantine ransomware"),
                PlaybookAction("block_c2", "block_ip", {"ip_address": "{{c2_ip}}"}, False, "Block C2 server"),
                PlaybookAction("alert_soc", "alert", {"level": "critical", "title": "Ransomware Detected"}, False, "Alert SOC team"),
                PlaybookAction("collect_evidence", "collect_evidence", {"evidence_type": "memory_dump"}, False, "Collect forensic evidence"),
                PlaybookAction("log_incident", "log", {"message": "Ransomware incident handled"}, False, "Log incident"),
            ],
            auto_execute=False,  # Requer aprovação humana
            mitre_techniques=["T1486", "T1490"],
            tags=["ransomware", "critical", "auto_response"]
        )

    def _template_c2(self) -> Playbook:
        """Template para resposta a C2"""
        return Playbook(
            playbook_id="template_c2",
            name="C2 Communication Response",
            description="Automated response to C2 communication detection",
            severity=PlaybookSeverity.HIGH,
            triggers=["pattern_category == 'network'", "threat_type == 'c2_communication'"],
            actions=[
                PlaybookAction("block_c2_ip", "block_ip", {"ip_address": "{{c2_ip}}"}, False, "Block C2 IP"),
                PlaybookAction("block_c2_domain", "block_domain", {"domain": "{{c2_domain}}"}, False, "Block C2 domain"),
                PlaybookAction("alert_soc", "alert", {"level": "high", "title": "C2 Communication Detected"}, False, "Alert team"),
                PlaybookAction("capture_traffic", "collect_evidence", {"evidence_type": "pcap", "duration_seconds": 300}, False, "Capture traffic"),
                PlaybookAction("log", "log", {"message": "C2 blocked"}, False, "Log event"),
            ],
            auto_execute=True,  # Pode auto-executar
            mitre_techniques=["T1071", "T1095"],
            tags=["c2", "network", "auto_execute"]
        )

    def _template_exfiltration(self) -> Playbook:
        """Template para exfiltração de dados"""
        return Playbook(
            playbook_id="template_exfiltration",
            name="Data Exfiltration Response",
            description="Response to data exfiltration attempts",
            severity=PlaybookSeverity.HIGH,
            triggers=["pattern_category == 'exfiltration'"],
            actions=[
                PlaybookAction("block_destination", "block_ip", {"ip_address": "{{exfil_target}}"}, False),
                PlaybookAction("isolate_source", "isolate_host", {"host_id": "{{source_host}}"}, True),
                PlaybookAction("alert", "alert", {"level": "high", "title": "Data Exfiltration Detected"}, False),
                PlaybookAction("collect_logs", "collect_evidence", {"evidence_type": "logs"}, False),
            ],
            auto_execute=False,
            mitre_techniques=["T1041", "T1048"],
            tags=["exfiltration", "data_loss"]
        )

    def _template_privesc(self) -> Playbook:
        """Template para privilege escalation"""
        return Playbook(
            playbook_id="template_privesc",
            name="Privilege Escalation Response",
            description="Response to privilege escalation attempts",
            severity=PlaybookSeverity.HIGH,
            triggers=["pattern_category == 'privilege_escalation'"],
            actions=[
                PlaybookAction("terminate_process", "kill_process", {"process_name": "{{suspicious_process}}"}, True),
                PlaybookAction("alert", "alert", {"level": "high", "title": "Privilege Escalation Detected"}, False),
                PlaybookAction("collect_evidence", "collect_evidence", {"evidence_type": "memory_dump"}, False),
            ],
            auto_execute=False,
            mitre_techniques=["T1134", "T1548"],
            tags=["privesc", "lateral_movement"]
        )

    def save_playbook(self, playbook: Playbook, output_dir: str = "."):
        """Salva playbook em arquivo YAML"""
        from pathlib import Path

        filename = f"{playbook.playbook_id}.yaml"
        filepath = Path(output_dir) / filename

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(playbook.to_yaml())

        logger.info(f"💾 Playbook salvo: {filepath}")
        return str(filepath)


if __name__ == "__main__":
    # Teste standalone
    logging.basicConfig(level=logging.INFO)

    generator = PlaybookGenerator()

    print("\n📋 TESTANDO GERAÇÃO DE PLAYBOOKS:\n")

    # Gera playbook de template
    print("1. Template: Ransomware Response")
    ransomware_pb = generator.generate_template_playbook("ransomware_response")
    print(ransomware_pb.to_yaml()[:500] + "\n...\n")

    # Salva playbook
    generator.save_playbook(ransomware_pb, "/tmp")
    print(f"✅ Playbook salvo em /tmp/{ransomware_pb.playbook_id}.yaml\n")

    print(f"\n✅ Total de playbooks gerados: {len(generator.generated_playbooks)}")
