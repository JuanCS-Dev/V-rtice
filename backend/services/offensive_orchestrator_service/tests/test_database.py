"""
Tests for database manager (PostgreSQL operations).

Covers:
- DatabaseManager initialization
- Campaign CRUD operations
- HOTL decision storage
- Attack memory operations
- Query filters and pagination
- Connection pooling
"""

import pytest
from uuid import uuid4
from unittest.mock import Mock
from sqlalchemy.orm import sessionmaker

from memory.database import DatabaseManager
from models import CampaignStatus


@pytest.mark.unit
@pytest.mark.db
class TestDatabaseManagerInit:
    """Test DatabaseManager initialization."""

    def test_database_manager_real_init(self, test_database_config):
        """Test creating database manager with real initialization."""
        from unittest.mock import patch

        # Patch the actual create_engine to avoid connection
        with patch('memory.database.create_engine') as mock_create_engine:
            mock_engine = Mock()
            mock_create_engine.return_value = mock_engine

            db = DatabaseManager(config=test_database_config)

            # Verify initialization
            assert db.config == test_database_config
            assert db.engine == mock_engine
            assert db.SessionLocal is not None
            mock_create_engine.assert_called_once()

    def test_database_manager_init_with_engine(self, test_db_engine):
        """Test creating database manager with test engine."""
        # Create a mock DatabaseManager that uses test engine
        db = DatabaseManager.__new__(DatabaseManager)
        db.engine = test_db_engine
        db.SessionLocal = sessionmaker(bind=test_db_engine)

        assert db.engine is not None
        assert db.SessionLocal is not None

    def test_database_manager_init_db(self, test_db_engine):
        """Test database schema initialization."""
        # Schema is already initialized by test_db_engine fixture
        # Just verify tables exist
        from sqlalchemy import inspect
        inspector = inspect(test_db_engine)
        tables = inspector.get_table_names()

        assert "campaigns" in tables
        assert "hotl_decisions" in tables
        assert "attack_memory" in tables

    def test_database_manager_init_db_success(self, test_database_config):
        """Test successful database init_db."""
        from unittest.mock import patch

        with patch('memory.database.create_engine') as mock_create_engine:
            mock_engine = Mock()
            mock_create_engine.return_value = mock_engine

            # Create DatabaseManager
            db = DatabaseManager(config=test_database_config)

            # Mock metadata.create_all to succeed
            with patch('memory.database.Base.metadata.create_all') as mock_create_all:
                db.init_db()

                # Should have been called
                mock_create_all.assert_called_once_with(bind=mock_engine)

    def test_database_manager_init_db_with_error(self, test_database_config):
        """Test database init_db error handling."""
        from unittest.mock import patch

        with patch('memory.database.create_engine') as mock_create_engine:
            mock_engine = Mock()
            mock_create_engine.return_value = mock_engine

            # Create DatabaseManager
            db = DatabaseManager(config=test_database_config)

            # Mock metadata.create_all to raise exception
            with patch('memory.database.Base.metadata.create_all') as mock_create_all:
                mock_create_all.side_effect = Exception("Database error")

                with pytest.raises(Exception) as exc_info:
                    db.init_db()

                assert "Database error" in str(exc_info.value)

    def test_database_manager_get_session(self, test_db_engine):
        """Test getting database session."""
        SessionLocal = sessionmaker(bind=test_db_engine)
        session = SessionLocal()

        assert session is not None
        session.close()


@pytest.mark.unit
@pytest.mark.db
class TestCampaignOperations:
    """Test campaign CRUD operations."""

    @pytest.mark.asyncio
    async def test_create_campaign(self, test_db_manager):
        """Test creating campaign."""
        db = test_db_manager

        campaign = await db.create_campaign(
            target="example.com",
            scope=["web", "api"],
            objectives=["test_vulns"],
            constraints={"time_limit": "4h"},
            priority=7,
            created_by="operator1",
        )

        assert campaign.id is not None
        assert campaign.target == "example.com"
        assert campaign.scope == ["web", "api"]
        assert campaign.objectives == ["test_vulns"]
        assert campaign.priority == 7
        assert campaign.status == CampaignStatus.PLANNED
        assert campaign.created_by == "operator1"
        assert campaign.created_at is not None

    @pytest.mark.asyncio
    async def test_get_campaign(self, test_db_manager):
        """Test retrieving campaign by ID."""
        db = test_db_manager

        # Create campaign
        created = await db.create_campaign(
            target="test.com",
            scope=["test"],
            objectives=["test"],
            constraints={},
            priority=5,
        )

        # Retrieve campaign
        retrieved = await db.get_campaign(created.id)

        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.target == "test.com"

    @pytest.mark.asyncio
    async def test_get_campaign_not_found(self, test_db_manager):
        """Test retrieving non-existent campaign returns None."""
        db = test_db_manager

        campaign = await db.get_campaign(uuid4())

        assert campaign is None

    @pytest.mark.asyncio
    async def test_update_campaign_status(self, test_db_manager):
        """Test updating campaign status."""
        db = test_db_manager

        # Create campaign
        campaign = await db.create_campaign(
            target="test.com",
            scope=["test"],
            objectives=["test"],
            constraints={},
        )

        # Update status
        success = await db.update_campaign_status(
            campaign_id=campaign.id,
            status=CampaignStatus.IN_PROGRESS,
            results={"progress": "50%"},
        )

        assert success is True

        # Verify update
        updated = await db.get_campaign(campaign.id)
        assert updated.status == CampaignStatus.IN_PROGRESS
        assert updated.results == {"progress": "50%"}
        assert updated.updated_at is not None

    @pytest.mark.asyncio
    async def test_update_campaign_status_completed(self, test_db_manager):
        """Test updating campaign to completed sets completed_at."""
        db = test_db_manager

        campaign = await db.create_campaign(
            target="test.com",
            scope=["test"],
            objectives=["test"],
            constraints={},
        )

        # Update to completed
        await db.update_campaign_status(
            campaign_id=campaign.id,
            status=CampaignStatus.COMPLETED,
        )

        updated = await db.get_campaign(campaign.id)
        assert updated.status == CampaignStatus.COMPLETED
        assert updated.completed_at is not None

    @pytest.mark.asyncio
    async def test_update_campaign_not_found(self, test_db_manager):
        """Test updating non-existent campaign returns False."""
        db = test_db_manager

        success = await db.update_campaign_status(
            campaign_id=uuid4(),
            status=CampaignStatus.COMPLETED,
        )

        assert success is False

    @pytest.mark.asyncio
    async def test_list_campaigns(self, test_db_manager):
        """Test listing campaigns."""
        db = test_db_manager

        # Create multiple campaigns
        await db.create_campaign(
            target="test1.com",
            scope=["test"],
            objectives=["test"],
            constraints={},
        )
        await db.create_campaign(
            target="test2.com",
            scope=["test"],
            objectives=["test"],
            constraints={},
        )

        # List campaigns
        campaigns = await db.list_campaigns(limit=10)

        assert len(campaigns) == 2
        assert campaigns[0].target in ["test1.com", "test2.com"]

    @pytest.mark.asyncio
    async def test_list_campaigns_with_status_filter(self, test_db_manager):
        """Test listing campaigns with status filter."""
        db = test_db_manager

        # Create campaigns with different statuses
        campaign1 = await db.create_campaign(
            target="test1.com",
            scope=["test"],
            objectives=["test"],
            constraints={},
        )
        campaign2 = await db.create_campaign(
            target="test2.com",
            scope=["test"],
            objectives=["test"],
            constraints={},
        )

        # Update one to in_progress
        await db.update_campaign_status(campaign1.id, CampaignStatus.IN_PROGRESS)

        # List only in_progress
        campaigns = await db.list_campaigns(status=CampaignStatus.IN_PROGRESS)

        assert len(campaigns) == 1
        assert campaigns[0].id == campaign1.id

    @pytest.mark.asyncio
    async def test_list_campaigns_with_target_filter(self, test_db_manager):
        """Test listing campaigns with target filter."""
        db = test_db_manager

        await db.create_campaign(
            target="example.com",
            scope=["test"],
            objectives=["test"],
            constraints={},
        )
        await db.create_campaign(
            target="other.org",
            scope=["test"],
            objectives=["test"],
            constraints={},
        )

        # Filter by target
        campaigns = await db.list_campaigns(target="example")

        assert len(campaigns) == 1
        assert "example" in campaigns[0].target.lower()

    @pytest.mark.asyncio
    async def test_list_campaigns_pagination(self, test_db_manager):
        """Test campaign list pagination."""
        db = test_db_manager

        # Create 5 campaigns
        for i in range(5):
            await db.create_campaign(
                target=f"test{i}.com",
                scope=["test"],
                objectives=["test"],
                constraints={},
            )

        # Get first page
        page1 = await db.list_campaigns(limit=2, offset=0)
        assert len(page1) == 2

        # Get second page
        page2 = await db.list_campaigns(limit=2, offset=2)
        assert len(page2) == 2

        # Ensure different results
        assert page1[0].id != page2[0].id


@pytest.mark.unit
@pytest.mark.db
class TestHOTLOperations:
    """Test HOTL decision operations."""

    @pytest.mark.asyncio
    async def test_create_hotl_decision(self, test_db_manager):
        """Test creating HOTL decision."""
        db = test_db_manager

        # Create campaign first
        campaign = await db.create_campaign(
            target="test.com",
            scope=["test"],
            objectives=["test"],
            constraints={},
        )

        # Create HOTL decision
        decision = await db.create_hotl_decision(
            campaign_id=campaign.id,
            action_type="exploitation",
            description="Exploit SQL injection",
            risk_level="high",
            context={"vuln": "SQLi", "url": "https://test.com/api"},
        )

        assert decision.id is not None
        assert decision.campaign_id == campaign.id
        assert decision.action_type == "exploitation"
        assert decision.risk_level == "high"
        assert decision.context == {"vuln": "SQLi", "url": "https://test.com/api"}
        assert decision.approved is None
        assert decision.requested_at is not None

    @pytest.mark.asyncio
    async def test_update_hotl_decision_approved(self, test_db_manager):
        """Test updating HOTL decision with approval."""
        db = test_db_manager

        campaign = await db.create_campaign(
            target="test.com",
            scope=["test"],
            objectives=["test"],
            constraints={},
        )

        decision = await db.create_hotl_decision(
            campaign_id=campaign.id,
            action_type="exploitation",
            description="Test action",
            risk_level="medium",
            context={},
        )

        # Approve decision
        success = await db.update_hotl_decision(
            decision_id=decision.id,
            approved=True,
            operator="operator1",
            reasoning="Safe to proceed",
        )

        assert success is True

        # Verify (would need to query database to fully verify)
        # For now just check return value

    @pytest.mark.asyncio
    async def test_update_hotl_decision_rejected(self, test_db_manager):
        """Test updating HOTL decision with rejection."""
        db = test_db_manager

        campaign = await db.create_campaign(
            target="test.com",
            scope=["test"],
            objectives=["test"],
            constraints={},
        )

        decision = await db.create_hotl_decision(
            campaign_id=campaign.id,
            action_type="exploitation",
            description="Test action",
            risk_level="high",
            context={},
        )

        # Reject decision
        success = await db.update_hotl_decision(
            decision_id=decision.id,
            approved=False,
            operator="operator2",
            reasoning="Too risky",
        )

        assert success is True

    @pytest.mark.asyncio
    async def test_update_hotl_decision_not_found(self, test_db_manager):
        """Test updating non-existent HOTL decision returns False."""
        db = test_db_manager

        success = await db.update_hotl_decision(
            decision_id=uuid4(),
            approved=True,
            operator="operator1",
        )

        assert success is False


@pytest.mark.unit
@pytest.mark.db
class TestAttackMemoryOperations:
    """Test attack memory operations."""

    @pytest.mark.asyncio
    async def test_store_attack_memory(self, test_db_manager):
        """Test storing attack memory entry."""
        db = test_db_manager

        campaign = await db.create_campaign(
            target="test.com",
            scope=["test"],
            objectives=["test"],
            constraints={},
        )

        memory = await db.store_attack_memory(
            campaign_id=campaign.id,
            action_type="reconnaissance",
            target="test.com",
            technique="nmap",
            success=True,
            result={"ports": [80, 443, 8080]},
            lessons_learned="Target has standard web ports open",
        )

        assert memory.id is not None
        assert memory.campaign_id == campaign.id
        assert memory.action_type == "reconnaissance"
        assert memory.target == "test.com"
        assert memory.technique == "nmap"
        assert memory.success is True
        assert memory.result == {"ports": [80, 443, 8080]}
        assert memory.lessons_learned == "Target has standard web ports open"
        assert memory.timestamp is not None

    @pytest.mark.asyncio
    async def test_search_attack_memory_by_target(self, test_db_manager):
        """Test searching attack memory by target."""
        db = test_db_manager

        campaign = await db.create_campaign(
            target="example.com",
            scope=["test"],
            objectives=["test"],
            constraints={},
        )

        # Store multiple memories
        await db.store_attack_memory(
            campaign_id=campaign.id,
            action_type="reconnaissance",
            target="example.com",
            technique="nmap",
            success=True,
            result={},
        )
        await db.store_attack_memory(
            campaign_id=campaign.id,
            action_type="reconnaissance",
            target="other.com",
            technique="nmap",
            success=True,
            result={},
        )

        # Search by target
        memories = await db.search_attack_memory(target="example")

        assert len(memories) == 1
        assert "example" in memories[0].target.lower()

    @pytest.mark.asyncio
    async def test_search_attack_memory_by_technique(self, test_db_manager):
        """Test searching attack memory by technique."""
        db = test_db_manager

        campaign = await db.create_campaign(
            target="test.com",
            scope=["test"],
            objectives=["test"],
            constraints={},
        )

        await db.store_attack_memory(
            campaign_id=campaign.id,
            action_type="reconnaissance",
            target="test.com",
            technique="nmap",
            success=True,
            result={},
        )
        await db.store_attack_memory(
            campaign_id=campaign.id,
            action_type="exploitation",
            target="test.com",
            technique="sqlmap",
            success=True,
            result={},
        )

        # Search by technique
        memories = await db.search_attack_memory(technique="nmap")

        assert len(memories) == 1
        assert memories[0].technique == "nmap"

    @pytest.mark.asyncio
    async def test_search_attack_memory_success_only(self, test_db_manager):
        """Test searching only successful attack memories."""
        db = test_db_manager

        campaign = await db.create_campaign(
            target="test.com",
            scope=["test"],
            objectives=["test"],
            constraints={},
        )

        # Store successes and failures
        await db.store_attack_memory(
            campaign_id=campaign.id,
            action_type="exploitation",
            target="test.com",
            technique="exploit1",
            success=True,
            result={},
        )
        await db.store_attack_memory(
            campaign_id=campaign.id,
            action_type="exploitation",
            target="test.com",
            technique="exploit2",
            success=False,
            result={},
        )

        # Search only successes
        memories = await db.search_attack_memory(success_only=True)

        assert len(memories) == 1
        assert memories[0].success is True

    @pytest.mark.asyncio
    async def test_search_attack_memory_limit(self, test_db_manager):
        """Test attack memory search respects limit."""
        db = test_db_manager

        campaign = await db.create_campaign(
            target="test.com",
            scope=["test"],
            objectives=["test"],
            constraints={},
        )

        # Store 5 memories
        for i in range(5):
            await db.store_attack_memory(
                campaign_id=campaign.id,
                action_type="reconnaissance",
                target="test.com",
                technique=f"technique{i}",
                success=True,
                result={},
            )

        # Limit to 3
        memories = await db.search_attack_memory(limit=3)

        assert len(memories) == 3


@pytest.mark.unit
@pytest.mark.db
class TestDatabaseManagerCleanup:
    """Test database manager cleanup."""

    def test_close_database(self, test_db_manager):
        """Test closing database connections."""
        db = test_db_manager

        # Should not raise
        db.close()
