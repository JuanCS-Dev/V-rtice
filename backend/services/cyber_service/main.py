# /home/juan/vertice-dev/backend/services/cyber_service/main.py

import subprocess
import psutil
import socket
import ssl
import json
import os
import hashlib
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(
    title="Cyber Security Service",
    description="Microsserviço para verificações reais de segurança e integridade do sistema",
    version="1.0.0",
)

# Modelos de dados
class NetworkScanRequest(BaseModel):
    target: str
    profile: str = "self-check"

class SecurityResult(BaseModel):
    timestamp: str
    success: bool
    data: Dict[str, Any]
    errors: List[str] = []

# --- Verificações de Segurança Real ---

@app.post("/cyber/network-scan", tags=["Security"])
async def network_scan(request: NetworkScanRequest):
    """Executa scan de rede usando nmap (se disponível)"""
    result = SecurityResult(
        timestamp=datetime.now().isoformat(),
        success=False,
        data={},
        errors=[]
    )
    
    try:
        # Verifica se nmap está disponível
        nmap_check = subprocess.run(["which", "nmap"], capture_output=True, text=True)
        if nmap_check.returncode != 0:
            # Fallback: usa netstat para informações básicas
            netstat_result = subprocess.run(
                ["netstat", "-tuln"], 
                capture_output=True, 
                text=True, 
                timeout=10
            )
            
            open_ports = []
            for line in netstat_result.stdout.split('\n'):
                if 'LISTEN' in line:
                    parts = line.split()
                    if len(parts) >= 4:
                        port_info = parts[3].split(':')[-1]
                        open_ports.append(port_info)
            
            result.data = {
                "method": "netstat",
                "target": request.target,
                "open_ports": list(set(open_ports)),
                "total_ports": len(set(open_ports))
            }
            result.success = True
        else:
            # Usa nmap para scan mais detalhado
            nmap_cmd = [
                "nmap", "-T4", "-F", "--open", 
                "-oX", "-", request.target
            ]
            
            nmap_result = subprocess.run(
                nmap_cmd, 
                capture_output=True, 
                text=True, 
                timeout=30
            )
            
            if nmap_result.returncode == 0:
                # Parse básico do XML do nmap
                open_ports = []
                for line in nmap_result.stdout.split('\n'):
                    if 'portid=' in line and 'open' in line:
                        port = line.split('portid="')[1].split('"')[0]
                        open_ports.append(port)
                
                result.data = {
                    "method": "nmap",
                    "target": request.target,
                    "open_ports": open_ports,
                    "total_ports": len(open_ports),
                    "raw_output": nmap_result.stdout[:1000]  # Limita tamanho
                }
                result.success = True
            else:
                result.errors.append(f"Nmap falhou: {nmap_result.stderr}")
                
    except subprocess.TimeoutExpired:
        result.errors.append("Timeout no scan de rede")
    except Exception as e:
        result.errors.append(f"Erro no network scan: {str(e)}")
    
    return result

@app.get("/cyber/port-analysis", tags=["Security"])
async def port_analysis():
    """Analisa portas abertas e conexões ativas"""
    result = SecurityResult(
        timestamp=datetime.now().isoformat(),
        success=False,
        data={},
        errors=[]
    )
    
    try:
        # Usa psutil para análise de rede
        connections = psutil.net_connections(kind='inet')
        listening_ports = []
        active_connections = []
        
        for conn in connections:
            if conn.status == 'LISTEN' and conn.laddr:
                listening_ports.append({
                    "port": conn.laddr.port,
                    "address": conn.laddr.ip,
                    "pid": conn.pid,
                    "process": psutil.Process(conn.pid).name() if conn.pid else "unknown"
                })
            elif conn.status == 'ESTABLISHED' and conn.raddr:
                active_connections.append({
                    "local_port": conn.laddr.port if conn.laddr else None,
                    "remote_addr": conn.raddr.ip if conn.raddr else None,
                    "remote_port": conn.raddr.port if conn.raddr else None,
                    "pid": conn.pid,
                    "process": psutil.Process(conn.pid).name() if conn.pid else "unknown"
                })
        
        # Verifica portas suspeitas (não essenciais para o Vértice)
        essential_ports = [22, 80, 443, 5173, 8000, 8001, 6379, 5432]
        suspicious_ports = [p for p in listening_ports if p["port"] not in essential_ports]
        
        result.data = {
            "listening_ports": listening_ports,
            "active_connections": active_connections[:20],  # Limita resultados
            "suspicious_ports": suspicious_ports,
            "total_listening": len(listening_ports),
            "total_connections": len(active_connections)
        }
        result.success = True
        
    except Exception as e:
        result.errors.append(f"Erro na análise de portas: {str(e)}")
    
    return result

@app.get("/cyber/file-integrity", tags=["Security"])
async def file_integrity():
    """Verifica integridade de arquivos críticos do Vértice"""
    result = SecurityResult(
        timestamp=datetime.now().isoformat(),
        success=False,
        data={},
        errors=[]
    )
    
    try:
        # Arquivos críticos do Vértice para verificar
        critical_files = [
            "/app/main.py",
            "/app/requirements.txt",
            "/etc/passwd",
            "/etc/shadow",
        ]
        
        checked_files = []
        modified_files = []
        missing_files = []
        
        for file_path in critical_files:
            if os.path.exists(file_path):
                try:
                    stat_info = os.stat(file_path)
                    file_info = {
                        "path": file_path,
                        "size": stat_info.st_size,
                        "mtime": datetime.fromtimestamp(stat_info.st_mtime).isoformat(),
                        "permissions": oct(stat_info.st_mode),
                        "uid": stat_info.st_uid,
                        "gid": stat_info.st_gid
                    }
                    
                    # Verifica se é arquivo SUID/SGID (potencialmente perigoso)
                    if stat_info.st_mode & 0o4000:  # SUID
                        file_info["suid"] = True
                    if stat_info.st_mode & 0o2000:  # SGID
                        file_info["sgid"] = True
                    
                    checked_files.append(file_info)
                    
                except Exception as e:
                    result.errors.append(f"Erro ao verificar {file_path}: {str(e)}")
            else:
                missing_files.append(file_path)
        
        # Procura por arquivos SUID suspeitos
        suid_files = []
        try:
            find_suid = subprocess.run(
                ["find", "/usr", "/bin", "/sbin", "-perm", "-4000", "-type", "f"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if find_suid.returncode == 0:
                suid_files = find_suid.stdout.strip().split('\n')[:10]  # Limita a 10
        except:
            pass
        
        result.data = {
            "checked_files": checked_files,
            "modified_files": modified_files,
            "missing_files": missing_files,
            "suid_files": suid_files,
            "total_checked": len(checked_files)
        }
        result.success = True
        
    except Exception as e:
        result.errors.append(f"Erro na verificação de integridade: {str(e)}")
    
    return result

@app.get("/cyber/process-analysis", tags=["Security"])
async def process_analysis():
    """Analisa processos do sistema"""
    result = SecurityResult(
        timestamp=datetime.now().isoformat(),
        success=False,
        data={},
        errors=[]
    )
    
    try:
        processes = []
        vertice_processes = []
        suspicious_processes = []
        
        for proc in psutil.process_iter(['pid', 'name', 'username', 'cpu_percent', 'memory_percent']):
            try:
                proc_info = proc.info
                processes.append(proc_info)
                
                # Identifica processos do Vértice
                if any(term in proc_info['name'].lower() for term in ['python', 'uvicorn', 'fastapi']):
                    vertice_processes.append(proc_info)
                
                # Identifica processos suspeitos (alta CPU/memória)
                if proc_info['cpu_percent'] and proc_info['cpu_percent'] > 80:
                    suspicious_processes.append({
                        **proc_info,
                        "reason": "High CPU usage"
                    })
                    
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        result.data = {
            "total_processes": len(processes),
            "vertice_processes": vertice_processes,
            "suspicious_processes": suspicious_processes,
            "system_load": os.getloadavg() if hasattr(os, 'getloadavg') else None,
            "memory_usage": psutil.virtual_memory()._asdict(),
            "cpu_usage": psutil.cpu_percent(interval=1)
        }
        result.success = True
        
    except Exception as e:
        result.errors.append(f"Erro na análise de processos: {str(e)}")
    
    return result

@app.get("/cyber/certificate-check", tags=["Security"])
async def certificate_check():
    """Verifica certificados SSL/TLS dos serviços"""
    result = SecurityResult(
        timestamp=datetime.now().isoformat(),
        success=False,
        data={},
        errors=[]
    )
    
    try:
        services_to_check = [
            {"host": "localhost", "port": 8000, "name": "API Gateway"},
            {"host": "localhost", "port": 443, "name": "HTTPS Service"}
        ]
        
        valid_certs = []
        expired_certs = []
        cert_errors = []
        
        for service in services_to_check:
            try:
                context = ssl.create_default_context()
                with socket.create_connection((service["host"], service["port"]), timeout=5) as sock:
                    with context.wrap_socket(sock, server_hostname=service["host"]) as ssock:
                        cert = ssock.getpeercert()
                        
                        cert_info = {
                            "service": service["name"],
                            "host": service["host"],
                            "port": service["port"],
                            "subject": dict(x[0] for x in cert.get("subject", [])),
                            "issuer": dict(x[0] for x in cert.get("issuer", [])),
                            "not_after": cert.get("notAfter"),
                            "not_before": cert.get("notBefore")
                        }
                        valid_certs.append(cert_info)
                        
            except ssl.SSLError:
                # Serviço não usa SSL ou certificado inválido
                continue
            except (socket.error, ConnectionRefusedError):
                # Serviço não está rodando
                continue
            except Exception as e:
                cert_errors.append(f"Erro ao verificar {service['name']}: {str(e)}")
        
        result.data = {
            "valid_certs": valid_certs,
            "expired_certs": expired_certs,
            "cert_errors": cert_errors,
            "total_checked": len(services_to_check)
        }
        result.success = True
        
    except Exception as e:
        result.errors.append(f"Erro na verificação de certificados: {str(e)}")
    
    return result

@app.get("/cyber/security-config", tags=["Security"])
async def security_config():
    """Verifica configurações de segurança do sistema"""
    result = SecurityResult(
        timestamp=datetime.now().isoformat(),
        success=False,
        data={},
        errors=[]
    )
    
    try:
        config_checks = {}
        
        # Verifica firewall
        try:
            ufw_status = subprocess.run(
                ["ufw", "status"], 
                capture_output=True, 
                text=True, 
                timeout=5
            )
            config_checks["firewall"] = {
                "ufw_active": "Status: active" in ufw_status.stdout,
                "status_output": ufw_status.stdout
            }
        except:
            config_checks["firewall"] = {"error": "Não foi possível verificar UFW"}
        
        # Verifica configuração SSH
        ssh_config_path = "/etc/ssh/sshd_config"
        if os.path.exists(ssh_config_path):
            try:
                with open(ssh_config_path, 'r') as f:
                    ssh_config = f.read()
                    config_checks["ssh"] = {
                        "root_login": "PermitRootLogin no" in ssh_config,
                        "password_auth": "PasswordAuthentication" in ssh_config,
                        "config_exists": True
                    }
            except:
                config_checks["ssh"] = {"error": "Não foi possível ler configuração SSH"}
        else:
            config_checks["ssh"] = {"config_exists": False}
        
        # Verifica usuários do sistema
        try:
            users = []
            with open("/etc/passwd", 'r') as f:
                for line in f:
                    if not line.startswith('#'):
                        parts = line.split(':')
                        if len(parts) >= 6:
                            users.append({
                                "username": parts[0],
                                "uid": parts[2],
                                "shell": parts[6].strip()
                            })
            config_checks["users"] = {
                "total_users": len(users),
                "shell_users": [u for u in users if '/bash' in u['shell'] or '/sh' in u['shell']]
            }
        except:
            config_checks["users"] = {"error": "Não foi possível ler usuários"}
        
        result.data = config_checks
        result.success = True
        
    except Exception as e:
        result.errors.append(f"Erro na verificação de configurações: {str(e)}")
    
    return result

@app.get("/cyber/security-logs", tags=["Security"])
async def security_logs():
    """Analisa logs de segurança do sistema"""
    result = SecurityResult(
        timestamp=datetime.now().isoformat(),
        success=False,
        data={},
        errors=[]
    )
    
    try:
        log_analysis = {}
        
        # Analisa logs de autenticação
        auth_logs = ["/var/log/auth.log", "/var/log/secure"]
        failed_logins = []
        successful_logins = []
        
        for log_path in auth_logs:
            if os.path.exists(log_path):
                try:
                    # Lê apenas as últimas 100 linhas para performance
                    tail_result = subprocess.run(
                        ["tail", "-n", "100", log_path],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    
                    for line in tail_result.stdout.split('\n'):
                        if 'Failed password' in line:
                            failed_logins.append(line.strip())
                        elif 'Accepted password' in line or 'Accepted publickey' in line:
                            successful_logins.append(line.strip())
                    
                    break  # Para no primeiro log encontrado
                except:
                    continue
        
        log_analysis = {
            "failed_logins": len(failed_logins),
            "successful_logins": len(successful_logins),
            "recent_failed": failed_logins[-5:] if failed_logins else [],
            "recent_successful": successful_logins[-3:] if successful_logins else [],
            "last_analysis": datetime.now().isoformat()
        }
        
        result.data = log_analysis
        result.success = True
        
    except Exception as e:
        result.errors.append(f"Erro na análise de logs: {str(e)}")
    
    return result

# Health check
@app.get("/", tags=["Root"])
async def health_check():
    return {
        "service": "Cyber Security Service",
        "status": "operational",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }
