# vertice_cli/utils/api_client.py

import requests
import json
from typing import Optional, Dict, Any
from .auth import AuthManager
from .console_utils import print_error, print_warning

class VerticeAPI:
    """Cliente API para comunicação com os microserviços do Vértice"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.auth = AuthManager()

    def _get_headers(self) -> Dict[str, str]:
        """Retorna headers com autenticação"""
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "VerticeConsole/1.0"
        }

        token = self.auth.get_token()
        if token:
            headers["Authorization"] = f"Bearer {token}"

        return headers

    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Optional[Dict[str, Any]]:
        """Faz requisição HTTP para a API"""
        url = f"{self.base_url}{endpoint}"
        headers = self._get_headers()

        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=headers, timeout=30)
            elif method.upper() == "POST":
                response = requests.post(url, json=data, headers=headers, timeout=30)
            else:
                raise ValueError(f"Método HTTP não suportado: {method}")

            if response.status_code == 401:
                print_error("Token de autenticação inválido ou expirado")
                return None
            elif response.status_code == 403:
                print_error("Acesso negado - permissões insuficientes")
                return None
            elif not response.ok:
                print_error(f"Erro na API: {response.status_code} - {response.text}")
                return None

            return response.json()

        except requests.exceptions.ConnectionError:
            print_error("Erro de conexão com a API. Verifique se os serviços estão rodando.")
            return None
        except requests.exceptions.Timeout:
            print_error("Timeout na requisição para a API")
            return None
        except Exception as e:
            print_error(f"Erro inesperado: {str(e)}")
            return None

    # OSINT Methods
    def analyze_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Analisa um endereço de email"""
        return self._make_request("POST", "/api/email/analyze", {"email": email})

    def analyze_phone(self, phone: str) -> Optional[Dict[str, Any]]:
        """Analisa um número de telefone"""
        return self._make_request("POST", "/api/phone/analyze", {"phone": phone})

    def investigate_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Investiga username em múltiplas plataformas"""
        return self._make_request("POST", "/api/username/investigate", {"username": username})

    def analyze_social_profile(self, platform: str, identifier: str) -> Optional[Dict[str, Any]]:
        """Analisa perfil em rede social"""
        return self._make_request("POST", "/api/social/profile", {
            "platform": platform,
            "identifier": identifier
        })

    # Cyber Security Methods
    def analyze_ip(self, ip: str) -> Optional[Dict[str, Any]]:
        """Analisa um endereço IP"""
        return self._make_request("POST", "/api/ip/analyze", {"ip": ip})

    def analyze_my_ip(self) -> Optional[Dict[str, Any]]:
        """Detecta e analisa o IP público do usuário"""
        return self._make_request("POST", "/api/ip/analyze-my-ip")

    def analyze_domain(self, domain: str) -> Optional[Dict[str, Any]]:
        """Analisa um domínio"""
        return self._make_request("POST", "/api/domain/analyze", {"domain": domain})

    # Offensive Security Methods (require special permissions)
    def start_vulnerability_scan(self, target: str, scan_type: str = "full") -> Optional[Dict[str, Any]]:
        """Inicia scan de vulnerabilidades"""
        return self._make_request("POST", "/api/vuln-scanner/scan", {
            "target": target,
            "scan_type": scan_type
        })

    def get_scan_status(self, scan_id: str) -> Optional[Dict[str, Any]]:
        """Verifica status de um scan"""
        return self._make_request("GET", f"/api/vuln-scanner/scan/{scan_id}")

    def list_exploits(self) -> Optional[Dict[str, Any]]:
        """Lista exploits disponíveis"""
        return self._make_request("GET", "/api/vuln-scanner/exploits")

    def execute_exploit(self, target: str, exploit_id: str, payload_options: Optional[Dict] = None) -> Optional[Dict[str, Any]]:
        """Executa um exploit"""
        return self._make_request("POST", "/api/vuln-scanner/exploit", {
            "target": target,
            "exploit_id": exploit_id,
            "payload_options": payload_options or {}
        })

    def create_phishing_campaign(self, campaign_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Cria campanha de phishing"""
        return self._make_request("POST", "/api/social-eng/campaign", campaign_data)

    def get_campaign_analytics(self, campaign_id: str) -> Optional[Dict[str, Any]]:
        """Obtém analytics de uma campanha"""
        return self._make_request("GET", f"/api/social-eng/analytics/{campaign_id}")

    def list_email_templates(self) -> Optional[Dict[str, Any]]:
        """Lista templates de email disponíveis"""
        return self._make_request("GET", "/api/social-eng/templates")

    def analyze_geospatial(self, coords: str) -> Optional[Dict[str, Any]]:
        """Analisa coordenadas geoespaciais"""
        return self._make_request("POST", "/api/geospatial/analyze", {"coords": coords})

    def check_service_health(self, base_url: str, endpoint: str) -> Optional[Dict[str, Any]]:
        """Verifica a saúde de um serviço"""
        url = f"{base_url}{endpoint}"
        try:
            response = requests.get(url, timeout=5) # Curto timeout para health checks
            if response.ok:
                return {"status": "ok", "message": response.json().get("status", "Online")} # Assumindo que o health endpoint retorna JSON com status
            else:
                return {"status": "error", "message": f"HTTP Status: {response.status_code}"}
        except requests.exceptions.ConnectionError:
            return {"status": "error", "message": "Erro de conexão"}
        except requests.exceptions.Timeout:
            return {"status": "error", "message": "Timeout"}
        except Exception as e:
            return {"status": "error", "message": f"Erro inesperado: {str(e)}"}

    def check_service_health(self, base_url: str, endpoint: str) -> Optional[Dict[str, Any]]:
        """Verifica a saúde de um serviço"""
        url = f"{base_url}{endpoint}"
        try:
            response = requests.get(url, timeout=5) # Curto timeout para health checks
            if response.ok:
                return {"status": "ok", "message": response.json().get("status", "Online")} # Assumindo que o health endpoint retorna JSON com status
            else:
                return {"status": "error", "message": f"HTTP Status: {response.status_code}"}
        except requests.exceptions.ConnectionError:
            return {"status": "error", "message": "Erro de conexão"}
        except requests.exceptions.Timeout:
            return {"status": "error", "message": "Timeout"}
        except Exception as e:
            return {"status": "error", "message": f"Erro inesperado: {str(e)}"}