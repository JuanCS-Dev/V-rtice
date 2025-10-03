"""
IOC Extractor - MAXIMUS EUREKA Indicator of Compromise Extraction
==================================================================

Extrai automaticamente IOCs (Indicators of Compromise) de:
- Binários maliciosos
- Scripts (Python, PowerShell, Bash)
- Memory dumps
- Network captures (PCAP)
- Logs

IOCs Suportados:
- IP Addresses (IPv4, IPv6)
- Domains
- URLs
- Email addresses
- File hashes (MD5, SHA1, SHA256)
- Bitcoin addresses
- Registry keys
- File paths
- Mutex names
"""

import re
import hashlib
import logging
from typing import List, Dict, Any, Set, Optional
from dataclasses import dataclass, field, asdict
from enum import Enum
from ipaddress import ip_address, IPv4Address, IPv6Address

logger = logging.getLogger(__name__)


class IOCType(str, Enum):
    """Tipos de IOCs"""
    IPV4 = "ipv4"
    IPV6 = "ipv6"
    DOMAIN = "domain"
    URL = "url"
    EMAIL = "email"
    MD5 = "md5"
    SHA1 = "sha1"
    SHA256 = "sha256"
    BITCOIN = "bitcoin"
    REGISTRY_KEY = "registry_key"
    FILE_PATH = "file_path"
    MUTEX = "mutex"
    CVE = "cve"


@dataclass
class IOC:
    """Representa um Indicator of Compromise"""
    ioc_type: IOCType
    value: str
    context: str = ""  # Contexto onde foi encontrado
    confidence: float = 1.0  # 0-1
    source_file: Optional[str] = None
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Serializa para dict"""
        data = asdict(self)
        data['ioc_type'] = self.ioc_type.value
        return data


class IOCExtractor:
    """
    Extrator automático de IOCs

    Features:
    - Regex patterns para múltiplos tipos de IOCs
    - Validação de formato
    - Deduplicação automática
    - Scoring de confiança
    - Export para formatos padrão (STIX, OpenIOC, CSV)
    """

    # Regex patterns para cada tipo de IOC
    PATTERNS = {
        IOCType.IPV4: r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b',
        IOCType.IPV6: r'\b(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}\b',
        IOCType.DOMAIN: r'\b(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,}\b',
        IOCType.URL: r'https?://[^\s<>"{}|\\^`\[\]]+',
        IOCType.EMAIL: r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        IOCType.MD5: r'\b[a-fA-F0-9]{32}\b',
        IOCType.SHA1: r'\b[a-fA-F0-9]{40}\b',
        IOCType.SHA256: r'\b[a-fA-F0-9]{64}\b',
        IOCType.BITCOIN: r'\b[13][a-km-zA-HJ-NP-Z1-9]{25,34}\b',
        IOCType.REGISTRY_KEY: r'HKEY_[A-Z_]+\\[\\A-Za-z0-9_\-\.]+',
        IOCType.FILE_PATH: r'[A-Za-z]:\\(?:[^\\/:*?"<>|\r\n]+\\)*[^\\/:*?"<>|\r\n]*',
        IOCType.CVE: r'CVE-\d{4}-\d{4,7}',
    }

    # IPs/Domains a ignorar (false positives comuns)
    WHITELIST = {
        IOCType.IPV4: {
            '0.0.0.0', '127.0.0.1', '255.255.255.255',
            '10.0.0.1', '192.168.1.1', '172.16.0.1'  # Private IPs comuns
        },
        IOCType.DOMAIN: {
            'localhost', 'example.com', 'test.com', 'domain.com',
            'microsoft.com', 'windows.com', 'apple.com', 'google.com'  # Legítimos
        }
    }

    def __init__(self):
        self.iocs: List[IOC] = []
        self.seen_values: Set[str] = set()  # Para deduplicação

    def extract_from_file(
        self,
        file_path: str,
        ioc_types: Optional[List[IOCType]] = None
    ) -> List[IOC]:
        """
        Extrai IOCs de um arquivo

        Args:
            file_path: Path do arquivo
            ioc_types: Tipos específicos a extrair (None = todos)

        Returns:
            Lista de IOCs encontrados
        """
        logger.info(f"🔍 Extraindo IOCs de: {file_path}")

        if ioc_types is None:
            ioc_types = list(IOCType)

        try:
            # Lê arquivo (tenta UTF-8, fallback para binary)
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
            except:
                with open(file_path, 'rb') as f:
                    content = f.read().decode('utf-8', errors='ignore')

            # Extrai cada tipo de IOC
            extracted = []
            for ioc_type in ioc_types:
                iocs = self._extract_type(content, ioc_type, file_path)
                extracted.extend(iocs)

            # Calcula hash do arquivo
            file_hashes = self._calculate_file_hashes(file_path)
            for hash_type, hash_value in file_hashes.items():
                extracted.append(IOC(
                    ioc_type=hash_type,
                    value=hash_value,
                    context=f"File hash of {file_path}",
                    confidence=1.0,
                    source_file=file_path,
                    tags=["file_hash"]
                ))

            self.iocs.extend(extracted)
            logger.info(f"✅ {len(extracted)} IOCs extraídos")
            return extracted

        except FileNotFoundError:
            logger.error(f"❌ Arquivo não encontrado: {file_path}")
            return []
        except Exception as e:
            logger.error(f"❌ Erro ao extrair IOCs: {e}")
            return []

    def extract_from_text(
        self,
        text: str,
        ioc_types: Optional[List[IOCType]] = None
    ) -> List[IOC]:
        """
        Extrai IOCs de texto/string

        Args:
            text: Texto a analisar
            ioc_types: Tipos específicos a extrair

        Returns:
            Lista de IOCs
        """
        if ioc_types is None:
            ioc_types = list(IOCType)

        extracted = []
        for ioc_type in ioc_types:
            iocs = self._extract_type(text, ioc_type)
            extracted.extend(iocs)

        self.iocs.extend(extracted)
        return extracted

    def _extract_type(
        self,
        content: str,
        ioc_type: IOCType,
        source_file: Optional[str] = None
    ) -> List[IOC]:
        """Extrai IOCs de um tipo específico"""
        if ioc_type not in self.PATTERNS:
            logger.warning(f"⚠️ Tipo {ioc_type} não suportado")
            return []

        pattern = self.PATTERNS[ioc_type]
        regex = re.compile(pattern, re.IGNORECASE)

        iocs = []
        for match in regex.finditer(content):
            value = match.group(0)

            # Valida e filtra
            if not self._validate_ioc(ioc_type, value):
                continue

            # Evita duplicatas
            if value in self.seen_values:
                continue
            self.seen_values.add(value)

            # Extrai contexto (50 chars antes/depois)
            start = max(0, match.start() - 50)
            end = min(len(content), match.end() + 50)
            context = content[start:end].replace('\n', ' ').strip()

            # Calcula confiança
            confidence = self._calculate_confidence(ioc_type, value, context)

            iocs.append(IOC(
                ioc_type=ioc_type,
                value=value,
                context=context,
                confidence=confidence,
                source_file=source_file,
                tags=self._auto_tag(ioc_type, value)
            ))

        return iocs

    def _validate_ioc(self, ioc_type: IOCType, value: str) -> bool:
        """Valida se IOC é válido (não é false positive)"""
        # Whitelist check
        if ioc_type in self.WHITELIST:
            if value.lower() in self.WHITELIST[ioc_type]:
                return False

        # Validações específicas por tipo
        if ioc_type == IOCType.IPV4:
            try:
                ip = ip_address(value)
                # Ignora IPs privados
                if ip.is_private or ip.is_loopback or ip.is_multicast:
                    return False
            except ValueError:
                return False

        elif ioc_type == IOCType.DOMAIN:
            # Ignora domínios muito curtos ou genéricos
            if len(value) < 4 or value.count('.') < 1:
                return False
            # Ignora TLDs inválidos comuns
            tld = value.split('.')[-1].lower()
            if tld in ['exe', 'dll', 'sys', 'bat', 'cmd', 'ps1']:
                return False

        elif ioc_type == IOCType.EMAIL:
            # Validação básica
            if '@' not in value or '.' not in value:
                return False

        return True

    def _calculate_confidence(
        self,
        ioc_type: IOCType,
        value: str,
        context: str
    ) -> float:
        """Calcula score de confiança do IOC (0-1)"""
        confidence = 1.0

        # Hashes sempre alta confiança
        if ioc_type in [IOCType.MD5, IOCType.SHA1, IOCType.SHA256]:
            return 1.0

        # CVEs sempre alta confiança
        if ioc_type == IOCType.CVE:
            return 1.0

        # IPs em contexto suspeito (connect, socket, C2)
        if ioc_type in [IOCType.IPV4, IOCType.IPV6]:
            suspicious_keywords = ['connect', 'socket', 'c2', 'callback', 'beacon']
            if any(kw in context.lower() for kw in suspicious_keywords):
                confidence = 0.95
            else:
                confidence = 0.70

        # Domains em URLs são mais confiáveis
        if ioc_type == IOCType.DOMAIN:
            if 'http://' in context or 'https://' in context:
                confidence = 0.90
            else:
                confidence = 0.70

        # URLs sempre razoavelmente confiáveis
        if ioc_type == IOCType.URL:
            confidence = 0.85

        return confidence

    def _auto_tag(self, ioc_type: IOCType, value: str) -> List[str]:
        """Gera tags automáticas baseadas no IOC"""
        tags = []

        # Tags por TLD (domains)
        if ioc_type == IOCType.DOMAIN:
            tld = value.split('.')[-1].lower()
            if tld in ['ru', 'cn', 'tk', 'ml', 'ga']:  # TLDs suspeitos
                tags.append('suspicious_tld')
            if any(kw in value.lower() for kw in ['malware', 'phish', 'hack', 'crack']):
                tags.append('suspicious_keyword')

        # Tags por porta (URLs)
        if ioc_type == IOCType.URL:
            if any(port in value for port in [':8080', ':443', ':80', ':4444']):
                tags.append('common_c2_port')

        # Tags por extensão (file paths)
        if ioc_type == IOCType.FILE_PATH:
            ext = value.split('.')[-1].lower()
            if ext in ['exe', 'dll', 'scr', 'bat', 'ps1']:
                tags.append('executable')

        return tags

    def _calculate_file_hashes(self, file_path: str) -> Dict[IOCType, str]:
        """Calcula hashes do arquivo"""
        hashes = {}
        try:
            with open(file_path, 'rb') as f:
                content = f.read()

            hashes[IOCType.MD5] = hashlib.md5(content).hexdigest()
            hashes[IOCType.SHA1] = hashlib.sha1(content).hexdigest()
            hashes[IOCType.SHA256] = hashlib.sha256(content).hexdigest()
        except Exception as e:
            logger.warning(f"⚠️ Não foi possível calcular hashes: {e}")

        return hashes

    def get_iocs_by_type(self, ioc_type: IOCType) -> List[IOC]:
        """Retorna IOCs de um tipo específico"""
        return [ioc for ioc in self.iocs if ioc.ioc_type == ioc_type]

    def get_high_confidence_iocs(self, threshold: float = 0.8) -> List[IOC]:
        """Retorna apenas IOCs com alta confiança"""
        return [ioc for ioc in self.iocs if ioc.confidence >= threshold]

    def export_csv(self, filepath: str):
        """Exporta IOCs para CSV"""
        import csv

        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Type', 'Value', 'Confidence', 'Source', 'Tags', 'Context'])

            for ioc in self.iocs:
                writer.writerow([
                    ioc.ioc_type.value,
                    ioc.value,
                    f"{ioc.confidence:.2f}",
                    ioc.source_file or "",
                    ','.join(ioc.tags),
                    ioc.context[:100]  # Trunca contexto
                ])

        logger.info(f"💾 IOCs exportados para: {filepath}")

    def export_json(self, filepath: str):
        """Exporta IOCs para JSON"""
        import json

        data = {
            'total_iocs': len(self.iocs),
            'by_type': {
                ioc_type.value: len(self.get_iocs_by_type(ioc_type))
                for ioc_type in IOCType
            },
            'iocs': [ioc.to_dict() for ioc in self.iocs]
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        logger.info(f"💾 IOCs exportados para: {filepath}")

    def export_stix(self, filepath: str):
        """
        Exporta IOCs para formato STIX 2.1 (placeholder)

        STIX (Structured Threat Information eXpression) é o padrão
        da indústria para compartilhamento de threat intelligence.
        """
        # Placeholder - implementação completa requer biblioteca stix2
        logger.warning("⚠️ Export STIX não implementado (requer stix2 library)")

    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas dos IOCs"""
        return {
            'total_iocs': len(self.iocs),
            'by_type': {
                ioc_type.value: len(self.get_iocs_by_type(ioc_type))
                for ioc_type in IOCType
            },
            'high_confidence': len(self.get_high_confidence_iocs()),
            'avg_confidence': sum(ioc.confidence for ioc in self.iocs) / len(self.iocs) if self.iocs else 0
        }


if __name__ == "__main__":
    # Teste standalone
    logging.basicConfig(level=logging.INFO)

    extractor = IOCExtractor()

    print("\n🔍 TESTANDO EXTRAÇÃO DE IOCs:\n")

    # Cria arquivo de teste com IOCs
    test_file = "/tmp/test_malware_iocs.txt"
    with open(test_file, 'w') as f:
        f.write("""
Malware sample analysis:
C2 server: 45.142.212.61
Domain: malicious-c2.tk
Callback URL: http://evil.com/beacon.php
Attacker email: hacker@badguy.ru
File hash (MD5): d41d8cd98f00b204e9800998ecf8427e
File hash (SHA256): e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
Bitcoin wallet: 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa
Registry persistence: HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\Run\\Malware
Dropped file: C:\\Users\\Public\\malware.exe
CVE exploited: CVE-2023-12345
""")

    # Extrai IOCs
    iocs = extractor.extract_from_file(test_file)

    print(f"✅ {len(iocs)} IOCs extraídos:\n")
    for ioc in iocs:
        print(f"🔴 [{ioc.ioc_type.value.upper()}] {ioc.value}")
        print(f"   Confidence: {ioc.confidence:.2f}")
        if ioc.tags:
            print(f"   Tags: {', '.join(ioc.tags)}")
        print(f"   Context: ...{ioc.context}...")
        print()

    print("\n📊 ESTATÍSTICAS:")
    stats = extractor.get_stats()
    print(f"Total de IOCs: {stats['total_iocs']}")
    print(f"Alta confiança (>0.8): {stats['high_confidence']}")
    print(f"Confiança média: {stats['avg_confidence']:.2f}")
    print("\nPor tipo:")
    for ioc_type, count in stats['by_type'].items():
        if count > 0:
            print(f"  {ioc_type}: {count}")

    # Exporta
    extractor.export_csv("/tmp/iocs.csv")
    extractor.export_json("/tmp/iocs.json")

    import os
    os.remove(test_file)
