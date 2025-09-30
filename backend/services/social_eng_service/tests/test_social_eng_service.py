import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from unittest.mock import patch

from social_eng_service import models, schemas

@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    assert "active_campaigns" in response.json()

@pytest.mark.asyncio
async def test_create_campaign(client: AsyncClient):
    campaign_data = {
        "name": "Test Campaign",
        "target_domain": "example.com",
        "email_template_name": "Office 365 Login Alert",
        "landing_page_template": "office365_login",
        "sender_name": "IT Support",
        "sender_email": "support@example.com",
        "tracking_enabled": True
    }
    response = await client.post("/campaigns", json=campaign_data)
    assert response.status_code == 201
    assert response.json()["message"] == "Phishing awareness campaign created successfully."
    assert "campaign" in response.json()
    assert response.json()["campaign"]["name"] == "Test Campaign"

@pytest.mark.asyncio
async def test_list_campaigns(client: AsyncClient, db_session: AsyncSession):
    # Create a campaign directly in the DB for listing
    campaign = models.Campaign(
        id="test_list_camp",
        name="List Campaign",
        target_domain="list.com",
        email_template_name="Office 365 Login Alert",
        landing_page_template="office365_login",
        sender_name="Admin",
        sender_email="admin@list.com",
    )
    db_session.add(campaign)
    await db_session.commit()

    response = await client.get("/campaigns")
    assert response.status_code == 200
    assert len(response.json()) >= 1
    assert any(c["name"] == "List Campaign" for c in response.json())

@pytest.mark.asyncio
async def test_get_campaign(client: AsyncClient, db_session: AsyncSession):
    campaign_id = "test_get_camp"
    campaign = models.Campaign(
        id=campaign_id,
        name="Get Campaign",
        target_domain="get.com",
        email_template_name="Office 365 Login Alert",
        landing_page_template="office365_login",
        sender_name="Admin",
        sender_email="admin@get.com",
    )
    db_session.add(campaign)
    await db_session.commit()

    response = await client.get(f"/campaigns/{campaign_id}")
    assert response.status_code == 200
    assert response.json()["name"] == "Get Campaign"

@pytest.mark.asyncio
async def test_delete_campaign(client: AsyncClient, db_session: AsyncSession):
    campaign_id = "test_del_camp"
    campaign = models.Campaign(
        id=campaign_id,
        name="Delete Campaign",
        target_domain="del.com",
        email_template_name="Office 365 Login Alert",
        landing_page_template="office365_login",
        sender_name="Admin",
        sender_email="admin@del.com",
    )
    db_session.add(campaign)
    await db_session.commit()

    response = await client.delete(f"/campaigns/{campaign_id}")
    assert response.status_code == 204

    # Verify it's deleted
    response = await client.get(f"/campaigns/{campaign_id}")
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_create_email_template(client: AsyncClient):
    template_data = {
        "name": "Custom Template",
        "subject": "Custom Subject",
        "body": "Custom Body {phishing_link}",
        "template_type": "phishing"
    }
    response = await client.post("/templates/email", json=template_data)
    assert response.status_code == 201
    assert response.json()["name"] == "Custom Template"

@pytest.mark.asyncio
async def test_list_email_templates(client: AsyncClient, db_session: AsyncSession):
    # Default templates are added on startup, so they should be present
    response = await client.get("/templates/email")
    assert response.status_code == 200
    assert len(response.json()) >= 3 # Default templates
    assert any(t["name"] == "Office 365 Login Alert" for t in response.json())

@pytest.mark.asyncio
async def test_send_campaign_emails(client: AsyncClient, db_session: AsyncSession):
    campaign_id = "test_send_camp"
    campaign = models.Campaign(
        id=campaign_id,
        name="Send Email Campaign",
        target_domain="send.com",
        email_template_name="Office 365 Login Alert", # Ensure this template exists
        landing_page_template="office365_login",
        sender_name="Admin",
        sender_email="admin@send.com",
    )
    db_session.add(campaign)
    
    # Ensure the default template exists for the campaign
    default_template = models.EmailTemplate(
        name="Office 365 Login Alert",
        subject="Default Subject",
        body="Default Body {phishing_link}",
        template_type="phishing"
    )
    db_session.add(default_template)
    await db_session.commit()

    targets_data = [
        {"email": "test1@example.com", "name": "Test User 1"},
        {"email": "test2@example.com", "name": "Test User 2"},
    ]
    response = await client.post(f"/campaigns/{campaign_id}/send", json=targets_data)
    assert response.status_code == 200
    assert response.json()["message"].startswith("Attempted to send")
    assert response.json()["emails_attempted"] == 2

    # Verify targets are in DB
    targets_in_db = (await db_session.execute(
        select(models.Target).filter_by(campaign_id=campaign_id)
    )).scalars().all()
    assert len(targets_in_db) == 2
    assert targets_in_db[0].email == "test1@example.com"

@pytest.mark.asyncio
async def test_serve_landing_page_and_track_interaction(client: AsyncClient, db_session: AsyncSession):
    campaign_id = "test_landing_camp"
    campaign = models.Campaign(
        id=campaign_id,
        name="Landing Page Campaign",
        target_domain="landing.com",
        email_template_name="Office 365 Login Alert",
        landing_page_template="office365_login",
        sender_name="Admin",
        sender_email="admin@landing.com",
    )
    db_session.add(campaign)
    await db_session.commit()

    # Simulate a target click
    tracking_id = "test_track_id"
    response = await client.get(f"/landing/{campaign_id}?t={tracking_id}")
    assert response.status_code == 200
    assert "Microsoft Office 365 - Sign In" in response.text

    # Verify interaction is tracked
    interaction = (await db_session.execute(
        select(models.Interaction).filter_by(campaign_id=campaign_id, tracking_id=tracking_id, action="page_visited")
    )).scalar_one_or_none()
    assert interaction is not None
    assert interaction.ip_address == "testclient"

@pytest.mark.asyncio
async def test_track_interaction_credentials_submitted(client: AsyncClient, db_session: AsyncSession):
    campaign_id = "test_track_cred_camp"
    campaign = models.Campaign(
        id=campaign_id,
        name="Track Creds Campaign",
        target_domain="creds.com",
        email_template_name="Office 365 Login Alert",
        landing_page_template="office365_login",
        sender_name="Admin",
        sender_email="admin@creds.com",
    )
    db_session.add(campaign)
    await db_session.commit()

    interaction_data = {
        "campaign_id": campaign_id,
        "action": "credentials_submitted",
        "tracking_id": "cred_track_id",
        "details": {"username": "test@creds.com"}
    }
    response = await client.post("/track-interaction", json=interaction_data)
    assert response.status_code == 202
    assert response.json()["status"] == "tracked"

    # Verify interaction is tracked
    interaction = (await db_session.execute(
        select(models.Interaction).filter_by(campaign_id=campaign_id, action="credentials_submitted")
    )).scalar_one_or_none()
    assert interaction is not None
    assert interaction.details["username"] == "test@creds.com"

@pytest.mark.asyncio
async def test_get_campaign_stats(client: AsyncClient, db_session: AsyncSession):
    campaign_id = "test_stats_camp"
    campaign = models.Campaign(
        id=campaign_id,
        name="Stats Campaign",
        target_domain="stats.com",
        email_template_name="Office 365 Login Alert",
        landing_page_template="office365_login",
        sender_name="Admin",
        sender_email="admin@stats.com",
    )
    db_session.add(campaign)

    # Add some targets
    target1 = models.Target(campaign_id=campaign_id, email="t1@s.com", name="T1", tracking_id="t1", phishing_link="link1")
    target2 = models.Target(campaign_id=campaign_id, email="t2@s.com", name="T2", tracking_id="t2", phishing_link="link2")
    db_session.add_all([target1, target2])

    # Add some interactions
    interaction1 = models.Interaction(campaign_id=campaign_id, tracking_id="t1", action="page_visited", ip_address="1.1.1.1")
    interaction2 = models.Interaction(campaign_id=campaign_id, tracking_id="t1", action="credentials_submitted", ip_address="1.1.1.1")
    interaction3 = models.Interaction(campaign_id=campaign_id, tracking_id="t2", action="page_visited", ip_address="2.2.2.2")
    interaction4 = models.Interaction(campaign_id=campaign_id, action="awareness_completed", ip_address="3.3.3.3")
    db_session.add_all([interaction1, interaction2, interaction3, interaction4])

    await db_session.commit()

    response = await client.get(f"/campaigns/{campaign_id}/stats")
    assert response.status_code == 200
    stats = response.json()["stats"]
    assert stats["emails_sent"] == 2
    assert stats["links_clicked"] == 2
    assert stats["credentials_submitted"] == 1
    assert stats["awareness_completed"] == 1
    assert stats["click_rate_percent"] == 100.0
    assert stats["submission_rate_percent"] == 50.0
    assert len(response.json()["recent_interactions"]) == 4 # All interactions added

@pytest.mark.asyncio
async def test_serve_awareness_training(client: AsyncClient, db_session: AsyncSession):
    campaign_id = "test_training_camp"
    campaign = models.Campaign(
        id=campaign_id,
        name="Training Campaign",
        target_domain="training.com",
        email_template_name="Office 365 Login Alert",
        landing_page_template="office365_login",
        sender_name="Admin",
        sender_email="admin@training.com",
    )
    db_session.add(campaign)
    await db_session.commit()

    response = await client.get(f"/training/{campaign_id}")
    assert response.status_code == 200
    assert "Security Awareness Training" in response.text
