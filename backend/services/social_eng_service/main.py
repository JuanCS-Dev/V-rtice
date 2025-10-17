"""Maximus Social Engineering Service - Main Application Entry Point.

This module serves as the main entry point for the Maximus Social Engineering
Service. It initializes and configures the FastAPI application, sets up event
handlers for startup and shutdown, and defines the API endpoints for simulating
and analyzing social engineering attack vectors.

It orchestrates the generation of realistic social engineering scenarios,
simulates human responses, and tracks campaign progress and effectiveness.
This service is crucial for assessing human vulnerabilities, developing
countermeasures, and supporting proactive cybersecurity defense by understanding
and mitigating the human element in security breaches.
"""

from typing import Dict, List

import uvicorn
from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session

import database
from backend.services.social_eng_service import models, schemas
from backend.services.social_eng_service.database import get_db

app = FastAPI(title="Maximus Social Engineering Service", version="1.0.0")


@app.on_event("startup")
async def startup_event():
    """Performs startup tasks for the Social Engineering Service."""
    print("🎣 Starting Maximus Social Engineering Service...")
    database.create_db_and_tables()
    print("✅ Maximus Social Engineering Service started successfully.")


@app.on_event("shutdown")
async def shutdown_event():
    """Performs shutdown tasks for the Social Engineering Service."""
    print("👋 Shutting down Maximus Social Engineering Service...")
    print("🛑 Maximus Social Engineering Service shut down.")


@app.get("/health")
async def health_check() -> Dict[str, str]:
    """Performs a health check of the Social Engineering Service.

    Returns:
        Dict[str, str]: A dictionary indicating the service status.
    """
    return {
        "status": "healthy",
        "message": "Social Engineering Service is operational.",
    }


@app.post("/campaigns/", response_model=schemas.Campaign)
async def create_campaign(campaign: schemas.CampaignCreate, db: Session = Depends(get_db)):
    """Creates a new social engineering campaign.

    Args:
        campaign (schemas.CampaignCreate): The campaign data.
        db (Session): The database session.

    Returns:
        schemas.Campaign: The created campaign.
    """
    db_campaign = models.Campaign(**campaign.dict())
    db.add(db_campaign)
    db.commit()
    db.refresh(db_campaign)
    return db_campaign


@app.get("/campaigns/", response_model=List[schemas.Campaign])
async def read_campaigns(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Retrieves a list of social engineering campaigns.

    Args:
        skip (int): Number of items to skip.
        limit (int): Maximum number of items to return.
        db (Session): The database session.

    Returns:
        List[schemas.Campaign]: A list of campaigns.
    """
    campaigns = db.query(models.Campaign).offset(skip).limit(limit).all()
    return campaigns


@app.get("/campaigns/{campaign_id}", response_model=schemas.Campaign)
async def read_campaign(campaign_id: int, db: Session = Depends(get_db)):
    """Retrieves a specific social engineering campaign by ID.

    Args:
        campaign_id (int): The ID of the campaign.
        db (Session): The database session.

    Returns:
        schemas.Campaign: The campaign details.

    Raises:
        HTTPException: If the campaign is not found.
    """
    campaign = db.query(models.Campaign).filter(models.Campaign.id == campaign_id).first()
    if campaign is None:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return campaign


@app.post("/targets/", response_model=schemas.Target)
async def create_target(target: schemas.TargetCreate, db: Session = Depends(get_db)):
    """Creates a new simulated human target.

    Args:
        target (schemas.TargetCreate): The target data.
        db (Session): The database session.

    Returns:
        schemas.Target: The created target.
    """
    db_target = models.Target(**target.dict())
    db.add(db_target)
    db.commit()
    db.refresh(db_target)
    return db_target


@app.get("/targets/", response_model=List[schemas.Target])
async def read_targets(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Retrieves a list of simulated human targets.

    Args:
        skip (int): Number of items to skip.
        limit (int): Maximum number of items to return.
        db (Session): The database session.

    Returns:
        List[schemas.Target]: A list of targets.
    """
    targets = db.query(models.Target).offset(skip).limit(limit).all()
    return targets


@app.post("/campaigns/{campaign_id}/interact", response_model=schemas.Interaction)
async def simulate_interaction(
    campaign_id: int,
    interaction: schemas.InteractionCreate,
    db: Session = Depends(get_db),
):
    """Simulates an interaction with a target within a campaign.

    Args:
        campaign_id (int): The ID of the campaign.
        interaction (schemas.InteractionCreate): The interaction data.
        db (Session): The database session.

    Returns:
        schemas.Interaction: The created interaction record.

    Raises:
        HTTPException: If the campaign or target is not found.
    """
    db_campaign = db.query(models.Campaign).filter(models.Campaign.id == campaign_id).first()
    if db_campaign is None:
        raise HTTPException(status_code=404, detail="Campaign not found")

    db_target = db.query(models.Target).filter(models.Target.id == interaction.target_id).first()
    if db_target is None:
        raise HTTPException(status_code=404, detail="Target not found")

    db_interaction = models.Interaction(**interaction.dict(), campaign_id=campaign_id)
    db.add(db_interaction)
    db.commit()
    db.refresh(db_interaction)
    return db_interaction


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8040)
