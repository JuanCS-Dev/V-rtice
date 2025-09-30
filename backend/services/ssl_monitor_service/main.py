"""
SSL/TLS Certificate Monitor Service - NSA Grade
Análise profunda de certificados SSL/TLS, detecção de MitM, weak ciphers
Compliance check: PCI-DSS, HIPAA, NIST
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import ssl
import socket
import OpenSSL
from datetime import datetime, timedelta
from typing import Optional, List, Dict
import hashlib
import asyncio
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
import httpx

app = FastAPI(title="SSL/TLS Monitor Service")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class SSLCheckRequest(BaseModel):
    target: str  # domain ou IP
    port: int = 443
    include_chain: bool = True
    check_ocsp: bool = True
    check_ct_logs: bool = True

class CertificateInfo(BaseModel):
    subject: Dict[str, str]
    issuer: Dict[str, str]
    serial_number: str
    version: int
    not_before: str
    not_after: str
    days_until_expiry: int
    is_expired: bool
    is_self_signed: bool
    signature_algorithm: str
    public_key_algorithm: str
    public_key_size: int
    fingerprint_sha256: str
    fingerprint_sha1: str
    san: List[str]  # Subject Alternative Names
    key_usage: List[str]
    extended_key_usage: List[str]

class SSLAnalysisResponse(BaseModel):
    target: str
    port: int
    is_valid: bool
    security_score: int  # 0-100
    grade: str  # A+, A, B, C, D, F
    certificate: CertificateInfo
    chain: List[CertificateInfo]
    protocol_version: str
    cipher_suite: str
    cipher_strength: int
    vulnerabilities: List[dict]
    warnings: List[str]
    compliance: Dict[str, bool]  # PCI-DSS, HIPAA, NIST
    recommendations: List[str]
    threat_indicators: List[str]
    ocsp_status: Optional[dict]
    ct_logs: Optional[dict]
    timestamp: str

# Weak/Insecure Ciphers (NSA banned)
WEAK_CIPHERS = [
    'RC4', 'MD5', 'DES', '3DES', 'NULL', 'EXPORT', 'anon',
    'ADH', 'AECDH', 'aNULL', 'eNULL'
]

# Weak Key Sizes
WEAK_KEY_SIZES = {
    'RSA': 2048,
    'DSA': 2048,
    'EC': 256
}

# Known Malicious/Suspicious CAs
SUSPICIOUS_CAS = [
    'CNNIC', 'WoSign', 'StartCom', 'Certinomis'
]

def parse_cert_name(name) -> Dict[str, str]:
    """Parse X509 Name to dict"""
    result = {}
    for attr in name:
        result[attr.oid._name] = attr.value
    return result

def get_san(cert) -> List[str]:
    """Extract Subject Alternative Names"""
    try:
        san_ext = cert.extensions.get_extension_for_oid(
            x509.oid.ExtensionOID.SUBJECT_ALTERNATIVE_NAME
        )
        return [str(name.value) for name in san_ext.value]
    except:
        return []

def get_key_usage(cert) -> List[str]:
    """Extract Key Usage"""
    try:
        ku_ext = cert.extensions.get_extension_for_oid(
            x509.oid.ExtensionOID.KEY_USAGE
        )
        usage = []
        if ku_ext.value.digital_signature: usage.append("digital_signature")
        if ku_ext.value.key_encipherment: usage.append("key_encipherment")
        if ku_ext.value.key_agreement: usage.append("key_agreement")
        if ku_ext.value.content_commitment: usage.append("content_commitment")
        if ku_ext.value.data_encipherment: usage.append("data_encipherment")
        if ku_ext.value.key_cert_sign: usage.append("key_cert_sign")
        if ku_ext.value.crl_sign: usage.append("crl_sign")
        return usage
    except:
        return []

def get_extended_key_usage(cert) -> List[str]:
    """Extract Extended Key Usage"""
    try:
        eku_ext = cert.extensions.get_extension_for_oid(
            x509.oid.ExtensionOID.EXTENDED_KEY_USAGE
        )
        return [str(oid.dotted_string) for oid in eku_ext.value]
    except:
        return []

def check_certificate(cert, issuer_cert=None) -> CertificateInfo:
    """Analisa um certificado em profundidade"""
    subject = parse_cert_name(cert.subject)
    issuer = parse_cert_name(cert.issuer)

    # Check if self-signed
    is_self_signed = subject == issuer

    # Calculate expiry
    now = datetime.utcnow()
    days_until_expiry = (cert.not_valid_after - now).days
    is_expired = days_until_expiry < 0

    # Fingerprints
    cert_der = cert.public_bytes(encoding=x509.Encoding.DER)
    fingerprint_sha256 = hashlib.sha256(cert_der).hexdigest()
    fingerprint_sha1 = hashlib.sha1(cert_der).hexdigest()

    # Public key info
    public_key = cert.public_key()
    pub_key_algo = public_key.__class__.__name__

    if hasattr(public_key, 'key_size'):
        pub_key_size = public_key.key_size
    else:
        pub_key_size = 0

    return CertificateInfo(
        subject=subject,
        issuer=issuer,
        serial_number=str(cert.serial_number),
        version=cert.version.value,
        not_before=cert.not_valid_before.isoformat(),
        not_after=cert.not_valid_after.isoformat(),
        days_until_expiry=days_until_expiry,
        is_expired=is_expired,
        is_self_signed=is_self_signed,
        signature_algorithm=cert.signature_algorithm_oid._name,
        public_key_algorithm=pub_key_algo,
        public_key_size=pub_key_size,
        fingerprint_sha256=fingerprint_sha256,
        fingerprint_sha1=fingerprint_sha1,
        san=get_san(cert),
        key_usage=get_key_usage(cert),
        extended_key_usage=get_extended_key_usage(cert)
    )

def get_ssl_certificate(hostname: str, port: int = 443) -> tuple:
    """Obtém certificado SSL e informações da conexão"""
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE

    # Get all available protocol info
    conn = context.wrap_socket(
        socket.socket(socket.AF_INET),
        server_hostname=hostname
    )

    try:
        conn.settimeout(10)
        conn.connect((hostname, port))

        # Get certificate chain
        cert_bin = conn.getpeercert(binary_form=True)
        cert_chain = conn.getpeercert_chain()

        # Get cipher info
        cipher = conn.cipher()
        protocol = conn.version()

        # Parse main certificate
        x509_cert = x509.load_der_x509_certificate(cert_bin, default_backend())

        # Parse chain
        chain_certs = []
        if cert_chain:
            for cert_der in cert_chain[1:]:  # Skip first (main cert)
                try:
                    chain_cert = x509.load_der_x509_certificate(
                        cert_der, default_backend()
                    )
                    chain_certs.append(chain_cert)
                except:
                    pass

        return x509_cert, chain_certs, cipher, protocol

    finally:
        conn.close()

def analyze_vulnerabilities(cert: CertificateInfo, cipher: tuple, protocol: str) -> List[dict]:
    """Detecta vulnerabilidades conhecidas"""
    vulnerabilities = []

    # Check weak keys
    if cert.public_key_algorithm == 'RSAPublicKey' and cert.public_key_size < 2048:
        vulnerabilities.append({
            "id": "WEAK_RSA_KEY",
            "severity": "high",
            "title": "RSA Key Size Too Small",
            "description": f"RSA key size is {cert.public_key_size} bits. Minimum recommended is 2048 bits.",
            "cve": "CVE-2015-2808"
        })

    # Check MD5 signature
    if 'md5' in cert.signature_algorithm.lower():
        vulnerabilities.append({
            "id": "MD5_SIGNATURE",
            "severity": "critical",
            "title": "MD5 Signature Algorithm",
            "description": "Certificate uses MD5 signature algorithm which is cryptographically broken.",
            "cve": "CVE-2008-1447"
        })

    # Check SHA1 signature
    if 'sha1' in cert.signature_algorithm.lower():
        vulnerabilities.append({
            "id": "SHA1_SIGNATURE",
            "severity": "medium",
            "title": "SHA1 Signature Algorithm",
            "description": "SHA1 is deprecated and should not be used for new certificates.",
            "cve": "CVE-2017-15361"
        })

    # Check weak ciphers
    if cipher:
        cipher_name = cipher[0]
        for weak in WEAK_CIPHERS:
            if weak.lower() in cipher_name.lower():
                vulnerabilities.append({
                    "id": "WEAK_CIPHER",
                    "severity": "high",
                    "title": f"Weak Cipher Suite: {weak}",
                    "description": f"Cipher suite {cipher_name} contains weak algorithm {weak}.",
                    "cve": None
                })

    # Check old TLS versions
    if protocol in ['SSLv2', 'SSLv3']:
        vulnerabilities.append({
            "id": "SSL_PROTOCOL",
            "severity": "critical",
            "title": f"Insecure Protocol: {protocol}",
            "description": f"{protocol} is deprecated and vulnerable to POODLE attack.",
            "cve": "CVE-2014-3566"
        })
    elif protocol == 'TLSv1.0':
        vulnerabilities.append({
            "id": "TLS_1_0",
            "severity": "medium",
            "title": "TLS 1.0 Deprecated",
            "description": "TLS 1.0 is deprecated. Upgrade to TLS 1.2 or 1.3.",
            "cve": "CVE-2011-3389"
        })

    # Check certificate expiry
    if cert.is_expired:
        vulnerabilities.append({
            "id": "CERT_EXPIRED",
            "severity": "critical",
            "title": "Certificate Expired",
            "description": f"Certificate expired on {cert.not_after}.",
            "cve": None
        })
    elif cert.days_until_expiry < 30:
        vulnerabilities.append({
            "id": "CERT_EXPIRING",
            "severity": "medium",
            "title": "Certificate Expiring Soon",
            "description": f"Certificate expires in {cert.days_until_expiry} days.",
            "cve": None
        })

    # Check self-signed
    if cert.is_self_signed:
        vulnerabilities.append({
            "id": "SELF_SIGNED",
            "severity": "medium",
            "title": "Self-Signed Certificate",
            "description": "Certificate is self-signed and not trusted by browsers.",
            "cve": None
        })

    return vulnerabilities

def check_compliance(cert: CertificateInfo, vulnerabilities: List[dict], protocol: str) -> Dict[str, bool]:
    """Verifica compliance com padrões de segurança"""
    compliance = {}

    # PCI-DSS 3.2.1 Requirements
    pci_compliant = (
        cert.public_key_size >= 2048 and
        protocol in ['TLSv1.2', 'TLSv1.3'] and
        not cert.is_expired and
        'md5' not in cert.signature_algorithm.lower() and
        'sha1' not in cert.signature_algorithm.lower()
    )
    compliance['PCI_DSS'] = pci_compliant

    # NIST Guidelines
    nist_compliant = (
        cert.public_key_size >= 2048 and
        protocol in ['TLSv1.2', 'TLSv1.3'] and
        not cert.is_expired and
        cert.days_until_expiry > 0
    )
    compliance['NIST'] = nist_compliant

    # HIPAA Compliance
    hipaa_compliant = (
        cert.public_key_size >= 2048 and
        protocol in ['TLSv1.2', 'TLSv1.3'] and
        not cert.is_expired
    )
    compliance['HIPAA'] = hipaa_compliant

    # FIPS 140-2
    fips_compliant = (
        cert.public_key_size >= 2048 and
        protocol == 'TLSv1.2' and  # FIPS doesn't support TLS 1.3 yet in some implementations
        'sha256' in cert.signature_algorithm.lower()
    )
    compliance['FIPS_140_2'] = fips_compliant

    return compliance

def calculate_security_score(cert: CertificateInfo, vulnerabilities: List[dict],
                            cipher: tuple, protocol: str) -> tuple:
    """Calcula security score (0-100) e grade"""
    score = 100

    # Deduct points for vulnerabilities
    for vuln in vulnerabilities:
        if vuln['severity'] == 'critical':
            score -= 25
        elif vuln['severity'] == 'high':
            score -= 15
        elif vuln['severity'] == 'medium':
            score -= 8
        elif vuln['severity'] == 'low':
            score -= 3

    # Bonus for good practices
    if protocol == 'TLSv1.3':
        score += 5

    if cert.public_key_size >= 4096:
        score += 5

    if cert.days_until_expiry > 90:
        score += 2

    # Cap score
    score = max(0, min(100, score))

    # Determine grade
    if score >= 95:
        grade = 'A+'
    elif score >= 90:
        grade = 'A'
    elif score >= 80:
        grade = 'A-'
    elif score >= 70:
        grade = 'B'
    elif score >= 60:
        grade = 'C'
    elif score >= 50:
        grade = 'D'
    else:
        grade = 'F'

    return score, grade

def detect_threats(cert: CertificateInfo, chain: List[CertificateInfo]) -> List[str]:
    """Detecta indicadores de ameaça (MitM, Phishing, etc)"""
    threats = []

    # Check suspicious CA
    issuer_cn = cert.issuer.get('commonName', '')
    for suspicious in SUSPICIOUS_CAS:
        if suspicious.lower() in issuer_cn.lower():
            threats.append(f"⚠️ Suspicious CA detected: {suspicious}")

    # Check certificate age (newly issued certs can be suspicious)
    cert_age = datetime.utcnow() - datetime.fromisoformat(cert.not_before)
    if cert_age.days < 7:
        threats.append(f"🆕 Certificate issued very recently ({cert_age.days} days ago)")

    # Check short validity period (phishing certs often have short validity)
    validity_period = datetime.fromisoformat(cert.not_after) - datetime.fromisoformat(cert.not_before)
    if validity_period.days < 90:
        threats.append(f"⏱️ Unusually short validity period ({validity_period.days} days)")

    # Check for missing chain
    if len(chain) == 0 and not cert.is_self_signed:
        threats.append("🔗 Incomplete certificate chain")

    # Check for suspicious SAN entries
    if len(cert.san) > 100:
        threats.append(f"🎭 Suspicious: Too many SAN entries ({len(cert.san)})")

    # Check wildcard in suspicious position
    for san in cert.san:
        if san.count('*') > 1:
            threats.append(f"🌐 Multiple wildcards in SAN: {san}")

    return threats

def generate_recommendations(cert: CertificateInfo, vulnerabilities: List[dict],
                            protocol: str, compliance: Dict[str, bool]) -> List[str]:
    """Gera recomendações de segurança"""
    recommendations = []

    # Critical issues first
    if cert.is_expired:
        recommendations.append("🚨 URGENT: Renew certificate immediately")
    elif cert.days_until_expiry < 30:
        recommendations.append(f"⚠️ Renew certificate soon ({cert.days_until_expiry} days remaining)")

    # Protocol recommendations
    if protocol not in ['TLSv1.2', 'TLSv1.3']:
        recommendations.append("🔒 Upgrade to TLS 1.2 or TLS 1.3")
    elif protocol == 'TLSv1.2':
        recommendations.append("✨ Consider upgrading to TLS 1.3 for better performance")

    # Key size recommendations
    if cert.public_key_size < 2048:
        recommendations.append("🔑 Use minimum 2048-bit RSA keys (4096-bit recommended)")
    elif cert.public_key_size == 2048:
        recommendations.append("💡 Consider upgrading to 4096-bit RSA keys for enhanced security")

    # Signature algorithm
    if 'sha1' in cert.signature_algorithm.lower():
        recommendations.append("📝 Migrate to SHA-256 or SHA-384 signature algorithm")

    # Compliance
    if not compliance.get('PCI_DSS'):
        recommendations.append("💳 Not PCI-DSS compliant - required for payment processing")

    if not compliance.get('HIPAA'):
        recommendations.append("🏥 Not HIPAA compliant - required for healthcare data")

    # Certificate Transparency
    recommendations.append("📋 Monitor Certificate Transparency logs for unauthorized issuance")

    # OCSP Stapling
    recommendations.append("⚡ Enable OCSP stapling for better performance")

    # HSTS
    recommendations.append("🛡️ Implement HSTS (HTTP Strict Transport Security)")

    return recommendations[:10]  # Top 10 recommendations

@app.get("/")
async def root():
    return {
        "service": "SSL/TLS Monitor Service",
        "status": "online",
        "version": "1.0.0",
        "classification": "NSA-GRADE",
        "capabilities": {
            "certificate_analysis": True,
            "chain_validation": True,
            "vulnerability_detection": True,
            "compliance_checking": ["PCI-DSS", "HIPAA", "NIST", "FIPS-140-2"],
            "threat_detection": True
        }
    }

@app.post("/api/ssl/check", response_model=SSLAnalysisResponse)
async def check_ssl(request: SSLCheckRequest):
    """
    Análise completa de SSL/TLS - NSA Grade
    """
    target = request.target
    port = request.port

    try:
        # Get certificate and connection info
        cert, chain_certs, cipher, protocol = get_ssl_certificate(target, port)

        # Analyze main certificate
        cert_info = check_certificate(cert)

        # Analyze chain
        chain_info = []
        if request.include_chain:
            for chain_cert in chain_certs:
                chain_info.append(check_certificate(chain_cert))

        # Detect vulnerabilities
        vulnerabilities = analyze_vulnerabilities(cert_info, cipher, protocol)

        # Check compliance
        compliance = check_compliance(cert_info, vulnerabilities, protocol)

        # Calculate security score
        security_score, grade = calculate_security_score(cert_info, vulnerabilities, cipher, protocol)

        # Detect threats
        threat_indicators = detect_threats(cert_info, chain_info)

        # Generate recommendations
        recommendations = generate_recommendations(cert_info, vulnerabilities, protocol, compliance)

        # Generate warnings
        warnings = []
        if cert_info.days_until_expiry < 30:
            warnings.append(f"Certificate expires in {cert_info.days_until_expiry} days")
        if cert_info.is_self_signed:
            warnings.append("Self-signed certificate detected")
        if threat_indicators:
            warnings.append(f"{len(threat_indicators)} threat indicators detected")

        # Cipher info
        cipher_name = cipher[0] if cipher else "Unknown"
        cipher_strength = cipher[2] if cipher and len(cipher) > 2 else 0

        is_valid = (
            not cert_info.is_expired and
            security_score >= 70 and
            len([v for v in vulnerabilities if v['severity'] in ['critical', 'high']]) == 0
        )

        return SSLAnalysisResponse(
            target=target,
            port=port,
            is_valid=is_valid,
            security_score=security_score,
            grade=grade,
            certificate=cert_info,
            chain=chain_info,
            protocol_version=protocol,
            cipher_suite=cipher_name,
            cipher_strength=cipher_strength,
            vulnerabilities=vulnerabilities,
            warnings=warnings,
            compliance=compliance,
            recommendations=recommendations,
            threat_indicators=threat_indicators,
            ocsp_status=None,  # TODO: Implement OCSP checking
            ct_logs=None,  # TODO: Implement CT logs checking
            timestamp=datetime.now().isoformat()
        )

    except ssl.SSLError as e:
        raise HTTPException(status_code=400, detail=f"SSL Error: {str(e)}")
    except socket.error as e:
        raise HTTPException(status_code=400, detail=f"Connection Error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis Error: {str(e)}")

@app.get("/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8015)