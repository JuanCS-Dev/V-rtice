"""
Database layer for Reactive Fabric Core Service
PostgreSQL with asyncpg connection pool

Sprint 1: Real implementation
"""

import asyncpg
import structlog
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from uuid import UUID
import os

from .models import (
    Honeypot, HoneypotCreate, HoneypotStats, HoneypotStatus,
    Attack, AttackCreate, AttackSummary,
    TTP, TTPCreate, TTPFrequency,
    IOC, IOCCreate,
    ForensicCapture, ForensicCaptureCreate, ProcessingStatus
)

logger = structlog.get_logger()


class Database:
    """PostgreSQL database manager with connection pool."""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.pool: Optional[asyncpg.Pool] = None
    
    def _ensure_pool(self) -> asyncpg.Pool:
        """Ensure pool is initialized, raise if not."""
        if self.pool is None:
            raise RuntimeError("Database pool not initialized. Call connect() first.")
        return self.pool
    
    async def connect(self) -> None:
        """Initialize connection pool."""
        try:
            self.pool = await asyncpg.create_pool(
                self.database_url,
                min_size=2,
                max_size=10,
                command_timeout=60
            )
            logger.info("database_pool_created", min_size=2, max_size=10)
            
            # Test connection
            if self.pool:
                async with self._ensure_pool().acquire() as conn:
                    version = await conn.fetchval("SELECT version()")
                    logger.info("database_connected", postgres_version=version[:50])
        except Exception as e:
            logger.error("database_connection_failed", error=str(e))
            raise
    
    async def disconnect(self) -> None:
        """Close connection pool."""
        if self.pool:
            await self.pool.close()
            logger.info("database_pool_closed")
    
    async def health_check(self) -> bool:
        """Check database connectivity."""
        if not self.pool:
            return False
        
        try:
            async with self._ensure_pool().acquire() as conn:
                await conn.fetchval("SELECT 1")
            return True
        except Exception as e:
            logger.error("database_health_check_failed", error=str(e))
            return False
    
    # ========================================================================
    # HONEYPOT QUERIES
    # ========================================================================
    
    async def get_honeypot_by_id(self, honeypot_id: str) -> Optional[Honeypot]:
        """Get honeypot by honeypot_id string."""
        query = """
            SELECT id, honeypot_id, type, container_name, port, status,
                   config, created_at, updated_at, last_health_check, metadata
            FROM reactive_fabric.honeypots
            WHERE honeypot_id = $1
        """
        
        async with self._ensure_pool().acquire() as conn:
            row = await conn.fetchrow(query, honeypot_id)
            if row:
                return Honeypot(**dict(row))
            return None
    
    async def list_honeypots(self) -> List[Honeypot]:
        """List all honeypots."""
        query = """
            SELECT id, honeypot_id, type, container_name, port, status,
                   config, created_at, updated_at, last_health_check, metadata
            FROM reactive_fabric.honeypots
            ORDER BY created_at ASC
        """
        
        async with self._ensure_pool().acquire() as conn:
            rows = await conn.fetch(query)
            return [Honeypot(**dict(row)) for row in rows]
    
    async def get_honeypot_stats(self) -> List[HoneypotStats]:
        """Get statistics for all honeypots."""
        query = """
            SELECT honeypot_id, type, status, total_attacks, unique_ips,
                   last_attack, critical_attacks, high_attacks
            FROM reactive_fabric.honeypot_stats
            ORDER BY total_attacks DESC
        """
        
        async with self._ensure_pool().acquire() as conn:
            rows = await conn.fetch(query)
            return [HoneypotStats(**dict(row)) for row in rows]
    
    async def update_honeypot_status(
        self, 
        honeypot_id: str, 
        status: HoneypotStatus,
        last_health_check: Optional[datetime] = None
    ) -> bool:
        """Update honeypot status."""
        query = """
            UPDATE reactive_fabric.honeypots
            SET status = $2, last_health_check = $3, updated_at = NOW()
            WHERE honeypot_id = $1
            RETURNING id
        """
        
        if last_health_check is None:
            last_health_check = datetime.utcnow()
        
        async with self._ensure_pool().acquire() as conn:
            result = await conn.fetchval(query, honeypot_id, status.value, last_health_check)
            return result is not None
    
    async def create_honeypot(self, honeypot: HoneypotCreate) -> Optional[Honeypot]:
        """Create a new honeypot."""
        query = """
            INSERT INTO reactive_fabric.honeypots 
            (honeypot_id, type, container_name, port, config, status)
            VALUES ($1, $2, $3, $4, $5, 'offline')
            RETURNING id, honeypot_id, type, container_name, port, status,
                      config, created_at, updated_at, last_health_check, metadata
        """
        
        async with self._ensure_pool().acquire() as conn:
            try:
                row = await conn.fetchrow(
                    query,
                    honeypot.honeypot_id,
                    honeypot.type.value,
                    honeypot.container_name,
                    honeypot.port,
                    honeypot.config
                )
                if row:
                    return Honeypot(**dict(row))
            except asyncpg.UniqueViolationError:
                logger.warning("honeypot_already_exists", honeypot_id=honeypot.honeypot_id)
            return None
    
    # ========================================================================
    # ATTACK QUERIES
    # ========================================================================
    
    async def create_attack(self, attack: AttackCreate) -> Optional[Attack]:
        """Create a new attack record."""
        query = """
            INSERT INTO reactive_fabric.attacks
            (honeypot_id, attacker_ip, attack_type, severity, confidence, 
             ttps, iocs, payload, captured_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            RETURNING id, honeypot_id, attacker_ip, attack_type, severity,
                      confidence, ttps, iocs, payload, captured_at, processed_at, metadata
        """
        
        async with self._ensure_pool().acquire() as conn:
            row = await conn.fetchrow(
                query,
                attack.honeypot_id,
                attack.attacker_ip,
                attack.attack_type,
                attack.severity.value,
                attack.confidence,
                attack.ttps,
                attack.iocs,
                attack.payload,
                attack.captured_at
            )
            if row:
                return Attack(**dict(row))
            return None
    
    async def get_recent_attacks(self, limit: int = 50, offset: int = 0) -> List[AttackSummary]:
        """Get recent attacks with honeypot_id as string."""
        query = """
            SELECT a.id, h.honeypot_id, a.attacker_ip, a.attack_type, 
                   a.severity, a.ttps, a.captured_at
            FROM reactive_fabric.attacks a
            JOIN reactive_fabric.honeypots h ON a.honeypot_id = h.id
            ORDER BY a.captured_at DESC
            LIMIT $1 OFFSET $2
        """
        
        async with self._ensure_pool().acquire() as conn:
            rows = await conn.fetch(query, limit, offset)
            return [AttackSummary(**dict(row)) for row in rows]
    
    async def count_attacks(self) -> int:
        """Count total attacks."""
        query = "SELECT COUNT(*) FROM reactive_fabric.attacks"
        
        async with self._ensure_pool().acquire() as conn:
            result = await conn.fetchval(query)
            return int(result) if result is not None else 0
    
    async def get_attacks_by_honeypot(
        self, 
        honeypot_id: str, 
        limit: int = 50
    ) -> List[AttackSummary]:
        """Get attacks for a specific honeypot."""
        query = """
            SELECT a.id, h.honeypot_id, a.attacker_ip, a.attack_type,
                   a.severity, a.ttps, a.captured_at
            FROM reactive_fabric.attacks a
            JOIN reactive_fabric.honeypots h ON a.honeypot_id = h.id
            WHERE h.honeypot_id = $1
            ORDER BY a.captured_at DESC
            LIMIT $2
        """
        
        async with self._ensure_pool().acquire() as conn:
            rows = await conn.fetch(query, honeypot_id, limit)
            return [AttackSummary(**dict(row)) for row in rows]
    
    async def get_attacks_today(self, honeypot_id: Optional[str] = None) -> int:
        """Count attacks captured today."""
        if honeypot_id:
            query = """
                SELECT COUNT(*)
                FROM reactive_fabric.attacks a
                JOIN reactive_fabric.honeypots h ON a.honeypot_id = h.id
                WHERE h.honeypot_id = $1
                  AND a.captured_at >= CURRENT_DATE
            """
            async with self._ensure_pool().acquire() as conn:
                result = await conn.fetchval(query, honeypot_id)
                return int(result) if result is not None else 0
        else:
            query = """
                SELECT COUNT(*)
                FROM reactive_fabric.attacks
                WHERE captured_at >= CURRENT_DATE
            """
            async with self._ensure_pool().acquire() as conn:
                result = await conn.fetchval(query)
                return int(result) if result is not None else 0
    
    # ========================================================================
    # TTP QUERIES
    # ========================================================================
    
    async def get_top_ttps(self, limit: int = 10) -> List[TTPFrequency]:
        """Get most frequently observed TTPs."""
        query = """
            SELECT technique_id, technique_name, tactic, observed_count,
                   last_observed, affected_honeypots
            FROM reactive_fabric.ttp_frequency
            ORDER BY observed_count DESC
            LIMIT $1
        """
        
        async with self._ensure_pool().acquire() as conn:
            rows = await conn.fetch(query, limit)
            return [TTPFrequency(**dict(row)) for row in rows]
    
    async def get_ttp_by_id(self, technique_id: str) -> Optional[TTP]:
        """Get TTP by technique ID."""
        query = """
            SELECT id, technique_id, technique_name, tactic, description,
                   observed_count, first_observed, last_observed, metadata
            FROM reactive_fabric.ttps
            WHERE technique_id = $1
        """
        
        async with self._ensure_pool().acquire() as conn:
            row = await conn.fetchrow(query, technique_id)
            if row:
                return TTP(**dict(row))
            return None
    
    async def create_ttp(self, ttp: TTPCreate) -> Optional[TTP]:
        """Create a new TTP record (usually auto-created by trigger)."""
        query = """
            INSERT INTO reactive_fabric.ttps
            (technique_id, technique_name, tactic, description)
            VALUES ($1, $2, $3, $4)
            RETURNING id, technique_id, technique_name, tactic, description,
                      observed_count, first_observed, last_observed, metadata
        """
        
        async with self._ensure_pool().acquire() as conn:
            try:
                row = await conn.fetchrow(
                    query,
                    ttp.technique_id,
                    ttp.technique_name,
                    ttp.tactic,
                    ttp.description
                )
                if row:
                    return TTP(**dict(row))
            except asyncpg.UniqueViolationError:
                logger.debug("ttp_already_exists", technique_id=ttp.technique_id)
            return None
    
    # ========================================================================
    # IOC QUERIES
    # ========================================================================
    
    async def create_or_update_ioc(
        self, 
        ioc_type: str, 
        ioc_value: str,
        threat_level: str = "unknown",
        attack_id: Optional[UUID] = None
    ) -> Optional[IOC]:
        """Create or update an IoC."""
        query = """
            INSERT INTO reactive_fabric.iocs
            (ioc_type, ioc_value, threat_level, first_seen, last_seen, occurrences, associated_attacks)
            VALUES ($1, $2, $3, NOW(), NOW(), 1, $4)
            ON CONFLICT (ioc_type, ioc_value) DO UPDATE SET
                last_seen = NOW(),
                occurrences = iocs.occurrences + 1,
                associated_attacks = array_append(iocs.associated_attacks, $4)
            RETURNING id, ioc_type, ioc_value, threat_level, first_seen, last_seen,
                      occurrences, associated_attacks, metadata
        """
        
        attack_ids = [attack_id] if attack_id else []
        
        async with self._ensure_pool().acquire() as conn:
            row = await conn.fetchrow(query, ioc_type, ioc_value, threat_level, attack_ids)
            if row:
                return IOC(**dict(row))
            return None
    
    # ========================================================================
    # FORENSIC CAPTURE QUERIES
    # ========================================================================
    
    async def create_forensic_capture(
        self, 
        capture: ForensicCaptureCreate
    ) -> Optional[ForensicCapture]:
        """Create a forensic capture record."""
        query = """
            INSERT INTO reactive_fabric.forensic_captures
            (honeypot_id, filename, file_path, file_type, file_size_bytes,
             file_hash, captured_at, processing_status)
            VALUES ($1, $2, $3, $4, $5, $6, $7, 'pending')
            RETURNING id, honeypot_id, filename, file_path, file_type, file_size_bytes,
                      file_hash, captured_at, processed_at, processing_status,
                      attacks_extracted, ttps_extracted, error_message, metadata
        """
        
        async with self._ensure_pool().acquire() as conn:
            row = await conn.fetchrow(
                query,
                capture.honeypot_id,
                capture.filename,
                capture.file_path,
                capture.file_type,
                capture.file_size_bytes,
                capture.file_hash,
                capture.captured_at
            )
            if row:
                return ForensicCapture(**dict(row))
            return None
    
    async def get_pending_captures(self, limit: int = 10) -> List[ForensicCapture]:
        """Get pending forensic captures for processing."""
        query = """
            SELECT id, honeypot_id, filename, file_path, file_type, file_size_bytes,
                   file_hash, captured_at, processed_at, processing_status,
                   attacks_extracted, ttps_extracted, error_message, metadata
            FROM reactive_fabric.forensic_captures
            WHERE processing_status = 'pending'
            ORDER BY captured_at ASC
            LIMIT $1
        """
        
        async with self._ensure_pool().acquire() as conn:
            rows = await conn.fetch(query, limit)
            return [ForensicCapture(**dict(row)) for row in rows]
    
    async def update_capture_status(
        self,
        capture_id: UUID,
        status: ProcessingStatus,
        attacks_extracted: int = 0,
        ttps_extracted: int = 0,
        error_message: Optional[str] = None
    ) -> bool:
        """Update forensic capture processing status."""
        query = """
            UPDATE reactive_fabric.forensic_captures
            SET processing_status = $2,
                processed_at = NOW(),
                attacks_extracted = $3,
                ttps_extracted = $4,
                error_message = $5
            WHERE id = $1
            RETURNING id
        """
        
        async with self._ensure_pool().acquire() as conn:
            result = await conn.fetchval(
                query, 
                capture_id, 
                status.value, 
                attacks_extracted, 
                ttps_extracted, 
                error_message
            )
            return result is not None
    
    # ========================================================================
    # METRICS QUERIES
    # ========================================================================
    
    async def get_unique_ips_today(self, honeypot_id: Optional[str] = None) -> int:
        """Count unique attacker IPs today."""
        if honeypot_id:
            query = """
                SELECT COUNT(DISTINCT a.attacker_ip)
                FROM reactive_fabric.attacks a
                JOIN reactive_fabric.honeypots h ON a.honeypot_id = h.id
                WHERE h.honeypot_id = $1
                  AND a.captured_at >= CURRENT_DATE
            """
            async with self._ensure_pool().acquire() as conn:
                result = await conn.fetchval(query, honeypot_id)
                return int(result) if result is not None else 0
        else:
            query = """
                SELECT COUNT(DISTINCT attacker_ip)
                FROM reactive_fabric.attacks
                WHERE captured_at >= CURRENT_DATE
            """
            async with self._ensure_pool().acquire() as conn:
                result = await conn.fetchval(query)
                return int(result) if result is not None else 0
