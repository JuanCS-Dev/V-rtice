"""
Pattern Detector - MAXIMUS EUREKA Malicious Pattern Detection
==============================================================

Detecta padrões maliciosos em binários, scripts e código.

Capacidades:
- Detecção de shellcode patterns
- API calls suspeitas (Windows/Linux)
- Obfuscação detectada
- Packing/crypting indicators
- Network communication patterns
- Persistence mechanisms
- Anti-analysis techniques
"""

import re
import os
import logging
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

logger = logging.getLogger(__name__)


class PatternCategory(str, Enum):
    """Categorias de padrões maliciosos"""
    SHELLCODE = "shellcode"
    SUSPICIOUS_API = "suspicious_api"
    OBFUSCATION = "obfuscation"
    PACKING = "packing"
    NETWORK = "network"
    PERSISTENCE = "persistence"
    ANTI_ANALYSIS = "anti_analysis"
    CRYPTO = "crypto"
    EXFILTRATION = "exfiltration"
    PRIVILEGE_ESCALATION = "privilege_escalation"


class Severity(str, Enum):
    """Severidade do padrão"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class MaliciousPattern:
    """Define um padrão malicioso"""
    pattern_id: str
    name: str
    description: str
    category: PatternCategory
    severity: Severity
    regex: str  # Regex pattern
    yara_rule: Optional[str] = None
    mitre_technique: Optional[str] = None  # e.g., "T1059.001" (PowerShell)
    references: List[str] = field(default_factory=list)


@dataclass
class PatternMatch:
    """Representa um match de padrão"""
    pattern: MaliciousPattern
    matched_content: str
    offset: int  # Byte offset no arquivo
    context: str  # Contexto ao redor do match (10 chars antes/depois)
    confidence: float  # 0-1


class PatternDetector:
    """
    Detector de padrões maliciosos em arquivos

    Features:
    - Biblioteca de padrões pré-definidos
    - Regex matching otimizado
    - Scoring de confiança
    - Suporte a YARA rules (futuro)
    - MITRE ATT&CK mapping
    """

    def __init__(self):
        self.patterns: List[MaliciousPattern] = []
        self._load_builtin_patterns()

    def _load_builtin_patterns(self):
        """Carrega padrões built-in"""
        logger.info("📚 Carregando padrões maliciosos built-in...")

        # SHELLCODE PATTERNS
        self.patterns.extend([
            MaliciousPattern(
                pattern_id="shellcode_001",
                name="Common x86 Shellcode Preamble",
                description="Detecta preamble comum de shellcode x86 (stack setup)",
                category=PatternCategory.SHELLCODE,
                severity=Severity.HIGH,
                regex=rb"\\x31\\xc0\\x50\\x68",  # xor eax,eax; push eax; push ...
                mitre_technique="T1055",  # Process Injection
                references=["https://github.com/rapid7/metasploit-framework/"]
            ),
            MaliciousPattern(
                pattern_id="shellcode_002",
                name="NOP Sled Detection",
                description="Detecta NOP sleds (sequências longas de NOPs)",
                category=PatternCategory.SHELLCODE,
                severity=Severity.MEDIUM,
                regex=rb"(\\x90){20,}",  # 20+ NOPs consecutivos
                mitre_technique="T1055"
            ),
            MaliciousPattern(
                pattern_id="shellcode_003",
                name="Egg Hunter Pattern",
                description="Detecta egg hunter shellcode (busca por tag no heap)",
                category=PatternCategory.SHELLCODE,
                severity=Severity.HIGH,
                regex=rb"\\x66\\x81\\xca\\xff\\x0f",  # or dx, 0x0fff (egg hunter)
                mitre_technique="T1055"
            ),
        ])

        # SUSPICIOUS API CALLS (Windows)
        self.patterns.extend([
            MaliciousPattern(
                pattern_id="api_001",
                name="VirtualAlloc/VirtualProtect Combo",
                description="Alocação de memória RWX (comum em process injection)",
                category=PatternCategory.SUSPICIOUS_API,
                severity=Severity.CRITICAL,
                regex=rb"VirtualAlloc.*VirtualProtect",
                mitre_technique="T1055",
                references=["https://attack.mitre.org/techniques/T1055/"]
            ),
            MaliciousPattern(
                pattern_id="api_002",
                name="CreateRemoteThread",
                description="Criação de thread remota (DLL injection)",
                category=PatternCategory.SUSPICIOUS_API,
                severity=Severity.CRITICAL,
                regex=rb"CreateRemoteThread|NtCreateThreadEx",
                mitre_technique="T1055.001",  # DLL Injection
            ),
            MaliciousPattern(
                pattern_id="api_003",
                name="Process Hollowing APIs",
                description="APIs usadas para process hollowing",
                category=PatternCategory.SUSPICIOUS_API,
                severity=Severity.CRITICAL,
                regex=rb"(NtUnmapViewOfSection|ZwUnmapViewOfSection).*WriteProcessMemory.*ResumeThread",
                mitre_technique="T1055.012",  # Process Hollowing
            ),
            MaliciousPattern(
                pattern_id="api_004",
                name="Keylogger APIs",
                description="APIs comumente usadas por keyloggers",
                category=PatternCategory.SUSPICIOUS_API,
                severity=Severity.HIGH,
                regex=rb"(GetAsyncKeyState|GetKeyboardState|SetWindowsHookEx.*WH_KEYBOARD)",
                mitre_technique="T1056.001",  # Input Capture: Keylogging
            ),
        ])

        # OBFUSCATION PATTERNS
        self.patterns.extend([
            MaliciousPattern(
                pattern_id="obf_001",
                name="Base64 Encoded PowerShell",
                description="PowerShell com comando encodado em Base64",
                category=PatternCategory.OBFUSCATION,
                severity=Severity.HIGH,
                regex=rb"powershell.*-enc(odedcommand)?\s+[A-Za-z0-9+/=]{50,}",
                mitre_technique="T1059.001",  # PowerShell
            ),
            MaliciousPattern(
                pattern_id="obf_002",
                name="Heavy String Obfuscation",
                description="Strings altamente ofuscadas (muitos caracteres especiais)",
                category=PatternCategory.OBFUSCATION,
                severity=Severity.MEDIUM,
                regex=rb"[\\x00-\\x1f\\x7f-\\xff]{30,}",  # 30+ non-printable chars
            ),
            MaliciousPattern(
                pattern_id="obf_003",
                name="XOR Decoding Loop",
                description="Loop de decodificação XOR (comum em packers)",
                category=PatternCategory.OBFUSCATION,
                severity=Severity.MEDIUM,
                regex=rb"\\x30[\\x00-\\xff]{1,3}\\x40\\x75",  # xor [reg], X; inc reg; jnz
                mitre_technique="T1027",  # Obfuscated Files or Information
            ),
        ])

        # PACKING/CRYPTING
        self.patterns.extend([
            MaliciousPattern(
                pattern_id="pack_001",
                name="UPX Packer Signature",
                description="Detecta binários empacotados com UPX",
                category=PatternCategory.PACKING,
                severity=Severity.MEDIUM,
                regex=rb"UPX[0-9!]",
                mitre_technique="T1027.002",  # Software Packing
            ),
            MaliciousPattern(
                pattern_id="pack_002",
                name="High Entropy Section",
                description="Seção com alta entropia (possível criptografia/packing)",
                category=PatternCategory.PACKING,
                severity=Severity.MEDIUM,
                regex=rb".{1000,}",  # Placeholder - entropia calculada separadamente
            ),
        ])

        # NETWORK PATTERNS
        self.patterns.extend([
            MaliciousPattern(
                pattern_id="net_001",
                name="Embedded IP Address",
                description="Endereço IP hardcoded (possível C2)",
                category=PatternCategory.NETWORK,
                severity=Severity.MEDIUM,
                regex=rb"\\b(?:[0-9]{1,3}\\.){3}[0-9]{1,3}\\b",
            ),
            MaliciousPattern(
                pattern_id="net_002",
                name="Embedded Domain",
                description="Domain hardcoded (possível C2)",
                category=PatternCategory.NETWORK,
                severity=Severity.MEDIUM,
                regex=rb"[a-z0-9-]+\\.(com|net|org|ru|cn|tk)\\b",
            ),
            MaliciousPattern(
                pattern_id="net_003",
                name="Reverse Shell Pattern",
                description="Padrão de reverse shell (bash/python)",
                category=PatternCategory.NETWORK,
                severity=Severity.CRITICAL,
                regex=rb"(bash -i >& /dev/tcp/|python.*socket\\.connect|nc.*-e /bin/(ba)?sh)",
                mitre_technique="T1059.004",  # Unix Shell
            ),
        ])

        # PERSISTENCE MECHANISMS
        self.patterns.extend([
            MaliciousPattern(
                pattern_id="pers_001",
                name="Registry Run Key Modification",
                description="Modificação de chaves de Run do registro (persistência)",
                category=PatternCategory.PERSISTENCE,
                severity=Severity.HIGH,
                regex=rb"Software\\\\Microsoft\\\\Windows\\\\CurrentVersion\\\\Run",
                mitre_technique="T1547.001",  # Registry Run Keys
            ),
            MaliciousPattern(
                pattern_id="pers_002",
                name="Scheduled Task Creation",
                description="Criação de tarefa agendada",
                category=PatternCategory.PERSISTENCE,
                severity=Severity.HIGH,
                regex=rb"schtasks.*/(create|change)",
                mitre_technique="T1053.005",  # Scheduled Task
            ),
            MaliciousPattern(
                pattern_id="pers_003",
                name="WMI Event Subscription",
                description="Criação de subscription WMI (persistência avançada)",
                category=PatternCategory.PERSISTENCE,
                severity=Severity.CRITICAL,
                regex=rb"(ActiveScriptEventConsumer|CommandLineEventConsumer)",
                mitre_technique="T1546.003",  # WMI Event Subscription
            ),
        ])

        # ANTI-ANALYSIS
        self.patterns.extend([
            MaliciousPattern(
                pattern_id="anti_001",
                name="Debugger Detection (IsDebuggerPresent)",
                description="Detecta presença de debugger",
                category=PatternCategory.ANTI_ANALYSIS,
                severity=Severity.MEDIUM,
                regex=rb"IsDebuggerPresent|CheckRemoteDebuggerPresent",
                mitre_technique="T1622",  # Debugger Evasion
            ),
            MaliciousPattern(
                pattern_id="anti_002",
                name="VM Detection Artifacts",
                description="Detecta execução em máquina virtual",
                category=PatternCategory.ANTI_ANALYSIS,
                severity=Severity.MEDIUM,
                regex=rb"(VMware|VBox|QEMU|Xen|Hyper-V)",
                mitre_technique="T1497.001",  # VM Detection
            ),
            MaliciousPattern(
                pattern_id="anti_003",
                name="Sleep/Delay Evasion",
                description="Sleep longo para evitar sandboxes",
                category=PatternCategory.ANTI_ANALYSIS,
                severity=Severity.LOW,
                regex=rb"Sleep\\([5-9][0-9]{4,}\\)",  # Sleep > 50000ms
                mitre_technique="T1497",  # Sandbox Evasion
            ),
        ])

        # CRYPTO/RANSOMWARE
        self.patterns.extend([
            MaliciousPattern(
                pattern_id="crypto_001",
                name="CryptEncrypt/CryptDecrypt",
                description="Uso de APIs de criptografia (possível ransomware)",
                category=PatternCategory.CRYPTO,
                severity=Severity.HIGH,
                regex=rb"CryptEncrypt|CryptDecrypt|BCryptEncrypt",
                mitre_technique="T1486",  # Data Encrypted for Impact
            ),
            MaliciousPattern(
                pattern_id="crypto_002",
                name="Ransom Note Keywords",
                description="Palavras-chave comuns em notas de resgate",
                category=PatternCategory.CRYPTO,
                severity=Severity.CRITICAL,
                regex=rb"(your files have been encrypted|pay.*bitcoin|restore.*files|decrypt)",
                mitre_technique="T1486",
            ),
        ])

        # PRIVILEGE ESCALATION
        self.patterns.extend([
            MaliciousPattern(
                pattern_id="privesc_001",
                name="Token Manipulation",
                description="Manipulação de tokens (impersonation)",
                category=PatternCategory.PRIVILEGE_ESCALATION,
                severity=Severity.CRITICAL,
                regex=rb"(AdjustTokenPrivileges|ImpersonateLoggedOnUser|DuplicateTokenEx)",
                mitre_technique="T1134",  # Access Token Manipulation
            ),
            MaliciousPattern(
                pattern_id="privesc_002",
                name="UAC Bypass Techniques",
                description="Técnicas de bypass de UAC",
                category=PatternCategory.PRIVILEGE_ESCALATION,
                severity=Severity.HIGH,
                regex=rb"(eventvwr\\.exe|fodhelper\\.exe|slui\\.exe).*\\\\shell\\\\open\\\\command",
                mitre_technique="T1548.002",  # Bypass UAC
            ),
        ])

        logger.info(f"✅ {len(self.patterns)} padrões carregados")

    def scan_file(self, file_path: str) -> List[PatternMatch]:
        """
        Escaneia arquivo em busca de padrões maliciosos

        Args:
            file_path: Path do arquivo a escanear

        Returns:
            Lista de matches encontrados
        """
        logger.info(f"🔍 Escaneando: {file_path}")

        matches: List[PatternMatch] = []

        try:
            # Lê arquivo em modo binário
            with open(file_path, 'rb') as f:
                content = f.read()

            # Testa cada padrão
            for pattern in self.patterns:
                try:
                    regex = re.compile(pattern.regex, re.IGNORECASE | re.DOTALL)
                    for match in regex.finditer(content):
                        offset = match.start()
                        matched_bytes = match.group(0)

                        # Contexto (10 bytes antes/depois)
                        context_start = max(0, offset - 10)
                        context_end = min(len(content), offset + len(matched_bytes) + 10)
                        context = content[context_start:context_end]

                        # Calcula confiança (placeholder - pode ser mais sofisticado)
                        confidence = self._calculate_confidence(pattern, matched_bytes, content)

                        matches.append(PatternMatch(
                            pattern=pattern,
                            matched_content=self._safe_decode(matched_bytes),
                            offset=offset,
                            context=self._safe_decode(context),
                            confidence=confidence
                        ))

                except re.error as e:
                    logger.warning(f"Regex inválida no padrão {pattern.pattern_id}: {e}")
                    continue

            logger.info(f"✅ {len(matches)} padrões detectados")
            return matches

        except FileNotFoundError:
            logger.error(f"❌ Arquivo não encontrado: {file_path}")
            return []
        except PermissionError:
            logger.error(f"❌ Sem permissão para ler: {file_path}")
            return []
        except Exception as e:
            logger.error(f"❌ Erro ao escanear {file_path}: {e}")
            return []

    def _calculate_confidence(
        self,
        pattern: MaliciousPattern,
        matched_bytes: bytes,
        full_content: bytes
    ) -> float:
        """
        Calcula score de confiança do match

        Fatores:
        - Severidade do padrão
        - Número de ocorrências
        - Contexto ao redor
        """
        # Score base por severidade
        severity_scores = {
            Severity.CRITICAL: 0.95,
            Severity.HIGH: 0.85,
            Severity.MEDIUM: 0.70,
            Severity.LOW: 0.50,
            Severity.INFO: 0.30
        }
        base_score = severity_scores[pattern.severity]

        # Penaliza se houver muitos matches (possível false positive)
        occurrences = full_content.count(matched_bytes)
        if occurrences > 10:
            base_score *= 0.7
        elif occurrences > 5:
            base_score *= 0.85

        return min(1.0, base_score)

    def _safe_decode(self, data: bytes, max_len: int = 100) -> str:
        """Decodifica bytes para string (safe)"""
        try:
            decoded = data.decode('utf-8', errors='replace')
        except:
            decoded = repr(data)

        # Trunca se muito longo
        if len(decoded) > max_len:
            decoded = decoded[:max_len] + "..."

        return decoded

    def get_patterns_by_category(self, category: PatternCategory) -> List[MaliciousPattern]:
        """Retorna padrões de uma categoria específica"""
        return [p for p in self.patterns if p.category == category]

    def get_patterns_by_severity(self, severity: Severity) -> List[MaliciousPattern]:
        """Retorna padrões de uma severidade específica"""
        return [p for p in self.patterns if p.severity == severity]

    def add_custom_pattern(self, pattern: MaliciousPattern):
        """Adiciona padrão customizado"""
        self.patterns.append(pattern)
        logger.info(f"✅ Padrão customizado adicionado: {pattern.pattern_id}")

    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas dos padrões"""
        return {
            'total_patterns': len(self.patterns),
            'by_category': {
                cat.value: len(self.get_patterns_by_category(cat))
                for cat in PatternCategory
            },
            'by_severity': {
                sev.value: len(self.get_patterns_by_severity(sev))
                for sev in Severity
            }
        }


if __name__ == "__main__":
    # Teste standalone
    logging.basicConfig(level=logging.INFO)

    detector = PatternDetector()

    print("\n📊 ESTATÍSTICAS DOS PADRÕES:")
    stats = detector.get_stats()
    print(f"Total de padrões: {stats['total_patterns']}")
    print("\nPor categoria:")
    for cat, count in stats['by_category'].items():
        print(f"  {cat}: {count}")
    print("\nPor severidade:")
    for sev, count in stats['by_severity'].items():
        print(f"  {sev}: {count}")

    print("\n\n🔍 TESTANDO DETECÇÃO:")
    # Cria arquivo de teste com padrão malicioso
    test_file = "/tmp/test_malware.txt"
    with open(test_file, 'wb') as f:
        f.write(b"Normal content\n")
        f.write(b"powershell -encodedcommand SGVsbG9Xb3JsZA==\n")  # Base64 PowerShell
        f.write(b"CreateRemoteThread detected\n")  # Suspicious API
        f.write(b"More normal content\n")

    matches = detector.scan_file(test_file)
    print(f"\n{len(matches)} padrões detectados:\n")
    for match in matches:
        print(f"🔴 {match.pattern.name}")
        print(f"   Category: {match.pattern.category.value}")
        print(f"   Severity: {match.pattern.severity.value}")
        print(f"   Confidence: {match.confidence:.2f}")
        print(f"   Matched: {match.matched_content}")
        if match.pattern.mitre_technique:
            print(f"   MITRE: {match.pattern.mitre_technique}")
        print()

    os.remove(test_file)
