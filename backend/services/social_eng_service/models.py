import datetime
from sqlalchemy import (Column, String, Integer, DateTime, Boolean, 
                        ForeignKey, Text, JSON)
from sqlalchemy.orm import relationship
from database import Base

class Campaign(Base):
    __tablename__ = "campaigns"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, index=True)
    target_domain = Column(String)
    email_template_name = Column(String)
    landing_page_template = Column(String)
    sender_name = Column(String)
    sender_email = Column(String)
    tracking_enabled = Column(Boolean, default=True)
    status = Column(String, default="active")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    targets = relationship("Target", back_populates="campaign", lazy="selectin")
    interactions = relationship("Interaction", back_populates="campaign", lazy="selectin")

class EmailTemplate(Base):
    __tablename__ = "email_templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    subject = Column(String)
    body = Column(Text)
    template_type = Column(String, default="custom")

class Target(Base):
    __tablename__ = "targets"

    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(String, ForeignKey("campaigns.id"))
    email = Column(String, index=True)
    name = Column(String)
    tracking_id = Column(String, unique=True)
    phishing_link = Column(String)
    sent_at = Column(DateTime, default=datetime.datetime.utcnow)
    status = Column(String, default="sent")

    campaign = relationship("Campaign", back_populates="targets")

class Interaction(Base):
    __tablename__ = "interactions"

    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(String, ForeignKey("campaigns.id"))
    tracking_id = Column(String, nullable=True)
    action = Column(String) # e.g., page_visited, credentials_submitted
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    ip_address = Column(String, nullable=True)
    details = Column(JSON, nullable=True) # For extra data

    campaign = relationship("Campaign", back_populates="interactions")
