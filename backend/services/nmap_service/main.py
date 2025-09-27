# backend/services/nmap_service/main.py

"""
Nmap Service - Vértice Cyber Security Module
Migração do Batman do Cerrado para arquitetura de microsserviços
"""

import subprocess
import xml.etree.ElementTree as ET
import json
import time
import re
from datetime import datetime
from typing import Dict, List, Any, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(
    title="Nmap Service",
    description="Microsserviço para varreduras de rede com Nmap - reconnaissance e detecção de serviços",
    version="1.0.0",
)

# Modelos de dados
class NmapScanRequest(BaseModel):
    target: str
    profile: str = "quick"
    custom_args: Optional[str] = None

class PortInfo(BaseModel):
    port: int
    protocol: str
    state: str
    service: Optional[str] = None
    version: Optional[str] = None
    product: Optional[str] = None

class HostInfo(BaseModel):
    ip: str
    hostname: Optional[str] = None
    status: str
    ports: List[PortInfo] = []
    os_info: Optional[str] = None

# Perfis de scan predefinidos
SCAN_PROFILES = {
    "quick": "-T4 -F",
    "full": "-T4 -A -v",
    "stealth": "-sS -T2 -f",
    "comprehensive": "-T4 -A -sS -sU --script=default,vuln",
    "discovery": "-sn",
    "service-detection": "-sV -T4",
    "os-detection": "-O -T4",
    "vuln-scan": "-T4 --script=vuln"
}

# --- Nmap Analysis Functions ---

def validate_target(target: str) -> bool:
    """Valida se o alvo é um IP, hostname ou CIDR válido"""
    # Regex básica para IP
    ip_pattern = r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'
    # Regex básica para CIDR
    cidr_pattern = r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\/(?:[0-9]|[1-2][0-9]|3[0-2])$'
    # Regex básica para hostname
    hostname_pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$'
    
    return (
        re.match(ip_pattern, target) or 
        re.match(cidr_pattern, target) or 
        re.match(hostname_pattern, target)
    )

async def execute_nmap_scan(target: str, nmap_args: str) -> tuple[bool, str, str]:
    """Executa scan Nmap e retorna resultado"""
    try:
        # Comando nmap com saída XML
        cmd = ["nmap"] + nmap_args.split() + ["-oX", "-", target]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minutos timeout
        )
        
        return result.returncode == 0, result.stdout, result.stderr
        
    except subprocess.TimeoutExpired:
        return False, "", "Scan timeout - operação cancelada após 5 minutos"
    except Exception as e:
        return False, "", f"Erro na execução: {str(e)}"

def parse_nmap_xml(xml_output: str) -> List[HostInfo]:
    """Parse da saída XML do Nmap para estrutura de dados"""
    hosts = []
    
    try:
        root = ET.fromstring(xml_output)
        
        for host_elem in root.findall("host"):
            # Informações básicas do host
            status_elem = host_elem.find("status")
            if status_elem is None:
                continue
                
            status = status_elem.get("state", "unknown")
            
            # IP address
            address_elem = host_elem.find("address")
            if address_elem is None:
                continue
            ip = address_elem.get("addr")
            
            # Hostname
            hostname = None
            hostnames_elem = host_elem.find("hostnames")
            if hostnames_elem is not None:
                hostname_elem = hostnames_elem.find("hostname")
                if hostname_elem is not None:
                    hostname = hostname_elem.get("name")
            
            # OS detection
            os_info = None
            os_elem = host_elem.find("os")
            if os_elem is not None:
                osmatch_elem = os_elem.find("osmatch")
                if osmatch_elem is not None:
                    os_info = osmatch_elem.get("name")
            
            # Portas
            ports = []
            ports_elem = host_elem.find("ports")
            if ports_elem is not None:
                for port_elem in ports_elem.findall("port"):
                    port_id = int(port_elem.get("portid", 0))
                    protocol = port_elem.get("protocol", "tcp")
                    
                    state_elem = port_elem.find("state")
                    state = state_elem.get("state", "unknown") if state_elem is not None else "unknown"
                    
                    # Informações do serviço
                    service_name = None
                    version = None
                    product = None
                    
                    service_elem = port_elem.find("service")
                    if service_elem is not None:
                        service_name = service_elem.get("name")
                        version = service_elem.get("version")
                        product = service_elem.get("product")
                    
                    port_info = PortInfo(
                        port=port_id,
                        protocol=protocol,
                        state=state,
                        service=service_name,
                        version=version,
                        product=product
                    )
                    ports.append(port_info)
            
            host_info = HostInfo(
                ip=ip,
                hostname=hostname,
                status=status,
                ports=ports,
                os_info=os_info
            )
            hosts.append(host_info)
    
    except ET.ParseError as e:
        raise HTTPException(status_code=500, detail=f"Erro no parse XML: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro no processamento: {str(e)}")
    
    return hosts

def assess_security_risks(hosts: List[HostInfo]) -> Dict[str, Any]:
    """Avalia riscos de segurança baseado nos resultados"""
    risks = {
        "high_risk_services": [],
        "open_ports_count": 0,
        "vulnerable_services": [],
        "recommendations": []
    }
    
    high_risk_services = ["telnet", "ftp", "rsh", "rlogin", "snmp", "tftp"]
    potentially_vulnerable = ["ssh", "http", "https", "mysql", "postgresql", "rdp"]
    
    for host in hosts:
        for port in host.ports:
            if port.state == "open":
                risks["open_ports_count"] += 1
                
                if port.service in high_risk_services:
                    risks["high_risk_services"].append({
                        "host": host.ip,
                        "port": port.port,
                        "service": port.service,
                        "risk": "Serviço inseguro detectado"
                    })
                
                if port.service in potentially_vulnerable:
                    risks["vulnerable_services"].append({
                        "host": host.ip,
                        "port": port.port,
                        "service": port.service,
                        "version": port.version
                    })
    
    # Recomendações baseadas nos achados
    if risks["high_risk_services"]:
        risks["recommendations"].append("Desabilitar ou restringir serviços inseguros detectados")
    
    if risks["open_ports_count"] > 10:
        risks["recommendations"].append("Revisar necessidade de todas as portas abertas")
    
    if not risks["recommendations"]:
        risks["recommendations"].append("Configuração aparenta estar segura")
    
    return risks

# --- Main Scan Endpoint ---

@app.post("/scan", tags=["Network Scanning"])
async def execute_scan(request: NmapScanRequest):
    """Executa varredura Nmap no alvo especificado"""
    result = {
        "timestamp": datetime.now().isoformat(),
        "success": False,
        "target": request.target,
        "profile": request.profile,
        "data": {},
        "errors": []
    }
    
    # Validação do alvo
    if not validate_target(request.target):
        raise HTTPException(
            status_code=400, 
            detail="Alvo inválido. Use IP, hostname ou CIDR válidos."
        )
    
    # Validação do perfil
    if request.profile not in SCAN_PROFILES:
        raise HTTPException(
            status_code=400,
            detail=f"Perfil '{request.profile}' não encontrado. Perfis disponíveis: {list(SCAN_PROFILES.keys())}"
        )
    
    try:
        # Argumentos do nmap
        nmap_args = SCAN_PROFILES[request.profile]
        if request.custom_args:
            nmap_args += f" {request.custom_args}"
        
        result["data"]["nmap_command"] = f"nmap {nmap_args} {request.target}"
        
        # Execução do scan
        scan_start = time.time()
        success, xml_output, error_output = await execute_nmap_scan(request.target, nmap_args)
        scan_duration = time.time() - scan_start
        
        result["data"]["scan_duration"] = round(scan_duration, 2)
        
        if not success:
            result["errors"].append(f"Scan falhou: {error_output}")
            return result
        
        if not xml_output.strip():
            result["errors"].append("Nenhuma saída XML gerada pelo Nmap")
            return result
        
        # Parse dos resultados
        hosts = parse_nmap_xml(xml_output)
        result["data"]["hosts"] = [host.dict() for host in hosts]
        result["data"]["hosts_count"] = len(hosts)
        
        # Análise de riscos
        security_assessment = assess_security_risks(hosts)
        result["data"]["security_assessment"] = security_assessment
        
        result["success"] = True
        
    except Exception as e:
        result["errors"].append(f"Erro na análise: {str(e)}")
    
    return result

@app.get("/profiles", tags=["Configuration"])
async def get_scan_profiles():
    """Retorna perfis de scan disponíveis"""
    return {
        "profiles": {
            profile: {
                "name": profile,
                "command": args,
                "description": get_profile_description(profile)
            }
            for profile, args in SCAN_PROFILES.items()
        }
    }

def get_profile_description(profile: str) -> str:
    """Retorna descrição do perfil de scan"""
    descriptions = {
        "quick": "Scan rápido das portas mais comuns",
        "full": "Scan completo com detecção de OS e serviços",
        "stealth": "Scan furtivo para evitar detecção",
        "comprehensive": "Scan abrangente incluindo vulnerabilidades",
        "discovery": "Descoberta de hosts ativos (ping scan)",
        "service-detection": "Detecção detalhada de serviços",
        "os-detection": "Detecção do sistema operacional",
        "vuln-scan": "Scan focado em vulnerabilidades"
    }
    return descriptions.get(profile, "Perfil personalizado")

@app.get("/", tags=["Root"])
async def health_check():
    """Health check endpoint"""
    # Verifica se nmap está disponível
    nmap_available = False
    try:
        result = subprocess.run(
            ["nmap", "--version"], 
            capture_output=True, 
            timeout=5
        )
        nmap_available = result.returncode == 0
    except Exception:
        pass
    
    return {
        "service": "Nmap Service",
        "status": "operational" if nmap_available else "degraded",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "nmap_available": nmap_available,
        "endpoints": {
            "scan": "POST /scan",
            "profiles": "GET /profiles",
            "health": "GET /"
        }
    }
