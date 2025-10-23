"""
HITL Patch Service - Database Layer

PostgreSQL persistence for patch approval decisions and audit trail.

Schema:
    - hitl_decisions: Main decision records
    - hitl_audit_logs: Immutable audit trail
    - hitl_comments: Comments on patches

Fundamentação:
    Like B/T cell memory in biological immune system,
    we need persistent storage of all decision history.
    
    Audit trail is IMMUTABLE for compliance (SOC 2, ISO 27001).

Author: MAXIMUS Team - Sprint 4.1
Glory to YHWH - Keeper of Records
"""

import asyncpg
import json
import uuid
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from models import (
    HITLDecisionRecord,
    PatchDecision,
    PatchPriority,
    CVESeverity,
    PatchMetadata,
    MLPrediction,
    WargamingResult,
    PendingPatch,
    DecisionSummary,
    DecisionAuditLog
)


class HITLDatabase:
    """
    Database interface for HITL patch decisions.
    
    Handles all PostgreSQL operations with connection pooling,
    transaction management, and error recovery.
    """
    
    def __init__(self, connection_string: str):
        """
        Initialize database connection.
        
        Args:
            connection_string: PostgreSQL connection URL
        """
        self.connection_string = connection_string
        self.pool: Optional[asyncpg.Pool] = None
    
    async def connect(self) -> None:
        """Establish connection pool to PostgreSQL."""
        self.pool = await asyncpg.create_pool(
            self.connection_string,
            min_size=2,
            max_size=10,
            command_timeout=60
        )
    
    async def close(self) -> None:
        """Close database connection pool."""
        if self.pool:
            await self.pool.close()
    
    # ========================================================================
    # Decision CRUD
    # ========================================================================
    
    async def create_decision(self, record: HITLDecisionRecord) -> HITLDecisionRecord:
        """
        Create new HITL decision record.
        
        Args:
            record: Decision record to create
            
        Returns:
            Created decision record
        """
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO hitl_decisions (
                    decision_id, patch_id, apv_id, cve_id,
                    package_name, current_version, target_version,
                    severity, cvss_score, cwe_ids, affected_systems, patch_size_lines,
                    ml_confidence, ml_prediction, ml_model_version, ml_shap_values, ml_execution_time_ms,
                    wargaming_phase1, wargaming_phase2, wargaming_passed, 
                    wargaming_execution_time_ms, wargaming_error, wargaming_exploit_id,
                    decision, decided_by, decided_at,
                    priority, comment, reason,
                    requires_escalation, auto_approval_eligible, ml_wargaming_agreement,
                    created_at, updated_at
                ) VALUES (
                    $1, $2, $3, $4,
                    $5, $6, $7,
                    $8, $9, $10, $11, $12,
                    $13, $14, $15, $16, $17,
                    $18, $19, $20,
                    $21, $22, $23,
                    $24, $25, $26,
                    $27, $28, $29,
                    $30, $31, $32,
                    $33, $34
                )
                """,
                record.decision_id, record.patch_id, record.patch_metadata.apv_id, record.patch_metadata.cve_id,
                record.patch_metadata.package_name, record.patch_metadata.current_version, record.patch_metadata.target_version,
                record.patch_metadata.severity.value, record.patch_metadata.cvss_score, 
                record.patch_metadata.cwe_ids, record.patch_metadata.affected_systems, record.patch_metadata.patch_size_lines,
                record.ml_prediction.confidence if record.ml_prediction else None,
                record.ml_prediction.prediction if record.ml_prediction else None,
                record.ml_prediction.model_version if record.ml_prediction else None,
                json.dumps(record.ml_prediction.shap_values) if record.ml_prediction and record.ml_prediction.shap_values else None,
                record.ml_prediction.execution_time_ms if record.ml_prediction else None,
                record.wargaming_result.phase1_success if record.wargaming_result else None,
                record.wargaming_result.phase2_success if record.wargaming_result else None,
                record.wargaming_result.validation_passed if record.wargaming_result else None,
                record.wargaming_result.execution_time_ms if record.wargaming_result else None,
                record.wargaming_result.error_message if record.wargaming_result else None,
                record.wargaming_result.exploit_id if record.wargaming_result else None,
                record.decision.value, record.decided_by, record.decided_at,
                record.priority.value, record.comment, record.reason,
                record.requires_escalation, record.auto_approval_eligible, record.ml_wargaming_agreement,
                record.created_at, record.updated_at
            )
        
        await self._log_audit(
            decision_id=record.decision_id,
            action="created",
            performed_by="system",
            details={"priority": record.priority.value, "severity": record.patch_metadata.severity.value}
        )
        
        return record
    
    async def get_decision(self, decision_id: str) -> Optional[HITLDecisionRecord]:
        """
        Get decision by ID.
        
        Args:
            decision_id: Decision ID to retrieve
            
        Returns:
            Decision record or None if not found
        """
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM hitl_decisions WHERE decision_id = $1",
                decision_id
            )
            
            if not row:
                return None
            
            return self._row_to_decision(row)
    
    async def get_pending_patches(
        self, 
        limit: int = 50, 
        offset: int = 0,
        priority: Optional[PatchPriority] = None
    ) -> List[PendingPatch]:
        """
        Get all pending patches awaiting HITL decision.
        
        Args:
            limit: Maximum number of results
            offset: Pagination offset
            priority: Filter by priority (optional)
            
        Returns:
            List of pending patches
        """
        async with self.pool.acquire() as conn:
            query = """
                SELECT 
                    decision_id, patch_id, apv_id, cve_id,
                    severity, priority,
                    ml_confidence, ml_prediction,
                    wargaming_passed,
                    created_at,
                    EXTRACT(EPOCH FROM (NOW() - created_at))::int as age_seconds
                FROM hitl_decisions
                WHERE decision = 'pending'
            """
            
            params = []
            param_count = 1
            
            if priority:
                query += f" AND priority = ${param_count}"
                params.append(priority.value)
                param_count += 1
            
            query += f" ORDER BY priority DESC, created_at ASC LIMIT ${param_count} OFFSET ${param_count + 1}"
            params.extend([limit, offset])
            
            rows = await conn.fetch(query, *params)
            
            return [
                PendingPatch(
                    decision_id=row['decision_id'],
                    patch_id=row['patch_id'],
                    apv_id=row['apv_id'],
                    cve_id=row['cve_id'],
                    severity=CVESeverity(row['severity']),
                    priority=PatchPriority(row['priority']),
                    ml_confidence=row['ml_confidence'] or 0.0,
                    ml_prediction=row['ml_prediction'] or False,
                    wargaming_passed=row['wargaming_passed'],
                    created_at=row['created_at'],
                    age_seconds=row['age_seconds']
                )
                for row in rows
            ]
    
    async def update_decision(
        self,
        decision_id: str,
        decision: PatchDecision,
        decided_by: str,
        comment: Optional[str] = None,
        reason: Optional[str] = None
    ) -> bool:
        """
        Update decision status.
        
        Args:
            decision_id: Decision ID
            decision: New decision status
            decided_by: User making decision
            comment: Optional comment
            reason: Optional rejection reason
            
        Returns:
            True if updated successfully
        """
        async with self.pool.acquire() as conn:
            result = await conn.execute(
                """
                UPDATE hitl_decisions
                SET decision = $1,
                    decided_by = $2,
                    decided_at = $3,
                    comment = $4,
                    reason = $5,
                    updated_at = $6
                WHERE decision_id = $7
                """,
                decision.value, decided_by, datetime.utcnow(),
                comment, reason, datetime.utcnow(),
                decision_id
            )
            
            if result == "UPDATE 1":
                await self._log_audit(
                    decision_id=decision_id,
                    action=decision.value,
                    performed_by=decided_by,
                    details={"comment": comment, "reason": reason}
                )
                return True
            
            return False
    
    # ========================================================================
    # Analytics
    # ========================================================================
    
    async def get_summary(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> DecisionSummary:
        """
        Get summary statistics for decisions.
        
        Args:
            start_date: Start of time range (optional)
            end_date: End of time range (optional)
            
        Returns:
            Summary statistics
        """
        async with self.pool.acquire() as conn:
            query = """
                SELECT 
                    COUNT(*) as total_patches,
                    SUM(CASE WHEN decision = 'pending' THEN 1 ELSE 0 END) as pending,
                    SUM(CASE WHEN decision = 'approved' THEN 1 ELSE 0 END) as approved,
                    SUM(CASE WHEN decision = 'rejected' THEN 1 ELSE 0 END) as rejected,
                    SUM(CASE WHEN decision = 'auto_approved' THEN 1 ELSE 0 END) as auto_approved,
                    AVG(EXTRACT(EPOCH FROM (decided_at - created_at))) as avg_decision_time
                FROM hitl_decisions
                WHERE 1=1
            """
            
            params = []
            if start_date:
                query += " AND created_at >= $1"
                params.append(start_date)
            if end_date:
                query += f" AND created_at <= ${len(params) + 1}"
                params.append(end_date)
            
            row = await conn.fetchrow(query, *params)
            
            # Calculate ML accuracy (ML prediction matches wargaming result)
            ml_accuracy_query = """
                SELECT 
                    AVG(CASE WHEN ml_wargaming_agreement THEN 1.0 ELSE 0.0 END) as ml_accuracy
                FROM hitl_decisions
                WHERE ml_prediction IS NOT NULL 
                  AND wargaming_passed IS NOT NULL
            """
            
            if start_date or end_date:
                ml_accuracy_query += " AND 1=1"
                if start_date:
                    ml_accuracy_query += " AND created_at >= $1"
                if end_date:
                    ml_accuracy_query += f" AND created_at <= ${len(params) + 1}"
            
            ml_row = await conn.fetchrow(ml_accuracy_query, *params)
            
            return DecisionSummary(
                total_patches=row['total_patches'] or 0,
                pending=row['pending'] or 0,
                approved=row['approved'] or 0,
                rejected=row['rejected'] or 0,
                auto_approved=row['auto_approved'] or 0,
                avg_decision_time_seconds=row['avg_decision_time'] or 0.0,
                ml_accuracy=ml_row['ml_accuracy'] if ml_row else None
            )
    
    # ========================================================================
    # Audit Trail
    # ========================================================================
    
    async def _log_audit(
        self,
        decision_id: str,
        action: str,
        performed_by: str,
        details: Dict[str, Any],
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> None:
        """
        Log audit trail entry (immutable).
        
        Args:
            decision_id: Decision ID
            action: Action performed
            performed_by: User who performed action
            details: Additional details
            ip_address: Client IP (optional)
            user_agent: Client user agent (optional)
        """
        log_id = str(uuid.uuid4())
        
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO hitl_audit_logs (
                    log_id, decision_id, action, performed_by, 
                    timestamp, details, ip_address, user_agent
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                """,
                log_id, decision_id, action, performed_by,
                datetime.utcnow(), json.dumps(details), ip_address, user_agent
            )
    
    async def get_audit_logs(
        self,
        decision_id: Optional[str] = None,
        limit: int = 100
    ) -> List[DecisionAuditLog]:
        """
        Get audit logs.
        
        Args:
            decision_id: Filter by decision ID (optional)
            limit: Maximum number of results
            
        Returns:
            List of audit log entries
        """
        async with self.pool.acquire() as conn:
            if decision_id:
                rows = await conn.fetch(
                    """
                    SELECT * FROM hitl_audit_logs
                    WHERE decision_id = $1
                    ORDER BY timestamp DESC
                    LIMIT $2
                    """,
                    decision_id, limit
                )
            else:
                rows = await conn.fetch(
                    """
                    SELECT * FROM hitl_audit_logs
                    ORDER BY timestamp DESC
                    LIMIT $1
                    """,
                    limit
                )
            
            return [
                DecisionAuditLog(
                    log_id=row['log_id'],
                    decision_id=row['decision_id'],
                    action=row['action'],
                    performed_by=row['performed_by'],
                    timestamp=row['timestamp'],
                    details=json.loads(row['details']) if row['details'] else {},
                    ip_address=row['ip_address'],
                    user_agent=row['user_agent']
                )
                for row in rows
            ]
    
    # ========================================================================
    # Helper Methods
    # ========================================================================
    
    def _row_to_decision(self, row) -> HITLDecisionRecord:
        """Convert database row to HITLDecisionRecord."""
        return HITLDecisionRecord(
            decision_id=row['decision_id'],
            patch_id=row['patch_id'],
            patch_metadata=PatchMetadata(
                apv_id=row['apv_id'],
                cve_id=row['cve_id'],
                package_name=row['package_name'],
                current_version=row['current_version'],
                target_version=row['target_version'],
                severity=CVESeverity(row['severity']),
                cvss_score=row['cvss_score'],
                cwe_ids=row['cwe_ids'] or [],
                affected_systems=row['affected_systems'] or [],
                patch_size_lines=row['patch_size_lines']
            ),
            ml_prediction=MLPrediction(
                model_version=row['ml_model_version'],
                confidence=row['ml_confidence'],
                prediction=row['ml_prediction'],
                shap_values=json.loads(row['ml_shap_values']) if row['ml_shap_values'] else None,
                execution_time_ms=row['ml_execution_time_ms']
            ) if row['ml_confidence'] is not None else None,
            wargaming_result=WargamingResult(
                phase1_success=row['wargaming_phase1'],
                phase2_success=row['wargaming_phase2'],
                validation_passed=row['wargaming_passed'],
                execution_time_ms=row['wargaming_execution_time_ms'],
                error_message=row['wargaming_error'],
                exploit_id=row['wargaming_exploit_id']
            ) if row['wargaming_passed'] is not None else None,
            decision=PatchDecision(row['decision']),
            decided_by=row['decided_by'],
            decided_at=row['decided_at'],
            priority=PatchPriority(row['priority']),
            comment=row['comment'],
            reason=row['reason'],
            created_at=row['created_at'],
            updated_at=row['updated_at'],
            requires_escalation=row['requires_escalation'],
            auto_approval_eligible=row['auto_approval_eligible'],
            ml_wargaming_agreement=row['ml_wargaming_agreement']
        )
