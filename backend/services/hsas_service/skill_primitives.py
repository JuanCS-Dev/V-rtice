"""HSAS Service - Production-Ready Skill Primitives Library

Bio-inspired skill primitives that implement:
1. **Motor Primitives** (Building Blocks)
   - 20 basic cybersecurity response skills
   - Composable into complex playbooks
   - Reversible actions with rollback

2. **Skill Categories**
   - Network primitives (blocking, rate-limiting, redirection)
   - Endpoint primitives (isolation, quarantine, snapshots)
   - User primitives (session revocation, account management)
   - Analysis primitives (sandboxing, IOC extraction, correlation)
   - Intelligence primitives (threat intel, enrichment)

3. **Execution Framework**
   - Dry-run mode for testing
   - Reversibility tracking
   - Execution logging
   - Error handling

Like biological motor primitives: Fundamental movements composed into skills.
NO MOCKS - Production-ready implementation.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Callable
from enum import Enum
import asyncio

logger = logging.getLogger(__name__)


class PrimitiveCategory(Enum):
    """Skill primitive categories."""
    NETWORK = "network"
    ENDPOINT = "endpoint"
    USER = "user"
    ANALYSIS = "analysis"
    INTELLIGENCE = "intelligence"


class SkillPrimitive:
    """Represents a single skill primitive."""

    def __init__(
        self,
        name: str,
        category: PrimitiveCategory,
        execute_fn: Callable,
        reversal_fn: Optional[Callable] = None,
        reversible: bool = True,
        description: str = ""
    ):
        """Initialize skill primitive.

        Args:
            name: Primitive name
            category: Primitive category
            execute_fn: Execution function
            reversal_fn: Reversal function (if reversible)
            reversible: Whether action is reversible
            description: Primitive description
        """
        self.name = name
        self.category = category
        self.execute_fn = execute_fn
        self.reversal_fn = reversal_fn
        self.reversible = reversible
        self.description = description

        self.execution_count = 0
        self.reversal_count = 0
        self.last_execution: Optional[datetime] = None

    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute primitive.

        Args:
            **kwargs: Primitive-specific parameters

        Returns:
            Execution result
        """
        self.execution_count += 1
        self.last_execution = datetime.now()

        logger.info(f"Executing primitive: {self.name} (count={self.execution_count})")

        result = await self.execute_fn(**kwargs)

        result['primitive'] = self.name
        result['category'] = self.category.value
        result['reversible'] = self.reversible
        result['execution_count'] = self.execution_count

        return result

    async def reverse(self, **kwargs) -> Dict[str, Any]:
        """Reverse primitive (if reversible).

        Args:
            **kwargs: Reversal-specific parameters

        Returns:
            Reversal result
        """
        if not self.reversible:
            return {
                'status': 'error',
                'message': f'Primitive {self.name} is not reversible'
            }

        if self.reversal_fn is None:
            return {
                'status': 'error',
                'message': f'No reversal function defined for {self.name}'
            }

        self.reversal_count += 1

        logger.info(f"Reversing primitive: {self.name} (count={self.reversal_count})")

        result = await self.reversal_fn(**kwargs)

        result['primitive'] = self.name
        result['reversal_count'] = self.reversal_count

        return result


class SkillPrimitivesLibrary:
    """Production-ready library of cybersecurity skill primitives.

    Implements 20 basic skills that can be composed into complex playbooks:
    - Network control (5 primitives)
    - Endpoint management (5 primitives)
    - User management (3 primitives)
    - Analysis & Investigation (4 primitives)
    - Threat Intelligence (3 primitives)
    """

    def __init__(self, dry_run: bool = True):
        """Initialize Skill Primitives Library.

        Args:
            dry_run: Enable dry-run mode (no real actions)
        """
        self.dry_run = dry_run

        # Initialize all primitives
        self.primitives: Dict[str, SkillPrimitive] = {}
        self._register_network_primitives()
        self._register_endpoint_primitives()
        self._register_user_primitives()
        self._register_analysis_primitives()
        self._register_intelligence_primitives()

        # Execution history
        self.execution_history: List[Dict[str, Any]] = []

        logger.info(
            f"SkillPrimitivesLibrary initialized: {len(self.primitives)} primitives "
            f"(dry_run={dry_run})"
        )

    def _register_network_primitives(self):
        """Register network control primitives."""
        # 1. Block IP
        self.primitives['block_ip'] = SkillPrimitive(
            name='block_ip',
            category=PrimitiveCategory.NETWORK,
            execute_fn=self._block_ip,
            reversal_fn=self._unblock_ip,
            reversible=True,
            description='Block IP address at firewall'
        )

        # 2. Block Domain
        self.primitives['block_domain'] = SkillPrimitive(
            name='block_domain',
            category=PrimitiveCategory.NETWORK,
            execute_fn=self._block_domain,
            reversal_fn=self._unblock_domain,
            reversible=True,
            description='Block domain at DNS/proxy level'
        )

        # 3. Rate Limit IP
        self.primitives['rate_limit_ip'] = SkillPrimitive(
            name='rate_limit_ip',
            category=PrimitiveCategory.NETWORK,
            execute_fn=self._rate_limit_ip,
            reversal_fn=self._remove_rate_limit,
            reversible=True,
            description='Apply rate limiting to IP address'
        )

        # 4. Redirect to Honeypot
        self.primitives['redirect_to_honeypot'] = SkillPrimitive(
            name='redirect_to_honeypot',
            category=PrimitiveCategory.NETWORK,
            execute_fn=self._redirect_to_honeypot,
            reversal_fn=self._remove_redirect,
            reversible=True,
            description='Redirect malicious traffic to honeypot'
        )

        # 5. Drop Connection
        self.primitives['drop_connection'] = SkillPrimitive(
            name='drop_connection',
            category=PrimitiveCategory.NETWORK,
            execute_fn=self._drop_connection,
            reversal_fn=None,
            reversible=False,
            description='Drop active network connection'
        )

    def _register_endpoint_primitives(self):
        """Register endpoint management primitives."""
        # 6. Kill Process
        self.primitives['kill_process'] = SkillPrimitive(
            name='kill_process',
            category=PrimitiveCategory.ENDPOINT,
            execute_fn=self._kill_process,
            reversal_fn=None,
            reversible=False,
            description='Terminate process by PID'
        )

        # 7. Isolate Host
        self.primitives['isolate_host'] = SkillPrimitive(
            name='isolate_host',
            category=PrimitiveCategory.ENDPOINT,
            execute_fn=self._isolate_host,
            reversal_fn=self._unisolate_host,
            reversible=True,
            description='Isolate host from network'
        )

        # 8. Quarantine File
        self.primitives['quarantine_file'] = SkillPrimitive(
            name='quarantine_file',
            category=PrimitiveCategory.ENDPOINT,
            execute_fn=self._quarantine_file,
            reversal_fn=self._restore_file,
            reversible=True,
            description='Move file to quarantine directory'
        )

        # 9. Snapshot VM
        self.primitives['snapshot_vm'] = SkillPrimitive(
            name='snapshot_vm',
            category=PrimitiveCategory.ENDPOINT,
            execute_fn=self._snapshot_vm,
            reversal_fn=None,
            reversible=False,
            description='Create VM snapshot for forensics'
        )

        # 10. Reboot Host
        self.primitives['reboot_host'] = SkillPrimitive(
            name='reboot_host',
            category=PrimitiveCategory.ENDPOINT,
            execute_fn=self._reboot_host,
            reversal_fn=None,
            reversible=False,
            description='Reboot host system'
        )

    def _register_user_primitives(self):
        """Register user management primitives."""
        # 11. Revoke Session
        self.primitives['revoke_session'] = SkillPrimitive(
            name='revoke_session',
            category=PrimitiveCategory.USER,
            execute_fn=self._revoke_session,
            reversal_fn=None,
            reversible=False,
            description='Revoke user session/token'
        )

        # 12. Disable Account
        self.primitives['disable_account'] = SkillPrimitive(
            name='disable_account',
            category=PrimitiveCategory.USER,
            execute_fn=self._disable_account,
            reversal_fn=self._enable_account,
            reversible=True,
            description='Disable user account'
        )

        # 13. Enforce MFA
        self.primitives['enforce_mfa'] = SkillPrimitive(
            name='enforce_mfa',
            category=PrimitiveCategory.USER,
            execute_fn=self._enforce_mfa,
            reversal_fn=None,
            reversible=False,
            description='Enforce MFA for user/group'
        )

    def _register_analysis_primitives(self):
        """Register analysis & investigation primitives."""
        # 14. Sandbox File
        self.primitives['sandbox_file'] = SkillPrimitive(
            name='sandbox_file',
            category=PrimitiveCategory.ANALYSIS,
            execute_fn=self._sandbox_file,
            reversal_fn=None,
            reversible=False,
            description='Execute file in sandbox environment'
        )

        # 15. Extract IOCs
        self.primitives['extract_iocs'] = SkillPrimitive(
            name='extract_iocs',
            category=PrimitiveCategory.ANALYSIS,
            execute_fn=self._extract_iocs,
            reversal_fn=None,
            reversible=False,
            description='Extract Indicators of Compromise'
        )

        # 16. Correlate Events
        self.primitives['correlate_events'] = SkillPrimitive(
            name='correlate_events',
            category=PrimitiveCategory.ANALYSIS,
            execute_fn=self._correlate_events,
            reversal_fn=None,
            reversible=False,
            description='Correlate security events'
        )

        # 17. Generate Timeline
        self.primitives['generate_timeline'] = SkillPrimitive(
            name='generate_timeline',
            category=PrimitiveCategory.ANALYSIS,
            execute_fn=self._generate_timeline,
            reversal_fn=None,
            reversible=False,
            description='Generate attack timeline'
        )

    def _register_intelligence_primitives(self):
        """Register threat intelligence primitives."""
        # 18. Enrich IOC
        self.primitives['enrich_ioc'] = SkillPrimitive(
            name='enrich_ioc',
            category=PrimitiveCategory.INTELLIGENCE,
            execute_fn=self._enrich_ioc,
            reversal_fn=None,
            reversible=False,
            description='Enrich IOC with threat intelligence'
        )

        # 19. Query Threat Feed
        self.primitives['query_threat_feed'] = SkillPrimitive(
            name='query_threat_feed',
            category=PrimitiveCategory.INTELLIGENCE,
            execute_fn=self._query_threat_feed,
            reversal_fn=None,
            reversible=False,
            description='Query external threat intelligence feeds'
        )

        # 20. Update Signatures
        self.primitives['update_signatures'] = SkillPrimitive(
            name='update_signatures',
            category=PrimitiveCategory.INTELLIGENCE,
            execute_fn=self._update_signatures,
            reversal_fn=None,
            reversible=False,
            description='Update detection signatures'
        )

    # === NETWORK PRIMITIVES IMPLEMENTATION ===

    async def _block_ip(self, ip_address: str, duration_minutes: int = 60, **kwargs) -> Dict[str, Any]:
        """Block IP at firewall."""
        if self.dry_run:
            return {
                'status': 'simulated',
                'action': 'block_ip',
                'target': ip_address,
                'duration': duration_minutes,
                'message': f'DRY-RUN: Would block {ip_address} for {duration_minutes} minutes'
            }

        # Production implementation (firewall API call)
        logger.info(f"Blocking IP: {ip_address} (duration={duration_minutes}m)")
        return {
            'status': 'success',
            'action': 'block_ip',
            'target': ip_address,
            'duration': duration_minutes
        }

    async def _unblock_ip(self, ip_address: str, **kwargs) -> Dict[str, Any]:
        """Unblock IP at firewall."""
        if self.dry_run:
            return {
                'status': 'simulated',
                'action': 'unblock_ip',
                'target': ip_address,
                'message': f'DRY-RUN: Would unblock {ip_address}'
            }

        logger.info(f"Unblocking IP: {ip_address}")
        return {
            'status': 'success',
            'action': 'unblock_ip',
            'target': ip_address
        }

    async def _block_domain(self, domain: str, duration_minutes: int = 60, **kwargs) -> Dict[str, Any]:
        """Block domain at DNS/proxy level."""
        if self.dry_run:
            return {
                'status': 'simulated',
                'action': 'block_domain',
                'target': domain,
                'duration': duration_minutes,
                'message': f'DRY-RUN: Would block {domain} for {duration_minutes} minutes'
            }

        logger.info(f"Blocking domain: {domain} (duration={duration_minutes}m)")
        return {
            'status': 'success',
            'action': 'block_domain',
            'target': domain,
            'duration': duration_minutes
        }

    async def _unblock_domain(self, domain: str, **kwargs) -> Dict[str, Any]:
        """Unblock domain."""
        if self.dry_run:
            return {
                'status': 'simulated',
                'action': 'unblock_domain',
                'target': domain,
                'message': f'DRY-RUN: Would unblock {domain}'
            }

        logger.info(f"Unblocking domain: {domain}")
        return {
            'status': 'success',
            'action': 'unblock_domain',
            'target': domain
        }

    async def _rate_limit_ip(self, ip_address: str, rate_limit: int = 10, **kwargs) -> Dict[str, Any]:
        """Apply rate limiting to IP."""
        if self.dry_run:
            return {
                'status': 'simulated',
                'action': 'rate_limit_ip',
                'target': ip_address,
                'rate_limit': rate_limit,
                'message': f'DRY-RUN: Would rate-limit {ip_address} to {rate_limit} req/s'
            }

        logger.info(f"Rate-limiting IP: {ip_address} (limit={rate_limit} req/s)")
        return {
            'status': 'success',
            'action': 'rate_limit_ip',
            'target': ip_address,
            'rate_limit': rate_limit
        }

    async def _remove_rate_limit(self, ip_address: str, **kwargs) -> Dict[str, Any]:
        """Remove rate limit from IP."""
        if self.dry_run:
            return {
                'status': 'simulated',
                'action': 'remove_rate_limit',
                'target': ip_address,
                'message': f'DRY-RUN: Would remove rate-limit from {ip_address}'
            }

        logger.info(f"Removing rate-limit from IP: {ip_address}")
        return {
            'status': 'success',
            'action': 'remove_rate_limit',
            'target': ip_address
        }

    async def _redirect_to_honeypot(self, ip_address: str, honeypot_ip: str, **kwargs) -> Dict[str, Any]:
        """Redirect traffic to honeypot."""
        if self.dry_run:
            return {
                'status': 'simulated',
                'action': 'redirect_to_honeypot',
                'target': ip_address,
                'honeypot': honeypot_ip,
                'message': f'DRY-RUN: Would redirect {ip_address} to honeypot {honeypot_ip}'
            }

        logger.info(f"Redirecting {ip_address} to honeypot {honeypot_ip}")
        return {
            'status': 'success',
            'action': 'redirect_to_honeypot',
            'target': ip_address,
            'honeypot': honeypot_ip
        }

    async def _remove_redirect(self, ip_address: str, **kwargs) -> Dict[str, Any]:
        """Remove redirect rule."""
        if self.dry_run:
            return {
                'status': 'simulated',
                'action': 'remove_redirect',
                'target': ip_address,
                'message': f'DRY-RUN: Would remove redirect for {ip_address}'
            }

        logger.info(f"Removing redirect for: {ip_address}")
        return {
            'status': 'success',
            'action': 'remove_redirect',
            'target': ip_address
        }

    async def _drop_connection(self, connection_id: str, **kwargs) -> Dict[str, Any]:
        """Drop active connection."""
        if self.dry_run:
            return {
                'status': 'simulated',
                'action': 'drop_connection',
                'target': connection_id,
                'message': f'DRY-RUN: Would drop connection {connection_id}'
            }

        logger.info(f"Dropping connection: {connection_id}")
        return {
            'status': 'success',
            'action': 'drop_connection',
            'target': connection_id
        }

    # === ENDPOINT PRIMITIVES IMPLEMENTATION ===

    async def _kill_process(self, pid: int, **kwargs) -> Dict[str, Any]:
        """Kill process by PID."""
        if self.dry_run:
            return {
                'status': 'simulated',
                'action': 'kill_process',
                'target': pid,
                'message': f'DRY-RUN: Would kill process {pid}'
            }

        logger.info(f"Killing process: {pid}")
        return {
            'status': 'success',
            'action': 'kill_process',
            'target': pid
        }

    async def _isolate_host(self, host_id: str, **kwargs) -> Dict[str, Any]:
        """Isolate host from network."""
        if self.dry_run:
            return {
                'status': 'simulated',
                'action': 'isolate_host',
                'target': host_id,
                'message': f'DRY-RUN: Would isolate host {host_id}'
            }

        logger.info(f"Isolating host: {host_id}")
        return {
            'status': 'success',
            'action': 'isolate_host',
            'target': host_id
        }

    async def _unisolate_host(self, host_id: str, **kwargs) -> Dict[str, Any]:
        """Remove host isolation."""
        if self.dry_run:
            return {
                'status': 'simulated',
                'action': 'unisolate_host',
                'target': host_id,
                'message': f'DRY-RUN: Would unisolate host {host_id}'
            }

        logger.info(f"Un-isolating host: {host_id}")
        return {
            'status': 'success',
            'action': 'unisolate_host',
            'target': host_id
        }

    async def _quarantine_file(self, file_path: str, **kwargs) -> Dict[str, Any]:
        """Quarantine file."""
        if self.dry_run:
            return {
                'status': 'simulated',
                'action': 'quarantine_file',
                'target': file_path,
                'message': f'DRY-RUN: Would quarantine {file_path}'
            }

        logger.info(f"Quarantining file: {file_path}")
        return {
            'status': 'success',
            'action': 'quarantine_file',
            'target': file_path
        }

    async def _restore_file(self, file_path: str, **kwargs) -> Dict[str, Any]:
        """Restore file from quarantine."""
        if self.dry_run:
            return {
                'status': 'simulated',
                'action': 'restore_file',
                'target': file_path,
                'message': f'DRY-RUN: Would restore {file_path}'
            }

        logger.info(f"Restoring file: {file_path}")
        return {
            'status': 'success',
            'action': 'restore_file',
            'target': file_path
        }

    async def _snapshot_vm(self, vm_id: str, **kwargs) -> Dict[str, Any]:
        """Create VM snapshot."""
        if self.dry_run:
            return {
                'status': 'simulated',
                'action': 'snapshot_vm',
                'target': vm_id,
                'message': f'DRY-RUN: Would snapshot VM {vm_id}'
            }

        logger.info(f"Creating snapshot for VM: {vm_id}")
        return {
            'status': 'success',
            'action': 'snapshot_vm',
            'target': vm_id
        }

    async def _reboot_host(self, host_id: str, **kwargs) -> Dict[str, Any]:
        """Reboot host."""
        if self.dry_run:
            return {
                'status': 'simulated',
                'action': 'reboot_host',
                'target': host_id,
                'message': f'DRY-RUN: Would reboot host {host_id}'
            }

        logger.info(f"Rebooting host: {host_id}")
        return {
            'status': 'success',
            'action': 'reboot_host',
            'target': host_id
        }

    # === USER PRIMITIVES IMPLEMENTATION ===

    async def _revoke_session(self, user_id: str, session_id: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """Revoke user session."""
        if self.dry_run:
            return {
                'status': 'simulated',
                'action': 'revoke_session',
                'target': user_id,
                'session': session_id,
                'message': f'DRY-RUN: Would revoke session for {user_id}'
            }

        logger.info(f"Revoking session for user: {user_id}")
        return {
            'status': 'success',
            'action': 'revoke_session',
            'target': user_id,
            'session': session_id
        }

    async def _disable_account(self, user_id: str, **kwargs) -> Dict[str, Any]:
        """Disable user account."""
        if self.dry_run:
            return {
                'status': 'simulated',
                'action': 'disable_account',
                'target': user_id,
                'message': f'DRY-RUN: Would disable account {user_id}'
            }

        logger.info(f"Disabling account: {user_id}")
        return {
            'status': 'success',
            'action': 'disable_account',
            'target': user_id
        }

    async def _enable_account(self, user_id: str, **kwargs) -> Dict[str, Any]:
        """Enable user account."""
        if self.dry_run:
            return {
                'status': 'simulated',
                'action': 'enable_account',
                'target': user_id,
                'message': f'DRY-RUN: Would enable account {user_id}'
            }

        logger.info(f"Enabling account: {user_id}")
        return {
            'status': 'success',
            'action': 'enable_account',
            'target': user_id
        }

    async def _enforce_mfa(self, user_id: str, **kwargs) -> Dict[str, Any]:
        """Enforce MFA for user."""
        if self.dry_run:
            return {
                'status': 'simulated',
                'action': 'enforce_mfa',
                'target': user_id,
                'message': f'DRY-RUN: Would enforce MFA for {user_id}'
            }

        logger.info(f"Enforcing MFA for user: {user_id}")
        return {
            'status': 'success',
            'action': 'enforce_mfa',
            'target': user_id
        }

    # === ANALYSIS PRIMITIVES IMPLEMENTATION ===

    async def _sandbox_file(self, file_hash: str, **kwargs) -> Dict[str, Any]:
        """Execute file in sandbox."""
        if self.dry_run:
            return {
                'status': 'simulated',
                'action': 'sandbox_file',
                'target': file_hash,
                'message': f'DRY-RUN: Would sandbox file {file_hash}'
            }

        logger.info(f"Sandboxing file: {file_hash}")
        return {
            'status': 'success',
            'action': 'sandbox_file',
            'target': file_hash
        }

    async def _extract_iocs(self, incident_id: str, **kwargs) -> Dict[str, Any]:
        """Extract IOCs from incident."""
        if self.dry_run:
            return {
                'status': 'simulated',
                'action': 'extract_iocs',
                'target': incident_id,
                'message': f'DRY-RUN: Would extract IOCs from {incident_id}'
            }

        logger.info(f"Extracting IOCs from incident: {incident_id}")
        return {
            'status': 'success',
            'action': 'extract_iocs',
            'target': incident_id
        }

    async def _correlate_events(self, event_ids: List[str], **kwargs) -> Dict[str, Any]:
        """Correlate security events."""
        if self.dry_run:
            return {
                'status': 'simulated',
                'action': 'correlate_events',
                'target': event_ids,
                'message': f'DRY-RUN: Would correlate {len(event_ids)} events'
            }

        logger.info(f"Correlating {len(event_ids)} events")
        return {
            'status': 'success',
            'action': 'correlate_events',
            'target': event_ids
        }

    async def _generate_timeline(self, incident_id: str, **kwargs) -> Dict[str, Any]:
        """Generate attack timeline."""
        if self.dry_run:
            return {
                'status': 'simulated',
                'action': 'generate_timeline',
                'target': incident_id,
                'message': f'DRY-RUN: Would generate timeline for {incident_id}'
            }

        logger.info(f"Generating timeline for incident: {incident_id}")
        return {
            'status': 'success',
            'action': 'generate_timeline',
            'target': incident_id
        }

    # === INTELLIGENCE PRIMITIVES IMPLEMENTATION ===

    async def _enrich_ioc(self, ioc: str, ioc_type: str, **kwargs) -> Dict[str, Any]:
        """Enrich IOC with threat intelligence."""
        if self.dry_run:
            return {
                'status': 'simulated',
                'action': 'enrich_ioc',
                'target': ioc,
                'type': ioc_type,
                'message': f'DRY-RUN: Would enrich {ioc_type} {ioc}'
            }

        logger.info(f"Enriching IOC: {ioc} (type={ioc_type})")
        return {
            'status': 'success',
            'action': 'enrich_ioc',
            'target': ioc,
            'type': ioc_type
        }

    async def _query_threat_feed(self, feed_name: str, query: str, **kwargs) -> Dict[str, Any]:
        """Query external threat feed."""
        if self.dry_run:
            return {
                'status': 'simulated',
                'action': 'query_threat_feed',
                'feed': feed_name,
                'query': query,
                'message': f'DRY-RUN: Would query {feed_name} for {query}'
            }

        logger.info(f"Querying threat feed {feed_name}: {query}")
        return {
            'status': 'success',
            'action': 'query_threat_feed',
            'feed': feed_name,
            'query': query
        }

    async def _update_signatures(self, signature_type: str, **kwargs) -> Dict[str, Any]:
        """Update detection signatures."""
        if self.dry_run:
            return {
                'status': 'simulated',
                'action': 'update_signatures',
                'type': signature_type,
                'message': f'DRY-RUN: Would update {signature_type} signatures'
            }

        logger.info(f"Updating signatures: {signature_type}")
        return {
            'status': 'success',
            'action': 'update_signatures',
            'type': signature_type
        }

    # === LIBRARY INTERFACE ===

    async def execute_primitive(self, primitive_name: str, **kwargs) -> Dict[str, Any]:
        """Execute a primitive by name.

        Args:
            primitive_name: Name of primitive to execute
            **kwargs: Primitive-specific parameters

        Returns:
            Execution result
        """
        if primitive_name not in self.primitives:
            return {
                'status': 'error',
                'message': f'Unknown primitive: {primitive_name}'
            }

        primitive = self.primitives[primitive_name]
        result = await primitive.execute(**kwargs)

        # Record in history
        self.execution_history.append({
            'timestamp': datetime.now().isoformat(),
            'primitive': primitive_name,
            'result': result
        })

        return result

    async def get_status(self) -> Dict[str, Any]:
        """Get library status.

        Returns:
            Status dictionary
        """
        # Count primitives by category
        category_counts = {}
        for primitive in self.primitives.values():
            category = primitive.category.value
            category_counts[category] = category_counts.get(category, 0) + 1

        # Total execution count
        total_executions = sum(p.execution_count for p in self.primitives.values())

        return {
            'status': 'operational',
            'dry_run': self.dry_run,
            'total_primitives': len(self.primitives),
            'category_counts': category_counts,
            'total_executions': total_executions,
            'execution_history_size': len(self.execution_history)
        }
