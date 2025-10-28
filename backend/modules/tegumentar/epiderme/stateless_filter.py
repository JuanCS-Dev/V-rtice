"""Stateless filtering logic backed by nftables."""

from __future__ import annotations

import ipaddress
import logging
import subprocess
from pathlib import Path
from typing import Iterable, List, Sequence

from ..config import TegumentarSettings

logger = logging.getLogger(__name__)


class StatelessFilterError(RuntimeError):
    """Raised when nftables commands fail."""


class StatelessFilter:
    """Manages nftables table/chain used by the epiderme layer."""

    def __init__(self, settings: TegumentarSettings):
        self._settings = settings

    @property
    def _table_spec(self) -> Sequence[str]:
        return ["inet", self._settings.nft_table_name]

    def ensure_table_structure(self) -> None:
        """Ensure the nftables table/chain/set exist with the correct rules."""

        if not Path(self._settings.nft_binary).exists():
            raise StatelessFilterError(
                f"nft binary not found at {self._settings.nft_binary}. "
                "The epiderme layer requires nftables."
            )

        table_family, table_name = self._table_spec
        chain_name = self._settings.nft_chain_name
        set_name = f"{chain_name}_blocked_ips"

        logger.debug("Ensuring nftables table %s %s", table_family, table_name)
        self._run_nft(["list", "table", table_family, table_name], check=False)
        self._run_nft(
            [
                "-f",
                "-",
            ],
            input_=f"add table {table_family} {table_name}\n",
            check=False,
        )

        logger.debug("Creating base chain %s", chain_name)
        self._run_nft(
            ["add", "chain", table_family, table_name, chain_name],
            check=False,
        )

        logger.debug("Ensuring verdict rules exist")
        base_rules = [
            f"flush chain {table_family} {table_name} {chain_name}",
            f"add set {table_family} {table_name} {set_name} {{ type ipv4_addr; flags interval; }}",
            f"add rule {table_family} {table_name} {chain_name} ip saddr @%s drop" % set_name,
        ]

        self._run_nft(["-f", "-"], input_="\n".join(base_rules) + "\n", check=False)

    def sync_blocked_ips(self, ips: Iterable[str]) -> None:
        """Replace the blocked IP set with the given list."""

        validated_ipv4: List[str] = []
        validated_ipv6: List[str] = []
        for ip in ips:
            try:
                network = ipaddress.ip_network(ip, strict=False)
                if network.version == 4:
                    validated_ipv4.append(ip)
                else:
                    validated_ipv6.append(ip)
            except ValueError:
                logger.warning("Skipping invalid IP/CIDR %s", ip)
                continue

        chain_name = self._settings.nft_chain_name
        set_name = f"{chain_name}_blocked_ips"
        table_family, table_name = self._table_spec

        if not validated_ipv4 and not validated_ipv6:
            logger.info("Clearing nftables blocked IP set")
            self._run_nft(
                ["flush", "set", table_family, table_name, set_name],
                check=False,
            )
            return

        # Only update IPv4 for now (IPv6 requires separate set configuration)
        elements = ", ".join(validated_ipv4)
        logger.debug("Updating blocked IP set with %d IPv4 entries (skipping %d IPv6)",
                     len(validated_ipv4), len(validated_ipv6))
        nft_input = (
            f"flush set {table_family} {table_name} {set_name}\n"
            f"add element {table_family} {table_name} {set_name} {{ {elements} }}\n"
        )
        self._run_nft(["-f", "-"], input_=nft_input)

    def attach_to_hook(self, priority: int = -100) -> None:
        """Attach the chain to the netfilter hook if not already attached."""

        table_family, table_name = self._table_spec
        chain_name = self._settings.nft_chain_name

        # Delete and recreate to ensure idempotency (handles CrashLoopBackOff state)
        hook_rule = (
            f"delete chain {table_family} {table_name} {chain_name}\n"
            f"add chain {table_family} {table_name} {chain_name} "
            f"{{ type filter hook prerouting priority {priority}; policy accept; }}\n"
            f"add rule {table_family} {table_name} {chain_name} ip saddr @{chain_name}_blocked_ips drop\n"
        )

        self._run_nft(["-f", "-"], input_=hook_rule, check=False)
        logger.info(
            "Epiderme chain %s attached to prerouting hook with priority %d",
            chain_name,
            priority,
        )

    def set_policy(self, policy: str) -> None:
        """Set the default policy for the epiderme chain."""

        if policy not in {"accept", "drop"}:
            raise ValueError("Policy must be 'accept' or 'drop'")
        table_family, table_name = self._table_spec
        chain_name = self._settings.nft_chain_name
        statement = (
            f"delete chain {table_family} {table_name} {chain_name}\n"
            f"add chain {table_family} {table_name} {chain_name} "
            f"{{ type filter hook prerouting priority -100; policy {policy}; }}\n"
            f"add rule {table_family} {table_name} {chain_name} ip saddr @{chain_name}_blocked_ips drop\n"
        )
        self._run_nft(["-f", "-"], input_=statement)
        logger.info("Updated epiderme policy to %s", policy.upper())

    def _run_nft(self, args: Sequence[str], input_: str | None = None, check: bool = True) -> subprocess.CompletedProcess:
        """Run nft command with consistent error handling."""

        command = [self._settings.nft_binary, *args]
        logger.debug("Executing nft command: %s", " ".join(command))
        try:
            proc = subprocess.run(
                command,
                input=input_.encode() if input_ else None,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=check,
            )
        except subprocess.CalledProcessError as exc:
            raise StatelessFilterError(
                f"nft command failed ({' '.join(command)}): {exc.stderr.decode().strip()}"
            ) from exc

        if proc.returncode != 0 and check:
            stderr = proc.stderr.decode().strip()
            raise StatelessFilterError(
                f"nft command {' '.join(command)} failed with rc={proc.returncode}: {stderr}"
            )

        if proc.stderr:
            logger.debug("nft stderr: %s", proc.stderr.decode().strip())
        return proc


__all__ = ["StatelessFilter", "StatelessFilterError"]
