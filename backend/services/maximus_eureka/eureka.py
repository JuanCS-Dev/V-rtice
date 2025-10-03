"""
MAXIMUS EUREKA - Deep Malware Analysis Orchestrator
===================================================

"Pela Arte. Pela Sociedade."

O Eureka orquestra análise profunda de malware, combinando:
1. Pattern Detection → Detecta padrões maliciosos
2. IOC Extraction → Extrai indicators of compromise
3. Malware Classification → Classifica família/tipo
4. Playbook Generation → Gera resposta automática customizada

PIPELINE:
┌──────────────┐
│ Malware File │
└──────┬───────┘
       │
       ▼
┌──────────────────┐
│ Pattern Detector │ → 40+ malicious patterns
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│  IOC Extractor   │ → IPs, domains, hashes, etc.
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│   Classifier     │ → Identifica família de malware
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│Playbook Generator│ → Gera resposta YAML customizada
└──────┬───────────┘
       │
       ▼
   ┌─────────┐
   │ Report  │ → JSON/HTML report completo
   └─────────┘
"""

import os
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path

from pattern_detector import PatternDetector, PatternMatch, PatternCategory
from ioc_extractor import IOCExtractor, IOC, IOCType
from playbook_generator import PlaybookGenerator, Playbook, PlaybookSeverity

logger = logging.getLogger(__name__)


@dataclass
class MalwareClassification:
    """Resultado da classificação de malware"""
    family: str  # e.g., "WannaCry", "Emotet", "Unknown"
    type: str    # e.g., "ransomware", "trojan", "worm"
    confidence: float  # 0-1
    reasoning: str  # Explicação da classificação


@dataclass
class EurekaAnalysisResult:
    """Resultado completo da análise EUREKA"""
    file_path: str
    timestamp: datetime
    file_hash_md5: str
    file_hash_sha256: str

    # Resultados de detecção
    patterns_detected: List[PatternMatch]
    iocs_extracted: List[IOC]
    classification: MalwareClassification

    # Playbook gerado
    response_playbook: Optional[Playbook]

    # Scoring
    threat_score: int  # 0-100
    severity: str  # critical/high/medium/low

    # Metadata
    analysis_duration_seconds: float

    def to_dict(self) -> Dict[str, Any]:
        """Serializa para dict"""
        return {
            'file_path': self.file_path,
            'timestamp': self.timestamp.isoformat(),
            'hashes': {
                'md5': self.file_hash_md5,
                'sha256': self.file_hash_sha256
            },
            'patterns': {
                'count': len(self.patterns_detected),
                'by_category': self._count_patterns_by_category(),
                'details': [
                    {
                        'pattern_id': p.pattern.pattern_id,
                        'name': p.pattern.name,
                        'category': p.pattern.category.value,
                        'severity': p.pattern.severity.value,
                        'confidence': p.confidence,
                        'mitre': p.pattern.mitre_technique
                    }
                    for p in self.patterns_detected
                ]
            },
            'iocs': {
                'count': len(self.iocs_extracted),
                'by_type': self._count_iocs_by_type(),
                'details': [ioc.to_dict() for ioc in self.iocs_extracted]
            },
            'classification': {
                'family': self.classification.family,
                'type': self.classification.type,
                'confidence': self.classification.confidence,
                'reasoning': self.classification.reasoning
            },
            'response_playbook': {
                'generated': self.response_playbook is not None,
                'playbook_id': self.response_playbook.playbook_id if self.response_playbook else None,
                'severity': self.response_playbook.severity.value if self.response_playbook else None,
                'actions_count': len(self.response_playbook.actions) if self.response_playbook else 0
            } if self.response_playbook else None,
            'assessment': {
                'threat_score': self.threat_score,
                'severity': self.severity
            },
            'metadata': {
                'analysis_duration_seconds': self.analysis_duration_seconds
            }
        }

    def _count_patterns_by_category(self) -> Dict[str, int]:
        """Conta padrões por categoria"""
        counts = {}
        for p in self.patterns_detected:
            cat = p.pattern.category.value
            counts[cat] = counts.get(cat, 0) + 1
        return counts

    def _count_iocs_by_type(self) -> Dict[str, int]:
        """Conta IOCs por tipo"""
        counts = {}
        for ioc in self.iocs_extracted:
            ioc_type = ioc.ioc_type.value
            counts[ioc_type] = counts.get(ioc_type, 0) + 1
        return counts


class Eureka:
    """
    Orquestrador de Análise Profunda de Malware

    Features:
    - Pipeline completo de análise
    - Classificação de malware
    - Geração automática de playbooks
    - Relatórios detalhados (JSON, HTML)
    - Integração com MITRE ATT&CK
    """

    def __init__(self):
        self.pattern_detector = PatternDetector()
        self.ioc_extractor = IOCExtractor()
        self.playbook_generator = PlaybookGenerator()
        self.analysis_history: List[EurekaAnalysisResult] = []

    def analyze_file(
        self,
        file_path: str,
        generate_playbook: bool = True
    ) -> EurekaAnalysisResult:
        """
        Analisa arquivo malicioso - PIPELINE COMPLETO

        Args:
            file_path: Path do arquivo a analisar
            generate_playbook: Se True, gera playbook de resposta

        Returns:
            EurekaAnalysisResult com análise completa
        """
        start_time = datetime.utcnow()
        logger.info("="*80)
        logger.info("🔬 MAXIMUS EUREKA - Deep Malware Analysis INICIADO")
        logger.info(f"File: {file_path}")
        logger.info(f"Timestamp: {start_time.isoformat()}")
        logger.info("="*80)

        # 1. PATTERN DETECTION
        logger.info("\n🔍 FASE 1: Pattern Detection...")
        patterns = self.pattern_detector.scan_file(file_path)
        logger.info(
            f"✅ {len(patterns)} padrões maliciosos detectados | "
            f"{len(set(p.pattern.category for p in patterns))} categorias"
        )

        # 2. IOC EXTRACTION
        logger.info("\n🎯 FASE 2: IOC Extraction...")
        iocs = self.ioc_extractor.extract_from_file(file_path)
        logger.info(
            f"✅ {len(iocs)} IOCs extraídos | "
            f"{len(set(ioc.ioc_type for ioc in iocs))} tipos"
        )

        # 3. MALWARE CLASSIFICATION
        logger.info("\n🧬 FASE 3: Malware Classification...")
        classification = self._classify_malware(patterns, iocs)
        logger.info(
            f"✅ Classificado como: {classification.family} ({classification.type}) | "
            f"Confidence: {classification.confidence:.2f}"
        )

        # 4. THREAT SCORING
        logger.info("\n📊 FASE 4: Threat Scoring...")
        threat_score, severity = self._calculate_threat_score(patterns, iocs, classification)
        logger.info(f"✅ Threat Score: {threat_score}/100 | Severity: {severity}")

        # 5. PLAYBOOK GENERATION
        playbook = None
        if generate_playbook:
            logger.info("\n📋 FASE 5: Playbook Generation...")
            playbook = self.playbook_generator.generate_from_analysis(
                patterns=patterns,
                iocs=iocs,
                malware_family=classification.family
            )
            logger.info(
                f"✅ Playbook gerado: {playbook.playbook_id} | "
                f"{len(playbook.actions)} ações | "
                f"Severity: {playbook.severity.value}"
            )

        # 6. CALCULA HASHES
        file_hashes = self._calculate_file_hashes(file_path)

        # Cria resultado
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()

        result = EurekaAnalysisResult(
            file_path=file_path,
            timestamp=start_time,
            file_hash_md5=file_hashes.get('md5', ''),
            file_hash_sha256=file_hashes.get('sha256', ''),
            patterns_detected=patterns,
            iocs_extracted=iocs,
            classification=classification,
            response_playbook=playbook,
            threat_score=threat_score,
            severity=severity,
            analysis_duration_seconds=duration
        )

        self.analysis_history.append(result)

        # RELATÓRIO FINAL
        self._display_analysis_report(result)

        logger.info("="*80)
        logger.info(f"🔬 EUREKA Analysis COMPLETO ({duration:.2f}s)")
        logger.info("="*80)

        return result

    def _classify_malware(
        self,
        patterns: List[PatternMatch],
        iocs: List[IOC]
    ) -> MalwareClassification:
        """
        Classifica malware baseado em padrões e IOCs

        Lógica de classificação:
        - Ransomware: padrões de crypto + ransom note keywords
        - Trojan: C2 communication + suspicious APIs
        - Worm: network propagation + file replication
        - Backdoor: C2 + persistence mechanisms
        - etc.
        """
        # Conta padrões por categoria
        pattern_categories = [p.pattern.category for p in patterns]
        category_counts = {
            cat: pattern_categories.count(cat)
            for cat in set(pattern_categories)
        }

        # Heurísticas de classificação
        confidence = 0.7  # Default
        malware_type = "unknown"
        family = "Unknown"
        reasoning = []

        # RANSOMWARE
        if (
            PatternCategory.CRYPTO in category_counts and
            any('ransom' in p.pattern.name.lower() for p in patterns)
        ):
            malware_type = "ransomware"
            confidence = 0.9
            reasoning.append("Detected crypto APIs + ransom note keywords")

            # Tenta identificar família específica
            for ioc in iocs:
                if 'wannacry' in ioc.value.lower():
                    family = "WannaCry"
                    confidence = 0.95
                elif 'lockbit' in ioc.value.lower():
                    family = "LockBit"
                    confidence = 0.95

        # C2 COMMUNICATION (Trojan/RAT)
        elif (
            PatternCategory.NETWORK in category_counts and
            PatternCategory.PERSISTENCE in category_counts
        ):
            malware_type = "trojan"
            confidence = 0.85
            reasoning.append("Detected C2 communication + persistence mechanisms")

            # Identifica famílias conhecidas
            c2_domains = [ioc.value for ioc in iocs if ioc.ioc_type == IOCType.DOMAIN]
            for domain in c2_domains:
                if 'emotet' in domain.lower():
                    family = "Emotet"
                    confidence = 0.95
                elif 'trickbot' in domain.lower():
                    family = "TrickBot"
                    confidence = 0.95

        # BACKDOOR
        elif (
            PatternCategory.SUSPICIOUS_API in category_counts and
            PatternCategory.PERSISTENCE in category_counts
        ):
            malware_type = "backdoor"
            confidence = 0.80
            reasoning.append("Detected remote access APIs + persistence")

        # SHELLCODE/EXPLOIT
        elif PatternCategory.SHELLCODE in category_counts:
            malware_type = "exploit"
            confidence = 0.85
            reasoning.append("Detected shellcode patterns")

        # GENERIC MALWARE
        else:
            malware_type = "malware"
            confidence = 0.60
            reasoning.append("Detected malicious patterns but unable to classify specifically")

        return MalwareClassification(
            family=family,
            type=malware_type,
            confidence=confidence,
            reasoning=" | ".join(reasoning)
        )

    def _calculate_threat_score(
        self,
        patterns: List[PatternMatch],
        iocs: List[IOC],
        classification: MalwareClassification
    ) -> tuple[int, str]:
        """
        Calcula threat score (0-100) e severidade

        Fatores:
        - Número de padrões críticos/high
        - Número de IOCs
        - Tipo de malware
        - Confiança da classificação
        """
        score = 0

        # Score por padrões (max 50 pontos)
        critical_patterns = sum(1 for p in patterns if p.pattern.severity.value == "critical")
        high_patterns = sum(1 for p in patterns if p.pattern.severity.value == "high")
        score += min(50, critical_patterns * 10 + high_patterns * 5)

        # Score por IOCs (max 30 pontos)
        malicious_iocs = len([ioc for ioc in iocs if ioc.confidence >= 0.8])
        score += min(30, malicious_iocs * 3)

        # Score por tipo de malware (max 20 pontos)
        malware_scores = {
            'ransomware': 20,
            'trojan': 15,
            'backdoor': 15,
            'exploit': 12,
            'malware': 10,
            'unknown': 5
        }
        score += malware_scores.get(classification.type, 5)

        # Ajusta por confiança
        score = int(score * classification.confidence)

        # Determina severidade
        if score >= 80:
            severity = "critical"
        elif score >= 60:
            severity = "high"
        elif score >= 40:
            severity = "medium"
        else:
            severity = "low"

        return min(100, score), severity

    def _calculate_file_hashes(self, file_path: str) -> Dict[str, str]:
        """Calcula hashes do arquivo"""
        import hashlib

        hashes = {}
        try:
            with open(file_path, 'rb') as f:
                content = f.read()

            hashes['md5'] = hashlib.md5(content).hexdigest()
            hashes['sha256'] = hashlib.sha256(content).hexdigest()
        except Exception as e:
            logger.warning(f"⚠️ Erro ao calcular hashes: {e}")

        return hashes

    def _display_analysis_report(self, result: EurekaAnalysisResult):
        """Exibe relatório de análise no console"""
        logger.info("\n" + "="*80)
        logger.info("📊 RELATÓRIO DE ANÁLISE - EUREKA")
        logger.info("="*80)

        logger.info(f"\n📁 ARQUIVO:")
        logger.info(f"   Path: {result.file_path}")
        logger.info(f"   MD5: {result.file_hash_md5}")
        logger.info(f"   SHA256: {result.file_hash_sha256}")

        logger.info(f"\n🧬 CLASSIFICAÇÃO:")
        logger.info(f"   Família: {result.classification.family}")
        logger.info(f"   Tipo: {result.classification.type}")
        logger.info(f"   Confiança: {result.classification.confidence:.2f}")
        logger.info(f"   Reasoning: {result.classification.reasoning}")

        logger.info(f"\n🔍 PADRÕES DETECTADOS: {len(result.patterns_detected)}")
        pattern_counts = result._count_patterns_by_category()
        for cat, count in sorted(pattern_counts.items(), key=lambda x: -x[1]):
            logger.info(f"   {cat}: {count}")

        logger.info(f"\n🎯 IOCs EXTRAÍDOS: {len(result.iocs_extracted)}")
        ioc_counts = result._count_iocs_by_type()
        for ioc_type, count in sorted(ioc_counts.items(), key=lambda x: -x[1]):
            logger.info(f"   {ioc_type}: {count}")

        logger.info(f"\n📊 ASSESSMENT:")
        logger.info(f"   Threat Score: {result.threat_score}/100")
        logger.info(f"   Severity: {result.severity.upper()}")

        if result.response_playbook:
            logger.info(f"\n📋 PLAYBOOK GERADO:")
            logger.info(f"   ID: {result.response_playbook.playbook_id}")
            logger.info(f"   Nome: {result.response_playbook.name}")
            logger.info(f"   Ações: {len(result.response_playbook.actions)}")
            logger.info(f"   Auto-execute: {'SIM' if result.response_playbook.auto_execute else 'NÃO'}")

        logger.info(f"\n⏱️ DURAÇÃO: {result.analysis_duration_seconds:.2f}s")

    def export_report(
        self,
        result: EurekaAnalysisResult,
        format: str = "json",
        output_path: Optional[str] = None
    ) -> str:
        """
        Exporta relatório de análise

        Args:
            result: Resultado da análise
            format: "json" ou "html"
            output_path: Path de saída (None = auto)

        Returns:
            Path do arquivo gerado
        """
        if output_path is None:
            timestamp = result.timestamp.strftime('%Y%m%d_%H%M%S')
            filename = f"eureka_report_{timestamp}.{format}"
            output_path = filename

        if format == "json":
            import json
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(result.to_dict(), f, indent=2, ensure_ascii=False)

        elif format == "html":
            html_content = self._generate_html_report(result)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)

        else:
            raise ValueError(f"Formato não suportado: {format}")

        logger.info(f"💾 Relatório exportado: {output_path}")
        return output_path

    def _generate_html_report(self, result: EurekaAnalysisResult) -> str:
        """Gera relatório HTML (placeholder - pode ser muito mais rico)"""
        return f"""<!DOCTYPE html>
<html>
<head>
    <title>MAXIMUS EUREKA - Analysis Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        h1 {{ color: #d32f2f; }}
        .section {{ margin: 20px 0; padding: 15px; background: #f5f5f5; }}
        .metric {{ display: inline-block; margin: 10px 20px; }}
        .critical {{ color: #d32f2f; font-weight: bold; }}
    </style>
</head>
<body>
    <h1>🔬 MAXIMUS EUREKA - Malware Analysis Report</h1>

    <div class="section">
        <h2>File Information</h2>
        <p><strong>Path:</strong> {result.file_path}</p>
        <p><strong>MD5:</strong> {result.file_hash_md5}</p>
        <p><strong>SHA256:</strong> {result.file_hash_sha256}</p>
    </div>

    <div class="section">
        <h2>Classification</h2>
        <p><strong>Family:</strong> {result.classification.family}</p>
        <p><strong>Type:</strong> {result.classification.type}</p>
        <p><strong>Confidence:</strong> {result.classification.confidence:.2%}</p>
    </div>

    <div class="section">
        <h2>Assessment</h2>
        <p class="critical">Threat Score: {result.threat_score}/100</p>
        <p class="critical">Severity: {result.severity.upper()}</p>
    </div>

    <div class="section">
        <h2>Detection Summary</h2>
        <div class="metric">
            <strong>Patterns:</strong> {len(result.patterns_detected)}
        </div>
        <div class="metric">
            <strong>IOCs:</strong> {len(result.iocs_extracted)}
        </div>
    </div>

    <p><em>Generated by MAXIMUS EUREKA at {result.timestamp.isoformat()}</em></p>
</body>
</html>"""

    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do Eureka"""
        if not self.analysis_history:
            return {'total_analyses': 0}

        return {
            'total_analyses': len(self.analysis_history),
            'avg_threat_score': sum(r.threat_score for r in self.analysis_history) / len(self.analysis_history),
            'by_severity': {
                'critical': len([r for r in self.analysis_history if r.severity == 'critical']),
                'high': len([r for r in self.analysis_history if r.severity == 'high']),
                'medium': len([r for r in self.analysis_history if r.severity == 'medium']),
                'low': len([r for r in self.analysis_history if r.severity == 'low']),
            },
            'avg_analysis_duration': sum(r.analysis_duration_seconds for r in self.analysis_history) / len(self.analysis_history)
        }


if __name__ == "__main__":
    # Teste standalone
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    print("\n" + "="*80)
    print("🔬 MAXIMUS EUREKA - Deep Malware Analysis Engine")
    print("\"Pela Arte. Pela Sociedade.\"")
    print("="*80)

    eureka = Eureka()

    # Cria arquivo de teste com múltiplos indicadores maliciosos
    test_file = "/tmp/test_malware_sample.txt"
    with open(test_file, 'wb') as f:
        f.write(b"Malware sample with multiple indicators:\n\n")
        f.write(b"powershell -encodedcommand SGVsbG9Xb3JsZA==\n")  # Obfuscation
        f.write(b"CreateRemoteThread detected\n")  # Suspicious API
        f.write(b"C2 server: 45.142.212.61\n")  # C2 IP
        f.write(b"Domain: malicious-c2.tk\n")  # C2 domain
        f.write(b"Registry: HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\Run\\Malware\n")  # Persistence
        f.write(b"VirtualAlloc and VirtualProtect for RWX memory\n")  # Process injection
        f.write(b"Ransomware note: your files have been encrypted, pay bitcoin to restore\n")  # Ransomware

    # Analisa arquivo
    result = eureka.analyze_file(test_file, generate_playbook=True)

    # Exporta relatório
    eureka.export_report(result, format="json", output_path="/tmp/eureka_report.json")
    eureka.export_report(result, format="html", output_path="/tmp/eureka_report.html")

    # Salva playbook
    if result.response_playbook:
        eureka.playbook_generator.save_playbook(result.response_playbook, "/tmp")

    # Estatísticas
    print("\n\n📊 ESTATÍSTICAS DO EUREKA:")
    stats = eureka.get_stats()
    print(f"Total de análises: {stats['total_analyses']}")
    print(f"Threat score médio: {stats['avg_threat_score']:.1f}")
    print(f"Duração média: {stats['avg_analysis_duration']:.2f}s")

    # Cleanup
    os.remove(test_file)
