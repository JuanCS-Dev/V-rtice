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
from cryptography.x509 import ocsp
import httpx
import base64

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

async def check_ocsp_status(cert, issuer_cert=None) -> Optional[dict]:
    """
    Verifica status OCSP (Online Certificate Status Protocol)

    Retorna status de revogação em tempo real:
    - good: certificado válido
    - revoked: certificado revogado
    - unknown: status desconhecido
    """
    try:
        # Extract OCSP URL from certificate
        try:
            aia = cert.extensions.get_extension_for_oid(
                x509.oid.ExtensionOID.AUTHORITY_INFORMATION_ACCESS
            )
            ocsp_url = None
            for desc in aia.value:
                if desc.access_method == x509.oid.AuthorityInformationAccessOID.OCSP:
                    ocsp_url = desc.access_location.value
                    break

            if not ocsp_url:
                return {
                    "status": "unavailable",
                    "message": "No OCSP URL found in certificate"
                }
        except Exception as e:
            return {
                "status": "unavailable",
                "message": f"Failed to extract OCSP URL: {str(e)}"
            }

        # If no issuer cert provided, can't build OCSP request
        if not issuer_cert:
            return {
                "status": "unavailable",
                "message": "Issuer certificate required for OCSP check",
                "ocsp_url": ocsp_url
            }

        # Build OCSP request
        builder = ocsp.OCSPRequestBuilder()
        builder = builder.add_certificate(cert, issuer_cert, hashes.SHA256())
        ocsp_request = builder.build()

        # Encode request
        ocsp_request_data = ocsp_request.public_bytes(x509.Encoding.DER)

        # Send OCSP request
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                ocsp_url,
                content=ocsp_request_data,
                headers={"Content-Type": "application/ocsp-request"}
            )

            if response.status_code != 200:
                return {
                    "status": "error",
                    "message": f"OCSP server returned {response.status_code}",
                    "ocsp_url": ocsp_url
                }

            # Parse OCSP response
            ocsp_response = ocsp.load_der_ocsp_response(response.content)

            # Check response status
            if ocsp_response.response_status != ocsp.OCSPResponseStatus.SUCCESSFUL:
                return {
                    "status": "error",
                    "message": f"OCSP response status: {ocsp_response.response_status.name}",
                    "ocsp_url": ocsp_url
                }

            # Get certificate status
            cert_status = ocsp_response.certificate_status

            if cert_status == ocsp.OCSPCertStatus.GOOD:
                status_str = "good"
                message = "Certificate is valid and not revoked"
            elif cert_status == ocsp.OCSPCertStatus.REVOKED:
                status_str = "revoked"
                revocation_time = ocsp_response.revocation_time
                revocation_reason = ocsp_response.revocation_reason
                message = f"Certificate revoked at {revocation_time}"
                if revocation_reason:
                    message += f" (Reason: {revocation_reason.name})"
            else:
                status_str = "unknown"
                message = "Certificate status unknown"

            # Get OCSP responder info
            produced_at = ocsp_response.produced_at
            this_update = ocsp_response.this_update
            next_update = ocsp_response.next_update

            return {
                "status": status_str,
                "message": message,
                "ocsp_url": ocsp_url,
                "produced_at": produced_at.isoformat() if produced_at else None,
                "this_update": this_update.isoformat() if this_update else None,
                "next_update": next_update.isoformat() if next_update else None,
                "responder": str(ocsp_response.responder_name) if hasattr(ocsp_response, 'responder_name') else "Unknown"
            }

    except httpx.TimeoutException:
        return {
            "status": "timeout",
            "message": "OCSP server timeout",
            "ocsp_url": ocsp_url if 'ocsp_url' in locals() else None
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"OCSP check failed: {str(e)}",
            "ocsp_url": ocsp_url if 'ocsp_url' in locals() else None
        }

async def check_ct_logs(cert) -> Optional[dict]:
    """
    Verifica Certificate Transparency (CT) Logs

    CT logs são registros públicos de todos os certificados SSL emitidos.
    Permite detectar certificados emitidos de forma não autorizada.
    """
    try:
        # Extract SCT (Signed Certificate Timestamp) from certificate
        scts = []
        try:
            sct_ext = cert.extensions.get_extension_for_oid(
                x509.oid.ExtensionOID.PRECERT_SIGNED_CERTIFICATE_TIMESTAMPS
            )
            # SCT extension found - certificate was submitted to CT logs
            scts_count = len(list(sct_ext.value))

            return {
                "status": "logged",
                "message": f"Certificate found in {scts_count} CT log(s)",
                "sct_count": scts_count,
                "compliance": "compliant",
                "logs": []  # Detailed log info would require parsing SCT
            }
        except x509.ExtensionNotFound:
            # No SCT extension - check via crt.sh API
            pass

        # Fallback: Query crt.sh (Certificate Transparency search)
        cert_sha256 = cert.fingerprint(hashes.SHA256()).hex()

        async with httpx.AsyncClient(timeout=10.0) as client:
            # Query crt.sh by SHA256 fingerprint
            response = await client.get(
                f"https://crt.sh/?sha256={cert_sha256}&output=json",
                follow_redirects=True
            )

            if response.status_code == 200:
                try:
                    ct_data = response.json()

                    if isinstance(ct_data, list) and len(ct_data) > 0:
                        # Certificate found in CT logs
                        logs = []
                        unique_log_names = set()

                        for entry in ct_data[:10]:  # Limit to 10 entries
                            log_name = entry.get('issuer_name', 'Unknown')
                            entry_timestamp = entry.get('entry_timestamp', '')
                            cert_id = entry.get('id')

                            unique_log_names.add(log_name)

                            logs.append({
                                "cert_id": cert_id,
                                "issuer": log_name,
                                "logged_at": entry_timestamp,
                                "not_before": entry.get('not_before'),
                                "not_after": entry.get('not_after')
                            })

                        return {
                            "status": "logged",
                            "message": f"Certificate found in CT logs ({len(ct_data)} entries)",
                            "total_entries": len(ct_data),
                            "unique_logs": len(unique_log_names),
                            "compliance": "compliant",
                            "logs": logs,
                            "crt_sh_url": f"https://crt.sh/?sha256={cert_sha256}"
                        }
                    else:
                        # Not found in CT logs - SUSPICIOUS
                        return {
                            "status": "not_found",
                            "message": "⚠️ Certificate NOT found in public CT logs - potentially suspicious",
                            "compliance": "non_compliant",
                            "severity": "high",
                            "crt_sh_url": f"https://crt.sh/?sha256={cert_sha256}"
                        }
                except (ValueError, KeyError) as e:
                    return {
                        "status": "error",
                        "message": f"Failed to parse CT log data: {str(e)}"
                    }
            else:
                return {
                    "status": "unavailable",
                    "message": f"CT log query failed (HTTP {response.status_code})"
                }

    except httpx.TimeoutException:
        return {
            "status": "timeout",
            "message": "CT log query timeout"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"CT log check failed: {str(e)}"
        }

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

        # Check OCSP status (if requested and chain available)
        ocsp_status = None
        if request.check_ocsp:
            issuer_cert_obj = chain_certs[0] if chain_certs else None
            ocsp_status = await check_ocsp_status(cert, issuer_cert_obj)

            # Add warning if certificate is revoked
            if ocsp_status and ocsp_status.get("status") == "revoked":
                vulnerabilities.append({
                    "id": "CERT_REVOKED",
                    "severity": "critical",
                    "title": "Certificate Revoked",
                    "description": ocsp_status.get("message", "Certificate has been revoked"),
                    "cve": None
                })

        # Check Certificate Transparency logs (if requested)
        ct_logs = None
        if request.check_ct_logs:
            ct_logs = await check_ct_logs(cert)

            # Add warning if not found in CT logs
            if ct_logs and ct_logs.get("status") == "not_found":
                threat_indicators.append("⚠️ Certificate not found in public CT logs")

        # Generate warnings
        warnings = []
        if cert_info.days_until_expiry < 30:
            warnings.append(f"Certificate expires in {cert_info.days_until_expiry} days")
        if cert_info.is_self_signed:
            warnings.append("Self-signed certificate detected")
        if threat_indicators:
            warnings.append(f"{len(threat_indicators)} threat indicators detected")
        if ocsp_status and ocsp_status.get("status") == "revoked":
            warnings.append("⚠️ CRITICAL: Certificate has been REVOKED")
        if ct_logs and ct_logs.get("status") == "not_found":
            warnings.append("⚠️ Certificate not logged in CT - potentially suspicious")

        # Cipher info
        cipher_name = cipher[0] if cipher else "Unknown"
        cipher_strength = cipher[2] if cipher and len(cipher) > 2 else 0

        is_valid = (
            not cert_info.is_expired and
            security_score >= 70 and
            len([v for v in vulnerabilities if v['severity'] in ['critical', 'high']]) == 0 and
            (not ocsp_status or ocsp_status.get("status") != "revoked")
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
            ocsp_status=ocsp_status,
            ct_logs=ct_logs,
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