"""
Phone Analyzer - Análise de números telefônicos
Verificação de operadora, localização e apps de mensagem
Projeto Vértice - SSP-GO
"""

import asyncio
import aiohttp
import phonenumbers
from phonenumbers import geocoder, carrier, timezone
from typing import Dict, Optional
from datetime import datetime
import logging
import re

logger = logging.getLogger(__name__)

class PhoneAnalyzer:
    def __init__(self):
        self.timeout = aiohttp.ClientTimeout(total=10)
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(timeout=self.timeout)
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
            
    async def analyze(self, phone: str, include_carrier: bool = True,
                     include_location: bool = True, 
                     check_messaging_apps: bool = True) -> dict:
        """Análise completa de número telefônico"""
        
        logger.info(f"Analisando telefone: {phone}")
        
        # Normalizar número
        normalized = self._normalize_phone(phone)
        
        try:
            # Parse com phonenumbers
            parsed = phonenumbers.parse(normalized, "BR")  # Default Brasil
            
            if not phonenumbers.is_valid_number(parsed):
                # Tentar com código do Brasil
                if not normalized.startswith("+"):
                    normalized = "+55" + normalized
                    parsed = phonenumbers.parse(normalized, None)
                    
            results = {
                "phone": phone,
                "normalized": phonenumbers.format_number(
                    parsed, 
                    phonenumbers.PhoneNumberFormat.INTERNATIONAL
                ),
                "valid": phonenumbers.is_valid_number(parsed),
                "possible": phonenumbers.is_possible_number(parsed),
                "country_code": parsed.country_code,
                "national_number": parsed.national_number,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Informações de localização
            if include_location:
                results["location"] = {
                    "country": geocoder.country_name_for_number(parsed, "pt"),
                    "region": geocoder.description_for_number(parsed, "pt"),
                    "timezones": timezone.time_zones_for_number(parsed)
                }
                
            # Informações de operadora
            if include_carrier:
                carrier_name = carrier.name_for_number(parsed, "pt")
                results["carrier"] = {
                    "name": carrier_name if carrier_name else "Desconhecida",
                    "type": self._get_phone_type(parsed)
                }
                
            # Verificar apps de mensagem
            if check_messaging_apps:
                apps = await self._check_messaging_apps(normalized)
                results["messaging_apps"] = apps
                
            # Análise adicional para números brasileiros
            if parsed.country_code == 55:
                results["brazil_info"] = self._analyze_brazilian_number(parsed)
                
            # Calcular score de risco
            results["risk_analysis"] = self._analyze_risk(results)
            
            return results
            
        except phonenumbers.NumberParseException as e:
            logger.error(f"Erro ao analisar número: {e}")
            return {
                "error": "Número inválido",
                "phone": phone,
                "details": str(e)
            }
            
    def _normalize_phone(self, phone: str) -> str:
        """Normaliza número de telefone"""
        # Remove caracteres não numéricos exceto +
        normalized = re.sub(r'[^\d+]', '', phone)
        
        # Se não tem código de país, assume Brasil
        if not normalized.startswith('+'):
            if normalized.startswith('55'):
                normalized = '+' + normalized
            else:
                # Verifica se é número brasileiro pelo padrão
                if len(normalized) in [10, 11]:  # Fixo ou celular brasileiro
                    normalized = '+55' + normalized
                    
        return normalized
        
    def _get_phone_type(self, parsed_number) -> str:
        """Determina tipo de telefone"""
        number_type = phonenumbers.number_type(parsed_number)
        
        types_map = {
            phonenumbers.PhoneNumberType.FIXED_LINE: "Fixo",
            phonenumbers.PhoneNumberType.MOBILE: "Móvel",
            phonenumbers.PhoneNumberType.FIXED_LINE_OR_MOBILE: "Fixo ou Móvel",
            phonenumbers.PhoneNumberType.TOLL_FREE: "Gratuito",
            phonenumbers.PhoneNumberType.PREMIUM_RATE: "Premium",
            phonenumbers.PhoneNumberType.SHARED_COST: "Custo Compartilhado",
            phonenumbers.PhoneNumberType.VOIP: "VoIP",
            phonenumbers.PhoneNumberType.PERSONAL_NUMBER: "Pessoal",
            phonenumbers.PhoneNumberType.PAGER: "Pager",
            phonenumbers.PhoneNumberType.UAN: "UAN",
            phonenumbers.PhoneNumberType.VOICEMAIL: "Correio de Voz",
            phonenumbers.PhoneNumberType.UNKNOWN: "Desconhecido"
        }
        
        return types_map.get(number_type, "Desconhecido")
        
    async def _check_messaging_apps(self, phone: str) -> dict:
        """Verifica presença em apps de mensagem"""
        apps = {
            "whatsapp": {"available": "unknown", "checked": False},
            "telegram": {"available": "unknown", "checked": False},
            "signal": {"available": "unknown", "checked": False}
        }
        
        # WhatsApp check (método simplificado)
        # Em produção, usar API oficial ou métodos mais robustos
        clean_number = phone.replace("+", "").replace(" ", "")
        
        try:
            if not self.session:
                self.session = aiohttp.ClientSession(timeout=self.timeout)
                
            # Verificação básica via WhatsApp Web (limitada)
            whatsapp_url = f"https://wa.me/{clean_number}"
            async with self.session.head(whatsapp_url) as response:
                if response.status == 200:
                    apps["whatsapp"]["available"] = "possible"
                    apps["whatsapp"]["checked"] = True
                    
        except Exception as e:
            logger.debug(f"Erro ao verificar WhatsApp: {e}")
            
        # Para Telegram e Signal, seria necessário usar suas respectivas APIs
        # Por enquanto, retornamos como não verificado
        
        return apps
        
    def _analyze_brazilian_number(self, parsed_number) -> dict:
        """Análise específica para números brasileiros"""
        info = {
            "ddd": None,
            "state": None,
            "region": None,
            "operator_hints": []
        }
        
        # Extrair DDD (2 primeiros dígitos após o código do país)
        national = str(parsed_number.national_number)
        if len(national) >= 10:
            ddd = national[:2]
            info["ddd"] = ddd
            
            # Mapeamento de DDDs para estados brasileiros
            ddd_map = {
                "11": "São Paulo - SP",
                "12": "São José dos Campos - SP",
                "13": "Santos - SP",
                "14": "Bauru - SP",
                "15": "Sorocaba - SP",
                "16": "Ribeirão Preto - SP",
                "17": "São José do Rio Preto - SP",
                "18": "Presidente Prudente - SP",
                "19": "Campinas - SP",
                "21": "Rio de Janeiro - RJ",
                "22": "Campos dos Goytacazes - RJ",
                "24": "Volta Redonda - RJ",
                "27": "Vitória - ES",
                "28": "Cachoeiro de Itapemirim - ES",
                "31": "Belo Horizonte - MG",
                "32": "Juiz de Fora - MG",
                "33": "Governador Valadares - MG",
                "34": "Uberlândia - MG",
                "35": "Poços de Caldas - MG",
                "37": "Divinópolis - MG",
                "38": "Montes Claros - MG",
                "41": "Curitiba - PR",
                "42": "Ponta Grossa - PR",
                "43": "Londrina - PR",
                "44": "Maringá - PR",
                "45": "Foz do Iguaçu - PR",
                "46": "Francisco Beltrão - PR",
                "47": "Joinville - SC",
                "48": "Florianópolis - SC",
                "49": "Chapecó - SC",
                "51": "Porto Alegre - RS",
                "53": "Pelotas - RS",
                "54": "Caxias do Sul - RS",
                "55": "Santa Maria - RS",
                "61": "Brasília - DF",
                "62": "Goiânia - GO",
                "63": "Palmas - TO",
                "64": "Rio Verde - GO",
                "65": "Cuiabá - MT",
                "66": "Rondonópolis - MT",
                "67": "Campo Grande - MS",
                "68": "Acre - AC",
                "69": "Rondônia - RO",
                "71": "Salvador - BA",
                "73": "Ilhéus - BA",
                "74": "Juazeiro - BA",
                "75": "Feira de Santana - BA",
                "77": "Barreiras - BA",
                "79": "Aracaju - SE",
                "81": "Recife - PE",
                "82": "Maceió - AL",
                "83": "João Pessoa - PB",
                "84": "Natal - RN",
                "85": "Fortaleza - CE",
                "86": "Teresina - PI",
                "87": "Petrolina - PE",
                "88": "Juazeiro do Norte - CE",
                "89": "Picos - PI",
                "91": "Belém - PA",
                "92": "Manaus - AM",
                "93": "Santarém - PA",
                "94": "Marabá - PA",
                "95": "Boa Vista - RR",
                "96": "Macapá - AP",
                "97": "Amazonas Interior - AM",
                "98": "São Luís - MA",
                "99": "Imperatriz - MA"
            }
            
            if ddd in ddd_map:
                location = ddd_map[ddd]
                info["region"] = location
                info["state"] = location.split(" - ")[-1] if " - " in location else location
                
            # Identificar possível operadora por padrão do número
            if len(national) == 11:  # Celular
                third_digit = national[2]
                if third_digit in ['9', '8', '7']:
                    info["operator_hints"].append("Celular pós-pago ou pré-pago")
                if third_digit == '9':
                    info["operator_hints"].append("Número mais recente (9º dígito)")
                    
        return info
        
    def _analyze_risk(self, results: dict) -> dict:
        """Analisa risco associado ao número"""
        risk_score = 0
        risk_factors = []
        
        # Verificar validade
        if not results.get("valid", False):
            risk_score += 30
            risk_factors.append("Número inválido ou mal formatado")
            
        # Verificar tipo
        carrier_info = results.get("carrier", {})
        if carrier_info.get("type") == "VoIP":
            risk_score += 20
            risk_factors.append("Número VoIP detectado")
        elif carrier_info.get("type") == "Desconhecido":
            risk_score += 15
            risk_factors.append("Tipo de número desconhecido")
            
        # Verificar apps de mensagem
        apps = results.get("messaging_apps", {})
        if not any(app.get("available") == "possible" for app in apps.values()):
            risk_score += 10
            risk_factors.append("Não encontrado em apps de mensagem comuns")
            
        # Classificar risco
        if risk_score >= 50:
            risk_level = "HIGH"
        elif risk_score >= 25:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"
            
        return {
            "score": risk_score,
            "level": risk_level,
            "factors": risk_factors
        }
