"""
RTE - Playbooks Reflexos
========================
Autonomous response actions executed by the Reflex Triage Engine.

5 core playbooks:
1. block_ip - Block malicious IP via iptables/nftables
2. kill_process - Terminate suspicious process
3. isolate_host - Network quarantine via K8s NetworkPolicy
4. quarantine_file - Move file to isolated sandbox
5. redirect_honeypot - Redirect traffic to honeypot

Target execution time: <5ms per action
"""

import logging
import subprocess
import shutil
import time
from typing import Dict, Optional, List
from dataclasses import dataclass
from pathlib import Path
from enum import Enum
import asyncio

logger = logging.getLogger(__name__)


class PlaybookStatus(str, Enum):
    """Playbook execution status"""
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    PARTIAL = "PARTIAL"
    DRY_RUN = "DRY_RUN"


@dataclass
class PlaybookResult:
    """Result from playbook execution"""
    playbook_name: str
    status: PlaybookStatus
    execution_time_ms: float
    actions_taken: List[str]
    error_message: Optional[str] = None
    rollback_info: Optional[Dict] = None
    metadata: Dict = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class PlaybookExecutor:
    """
    Base class for playbook execution with safety checks.

    All playbooks support:
    - Dry-run mode (for testing)
    - Rollback capability
    - Execution time tracking
    - Error handling
    """

    def __init__(self, dry_run: bool = False, enable_rollback: bool = True):
        self.dry_run = dry_run
        self.enable_rollback = enable_rollback
        self.execution_history: List[PlaybookResult] = []

        logger.info(
            f"Playbook executor initialized (dry_run={dry_run}, "
            f"rollback={enable_rollback})"
        )

    async def execute(
        self,
        playbook_name: str,
        params: Dict
    ) -> PlaybookResult:
        """
        Execute a playbook with timing and error handling.

        Args:
            playbook_name: Name of playbook to execute
            params: Playbook-specific parameters

        Returns:
            PlaybookResult with execution details
        """
        start_time = time.time()

        try:
            # Dispatch to specific playbook
            if playbook_name == "block_ip":
                result = await self.block_ip(**params)
            elif playbook_name == "kill_process":
                result = await self.kill_process(**params)
            elif playbook_name == "isolate_host":
                result = await self.isolate_host(**params)
            elif playbook_name == "quarantine_file":
                result = await self.quarantine_file(**params)
            elif playbook_name == "redirect_honeypot":
                result = await self.redirect_honeypot(**params)
            else:
                raise ValueError(f"Unknown playbook: {playbook_name}")

            execution_time_ms = (time.time() - start_time) * 1000
            result.execution_time_ms = execution_time_ms

            # Store in history
            self.execution_history.append(result)

            logger.info(
                f"Playbook {playbook_name} completed: {result.status} "
                f"in {execution_time_ms:.2f}ms"
            )

            return result

        except Exception as e:
            execution_time_ms = (time.time() - start_time) * 1000
            logger.error(f"Playbook {playbook_name} failed: {e}")

            result = PlaybookResult(
                playbook_name=playbook_name,
                status=PlaybookStatus.FAILED,
                execution_time_ms=execution_time_ms,
                actions_taken=[],
                error_message=str(e)
            )

            self.execution_history.append(result)
            return result

    async def block_ip(
        self,
        ip_address: str,
        protocol: str = "tcp",
        port: Optional[int] = None,
        duration_seconds: Optional[int] = None
    ) -> PlaybookResult:
        """
        Block malicious IP using iptables/nftables.

        Args:
            ip_address: IP to block (e.g., "192.168.1.100")
            protocol: Protocol to block ("tcp", "udp", "all")
            port: Specific port to block (optional)
            duration_seconds: Auto-unblock after duration (optional)

        Returns:
            PlaybookResult with iptables commands executed
        """
        actions = []
        rollback_commands = []

        # Build iptables command
        if port:
            rule = f"-A INPUT -s {ip_address} -p {protocol} --dport {port} -j DROP"
            rollback_rule = f"-D INPUT -s {ip_address} -p {protocol} --dport {port} -j DROP"
            description = f"Block {ip_address}:{port}/{protocol}"
        else:
            rule = f"-A INPUT -s {ip_address} -j DROP"
            rollback_rule = f"-D INPUT -s {ip_address} -j DROP"
            description = f"Block {ip_address} (all traffic)"

        cmd = ["iptables", rule.split()[0], *rule.split()[1:]]

        if self.dry_run:
            logger.info(f"[DRY-RUN] Would execute: {' '.join(cmd)}")
            return PlaybookResult(
                playbook_name="block_ip",
                status=PlaybookStatus.DRY_RUN,
                execution_time_ms=0.0,
                actions_taken=[description],
                rollback_info={"commands": [rollback_rule]}
            )

        try:
            # Execute iptables command
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                actions.append(description)
                rollback_commands.append(rollback_rule)

                # Schedule auto-unblock if duration specified
                if duration_seconds:
                    asyncio.create_task(
                        self._schedule_unblock(ip_address, duration_seconds)
                    )
                    actions.append(f"Scheduled unblock in {duration_seconds}s")

                return PlaybookResult(
                    playbook_name="block_ip",
                    status=PlaybookStatus.SUCCESS,
                    execution_time_ms=0.0,  # Will be set by execute()
                    actions_taken=actions,
                    rollback_info={"commands": rollback_commands} if self.enable_rollback else None,
                    metadata={"ip": ip_address, "port": port, "protocol": protocol}
                )
            else:
                raise RuntimeError(f"iptables failed: {result.stderr}")

        except subprocess.TimeoutExpired:
            raise RuntimeError("iptables command timed out")
        except FileNotFoundError:
            raise RuntimeError("iptables not found (not running as root?)")

    async def _schedule_unblock(self, ip_address: str, delay_seconds: int):
        """Schedule automatic IP unblock after delay"""
        await asyncio.sleep(delay_seconds)

        unblock_cmd = ["iptables", "-D", "INPUT", "-s", ip_address, "-j", "DROP"]

        try:
            subprocess.run(unblock_cmd, capture_output=True, timeout=5)
            logger.info(f"Auto-unblocked {ip_address} after {delay_seconds}s")
        except Exception as e:
            logger.error(f"Failed to auto-unblock {ip_address}: {e}")

    async def kill_process(
        self,
        pid: int,
        signal: str = "SIGTERM",
        force_after_seconds: int = 5
    ) -> PlaybookResult:
        """
        Terminate suspicious process.

        Args:
            pid: Process ID to kill
            signal: Signal to send (SIGTERM, SIGKILL)
            force_after_seconds: Send SIGKILL after timeout if still alive

        Returns:
            PlaybookResult with kill commands executed
        """
        actions = []

        # Validate PID exists
        try:
            proc_path = Path(f"/proc/{pid}")
            if not proc_path.exists():
                raise ValueError(f"Process {pid} does not exist")

            # Read process info for logging
            cmdline = (proc_path / "cmdline").read_text().replace("\x00", " ")
            actions.append(f"Target process: {cmdline}")
        except Exception as e:
            raise ValueError(f"Cannot access process {pid}: {e}")

        if self.dry_run:
            logger.info(f"[DRY-RUN] Would kill process {pid} with {signal}")
            return PlaybookResult(
                playbook_name="kill_process",
                status=PlaybookStatus.DRY_RUN,
                execution_time_ms=0.0,
                actions_taken=[f"Kill process {pid} ({signal})"],
                metadata={"pid": pid, "signal": signal}
            )

        try:
            # Send initial signal
            subprocess.run(
                ["kill", f"-{signal}", str(pid)],
                capture_output=True,
                check=True,
                timeout=2
            )
            actions.append(f"Sent {signal} to process {pid}")

            # Check if process is still alive
            if signal == "SIGTERM":
                await asyncio.sleep(force_after_seconds)

                if Path(f"/proc/{pid}").exists():
                    # Process still alive, force kill
                    subprocess.run(
                        ["kill", "-SIGKILL", str(pid)],
                        capture_output=True,
                        check=True,
                        timeout=2
                    )
                    actions.append(f"Forced SIGKILL after {force_after_seconds}s")

            return PlaybookResult(
                playbook_name="kill_process",
                status=PlaybookStatus.SUCCESS,
                execution_time_ms=0.0,
                actions_taken=actions,
                rollback_info=None,  # Cannot rollback process termination
                metadata={"pid": pid, "signal": signal}
            )

        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to kill process: {e.stderr}")

    async def isolate_host(
        self,
        namespace: str,
        pod_name: str,
        isolation_type: str = "full"
    ) -> PlaybookResult:
        """
        Isolate Kubernetes pod via NetworkPolicy.

        Args:
            namespace: K8s namespace
            pod_name: Pod to isolate
            isolation_type: "full" (no traffic) or "egress_only" (no ingress)

        Returns:
            PlaybookResult with NetworkPolicy created
        """
        actions = []

        # Generate NetworkPolicy YAML
        if isolation_type == "full":
            policy = f"""
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: isolate-{pod_name}
  namespace: {namespace}
spec:
  podSelector:
    matchLabels:
      app: {pod_name}
  policyTypes:
  - Ingress
  - Egress
  # Empty ingress/egress = deny all
"""
        else:  # egress_only
            policy = f"""
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: isolate-{pod_name}
  namespace: {namespace}
spec:
  podSelector:
    matchLabels:
      app: {pod_name}
  policyTypes:
  - Ingress
  # Empty ingress = deny all incoming
"""

        if self.dry_run:
            logger.info(f"[DRY-RUN] Would apply NetworkPolicy to isolate {pod_name}")
            return PlaybookResult(
                playbook_name="isolate_host",
                status=PlaybookStatus.DRY_RUN,
                execution_time_ms=0.0,
                actions_taken=[f"Isolate pod {namespace}/{pod_name} ({isolation_type})"],
                rollback_info={"policy_name": f"isolate-{pod_name}", "namespace": namespace}
            )

        try:
            # Write policy to temp file
            policy_file = Path(f"/tmp/netpol-{pod_name}.yaml")
            policy_file.write_text(policy)

            # Apply with kubectl
            result = subprocess.run(
                ["kubectl", "apply", "-f", str(policy_file)],
                capture_output=True,
                text=True,
                check=True,
                timeout=10
            )

            actions.append(f"Applied NetworkPolicy isolate-{pod_name}")
            actions.append(f"Isolation type: {isolation_type}")

            # Cleanup temp file
            policy_file.unlink()

            return PlaybookResult(
                playbook_name="isolate_host",
                status=PlaybookStatus.SUCCESS,
                execution_time_ms=0.0,
                actions_taken=actions,
                rollback_info={
                    "policy_name": f"isolate-{pod_name}",
                    "namespace": namespace,
                    "command": f"kubectl delete networkpolicy isolate-{pod_name} -n {namespace}"
                } if self.enable_rollback else None,
                metadata={"namespace": namespace, "pod": pod_name, "type": isolation_type}
            )

        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to apply NetworkPolicy: {e.stderr}")
        except FileNotFoundError:
            raise RuntimeError("kubectl not found")

    async def quarantine_file(
        self,
        file_path: str,
        quarantine_dir: str = "/var/quarantine"
    ) -> PlaybookResult:
        """
        Move suspicious file to isolated quarantine directory.

        Args:
            file_path: Path to suspicious file
            quarantine_dir: Quarantine directory (isolated mount)

        Returns:
            PlaybookResult with file moved
        """
        actions = []
        source_path = Path(file_path)

        # Validate file exists
        if not source_path.exists():
            raise ValueError(f"File does not exist: {file_path}")

        # Create quarantine directory
        quarantine_path = Path(quarantine_dir)
        quarantine_path.mkdir(parents=True, exist_ok=True)

        # Generate unique quarantine filename with timestamp
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        quarantine_file = quarantine_path / f"{timestamp}_{source_path.name}"

        if self.dry_run:
            logger.info(f"[DRY-RUN] Would quarantine {file_path} to {quarantine_file}")
            return PlaybookResult(
                playbook_name="quarantine_file",
                status=PlaybookStatus.DRY_RUN,
                execution_time_ms=0.0,
                actions_taken=[f"Quarantine {file_path}"],
                rollback_info={"original_path": file_path, "quarantine_path": str(quarantine_file)}
            )

        try:
            # Move file (atomic operation)
            shutil.move(str(source_path), str(quarantine_file))
            actions.append(f"Moved {file_path} to quarantine")

            # Set restrictive permissions
            quarantine_file.chmod(0o000)  # No permissions
            actions.append("Set permissions to 000 (no access)")

            # Log quarantine metadata
            metadata_file = quarantine_file.with_suffix(".json")
            metadata = {
                "original_path": file_path,
                "quarantined_at": timestamp,
                "file_size": quarantine_file.stat().st_size,
                "reason": "RTE detection"
            }

            import json
            metadata_file.write_text(json.dumps(metadata, indent=2))
            actions.append("Created quarantine metadata")

            return PlaybookResult(
                playbook_name="quarantine_file",
                status=PlaybookStatus.SUCCESS,
                execution_time_ms=0.0,
                actions_taken=actions,
                rollback_info={
                    "original_path": file_path,
                    "quarantine_path": str(quarantine_file),
                    "restore_command": f"mv {quarantine_file} {file_path}"
                } if self.enable_rollback else None,
                metadata={
                    "original_path": file_path,
                    "quarantine_path": str(quarantine_file),
                    "file_size": metadata["file_size"]
                }
            )

        except Exception as e:
            raise RuntimeError(f"Failed to quarantine file: {e}")

    async def redirect_honeypot(
        self,
        source_ip: str,
        honeypot_ip: str,
        honeypot_port: int,
        protocol: str = "tcp"
    ) -> PlaybookResult:
        """
        Redirect malicious traffic to honeypot using iptables DNAT.

        Args:
            source_ip: Attacker IP to redirect
            honeypot_ip: Honeypot destination IP
            honeypot_port: Honeypot port
            protocol: Protocol to redirect ("tcp", "udp")

        Returns:
            PlaybookResult with DNAT rule applied
        """
        actions = []

        # Build iptables DNAT rule
        rule = (
            f"-t nat -A PREROUTING -s {source_ip} -p {protocol} "
            f"-j DNAT --to-destination {honeypot_ip}:{honeypot_port}"
        )

        rollback_rule = (
            f"-t nat -D PREROUTING -s {source_ip} -p {protocol} "
            f"-j DNAT --to-destination {honeypot_ip}:{honeypot_port}"
        )

        cmd = ["iptables"] + rule.split()

        if self.dry_run:
            logger.info(f"[DRY-RUN] Would redirect {source_ip} to honeypot {honeypot_ip}:{honeypot_port}")
            return PlaybookResult(
                playbook_name="redirect_honeypot",
                status=PlaybookStatus.DRY_RUN,
                execution_time_ms=0.0,
                actions_taken=[f"Redirect {source_ip} to honeypot"],
                rollback_info={"commands": [rollback_rule]}
            )

        try:
            # Apply DNAT rule
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                timeout=5
            )

            actions.append(f"Redirected {source_ip} to honeypot {honeypot_ip}:{honeypot_port}")
            actions.append(f"Protocol: {protocol}")

            return PlaybookResult(
                playbook_name="redirect_honeypot",
                status=PlaybookStatus.SUCCESS,
                execution_time_ms=0.0,
                actions_taken=actions,
                rollback_info={"commands": [rollback_rule]} if self.enable_rollback else None,
                metadata={
                    "source_ip": source_ip,
                    "honeypot_ip": honeypot_ip,
                    "honeypot_port": honeypot_port,
                    "protocol": protocol
                }
            )

        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"iptables DNAT failed: {e.stderr}")
        except FileNotFoundError:
            raise RuntimeError("iptables not found")

    async def rollback(self, result: PlaybookResult) -> bool:
        """
        Rollback a previously executed playbook.

        Args:
            result: PlaybookResult from previous execution

        Returns:
            True if rollback succeeded, False otherwise
        """
        if not self.enable_rollback:
            logger.warning("Rollback disabled")
            return False

        if not result.rollback_info:
            logger.warning(f"No rollback info for {result.playbook_name}")
            return False

        logger.info(f"Rolling back playbook: {result.playbook_name}")

        try:
            if result.playbook_name == "block_ip":
                # Execute rollback commands
                for cmd_str in result.rollback_info.get("commands", []):
                    cmd = ["iptables"] + cmd_str.split()
                    subprocess.run(cmd, capture_output=True, check=True, timeout=5)
                return True

            elif result.playbook_name == "isolate_host":
                # Delete NetworkPolicy
                cmd = result.rollback_info.get("command", "")
                subprocess.run(cmd.split(), capture_output=True, check=True, timeout=10)
                return True

            elif result.playbook_name == "quarantine_file":
                # Restore file
                cmd = result.rollback_info.get("restore_command", "")
                subprocess.run(cmd.split(), capture_output=True, check=True, timeout=5)
                return True

            elif result.playbook_name == "redirect_honeypot":
                # Remove DNAT rule
                for cmd_str in result.rollback_info.get("commands", []):
                    cmd = ["iptables"] + cmd_str.split()
                    subprocess.run(cmd, capture_output=True, check=True, timeout=5)
                return True

            else:
                logger.warning(f"No rollback handler for {result.playbook_name}")
                return False

        except Exception as e:
            logger.error(f"Rollback failed: {e}")
            return False

    def get_execution_history(self) -> List[PlaybookResult]:
        """Get history of all playbook executions"""
        return self.execution_history.copy()

    def get_stats(self) -> Dict:
        """Get playbook execution statistics"""
        if not self.execution_history:
            return {"total_executions": 0}

        total = len(self.execution_history)
        success = sum(1 for r in self.execution_history if r.status == PlaybookStatus.SUCCESS)
        failed = sum(1 for r in self.execution_history if r.status == PlaybookStatus.FAILED)

        avg_time = sum(r.execution_time_ms for r in self.execution_history) / total

        by_playbook = {}
        for result in self.execution_history:
            name = result.playbook_name
            if name not in by_playbook:
                by_playbook[name] = {"count": 0, "success": 0, "failed": 0}
            by_playbook[name]["count"] += 1
            if result.status == PlaybookStatus.SUCCESS:
                by_playbook[name]["success"] += 1
            elif result.status == PlaybookStatus.FAILED:
                by_playbook[name]["failed"] += 1

        return {
            "total_executions": total,
            "success_count": success,
            "failed_count": failed,
            "success_rate": success / total if total > 0 else 0,
            "avg_execution_time_ms": avg_time,
            "by_playbook": by_playbook
        }


# Test
if __name__ == "__main__":
    import json

    logging.basicConfig(level=logging.INFO)

    print("\n" + "="*80)
    print("PLAYBOOKS REFLEXOS TEST")
    print("="*80 + "\n")

    async def run_tests():
        # Initialize executor in DRY-RUN mode (safe for testing)
        executor = PlaybookExecutor(dry_run=True, enable_rollback=True)

        test_cases = [
            {
                "name": "Block malicious IP",
                "playbook": "block_ip",
                "params": {
                    "ip_address": "192.168.1.100",
                    "protocol": "tcp",
                    "port": 22,
                    "duration_seconds": 300
                }
            },
            {
                "name": "Kill suspicious process",
                "playbook": "kill_process",
                "params": {
                    "pid": 1234,  # Fake PID for testing
                    "signal": "SIGTERM"
                }
            },
            {
                "name": "Isolate compromised pod",
                "playbook": "isolate_host",
                "params": {
                    "namespace": "production",
                    "pod_name": "web-server-abc123",
                    "isolation_type": "full"
                }
            },
            {
                "name": "Quarantine malware file",
                "playbook": "quarantine_file",
                "params": {
                    "file_path": "/tmp/malware.exe",
                    "quarantine_dir": "/var/quarantine"
                }
            },
            {
                "name": "Redirect to honeypot",
                "playbook": "redirect_honeypot",
                "params": {
                    "source_ip": "10.0.0.50",
                    "honeypot_ip": "10.0.99.1",
                    "honeypot_port": 8080,
                    "protocol": "tcp"
                }
            }
        ]

        print("Testing playbooks (DRY-RUN mode):\n")

        for test in test_cases:
            print(f"Test: {test['name']}")
            print(f"  Playbook: {test['playbook']}")
            print(f"  Params: {json.dumps(test['params'], indent=4)}")

            try:
                result = await executor.execute(test["playbook"], test["params"])

                print(f"  → Status: {result.status}")
                print(f"  → Execution time: {result.execution_time_ms:.2f}ms")
                print(f"  → Actions taken:")
                for action in result.actions_taken:
                    print(f"      - {action}")

                if result.rollback_info:
                    print(f"  → Rollback available: Yes")

                if result.error_message:
                    print(f"  → Error: {result.error_message}")

            except Exception as e:
                print(f"  → FAILED: {e}")

            print()

        # Stats
        print("="*80)
        print("PERFORMANCE STATISTICS")
        print("="*80)
        stats = executor.get_stats()
        print(f"Total executions: {stats['total_executions']}")
        print(f"Success rate: {stats['success_rate']*100:.1f}%")
        print(f"Average execution time: {stats['avg_execution_time_ms']:.2f}ms")
        print(f"\nBy playbook:")
        for name, data in stats['by_playbook'].items():
            print(f"  {name}: {data['count']} executions, {data['success']} success")

        print("\n" + "="*80)
        print("PLAYBOOKS TEST COMPLETE!")
        print("="*80 + "\n")

    # Run async tests
    asyncio.run(run_tests())
