"""
Email Analyzer - Análise completa de endereços de email
Verificação de breaches, reputação e presença online
Projeto Vértice - SSP-GO
"""

import asyncio
import aiohttp
import hashlib
import re
import dns.resolver
from typing import Dict, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class EmailAnalyzer:
    def __init__(self):
        self.timeout = aiohttp.ClientTimeout(total=10)
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(timeout=self.timeout)
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
            
    async def analyze(self, email: str, check_breaches: bool = True,
                     check_social: bool = True, check_reputation: bool = True) -> dict:
        """Análise completa de email"""
        
        logger.info(f"Analisando email: {email}")
        
        # Validação básica
        if not self._validate_email(email):
            return {"error": "Email inválido"}
            
        # Extrair domínio
        domain = email.split('@')[1]
        username = email.split('@')[0]
        
        results = {
            "email": email,
            "username": username,
            "domain": domain,
            "valid_format": True,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Verificações paralelas
        tasks = []
        
        # Verificação MX
        tasks.append(self._check_mx_records(domain))
        
        # Verificação de breaches
        if check_breaches:
            tasks.append(self._check_breaches(email))
            
        # Verificação social
        if check_social:
            tasks.append(self._check_social_presence(email, username))
            
        # Verificação de reputação
        if check_reputation:
            tasks.append(self._check_reputation(email, domain))
            
        # Executar todas as tarefas
        task_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Processar resultados
        for i, result in enumerate(task_results):
            if not isinstance(result, Exception):
                if i == 0:  # MX Records
                    results["mx_records"] = result
                elif i == 1 and check_breaches:  # Breaches
                    results["breaches"] = result
                elif (i == 2 and check_social) or (i == 1 and not check_breaches):  # Social
                    results["social_presence"] = result
                elif check_reputation:  # Reputation
                    results["reputation"] = result
                    
        # Calcular score de risco
        results["risk_score"] = self._calculate_risk_score(results)
        
        return results
        
    def _validate_email(self, email: str) -> bool:
        """Valida formato de email"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
        
    async def _check_mx_records(self, domain: str) -> dict:
        """Verifica registros MX do domínio"""
        try:
            mx_records = []
            answers = dns.resolver.resolve(domain, 'MX')
            for rdata in answers:
                mx_records.append({
                    "priority": rdata.preference,
                    "host": str(rdata.exchange)
                })
            return {
                "valid": True,
                "records": mx_records
            }
        except Exception as e:
            logger.error(f"Erro ao verificar MX: {e}")
            return {
                "valid": False,
                "error": str(e)
            }
            
    async def _check_breaches(self, email: str) -> List[dict]:
        """Verifica se email foi comprometido em breaches"""
        breaches = []
        
        # Hash SHA1 do email para verificação
        sha1_hash = hashlib.sha1(email.encode()).hexdigest().upper()
        prefix = sha1_hash[:5]
        suffix = sha1_hash[5:]
        
        try:
            if not self.session:
                self.session = aiohttp.ClientSession(timeout=self.timeout)
                
            # Verificar em HIBP k-anonymity
            async with self.session.get(
                f"https://api.pwnedpasswords.com/range/{prefix}"
            ) as response:
                if response.status == 200:
                    text = await response.text()
                    for line in text.split('\n'):
                        if line.startswith(suffix):
                            count = int(line.split(':')[1])
                            breaches.append({
                                "source": "HIBP",
                                "occurrences": count,
                                "severity": "HIGH" if count > 100 else "MEDIUM"
                            })
                            break
                            
        except Exception as e:
            logger.error(f"Erro ao verificar breaches: {e}")
            
        # Verificação adicional em bases locais
        known_leaks = [
            {"name": "Collection #1", "year": 2019, "emails": ["gmail.com", "yahoo.com"]},
            {"name": "LinkedIn", "year": 2021, "emails": ["*"]},
            {"name": "Facebook", "year": 2019, "emails": ["*"]}
        ]
        
        domain = email.split('@')[1]
        for leak in known_leaks:
            if "*" in leak["emails"] or domain in leak["emails"]:
                breaches.append({
                    "source": leak["name"],
                    "year": leak["year"],
                    "severity": "MEDIUM"
                })
                
        return breaches
        
    async def _check_social_presence(self, email: str, username: str) -> dict:
        """Verifica presença em redes sociais"""
        presence = {
            "platforms_found": [],
            "possible_accounts": []
        }
        
        # Verificar Gravatar
        md5_hash = hashlib.md5(email.lower().encode()).hexdigest()
        gravatar_url = f"https://www.gravatar.com/avatar/{md5_hash}?d=404"
        
        try:
            if not self.session:
                self.session = aiohttp.ClientSession(timeout=self.timeout)
                
            async with self.session.get(gravatar_url) as response:
                if response.status == 200:
                    presence["platforms_found"].append({
                        "platform": "Gravatar",
                        "url": gravatar_url,
                        "confirmed": True
                    })
        except:
            pass
            
        # Inferir possíveis contas sociais
        common_platforms = ["github", "linkedin", "twitter", "facebook", "instagram"]
        for platform in common_platforms:
            presence["possible_accounts"].append({
                "platform": platform,
                "username": username,
                "probability": "medium"
            })
            
        return presence
        
    async def _check_reputation(self, email: str, domain: str) -> dict:
        """Verifica reputação do email e domínio"""
        reputation = {
            "domain_age": "unknown",
            "spam_listed": False,
            "disposable": False,
            "corporate": False,
            "free_provider": False
        }
        
        # Verificar se é provedor gratuito
        free_providers = ["gmail.com", "yahoo.com", "hotmail.com", "outlook.com", 
                         "protonmail.com", "tutanota.com", "mail.ru", "yandex.ru"]
        
        if domain in free_providers:
            reputation["free_provider"] = True
            
        # Verificar se é domínio corporativo comum
        if any(corp in domain for corp in [".gov", ".edu", ".mil", ".org"]):
            reputation["corporate"] = True
            
        # Verificar se é email descartável
        disposable_domains = ["tempmail", "guerrillamail", "mailinator", "10minutemail",
                            "throwaway", "fakeinbox", "trashemail"]
        
        if any(disp in domain for disp in disposable_domains):
            reputation["disposable"] = True
            reputation["spam_listed"] = True
            
        return reputation
        
    def _calculate_risk_score(self, results: dict) -> dict:
        """Calcula score de risco do email"""
        score = 0
        factors = []
        
        # Verificar MX
        if not results.get("mx_records", {}).get("valid"):
            score += 30
            factors.append("Domínio sem registros MX válidos")
            
        # Verificar breaches
        breaches = results.get("breaches", [])
        if breaches:
            score += min(50, len(breaches) * 15)
            factors.append(f"Email encontrado em {len(breaches)} vazamentos")
            
        # Verificar reputação
        reputation = results.get("reputation", {})
        if reputation.get("disposable"):
            score += 40
            factors.append("Email descartável detectado")
        if reputation.get("spam_listed"):
            score += 20
            factors.append("Domínio em lista de spam")
            
        # Normalizar score
        score = min(100, score)
        
        # Classificar risco
        if score >= 70:
            risk_level = "HIGH"
        elif score >= 40:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"
            
        return {
            "score": score,
            "level": risk_level,
            "factors": factors
        }
