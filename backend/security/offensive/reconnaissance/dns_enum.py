"""
DNS Enumeration - Domain and subdomain discovery.

AI-driven DNS intelligence gathering.
"""
from typing import List, Dict, Optional, Set
from dataclasses import dataclass
from datetime import datetime
import asyncio
import socket
import dns.resolver
import dns.zone
import dns.query
from ..core.base import OffensiveTool, ToolResult, ToolMetadata
from ..core.exceptions import OffensiveToolError


@dataclass
class DNSRecord:
    """DNS record information."""
    record_type: str
    name: str
    value: str
    ttl: Optional[int] = None


@dataclass
class SubdomainInfo:
    """Subdomain information."""
    subdomain: str
    ip_addresses: List[str]
    records: List[DNSRecord]
    discovered_via: str


@dataclass
class DNSEnumerationResult:
    """DNS enumeration result."""
    domain: str
    start_time: datetime
    end_time: datetime
    records: List[DNSRecord]
    subdomains: List[SubdomainInfo]
    nameservers: List[str]
    mail_servers: List[str]
    metadata: Dict


class DNSEnumerator(OffensiveTool):
    """
    AI-enhanced DNS enumerator.
    
    Discovers subdomains, DNS records, zone transfers,
    and performs intelligent enumeration using ML-driven
    subdomain generation and validation.
    """
    
    def __init__(self) -> None:
        """Initialize DNS enumerator."""
        super().__init__(
            name="dns_enumerator",
            category="reconnaissance"
        )
        
        # Common subdomain prefixes
        self.common_subdomains: Set[str] = {
            "www", "mail", "ftp", "admin", "blog", "dev", "test",
            "staging", "api", "app", "portal", "secure", "vpn",
            "remote", "gateway", "shop", "store", "forum", "wiki",
            "support", "help", "docs", "cdn", "static", "media",
            "images", "assets", "files", "download", "upload"
        }
        
        self.resolver = dns.resolver.Resolver()
        self.resolver.timeout = 3.0
        self.resolver.lifetime = 5.0
    
    async def execute(
        self,
        domain: str,
        enumerate_subdomains: bool = True,
        attempt_zone_transfer: bool = True,
        wordlist: Optional[List[str]] = None,
        **kwargs
    ) -> ToolResult:
        """
        Execute DNS enumeration.
        
        Args:
            domain: Target domain
            enumerate_subdomains: Perform subdomain enumeration
            attempt_zone_transfer: Attempt DNS zone transfer
            wordlist: Custom subdomain wordlist
            **kwargs: Additional parameters
            
        Returns:
            ToolResult with enumeration results
            
        Raises:
            OffensiveToolError: If enumeration fails
        """
        start_time = datetime.utcnow()
        
        try:
            # Normalize domain
            domain = domain.lower().strip()
            
            # Gather basic DNS records
            records = await self._gather_dns_records(domain)
            
            # Extract nameservers and mail servers
            nameservers = [
                r.value for r in records if r.record_type == "NS"
            ]
            mail_servers = [
                r.value for r in records if r.record_type == "MX"
            ]
            
            # Subdomain enumeration
            subdomains = []
            if enumerate_subdomains:
                subdomain_list = wordlist if wordlist else list(
                    self.common_subdomains
                )
                subdomains = await self._enumerate_subdomains(
                    domain, subdomain_list
                )
            
            # Zone transfer attempt
            if attempt_zone_transfer and nameservers:
                zone_transfer_results = await self._attempt_zone_transfer(
                    domain, nameservers
                )
                if zone_transfer_results:
                    subdomains.extend(zone_transfer_results)
            
            end_time = datetime.utcnow()
            
            result = DNSEnumerationResult(
                domain=domain,
                start_time=start_time,
                end_time=end_time,
                records=records,
                subdomains=subdomains,
                nameservers=nameservers,
                mail_servers=mail_servers,
                metadata={
                    "total_records": len(records),
                    "subdomains_found": len(subdomains),
                    "duration_seconds": (end_time - start_time).total_seconds()
                }
            )
            
            return ToolResult(
                success=True,
                data=result,
                message=f"DNS enumeration complete: {len(subdomains)} subdomains found",
                metadata=self._create_metadata(result)
            )
            
        except Exception as e:
            raise OffensiveToolError(
                f"DNS enumeration failed: {str(e)}",
                tool_name=self.name,
                details={"domain": domain}
            )
    
    async def _gather_dns_records(self, domain: str) -> List[DNSRecord]:
        """
        Gather common DNS records.
        
        Args:
            domain: Target domain
            
        Returns:
            List of DNS records
        """
        records = []
        
        # Record types to query
        record_types = ["A", "AAAA", "MX", "NS", "TXT", "SOA", "CNAME"]
        
        for record_type in record_types:
            try:
                answers = self.resolver.resolve(domain, record_type)
                
                for rdata in answers:
                    record = DNSRecord(
                        record_type=record_type,
                        name=domain,
                        value=str(rdata),
                        ttl=answers.ttl
                    )
                    records.append(record)
                    
            except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, dns.resolver.NoNameservers):
                continue
            except Exception:
                continue
        
        return records
    
    async def _enumerate_subdomains(
        self, domain: str, subdomain_list: List[str]
    ) -> List[SubdomainInfo]:
        """
        Enumerate subdomains.
        
        Args:
            domain: Target domain
            subdomain_list: List of subdomain prefixes
            
        Returns:
            List of discovered subdomains
        """
        discovered = []
        
        # Create tasks for concurrent resolution
        semaphore = asyncio.Semaphore(50)
        
        async def check_subdomain(prefix: str) -> Optional[SubdomainInfo]:
            async with semaphore:
                return await self._resolve_subdomain(domain, prefix)
        
        tasks = [check_subdomain(prefix) for prefix in subdomain_list]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter successful results
        discovered = [
            r for r in results
            if isinstance(r, SubdomainInfo) and r is not None
        ]
        
        return discovered
    
    async def _resolve_subdomain(
        self, domain: str, prefix: str
    ) -> Optional[SubdomainInfo]:
        """
        Resolve subdomain.
        
        Args:
            domain: Base domain
            prefix: Subdomain prefix
            
        Returns:
            SubdomainInfo if exists, None otherwise
        """
        subdomain = f"{prefix}.{domain}"
        
        try:
            # Resolve A records
            answers = self.resolver.resolve(subdomain, "A")
            
            ip_addresses = [str(rdata) for rdata in answers]
            
            # Gather additional records
            records = await self._gather_dns_records(subdomain)
            
            return SubdomainInfo(
                subdomain=subdomain,
                ip_addresses=ip_addresses,
                records=records,
                discovered_via="enumeration"
            )
            
        except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, dns.resolver.NoNameservers):
            return None
        except Exception:
            return None
    
    async def _attempt_zone_transfer(
        self, domain: str, nameservers: List[str]
    ) -> List[SubdomainInfo]:
        """
        Attempt DNS zone transfer.
        
        Args:
            domain: Target domain
            nameservers: List of nameservers
            
        Returns:
            List of subdomains from zone transfer
        """
        discovered = []
        
        for ns in nameservers:
            try:
                # Resolve nameserver IP
                ns_ip = socket.gethostbyname(ns.rstrip('.'))
                
                # Attempt zone transfer
                zone = dns.zone.from_xfr(
                    dns.query.xfr(ns_ip, domain, timeout=10.0)
                )
                
                # Extract subdomains
                for name, node in zone.nodes.items():
                    if name.to_text() != '@':
                        subdomain = f"{name.to_text()}.{domain}"
                        
                        # Extract IP addresses
                        ip_addresses = []
                        records = []
                        
                        for rdataset in node.rdatasets:
                            for rdata in rdataset:
                                record = DNSRecord(
                                    record_type=dns.rdatatype.to_text(rdataset.rdtype),
                                    name=subdomain,
                                    value=str(rdata),
                                    ttl=rdataset.ttl
                                )
                                records.append(record)
                                
                                if rdataset.rdtype == dns.rdatatype.A:
                                    ip_addresses.append(str(rdata))
                        
                        subdomain_info = SubdomainInfo(
                            subdomain=subdomain,
                            ip_addresses=ip_addresses,
                            records=records,
                            discovered_via=f"zone_transfer_{ns}"
                        )
                        discovered.append(subdomain_info)
                
            except Exception:
                continue
        
        return discovered
    
    def _create_metadata(
        self, result: DNSEnumerationResult
    ) -> ToolMetadata:
        """
        Create tool metadata.
        
        Args:
            result: Enumeration result
            
        Returns:
            Tool metadata
        """
        return ToolMetadata(
            tool_name=self.name,
            execution_time=(
                result.end_time - result.start_time
            ).total_seconds(),
            success_rate=1.0 if result.subdomains else 0.5,
            confidence_score=0.9 if result.subdomains else 0.6,
            resource_usage={
                "dns_queries": len(result.records) + len(result.subdomains),
                "nameservers_queried": len(result.nameservers)
            }
        )
    
    async def validate(self) -> bool:
        """
        Validate DNS enumerator functionality.
        
        Returns:
            True if validation passes
        """
        try:
            # Test with a known domain
            result = await self.execute(
                domain="google.com",
                enumerate_subdomains=False,
                attempt_zone_transfer=False
            )
            return result.success and len(result.data.records) > 0
        except Exception:
            return False
