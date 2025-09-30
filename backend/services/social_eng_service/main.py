import uuid
import random
import string
import smtplib
from email.mime.text import MIMEText
from email.header import Header
from datetime import datetime, timedelta
from typing import List, Dict, Optional

from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

# Internal imports
import models
import schemas
from database import engine, get_db, Base, AsyncSessionLocal
from config import settings

app = FastAPI(
    title="Social Engineering Toolkit",
    description="Ferramenta de engenharia social para testes de conscientização - Projeto Vértice",
    version="2.0.0"
)

# Middleware for CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup Jinja2 templates
templates = Jinja2Templates(directory="templates")

@app.on_event("startup")
async def startup():
    """Create database tables and default email templates on startup."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with AsyncSessionLocal() as session:
        # Check and add default email templates
        default_templates_data = {
            "office365_login": {
                "name": "Office 365 Login Alert",
                "subject": "🔔 Unusual sign-in activity detected",
                "body": """
        Dear {target_name},

        We detected unusual sign-in activity on your Office 365 account.

        📍 Location: {random_location}
        🕒 Time: {current_time}
        🖥️ Device: {random_device}

        If this was not you, please verify your account immediately:
        👉 {phishing_link}

        This link will expire in 24 hours for security reasons.

        Best regards,
        IT Security Team
        """,
                "template_type": "phishing"
            },
            "payroll_update": {
                "name": "Urgent Payroll Information Update",
                "subject": "🚨 URGENT: Update Required for Payroll Processing",
                "body": """
        Dear {target_name},

        Our payroll system requires immediate verification of your information
        to ensure your next payment is processed correctly.

        ⚠️ Action Required by: {deadline}
        💰 Affected: Next payroll cycle

        Please update your information here:
        👉 {phishing_link}

        Failure to update may result in payment delays.

        HR Department
        """,
                "template_type": "spear_phishing"
            },
            "security_awareness": {
                "name": "Security Awareness Test",
                "subject": "Security Training: How to Identify Phishing",
                "body": """
        Dear {target_name},

        This is a security awareness test. The email you received was a
        simulated phishing attempt to help you recognize real threats.

        🎯 You correctly identified this as suspicious! (or clicked the link)

        📚 Learn more about phishing protection:
        👉 {training_link}

        Thank you for helping keep our organization secure.

        Security Team
        """,
                "template_type": "awareness"
            }
        }

        for template_key, template_data in default_templates_data.items():
            existing_template = await session.execute(
                select(models.EmailTemplate).filter_by(name=template_data["name"])
            )
            if not existing_template.scalar_one_or_none():
                new_template = models.EmailTemplate(
                    name=template_data["name"],
                    subject=template_data["subject"],
                    body=template_data["body"],
                    template_type=template_data["template_type"]
                )
                session.add(new_template)
        await session.commit()

# --- Helper Functions ---

def generate_campaign_id() -> str:
    """Generate a unique campaign ID."""
    return f"camp_{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}"

def generate_tracking_id() -> str:
    """Generate a unique tracking ID for links."""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=12))

def create_phishing_link(campaign_id: str, tracking_id: str) -> str:
    """Create a tracked phishing link using the base URL from settings."""
    return f"{settings.APP_BASE_URL}/landing/{campaign_id}?t={tracking_id}"

def create_awareness_link(campaign_id: str) -> str:
    """Create an awareness training link."""
    return f"{settings.APP_BASE_URL}/training/{campaign_id}"

def personalize_template(template_body: str, target_data: Dict) -> str:
    """Personalize email template with target data."""
    replacements = {
        "{target_name}": target_data.get("name", "User"),
        "{company_name}": target_data.get("company", "Your Company"),
        "{current_time}": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "{deadline}": (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d"),
        "{random_location}": random.choice(["São Paulo, BR", "New York, US", "London, UK", "Tokyo, JP"]),
        "{random_device}": random.choice(["Windows PC", "iPhone 12", "Android Device", "MacBook Pro"]),
        "{phishing_link}": target_data.get("phishing_link", "#"),
        "{training_link}": target_data.get("training_link", "#"),
        "{awareness_link}": target_data.get("awareness_link", "#")
    }

    result = template_body
    for placeholder, value in replacements.items():
        result = result.replace(placeholder, value)
    return result

async def send_email_via_smtp(
    sender_email: str, recipient_email: str, subject: str, body: str
):
    """Sends an email using configured SMTP settings."""
    if not settings.SMTP_HOST or not settings.SMTP_PORT:
        raise ValueError("SMTP host and port must be configured in .env")

    msg = MIMEText(body, "html", "utf-8")
    msg["From"] = str(Header(f"{settings.SMTP_SENDER_EMAIL} <{sender_email}>", "utf-8"))
    msg["To"] = recipient_email
    msg["Subject"] = str(Header(subject, "utf-8"))

    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls()
            if settings.SMTP_USERNAME and settings.SMTP_PASSWORD:
                server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            server.sendmail(sender_email, recipient_email, msg.as_string())
        print(f"Email sent to {recipient_email}")
    except Exception as e:
        print(f"Failed to send email to {recipient_email}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to send email: {e}")

# --- API Routes ---

@app.get("/health", tags=["General"])
async def health_check(db: AsyncSession = Depends(get_db)):
    """Check the health of the service."""
    campaign_count = (await db.execute(select(models.Campaign))).scalars().all()
    template_count = (await db.execute(select(models.EmailTemplate))).scalars().all()
    return {
        "status": "healthy",
        "database_status": "connected",
        "active_campaigns": len(campaign_count),
        "email_templates": len(template_count),
        "service": "social-engineering-toolkit"
    }

@app.post("/campaigns", status_code=201, response_model=schemas.CampaignResponse, tags=["Campaigns"])
async def create_campaign(
    campaign_request: schemas.CampaignCreate, db: AsyncSession = Depends(get_db)
):
    """Create a new phishing awareness campaign."""
    campaign_id = generate_campaign_id()
    
    new_campaign = models.Campaign(
        id=campaign_id,
        name=campaign_request.name,
        target_domain=campaign_request.target_domain,
        email_template_name=campaign_request.email_template_name,
        landing_page_template=campaign_request.landing_page_template,
        sender_name=campaign_request.sender_name,
        sender_email=campaign_request.sender_email,
        tracking_enabled=campaign_request.tracking_enabled,
    )
    db.add(new_campaign)
    await db.commit()
    await db.refresh(new_campaign)

    return {
        "message": "Phishing awareness campaign created successfully.",
        "campaign": new_campaign,
        "landing_page_url": f"{settings.APP_BASE_URL}/landing/{campaign_id}",
        "awareness_url": f"{settings.APP_BASE_URL}/training/{campaign_id}",
    }

@app.get("/campaigns", response_model=List[schemas.Campaign], tags=["Campaigns"])
async def list_campaigns(db: AsyncSession = Depends(get_db)):
    """List all campaigns."""
    result = await db.execute(select(models.Campaign))
    return result.scalars().all()

@app.get("/campaigns/{campaign_id}", response_model=schemas.Campaign, tags=["Campaigns"])
async def get_campaign(campaign_id: str, db: AsyncSession = Depends(get_db)):
    """Get details for a specific campaign."""
    campaign = await db.get(models.Campaign, campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return campaign

@app.delete("/campaigns/{campaign_id}", status_code=204, tags=["Campaigns"])
async def delete_campaign(campaign_id: str, db: AsyncSession = Depends(get_db)):
    """Delete a campaign and all its related data."""
    campaign = await db.get(models.Campaign, campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    await db.delete(campaign)
    await db.commit()
    return None

@app.post("/campaigns/{campaign_id}/send", tags=["Execution"])
async def send_campaign_emails(
    campaign_id: str, targets: List[schemas.TargetBase], db: AsyncSession = Depends(get_db)
):
    """Send phishing awareness emails to a list of targets."""
    campaign = await db.get(models.Campaign, campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    email_template = await db.execute(
        select(models.EmailTemplate).filter_by(name=campaign.email_template_name)
    )
    email_template = email_template.scalar_one_or_none()
    if not email_template:
        raise HTTPException(status_code=404, detail="Email template not found")

    sent_count = 0
    for target_data in targets:
        tracking_id = generate_tracking_id()
        phishing_link = create_phishing_link(campaign_id, tracking_id)
        awareness_link = create_awareness_link(campaign_id)

        target_email = target_data.email
        target_name = target_data.name

        personalized_body = personalize_template(
            email_template.body,
            {
                "name": target_name,
                "email": target_email,
                "phishing_link": phishing_link,
                "training_link": awareness_link,
                "awareness_link": awareness_link,
                "company": campaign.target_domain # Pass target_domain as company
            }
        )

        try:
            await send_email_via_smtp(
                sender_email=campaign.sender_email,
                recipient_email=target_email,
                subject=email_template.subject,
                body=personalized_body,
            )
            status = "sent"
        except HTTPException: # Catch the HTTPException raised by send_email_via_smtp
            status = "failed"

        new_target = models.Target(
            campaign_id=campaign_id,
            email=target_email,
            name=target_name,
            tracking_id=tracking_id,
            phishing_link=phishing_link,
            status=status
        )
        db.add(new_target)
        sent_count += 1
    
    await db.commit()

    return {
        "message": f"Attempted to send {sent_count} emails for awareness campaign.",
        "campaign_id": campaign_id,
        "emails_attempted": sent_count,
        "note": "Check logs for individual email sending status."
    }

@app.get("/landing/{campaign_id}", response_class=HTMLResponse, tags=["Execution"])
async def serve_landing_page(
    request: Request, campaign_id: str, t: Optional[str] = None, db: AsyncSession = Depends(get_db)
):
    """Serve the phishing landing page and track the visit."""
    campaign = await db.get(models.Campaign, campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    # Track the page visit interaction
    if t:
        interaction = models.Interaction(
            campaign_id=campaign_id,
            tracking_id=t,
            action="page_visited",
            ip_address=request.client.host, # Capture real IP address
        )
        db.add(interaction)
        await db.commit()

    template_name = campaign.landing_page_template
    if template_name not in ["office365_login", "bank_login"]:
        template_name = "office365_login.html" # Default
    else:
        template_name += ".html"

    context = {
        "request": request,
        "campaign_id": campaign_id,
        "company_name": campaign.target_domain,
        "tracking_enabled": str(campaign.tracking_enabled).lower(),
        "awareness_link": create_awareness_link(campaign_id),
        "app_base_url": settings.APP_BASE_URL,
    }
    return templates.TemplateResponse(template_name, context)

@app.get("/training/{campaign_id}", response_class=HTMLResponse, tags=["Execution"])
async def serve_awareness_training(request: Request, campaign_id: str, db: AsyncSession = Depends(get_db)):
    """Serve the awareness training page."""
    campaign = await db.get(models.Campaign, campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    context = {
        "request": request,
        "campaign_id": campaign_id,
        "app_base_url": settings.APP_BASE_URL,
    }
    return templates.TemplateResponse("training.html", context)

@app.post("/track-interaction", status_code=202, tags=["Execution"])
async def track_interaction(
    interaction_data: schemas.InteractionCreate, db: AsyncSession = Depends(get_db)
):
    """Track a user interaction, like a credential submission or training completion."""
    campaign = await db.get(models.Campaign, interaction_data.campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    new_interaction = models.Interaction(**interaction_data.dict())
    db.add(new_interaction)
    await db.commit()
    
    return {"status": "tracked"}

@app.get("/campaigns/{campaign_id}/stats", response_model=schemas.CampaignStats, tags=["Stats"])
async def get_campaign_stats(campaign_id: str, db: AsyncSession = Depends(get_db)):
    """Get detailed statistics for a campaign."""
    campaign = await db.get(models.Campaign, campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    # Query for stats
    total_sent = (await db.execute(
        select(models.Target).filter_by(campaign_id=campaign_id)
    )).scalars().all()
    
    links_clicked = (await db.execute(
        select(models.Interaction).where(
            models.Interaction.campaign_id == campaign_id,
            models.Interaction.action == "page_visited"
        )
    )).scalars().all()
    
    credentials_submitted = (await db.execute(
        select(models.Interaction).where(
            models.Interaction.campaign_id == campaign_id,
            models.Interaction.action == "credentials_submitted"
        )
    )).scalars().all()

    awareness_completed = (await db.execute(
        select(models.Interaction).where(
            models.Interaction.campaign_id == campaign_id,
            models.Interaction.action == "awareness_completed"
        )
    )).scalars().all()

    click_rate = (len(links_clicked) / len(total_sent) * 100) if len(total_sent) > 0 else 0
    submission_rate = (len(credentials_submitted) / len(total_sent) * 100) if len(total_sent) > 0 else 0

    # Fetch recent interactions directly from the campaign relationship
    # This assumes campaign.interactions is loaded, which it should be with relationship
    recent_interactions = sorted(campaign.interactions, key=lambda x: x.timestamp, reverse=True)[:10]

    return {
        "campaign_id": campaign.id,
        "campaign_name": campaign.name,
        "stats": {
            "emails_sent": len(total_sent),
            "links_clicked": len(links_clicked),
            "credentials_submitted": len(credentials_submitted),
            "awareness_completed": len(awareness_completed),
            "click_rate_percent": round(click_rate, 2),
            "submission_rate_percent": round(submission_rate, 2),
        },
        "recent_interactions": recent_interactions
    }

# --- Template Management ---

@app.post("/templates/email", status_code=201, response_model=schemas.EmailTemplate, tags=["Templates"])
async def create_email_template(
    template_data: schemas.EmailTemplateCreate, db: AsyncSession = Depends(get_db)
):
    """Create a new custom email template."""
    new_template = models.EmailTemplate(**template_data.dict())
    db.add(new_template)
    await db.commit()
    await db.refresh(new_template)
    return new_template

@app.get("/templates/email", response_model=List[schemas.EmailTemplate], tags=["Templates"])
async def list_email_templates(db: AsyncSession = Depends(get_db)):
    """List all available email templates."""
    result = await db.execute(select(models.EmailTemplate))
    return result.scalars().all()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=80)