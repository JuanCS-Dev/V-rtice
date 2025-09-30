"""
Offline Threat Intelligence Engine
Não depende de APIs externas - usa bases locais e heurísticas
"""

import ipaddress
import re
import dns.resolver
import socket
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import sqlite3
import os

class OfflineThreatIntel:
    """
    Engine de threat intel completamente offline
    Usa databases locais e heurísticas avançadas
    """

    def __init__(self, db_path="threat_intel.db"):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """Inicializa database local de threat intel"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Tabela de IPs conhecidos maliciosos
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS malicious_ips (
                ip TEXT PRIMARY KEY,
                threat_type TEXT,
                confidence INTEGER,
                first_seen TEXT,
                last_seen TEXT,
                description TEXT,
                source TEXT
            )
        """)

        # Tabela de domains maliciosos
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS malicious_domains (
                domain TEXT PRIMARY KEY,
                threat_type TEXT,
                confidence INTEGER,
                first_seen TEXT,
                last_seen TEXT,
                description TEXT,
                source TEXT
            )
        """)

        # Tabela de ASN suspeitos
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS suspicious_asn (
                asn INTEGER PRIMARY KEY,
                name TEXT,
                country TEXT,
                risk_score INTEGER,
                description TEXT
            )
        """)

        # Tabela de CIDRs suspeitos (ranges de IPs)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS suspicious_cidrs (
                cidr TEXT PRIMARY KEY,
                threat_type TEXT,
                risk_score INTEGER,
                description TEXT
            )
        """)

        conn.commit()
        conn.close()

        # Popular com dados iniciais
        self.populate_initial_data()

    def populate_initial_data(self):
        """Popula database com dados conhecidos de ameaças"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Known bad IP ranges (exemplo: Tor exit nodes, VPN abuse, etc)
        known_bad_cidrs = [
            # Tor exit nodes ranges (exemplo)
            ("185.220.100.0/22", "tor_exit_node", 70, "Known Tor exit node range"),
            # Hosting abuse ranges
            ("5.188.0.0/16", "hosting_abuse", 60, "Known for hosting malicious content"),
            # Cloud provider abuse
            ("103.253.145.0/24", "vpn_abuse", 50, "VPN service abuse"),
        ]

        cursor.executemany("""
            INSERT OR IGNORE INTO suspicious_cidrs (cidr, threat_type, risk_score, description)
            VALUES (?, ?, ?, ?)
        """, known_bad_cidrs)

        # Known malicious ASNs
        known_bad_asns = [
            (60068, "CDN77", "CZ", 40, "Bulletproof hosting history"),
            (206264, "Amarutu Technology", "SC", 80, "Known for hosting malware"),
        ]

        cursor.executemany("""
            INSERT OR IGNORE INTO suspicious_asn (asn, name, country, risk_score, description)
            VALUES (?, ?, ?, ?, ?)
        """, known_bad_asns)

        conn.commit()
        conn.close()

    def check_ip(self, ip: str) -> Dict:
        """Análise offline de IP usando heurísticas e base local"""
        result = {
            "ip": ip,
            "threat_score": 0,
            "is_malicious": False,
            "indicators": [],
            "confidence": "medium",
            "details": {}
        }

        try:
            # 1. Check database local
            local_threat = self._check_local_database(ip, "ip")
            if local_threat:
                result["threat_score"] += 60
                result["indicators"].append(f"Found in local threat database: {local_threat['threat_type']}")
                result["details"]["database_match"] = local_threat

            # 2. Check CIDR ranges suspeitos
            cidr_check = self._check_cidr_ranges(ip)
            if cidr_check:
                result["threat_score"] += cidr_check["risk_score"]
                result["indicators"].append(f"IP in suspicious range: {cidr_check['description']}")
                result["details"]["cidr_match"] = cidr_check

            # 3. DNS reverse lookup heuristics
            dns_analysis = self._analyze_reverse_dns(ip)
            if dns_analysis["suspicious"]:
                result["threat_score"] += dns_analysis["score"]
                result["indicators"].extend(dns_analysis["indicators"])
                result["details"]["dns_analysis"] = dns_analysis

            # 4. Port scan footprint (detecta se IP está fazendo scanning)
            scan_detection = self._detect_scanning_behavior(ip)
            if scan_detection["is_scanner"]:
                result["threat_score"] += 30
                result["indicators"].append("IP exhibits scanning behavior")
                result["details"]["scan_detection"] = scan_detection

            # 5. Geolocation heuristics
            geo_analysis = self._analyze_geolocation(ip)
            if geo_analysis["suspicious"]:
                result["threat_score"] += geo_analysis["score"]
                result["indicators"].extend(geo_analysis["indicators"])
                result["details"]["geolocation"] = geo_analysis

            # 6. Check if IP is in known good lists (whitelist)
            if self._is_whitelisted(ip):
                result["threat_score"] = max(0, result["threat_score"] - 50)
                result["indicators"].append("IP in whitelist (known good)")

            # Determine if malicious
            result["is_malicious"] = result["threat_score"] >= 60

            # Determine confidence
            indicator_count = len(result["indicators"])
            if indicator_count >= 3:
                result["confidence"] = "high"
            elif indicator_count >= 1:
                result["confidence"] = "medium"
            else:
                result["confidence"] = "low"

        except Exception as e:
            result["error"] = str(e)

        return result

    def check_domain(self, domain: str) -> Dict:
        """Análise offline de domínio"""
        result = {
            "domain": domain,
            "threat_score": 0,
            "is_malicious": False,
            "indicators": [],
            "confidence": "medium",
            "details": {}
        }

        try:
            # 1. Check database local
            local_threat = self._check_local_database(domain, "domain")
            if local_threat:
                result["threat_score"] += 70
                result["indicators"].append(f"Found in local threat database: {local_threat['threat_type']}")
                result["details"]["database_match"] = local_threat

            # 2. Domain age heuristics (domains muito novos são suspeitos)
            age_analysis = self._analyze_domain_age(domain)
            if age_analysis["suspicious"]:
                result["threat_score"] += age_analysis["score"]
                result["indicators"].extend(age_analysis["indicators"])
                result["details"]["age_analysis"] = age_analysis

            # 3. Domain name heuristics (typosquatting, homographs, etc)
            name_analysis = self._analyze_domain_name(domain)
            if name_analysis["suspicious"]:
                result["threat_score"] += name_analysis["score"]
                result["indicators"].extend(name_analysis["indicators"])
                result["details"]["name_analysis"] = name_analysis

            # 4. DNS records analysis
            dns_analysis = self._analyze_dns_records(domain)
            if dns_analysis["suspicious"]:
                result["threat_score"] += dns_analysis["score"]
                result["indicators"].extend(dns_analysis["indicators"])
                result["details"]["dns_analysis"] = dns_analysis

            # 5. TLD analysis (alguns TLDs são mais abusados)
            tld_analysis = self._analyze_tld(domain)
            if tld_analysis["suspicious"]:
                result["threat_score"] += tld_analysis["score"]
                result["indicators"].extend(tld_analysis["indicators"])
                result["details"]["tld_analysis"] = tld_analysis

            # Determine if malicious
            result["is_malicious"] = result["threat_score"] >= 60

            # Determine confidence
            indicator_count = len(result["indicators"])
            if indicator_count >= 3:
                result["confidence"] = "high"
            elif indicator_count >= 1:
                result["confidence"] = "medium"
            else:
                result["confidence"] = "low"

        except Exception as e:
            result["error"] = str(e)

        return result

    def _check_local_database(self, target: str, target_type: str) -> Optional[Dict]:
        """Verifica se target está no database local"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        if target_type == "ip":
            cursor.execute("""
                SELECT threat_type, confidence, description, source
                FROM malicious_ips
                WHERE ip = ?
            """, (target,))
        else:
            cursor.execute("""
                SELECT threat_type, confidence, description, source
                FROM malicious_domains
                WHERE domain = ?
            """, (target,))

        row = cursor.fetchone()
        conn.close()

        if row:
            return {
                "threat_type": row[0],
                "confidence": row[1],
                "description": row[2],
                "source": row[3]
            }
        return None

    def _check_cidr_ranges(self, ip: str) -> Optional[Dict]:
        """Verifica se IP está em range suspeito"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT cidr, threat_type, risk_score, description FROM suspicious_cidrs")

        ip_obj = ipaddress.ip_address(ip)

        for row in cursor.fetchall():
            cidr = row[0]
            try:
                if ip_obj in ipaddress.ip_network(cidr):
                    conn.close()
                    return {
                        "cidr": cidr,
                        "threat_type": row[1],
                        "risk_score": row[2],
                        "description": row[3]
                    }
            except:
                continue

        conn.close()
        return None

    def _analyze_reverse_dns(self, ip: str) -> Dict:
        """Analisa DNS reverso para heurísticas"""
        result = {
            "suspicious": False,
            "score": 0,
            "indicators": [],
            "ptr_record": None
        }

        try:
            ptr_record = socket.gethostbyaddr(ip)[0]
            result["ptr_record"] = ptr_record

            # Heurísticas de PTR suspeitos
            suspicious_patterns = [
                r'\.dynamic\.',
                r'\.dyn\.',
                r'\.pool\.',
                r'\.dhcp\.',
                r'\.cable\.',
                r'\.adsl\.',
                r'generic',
                r'unassigned',
                r'\d{1,3}-\d{1,3}-\d{1,3}-\d{1,3}',  # IP in hostname
            ]

            for pattern in suspicious_patterns:
                if re.search(pattern, ptr_record, re.IGNORECASE):
                    result["suspicious"] = True
                    result["score"] += 10
                    result["indicators"].append(f"Suspicious PTR pattern: {pattern}")

        except:
            # No PTR record pode ser suspeito para servidores
            result["suspicious"] = True
            result["score"] = 5
            result["indicators"].append("No reverse DNS record")

        return result

    def _detect_scanning_behavior(self, ip: str) -> Dict:
        """Detecta comportamento de scanning (placeholder - requer logs)"""
        # Em produção, isso analisaria logs de firewall/IDS
        # Por enquanto, retorna False
        return {
            "is_scanner": False,
            "scan_attempts": 0,
            "last_scan": None
        }

    def _analyze_geolocation(self, ip: str) -> Dict:
        """Analisa geolocalização do IP (heurísticas)"""
        result = {
            "suspicious": False,
            "score": 0,
            "indicators": []
        }

        # Verifica se é IP privado
        try:
            ip_obj = ipaddress.ip_address(ip)
            if ip_obj.is_private:
                result["indicators"].append("Private IP address")
                return result

            if ip_obj.is_reserved or ip_obj.is_loopback:
                result["suspicious"] = True
                result["score"] = 80
                result["indicators"].append("Reserved or loopback IP")
        except:
            pass

        return result

    def _is_whitelisted(self, ip: str) -> bool:
        """Verifica se IP está em whitelist (known good)"""
        # Known good IPs (Google DNS, Cloudflare, etc)
        whitelist = [
            "8.8.8.8", "8.8.4.4",  # Google DNS
            "1.1.1.1", "1.0.0.1",  # Cloudflare DNS
            "208.67.222.222", "208.67.220.220",  # OpenDNS
        ]

        return ip in whitelist

    def _analyze_domain_age(self, domain: str) -> Dict:
        """Analisa idade do domínio (heurística)"""
        # Em produção, consultaria WHOIS local
        # Por enquanto, análise básica
        return {
            "suspicious": False,
            "score": 0,
            "indicators": [],
            "age_days": None
        }

    def _analyze_domain_name(self, domain: str) -> Dict:
        """Analisa nome do domínio para padrões suspeitos"""
        result = {
            "suspicious": False,
            "score": 0,
            "indicators": []
        }

        # Patterns suspeitos em domain names
        suspicious_keywords = [
            'verify', 'account', 'secure', 'login', 'signin', 'update',
            'banking', 'paypal', 'amazon', 'apple', 'microsoft',
            'verification', 'suspended', 'locked', 'confirm'
        ]

        domain_lower = domain.lower()

        for keyword in suspicious_keywords:
            if keyword in domain_lower:
                result["suspicious"] = True
                result["score"] += 15
                result["indicators"].append(f"Suspicious keyword in domain: {keyword}")

        # Detect excessive hyphens (typosquatting technique)
        if domain_lower.count('-') > 2:
            result["suspicious"] = True
            result["score"] += 10
            result["indicators"].append("Excessive hyphens in domain name")

        # Detect numbers in suspicious places
        if re.search(r'\d{3,}', domain):
            result["suspicious"] = True
            result["score"] += 10
            result["indicators"].append("Suspicious number pattern in domain")

        # Very long domain names
        if len(domain) > 50:
            result["suspicious"] = True
            result["score"] += 10
            result["indicators"].append("Unusually long domain name")

        return result

    def _analyze_dns_records(self, domain: str) -> Dict:
        """Analisa registros DNS do domínio"""
        result = {
            "suspicious": False,
            "score": 0,
            "indicators": [],
            "records": {}
        }

        try:
            # Check A records
            try:
                answers = dns.resolver.resolve(domain, 'A')
                ips = [str(rdata) for rdata in answers]
                result["records"]["A"] = ips

                # Se tem muitos A records (CDN ou distribuído demais)
                if len(ips) > 10:
                    result["suspicious"] = True
                    result["score"] += 5
                    result["indicators"].append("Excessive A records (possible DGA)")
            except:
                result["indicators"].append("No A records found")
                result["suspicious"] = True
                result["score"] += 15

            # Check MX records (phishing domains geralmente não têm)
            try:
                mx_answers = dns.resolver.resolve(domain, 'MX')
                result["records"]["MX"] = [str(rdata) for rdata in mx_answers]
            except:
                result["indicators"].append("No MX records (suspicious for business domain)")
                result["score"] += 5

            # Check TXT records
            try:
                txt_answers = dns.resolver.resolve(domain, 'TXT')
                result["records"]["TXT"] = [str(rdata) for rdata in txt_answers]
            except:
                pass

        except Exception as e:
            result["error"] = str(e)

        return result

    def _analyze_tld(self, domain: str) -> Dict:
        """Analisa TLD do domínio"""
        result = {
            "suspicious": False,
            "score": 0,
            "indicators": [],
            "tld": None
        }

        # Extract TLD
        parts = domain.split('.')
        if len(parts) < 2:
            return result

        tld = parts[-1].lower()
        result["tld"] = tld

        # TLDs frequentemente abusados
        high_risk_tlds = [
            'tk', 'ml', 'ga', 'cf', 'gq',  # Free TLDs
            'top', 'xyz', 'club', 'work',
            'ru', 'cn',  # High abuse rates
        ]

        if tld in high_risk_tlds:
            result["suspicious"] = True
            result["score"] = 20
            result["indicators"].append(f"High-risk TLD: .{tld}")

        return result

    def add_threat(self, target: str, target_type: str, threat_type: str,
                   confidence: int, description: str, source: str = "manual"):
        """Adiciona nova ameaça ao database local"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        now = datetime.now().isoformat()

        if target_type == "ip":
            cursor.execute("""
                INSERT OR REPLACE INTO malicious_ips
                (ip, threat_type, confidence, first_seen, last_seen, description, source)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (target, threat_type, confidence, now, now, description, source))
        else:
            cursor.execute("""
                INSERT OR REPLACE INTO malicious_domains
                (domain, threat_type, confidence, first_seen, last_seen, description, source)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (target, threat_type, confidence, now, now, description, source))

        conn.commit()
        conn.close()

    def update_from_feed(self, feed_data: List[Dict]):
        """Atualiza database com feed de ameaças (ex: de threat intel sharing communities)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        for item in feed_data:
            target = item.get("target")
            target_type = item.get("type", "ip")
            threat_type = item.get("threat_type", "unknown")
            confidence = item.get("confidence", 50)
            description = item.get("description", "")
            source = item.get("source", "feed")

            self.add_threat(target, target_type, threat_type, confidence, description, source)

        conn.close()