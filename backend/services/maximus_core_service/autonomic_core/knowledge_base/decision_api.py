"""FastAPI endpoints for HCL Decision CRUD operations"""

import logging
from typing import Dict, List, Optional
from datetime import datetime
import asyncpg

logger = logging.getLogger(__name__)


class DecisionAPI:
    """API for HCL decision storage and retrieval."""

    def __init__(self, db_url: str = "postgresql://localhost/vertice"):
        self.db_url = db_url
        self.pool = None

    async def create_decision(self, decision: Dict) -> Dict:
        """Log a new HCL decision."""
        async with self.pool.acquire() as conn:
            result = await conn.fetchrow("""
                INSERT INTO hcl_decisions
                (trigger, operational_mode, actions_taken, state_before, state_after, outcome, reward_signal, human_feedback)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                RETURNING id, timestamp
            """,
                decision['trigger'],
                decision['operational_mode'],
                decision['actions_taken'],
                decision['state_before'],
                decision.get('state_after'),
                decision.get('outcome'),
                decision.get('reward_signal'),
                decision.get('human_feedback')
            )

            return {'id': str(result['id']), 'timestamp': result['timestamp'].isoformat()}

    async def get_decision(self, decision_id: str) -> Optional[Dict]:
        """Retrieve a specific decision."""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM hcl_decisions WHERE id = $1", decision_id
            )
            return dict(row) if row else None

    async def query_decisions(
        self,
        mode: str = None,
        outcome: str = None,
        limit: int = 100
    ) -> List[Dict]:
        """Query decisions with filters."""
        query = "SELECT * FROM hcl_decisions WHERE 1=1"
        params = []

        if mode:
            params.append(mode)
            query += f" AND operational_mode = ${len(params)}"
        if outcome:
            params.append(outcome)
            query += f" AND outcome = ${len(params)}"

        query += f" ORDER BY timestamp DESC LIMIT {limit}"

        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, *params)
            return [dict(row) for row in rows]
