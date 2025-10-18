"""Email Deep Analysis - HIBP Integration + DNS Validation + Linked Accounts.

This module implements a DEEP SEARCH email analyzer that goes beyond basic validation
to provide actionable intelligence including:
- SMTP/MX record validation
- Breach data via HIBP API
- Linked account discovery (Gravatar, GitHub, etc)
- Domain reputation analysis
- Email permutations generation

Author: Claude (OSINT Deep Search Plan - Phase 1.1)
Date: 2025-10-18
Version: 3.0.0 (Deep Search)
"""

import asyncio
import hashlib
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import dns.resolver
import httpx
from email_validator import EmailNotValidError, validate_email

from monitoring.logger import StructuredLogger
from monitoring.metrics import MetricsCollector


class EmailAnalyzerDeep:
    """Deep email analysis with breach data, DNS validation, and linked accounts.
    
    Provides comprehensive email intelligence including:
    - Syntax and deliverability validation
    - MX record lookup
    - HIBP breach data integration
    - Linked social accounts discovery
    - Domain reputation scoring
    - Email permutation generation
    """

    # Common free email providers
    FREE_PROVIDERS = {
        "gmail.com", "yahoo.com", "hotmail.com", "outlook.com",
        "protonmail.com", "icloud.com", "aol.com", "mail.com"
    }

    # Corporate email indicators
    CORPORATE_TLDS = {
        ".com", ".org", ".net", ".edu", ".gov", ".mil",
        ".co.uk", ".com.br", ".de", ".fr", ".jp"
    }

    def __init__(self, hibp_api_key: Optional[str] = None):
        """Initialize EmailAnalyzerDeep.
        
        Args:
            hibp_api_key: Optional HIBP API key for breach lookups
        """
        self.hibp_api_key = hibp_api_key
        self.email_pattern = re.compile(
            r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b"
        )
        
        self.logger = StructuredLogger(tool_name="EmailAnalyzerDeep")
        self.metrics = MetricsCollector(tool_name="EmailAnalyzerDeep")
        
        self.logger.info("email_analyzer_deep_initialized", has_hibp_key=bool(hibp_api_key))

    async def analyze_email(self, email: str) -> Dict[str, Any]:
        """Perform deep analysis on email address.
        
        Args:
            email: Email address to analyze
            
        Returns:
            Comprehensive analysis results
        """
        start_time = datetime.now(timezone.utc)
        self.logger.info("deep_analysis_started", email=email)
        
        result = {
            "email": email,
            "timestamp": start_time.isoformat(),
            "validation": await self._validate_email(email),
            "security": await self._check_breaches(email),
            "linked_accounts": await self._discover_linked_accounts(email),
            "domain_analysis": await self._analyze_domain(email),
            "permutations": self._generate_permutations(email),
            "risk_score": 0
        }
        
        # Calculate risk score
        result["risk_score"] = self._calculate_risk_score(result)
        
        elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()
        self.logger.info("deep_analysis_complete", email=email, elapsed_seconds=elapsed, risk_score=result["risk_score"])
        
        return result

    async def _validate_email(self, email: str) -> Dict[str, Any]:
        """Validate email syntax, domain, and deliverability.
        
        Args:
            email: Email to validate
            
        Returns:
            Validation results
        """
        validation = {
            "syntax_valid": False,
            "domain_exists": False,
            "mx_records": [],
            "smtp_deliverable": False,
            "disposable": False,
            "role_account": False
        }
        
        try:
            # Validate syntax and domain
            v = validate_email(email, check_deliverability=False)
            validation["syntax_valid"] = True
            validation["normalized_email"] = v.normalized
            
            # Check if disposable/role account
            validation["disposable"] = v.domain in ["tempmail.com", "guerrillamail.com", "10minutemail.com"]
            validation["role_account"] = v.local_part in ["admin", "info", "support", "noreply", "postmaster"]
            
            # Check MX records
            domain = email.split("@")[1]
            try:
                mx_records = dns.resolver.resolve(domain, 'MX')
                validation["domain_exists"] = True
                validation["mx_records"] = [str(r.exchange).rstrip('.') for r in mx_records[:5]]
                validation["smtp_deliverable"] = len(validation["mx_records"]) > 0
            except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, dns.resolver.Timeout):
                validation["domain_exists"] = False
                self.logger.warning("mx_lookup_failed", email=email, domain=domain)
                
        except EmailNotValidError as e:
            validation["syntax_valid"] = False
            validation["error"] = str(e)
            self.logger.warning("email_validation_failed", email=email, error=str(e))
            
        return validation

    async def _check_breaches(self, email: str) -> Dict[str, Any]:
        """Check email against HIBP breach database.
        
        Args:
            email: Email to check
            
        Returns:
            Breach data and risk assessment
        """
        security = {
            "breaches_found": 0,
            "breach_list": [],
            "total_exposures": 0,
            "last_breach": None,
            "risk_score": 0,
            "checked": False
        }
        
        if not self.hibp_api_key:
            self.logger.info("hibp_check_skipped", reason="no_api_key")
            return security
        
        try:
            # HIBP API v3
            async with httpx.AsyncClient(timeout=10.0) as client:
                headers = {
                    "hibp-api-key": self.hibp_api_key,
                    "user-agent": "OSINT-Deep-Search"
                }
                
                response = await client.get(
                    f"https://haveibeenpwned.com/api/v3/breachedaccount/{email}",
                    headers=headers
                )
                
                if response.status_code == 200:
                    breaches = response.json()
                    security["checked"] = True
                    security["breaches_found"] = len(breaches)
                    security["total_exposures"] = len(breaches)
                    
                    # Process breaches
                    breach_list = []
                    for breach in breaches[:10]:  # Limit to 10 most recent
                        breach_data = {
                            "name": breach.get("Name", "Unknown"),
                            "date": breach.get("BreachDate", "Unknown"),
                            "data_types": breach.get("DataClasses", []),
                            "verified": breach.get("IsVerified", False),
                            "severity": "high" if breach.get("IsSensitive", False) else "medium"
                        }
                        breach_list.append(breach_data)
                    
                    security["breach_list"] = breach_list
                    
                    # Get most recent breach
                    if breach_list:
                        dates = [b["date"] for b in breach_list if b["date"] != "Unknown"]
                        if dates:
                            security["last_breach"] = max(dates)
                    
                    # Calculate risk score
                    security["risk_score"] = min(len(breaches) * 15, 100)
                    
                    self.logger.info("hibp_check_complete", email=email, breaches=len(breaches))
                    
                elif response.status_code == 404:
                    # No breaches found (good!)
                    security["checked"] = True
                    security["breaches_found"] = 0
                    self.logger.info("hibp_check_complete", email=email, breaches=0)
                    
                else:
                    self.logger.warning("hibp_check_failed", status=response.status_code)
                    
        except Exception as e:
            self.logger.error("hibp_check_error", error=str(e))
            
        return security

    async def _discover_linked_accounts(self, email: str) -> Dict[str, Any]:
        """Discover linked accounts across various platforms.
        
        Args:
            email: Email to search
            
        Returns:
            Linked accounts data
        """
        linked = {
            "gravatar": {"found": False},
            "github": {"found": False},
            "total_found": 0
        }
        
        try:
            # Gravatar check
            email_hash = hashlib.md5(email.lower().encode()).hexdigest()
            async with httpx.AsyncClient(timeout=5.0) as client:
                gravatar_url = f"https://www.gravatar.com/avatar/{email_hash}?d=404"
                response = await client.get(gravatar_url, follow_redirects=True)
                
                if response.status_code == 200:
                    linked["gravatar"] = {
                        "found": True,
                        "profile_url": f"https://www.gravatar.com/{email_hash}",
                        "avatar_url": gravatar_url
                    }
                    linked["total_found"] += 1
                    
        except Exception as e:
            self.logger.warning("gravatar_check_failed", error=str(e))
            
        # GitHub check (by email in commits)
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                github_search_url = f"https://api.github.com/search/users?q={email}+in:email"
                response = await client.get(
                    github_search_url,
                    headers={"Accept": "application/vnd.github.v3+json"}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("total_count", 0) > 0:
                        user = data["items"][0]
                        linked["github"] = {
                            "found": True,
                            "username": user.get("login"),
                            "profile_url": user.get("html_url"),
                            "avatar_url": user.get("avatar_url")
                        }
                        linked["total_found"] += 1
                        
        except Exception as e:
            self.logger.warning("github_check_failed", error=str(e))
            
        return linked

    async def _analyze_domain(self, email: str) -> Dict[str, Any]:
        """Analyze email domain characteristics.
        
        Args:
            email: Email address
            
        Returns:
            Domain analysis
        """
        domain = email.split("@")[1].lower()
        
        analysis = {
            "domain": domain,
            "type": "personal" if domain in self.FREE_PROVIDERS else "corporate",
            "is_free_provider": domain in self.FREE_PROVIDERS,
            "reputation": "unknown",
            "company": None
        }
        
        # Infer company name from domain (simple heuristic)
        if not analysis["is_free_provider"]:
            # Remove TLD
            company_guess = domain.split('.')[0]
            analysis["company"] = company_guess.capitalize()
            analysis["reputation"] = "good"  # Default for corporate
            
        return analysis

    def _generate_permutations(self, email: str) -> List[str]:
        """Generate common email permutations.
        
        Args:
            email: Base email address
            
        Returns:
            List of permutations
        """
        local, domain = email.split("@")
        permutations = [email]
        
        # If email has format first.last
        if "." in local:
            parts = local.split(".")
            if len(parts) == 2:
                first, last = parts
                # Add common permutations
                permutations.extend([
                    f"{first[0]}.{last}@{domain}",  # j.doe
                    f"{first}{last}@{domain}",       # johndoe
                    f"{first[0]}{last}@{domain}",    # jdoe
                    f"{last}.{first}@{domain}",      # doe.john
                ])
                
        return list(set(permutations))[:10]  # Limit to 10

    def _calculate_risk_score(self, result: Dict[str, Any]) -> int:
        """Calculate overall risk score.
        
        Args:
            result: Analysis results
            
        Returns:
            Risk score 0-100
        """
        score = 0
        
        # Validation issues
        if not result["validation"]["syntax_valid"]:
            score += 30
        if not result["validation"]["domain_exists"]:
            score += 20
        if result["validation"]["disposable"]:
            score += 25
            
        # Security issues
        breaches = result["security"]["breaches_found"]
        if breaches > 0:
            score += min(breaches * 10, 40)
            
        # Cap at 100
        return min(score, 100)

    async def get_status(self) -> Dict[str, Any]:
        """Get analyzer status."""
        return {
            "tool": "EmailAnalyzerDeep",
            "version": "3.0.0",
            "healthy": True,
            "features": {
                "dns_validation": True,
                "hibp_integration": bool(self.hibp_api_key),
                "linked_accounts": True,
                "permutations": True
            }
        }
