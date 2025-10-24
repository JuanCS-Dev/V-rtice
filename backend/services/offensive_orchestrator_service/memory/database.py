"""
Database manager for PostgreSQL persistence.

Handles:
- Connection pooling
- Campaign CRUD operations
- HOTL decisions storage
- Attack memory entries
- Query optimization
"""

import logging
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime

from sqlalchemy import create_engine, select, and_
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool

from config import DatabaseConfig, get_config
from models import Base, CampaignDB, HOTLDecisionDB, AttackMemoryDB, CampaignStatus


logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    PostgreSQL database manager with connection pooling.

    Provides high-level operations for:
    - Campaigns
    - HOTL decisions
    - Attack memory
    """

    def __init__(self, config: Optional[DatabaseConfig] = None):
        """
        Initialize database manager.

        Args:
            config: Database configuration (defaults to global config)
        """
        self.config = config or get_config().database

        # Create engine with connection pooling
        self.engine = create_engine(
            self.config.connection_string,
            poolclass=QueuePool,
            pool_size=self.config.pool_size,
            max_overflow=20,
            pool_pre_ping=True,  # Verify connections before use
            echo=False,  # Set to True for SQL debugging
        )

        # Create session factory
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine,
        )

        logger.info(
            f"DatabaseManager initialized: host={self.config.host}, "
            f"db={self.config.database}, pool_size={self.config.pool_size}"
        )

    def init_db(self):
        """
        Initialize database schema.

        Creates all tables if they don't exist.
        Should be called on service startup.
        """
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("Database schema initialized")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}", exc_info=True)
            raise

    def get_session(self) -> Session:
        """
        Get database session.

        Returns:
            Session: SQLAlchemy session

        Usage:
            with db.get_session() as session:
                # Use session
                pass
        """
        return self.SessionLocal()

    # Campaign operations
    async def create_campaign(
        self,
        target: str,
        scope: List[str],
        objectives: List[str],
        constraints: Dict[str, Any],
        priority: int = 5,
        created_by: Optional[str] = None,
    ) -> CampaignDB:
        """
        Create new campaign.

        Args:
            target: Target identifier
            scope: Attack scope
            objectives: Campaign objectives
            constraints: Campaign constraints
            priority: Priority level (1-10)
            created_by: Creator identifier

        Returns:
            CampaignDB: Created campaign
        """
        campaign = CampaignDB(
            target=target,
            scope=scope,
            objectives=objectives,
            constraints=constraints,
            priority=priority,
            status=CampaignStatus.PLANNED,
            created_by=created_by,
        )

        with self.get_session() as session:
            session.add(campaign)
            session.commit()
            session.refresh(campaign)
            logger.info(f"Campaign created: {campaign.id}")
            return campaign

    async def get_campaign(self, campaign_id: UUID) -> Optional[CampaignDB]:
        """
        Get campaign by ID.

        Args:
            campaign_id: Campaign UUID

        Returns:
            CampaignDB or None if not found
        """
        with self.get_session() as session:
            stmt = select(CampaignDB).where(CampaignDB.id == campaign_id)
            campaign = session.execute(stmt).scalar_one_or_none()
            return campaign

    async def update_campaign_status(
        self,
        campaign_id: UUID,
        status: CampaignStatus,
        results: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Update campaign status.

        Args:
            campaign_id: Campaign UUID
            status: New status
            results: Optional results data

        Returns:
            bool: True if updated, False if not found
        """
        with self.get_session() as session:
            stmt = select(CampaignDB).where(CampaignDB.id == campaign_id)
            campaign = session.execute(stmt).scalar_one_or_none()

            if not campaign:
                return False

            campaign.status = status
            campaign.updated_at = datetime.utcnow()

            if results:
                campaign.results = results

            if status == CampaignStatus.COMPLETED or status == CampaignStatus.FAILED:
                campaign.completed_at = datetime.utcnow()

            session.commit()
            logger.info(f"Campaign {campaign_id} status updated: {status}")
            return True

    async def list_campaigns(
        self,
        status: Optional[CampaignStatus] = None,
        target: Optional[str] = None,
        limit: int = 10,
        offset: int = 0,
    ) -> List[CampaignDB]:
        """
        List campaigns with filters.

        Args:
            status: Optional status filter
            target: Optional target filter
            limit: Max results
            offset: Result offset

        Returns:
            List of campaigns
        """
        with self.get_session() as session:
            stmt = select(CampaignDB)

            # Apply filters
            filters = []
            if status:
                filters.append(CampaignDB.status == status)
            if target:
                filters.append(CampaignDB.target.ilike(f"%{target}%"))

            if filters:
                stmt = stmt.where(and_(*filters))

            # Order by creation time (newest first)
            stmt = stmt.order_by(CampaignDB.created_at.desc())

            # Pagination
            stmt = stmt.limit(limit).offset(offset)

            campaigns = session.execute(stmt).scalars().all()
            return list(campaigns)

    # HOTL operations
    async def create_hotl_decision(
        self,
        campaign_id: UUID,
        action_type: str,
        description: str,
        risk_level: str,
        context: Dict[str, Any],
    ) -> HOTLDecisionDB:
        """
        Create HOTL decision record.

        Args:
            campaign_id: Campaign UUID
            action_type: Action type
            description: Human-readable description
            risk_level: Risk level
            context: Additional context

        Returns:
            HOTLDecisionDB: Created decision
        """
        decision = HOTLDecisionDB(
            campaign_id=campaign_id,
            action_type=action_type,
            description=description,
            risk_level=risk_level,
            context=context,
        )

        with self.get_session() as session:
            session.add(decision)
            session.commit()
            session.refresh(decision)
            logger.info(f"HOTL decision created: {decision.id}")
            return decision

    async def update_hotl_decision(
        self,
        decision_id: UUID,
        approved: bool,
        operator: str,
        reasoning: Optional[str] = None,
    ) -> bool:
        """
        Update HOTL decision with approval.

        Args:
            decision_id: Decision UUID
            approved: Approval status
            operator: Operator identifier
            reasoning: Optional reasoning

        Returns:
            bool: True if updated
        """
        with self.get_session() as session:
            stmt = select(HOTLDecisionDB).where(HOTLDecisionDB.id == decision_id)
            decision = session.execute(stmt).scalar_one_or_none()

            if not decision:
                return False

            decision.approved = approved
            decision.operator = operator
            decision.reasoning = reasoning
            decision.status = "approved" if approved else "rejected"
            decision.resolved_at = datetime.utcnow()

            session.commit()
            logger.info(f"HOTL decision {decision_id} updated: approved={approved}")
            return True

    # Attack Memory operations
    async def store_attack_memory(
        self,
        campaign_id: UUID,
        action_type: str,
        target: str,
        technique: str,
        success: bool,
        result: Dict[str, Any],
        lessons_learned: Optional[str] = None,
        vector_id: Optional[str] = None,
    ) -> AttackMemoryDB:
        """
        Store attack memory entry.

        Args:
            campaign_id: Campaign UUID
            action_type: Action type
            target: Target identifier
            technique: Technique used
            success: Whether action succeeded
            result: Result data
            lessons_learned: Optional lessons
            vector_id: Optional Qdrant vector ID

        Returns:
            AttackMemoryDB: Created memory entry
        """
        memory = AttackMemoryDB(
            campaign_id=campaign_id,
            action_type=action_type,
            target=target,
            technique=technique,
            success=success,
            result=result,
            lessons_learned=lessons_learned,
            vector_id=vector_id,
        )

        with self.get_session() as session:
            session.add(memory)
            session.commit()
            session.refresh(memory)
            logger.info(f"Attack memory stored: {memory.id}")
            return memory

    async def search_attack_memory(
        self,
        target: Optional[str] = None,
        technique: Optional[str] = None,
        success_only: bool = False,
        limit: int = 10,
    ) -> List[AttackMemoryDB]:
        """
        Search attack memory.

        Args:
            target: Optional target filter
            technique: Optional technique filter
            success_only: Only successful attacks
            limit: Max results

        Returns:
            List of memory entries
        """
        with self.get_session() as session:
            stmt = select(AttackMemoryDB)

            filters = []
            if target:
                filters.append(AttackMemoryDB.target.ilike(f"%{target}%"))
            if technique:
                filters.append(AttackMemoryDB.technique.ilike(f"%{technique}%"))
            if success_only:
                filters.append(AttackMemoryDB.success == True)

            if filters:
                stmt = stmt.where(and_(*filters))

            stmt = stmt.order_by(AttackMemoryDB.timestamp.desc()).limit(limit)

            memories = session.execute(stmt).scalars().all()
            return list(memories)

    def close(self):
        """Close database connections."""
        self.engine.dispose()
        logger.info("Database connections closed")
