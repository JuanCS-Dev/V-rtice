"""
Security Utils - Utilitários de segurança
Projeto Vértice - SSP-GO
"""

import re
import hashlib
import hmac
from typing import Optional, List
import logging

logger = logging.getLogger(__name__)

class SecurityUtils:
    """Utilitários de segurança para OSINT"""
    
    @staticmethod
    def sanitize_input(text: str) -> str:
        """Sanitiza entrada do usuário"""
        if not text:
            return ""
            
        # Remove caracteres de controle
        text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)
        
        # Remove tags HTML/JavaScript
        text = re.sub(r'<[^>]*>', '', text)
        
        # Escape caracteres especiais
        dangerous_chars = {
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#x27;',
            '&': '&amp;',
            '/': '&#x2F;'
        }
        
        for char, escape in dangerous_chars.items():
            text = text.replace(char, escape)
            
        return text.strip()
        
    @staticmethod
    def validate_email(email: str) -> bool:
        """Valida formato de email"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
        
    @staticmethod
    def validate_phone(phone: str) -> bool:
        """Valida formato de telefone"""
        # Remove caracteres não numéricos
        digits = re.sub(r'\D', '', phone)
        
        # Verifica comprimento (mínimo 10, máximo 15)
        if len(digits) < 10 or len(digits) > 15:
            return False
            
        return True
        
    @staticmethod
    def hash_password(password: str, salt: Optional[str] = None) -> str:
        """Hash seguro de senha"""
        if not salt:
            import secrets
            salt = secrets.token_hex(32)
            
        key = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000  # iterations
        )
        
        return f"{salt}:{key.hex()}"
        
    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        """Verifica senha contra hash"""
        try:
            salt, key = password_hash.split(':')
            new_hash = SecurityUtils.hash_password(password, salt)
            return new_hash == password_hash
        except:
            return False
            
    @staticmethod
    def detect_sql_injection(text: str) -> bool:
        """Detecta tentativas de SQL injection"""
        sql_patterns = [
            r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|UNION|ALTER|CREATE)\b)",
            r"(--|#|\/\*|\*\/)",
            r"(\bOR\b\s*\d+\s*=\s*\d+)",
            r"(\bAND\b\s*\d+\s*=\s*\d+)",
            r"('|\"|;|\\x00|\\n|\\r|\\x1a)"
        ]
        
        for pattern in sql_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                logger.warning(f"Possível SQL injection detectado: {text[:50]}")
                return True
                
        return False
        
    @staticmethod
    def anonymize_data(data: dict, fields: List[str]) -> dict:
        """Anonimiza campos sensíveis"""
        anonymized = data.copy()
        
        for field in fields:
            if field in anonymized:
                value = str(anonymized[field])
                
                if '@' in value:  # Email
                    parts = value.split('@')
                    anonymized[field] = f"{parts[0][:3]}***@{parts[1]}"
                elif value.isdigit() and len(value) > 6:  # Telefone
                    anonymized[field] = f"{value[:3]}***{value[-2:]}"
                else:  # Outros
                    anonymized[field] = f"{value[:2]}***"
                    
        return anonymized
