from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime

# --- Base Schemas ---

class TargetBase(BaseModel):
    email: EmailStr
    name: str = "User"

class InteractionCreate(BaseModel):
    campaign_id: str
    action: str
    tracking_id: Optional[str] = None
    details: Optional[dict] = None

class EmailTemplateBase(BaseModel):
    name: str
    subject: str
    body: str
    template_type: str

class EmailTemplateCreate(EmailTemplateBase):
    pass

class CampaignBase(BaseModel):
    name: str
    target_domain: str
    email_template_name: str
    landing_page_template: str
    sender_name: str = "IT Support"
    sender_email: EmailStr = "noreply@company.com"
    tracking_enabled: bool = True

class CampaignCreate(CampaignBase):
    pass

# --- ORM Mode Schemas (for responses) ---

class Interaction(InteractionCreate):
    id: int
    timestamp: datetime
    ip_address: Optional[str] = None

    class Config:
        orm_mode = True

class Target(TargetBase):
    id: int
    campaign_id: str
    tracking_id: str
    sent_at: datetime

    class Config:
        orm_mode = True

class EmailTemplate(EmailTemplateBase):
    id: int

    class Config:
        orm_mode = True

class Campaign(CampaignBase):
    id: str
    status: str
    created_at: datetime
    targets: List[Target] = []
    interactions: List[Interaction] = []

    class Config:
        orm_mode = True

# --- Complex Response Schemas ---

class CampaignResponse(BaseModel):
    message: str
    campaign: Campaign
    landing_page_url: str
    awareness_url: str

class CampaignStatsDetail(BaseModel):
    emails_sent: int
    links_clicked: int
    credentials_submitted: int
    awareness_completed: int
    click_rate_percent: float
    submission_rate_percent: float

class CampaignStats(BaseModel):
    campaign_id: str
    campaign_name: str
    stats: CampaignStatsDetail
    recent_interactions: List[Interaction]
