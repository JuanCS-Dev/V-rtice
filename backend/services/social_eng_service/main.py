#!/usr/bin/env python3

import os
import json
import random
import string
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
import asyncio
import httpx
import tempfile
import base64

app = FastAPI(
    title="Social Engineering Toolkit",
    description="Ferramenta de engenharia social para testes de conscientização - Projeto Vértice",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class PhishingCampaignRequest(BaseModel):
    name: str
    target_domain: str
    email_template: str
    sender_name: str = "IT Support"
    sender_email: str = "noreply@company.com"
    landing_page_template: str = "office365"
    tracking_enabled: bool = True

class EmailTemplate(BaseModel):
    name: str
    subject: str
    body: str
    template_type: str  # phishing, spear_phishing, awareness

class LandingPageRequest(BaseModel):
    template_name: str
    company_name: str
    logo_url: Optional[str] = None
    redirect_url: Optional[str] = None

class AwarenessTrainingRequest(BaseModel):
    campaign_id: str
    training_type: str  # interactive, video, quiz
    difficulty: str = "medium"  # easy, medium, hard

# Storage (in production, use database)
campaigns = {}
email_templates = {}
landing_pages = {}
training_sessions = {}
campaign_stats = {}

# Pre-built email templates
DEFAULT_TEMPLATES = {
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

# Landing page templates
LANDING_PAGE_TEMPLATES = {
    "office365": {
        "name": "Office 365 Login",
        "html": """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Microsoft Office 365 - Sign In</title>
            <style>
                body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; background: #f3f2f1; }
                .container { max-width: 440px; margin: 100px auto; background: white; padding: 60px 40px; box-shadow: 0 2px 6px rgba(0,0,0,0.2); }
                .logo { text-align: center; margin-bottom: 20px; }
                .title { font-size: 24px; font-weight: 600; color: #323130; margin-bottom: 8px; }
                .subtitle { color: #605e5c; margin-bottom: 24px; }
                input { width: 100%; padding: 11px; border: 1px solid #605e5c; margin-bottom: 16px; font-size: 15px; }
                .btn { background: #0078d4; color: white; border: none; padding: 12px 24px; font-size: 15px; cursor: pointer; width: 100%; }
                .warning { background: #fff4ce; border: 1px solid #d83b01; padding: 12px; margin-top: 20px; border-radius: 2px; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="logo">
                    <img src="data:image/png;base64,{ms_logo}" alt="Microsoft" width="108" height="24">
                </div>
                <div class="title">Sign in</div>
                <div class="subtitle">to continue to {company_name}</div>
                <form id="loginForm" onsubmit="captureCredentials(event)">
                    <input type="email" placeholder="Email, phone, or Skype" required>
                    <input type="password" placeholder="Password" required>
                    <button class="btn" type="submit">Sign in</button>
                </form>
                <div class="warning" style="display:none;" id="warning">
                    <strong>⚠️ SECURITY AWARENESS TEST</strong><br>
                    This was a simulated phishing attempt. Your credentials were NOT captured.
                    <a href="{awareness_link}">Learn more about phishing protection</a>
                </div>
            </div>
            <script>
                function captureCredentials(event) {
                    event.preventDefault();

                    // Show awareness message instead of capturing credentials
                    document.getElementById('warning').style.display = 'block';
                    document.getElementById('loginForm').style.display = 'none';

                    // Track interaction for awareness metrics
                    if ('{tracking_enabled}' === 'true') {
                        fetch('/track-interaction', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({
                                campaign_id: '{campaign_id}',
                                action: 'credentials_submitted',
                                timestamp: new Date().toISOString()
                            })
                        });
                    }
                }
            </script>
        </body>
        </html>
        """
    },
    "bank_login": {
        "name": "Bank Login Portal",
        "html": """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Secure Banking - Login</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 0; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; display: flex; align-items: center; justify-content: center; }
                .container { background: white; padding: 40px; border-radius: 10px; box-shadow: 0 10px 30px rgba(0,0,0,0.3); min-width: 350px; }
                .logo { text-align: center; margin-bottom: 30px; font-size: 28px; color: #1a73e8; font-weight: bold; }
                .form-group { margin-bottom: 20px; }
                label { display: block; margin-bottom: 5px; color: #333; font-weight: 500; }
                input { width: 100%; padding: 12px; border: 2px solid #e1e5e9; border-radius: 5px; font-size: 16px; }
                input:focus { border-color: #1a73e8; outline: none; }
                .btn { background: #1a73e8; color: white; border: none; padding: 12px 24px; font-size: 16px; border-radius: 5px; cursor: pointer; width: 100%; margin-top: 10px; }
                .security-note { text-align: center; margin-top: 20px; font-size: 12px; color: #666; }
                .warning { background: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; margin-top: 20px; border-radius: 5px; display: none; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="logo">🏦 SecureBank</div>
                <form id="bankForm" onsubmit="showAwareness(event)">
                    <div class="form-group">
                        <label>Account Number</label>
                        <input type="text" placeholder="Enter account number" required>
                    </div>
                    <div class="form-group">
                        <label>PIN</label>
                        <input type="password" placeholder="Enter PIN" required>
                    </div>
                    <button class="btn" type="submit">🔐 Secure Login</button>
                </form>
                <div class="security-note">
                    🔒 Your connection is secured with 256-bit encryption
                </div>
                <div class="warning" id="awareness">
                    <strong>🎯 SECURITY TRAINING COMPLETE</strong><br>
                    This was a simulated phishing site for awareness training.
                    Never enter banking credentials on suspicious sites!
                </div>
            </div>
            <script>
                function showAwareness(event) {
                    event.preventDefault();
                    document.getElementById('awareness').style.display = 'block';
                    document.getElementById('bankForm').style.display = 'none';
                }
            </script>
        </body>
        </html>
        """
    }
}

def generate_campaign_id() -> str:
    """Generate unique campaign ID"""
    return f"camp_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}"

def generate_tracking_id() -> str:
    """Generate tracking ID for links"""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=12))

def create_phishing_link(campaign_id: str, tracking_id: str) -> str:
    """Create tracked phishing link"""
    return f"http://localhost:8011/landing/{campaign_id}?t={tracking_id}"

def create_awareness_link(campaign_id: str) -> str:
    """Create awareness training link"""
    return f"http://localhost:8011/training/{campaign_id}"

def personalize_template(template: str, target_data: Dict) -> str:
    """Personalize email template with target data"""
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

    result = template
    for placeholder, value in replacements.items():
        result = result.replace(placeholder, value)
    return result

# API Routes
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "active_campaigns": len(campaigns),
        "email_templates": len(email_templates) + len(DEFAULT_TEMPLATES),
        "service": "social-engineering-toolkit"
    }

@app.post("/campaigns/create")
async def create_phishing_campaign(campaign_request: PhishingCampaignRequest, background_tasks: BackgroundTasks):
    """Create new phishing awareness campaign"""
    campaign_id = generate_campaign_id()

    campaign = {
        "campaign_id": campaign_id,
        "name": campaign_request.name,
        "target_domain": campaign_request.target_domain,
        "email_template": campaign_request.email_template,
        "sender_name": campaign_request.sender_name,
        "sender_email": campaign_request.sender_email,
        "landing_page_template": campaign_request.landing_page_template,
        "tracking_enabled": campaign_request.tracking_enabled,
        "status": "active",
        "created_at": datetime.utcnow().isoformat(),
        "targets": [],
        "interactions": [],
        "stats": {
            "emails_sent": 0,
            "links_clicked": 0,
            "credentials_submitted": 0,
            "awareness_completed": 0
        }
    }

    campaigns[campaign_id] = campaign

    # Generate landing page
    landing_page = generate_landing_page(campaign_id, campaign_request.landing_page_template, campaign_request.target_domain)
    landing_pages[campaign_id] = landing_page

    return {
        "message": "Phishing awareness campaign created successfully",
        "campaign_id": campaign_id,
        "landing_page_url": f"http://localhost:8011/landing/{campaign_id}",
        "awareness_url": f"http://localhost:8011/training/{campaign_id}",
        "status": "ready"
    }

@app.post("/campaigns/{campaign_id}/send-email")
async def send_campaign_email(campaign_id: str, targets: List[Dict[str, str]]):
    """Send phishing awareness emails to targets"""
    if campaign_id not in campaigns:
        raise HTTPException(status_code=404, detail="Campaign not found")

    campaign = campaigns[campaign_id]
    template_name = campaign["email_template"]

    if template_name not in DEFAULT_TEMPLATES:
        raise HTTPException(status_code=404, detail="Email template not found")

    template = DEFAULT_TEMPLATES[template_name]
    sent_emails = []

    for target in targets:
        tracking_id = generate_tracking_id()
        phishing_link = create_phishing_link(campaign_id, tracking_id)
        awareness_link = create_awareness_link(campaign_id)

        target_data = {
            **target,
            "phishing_link": phishing_link,
            "training_link": awareness_link,
            "awareness_link": awareness_link
        }

        personalized_email = personalize_template(template["body"], target_data)

        email_record = {
            "target_email": target.get("email"),
            "target_name": target.get("name", "User"),
            "tracking_id": tracking_id,
            "phishing_link": phishing_link,
            "sent_at": datetime.utcnow().isoformat(),
            "status": "sent"  # In production, integrate with email service
        }

        campaign["targets"].append(email_record)
        sent_emails.append(email_record)

    campaign["stats"]["emails_sent"] += len(sent_emails)
    campaigns[campaign_id] = campaign

    return {
        "message": f"Simulated {len(sent_emails)} emails sent for awareness campaign",
        "campaign_id": campaign_id,
        "emails_sent": len(sent_emails),
        "note": "⚠️ SIMULATION MODE: No real emails sent - this is for awareness testing only"
    }

@app.get("/landing/{campaign_id}")
async def serve_landing_page(campaign_id: str, t: Optional[str] = None):
    """Serve phishing landing page"""
    if campaign_id not in campaigns:
        raise HTTPException(status_code=404, detail="Campaign not found")

    if campaign_id not in landing_pages:
        raise HTTPException(status_code=404, detail="Landing page not found")

    # Track page visit
    if t:  # tracking ID provided
        interaction = {
            "tracking_id": t,
            "action": "page_visited",
            "timestamp": datetime.utcnow().isoformat(),
            "ip_address": "simulated"  # In production, get real IP
        }
        campaigns[campaign_id]["interactions"].append(interaction)
        campaigns[campaign_id]["stats"]["links_clicked"] += 1

    return landing_pages[campaign_id]

@app.post("/track-interaction")
async def track_interaction(interaction_data: Dict):
    """Track user interaction with phishing elements"""
    campaign_id = interaction_data.get("campaign_id")
    if not campaign_id or campaign_id not in campaigns:
        return {"status": "campaign not found"}

    campaigns[campaign_id]["interactions"].append({
        **interaction_data,
        "timestamp": datetime.utcnow().isoformat()
    })

    # Update stats based on action
    action = interaction_data.get("action")
    if action == "credentials_submitted":
        campaigns[campaign_id]["stats"]["credentials_submitted"] += 1
    elif action == "awareness_completed":
        campaigns[campaign_id]["stats"]["awareness_completed"] += 1

    return {"status": "tracked"}

@app.get("/campaigns/{campaign_id}/stats")
async def get_campaign_stats(campaign_id: str):
    """Get campaign statistics and analytics"""
    if campaign_id not in campaigns:
        raise HTTPException(status_code=404, detail="Campaign not found")

    campaign = campaigns[campaign_id]
    stats = campaign["stats"]

    # Calculate success rate
    emails_sent = stats["emails_sent"]
    links_clicked = stats["links_clicked"]
    credentials_submitted = stats["credentials_submitted"]

    click_rate = (links_clicked / emails_sent * 100) if emails_sent > 0 else 0
    success_rate = (credentials_submitted / emails_sent * 100) if emails_sent > 0 else 0

    return {
        "campaign_id": campaign_id,
        "campaign_name": campaign["name"],
        "status": campaign["status"],
        "created_at": campaign["created_at"],
        "stats": {
            "emails_sent": emails_sent,
            "links_clicked": links_clicked,
            "credentials_submitted": credentials_submitted,
            "awareness_completed": stats["awareness_completed"],
            "click_rate_percent": round(click_rate, 2),
            "success_rate_percent": round(success_rate, 2)
        },
        "recent_interactions": campaign["interactions"][-10:],  # Last 10 interactions
        "recommendations": generate_campaign_recommendations(stats, emails_sent)
    }

def generate_landing_page(campaign_id: str, template_name: str, company_name: str) -> str:
    """Generate personalized landing page"""
    if template_name not in LANDING_PAGE_TEMPLATES:
        template_name = "office365"  # Default template

    template = LANDING_PAGE_TEMPLATES[template_name]["html"]

    # Replace placeholders
    html = template.replace("{campaign_id}", campaign_id)
    html = html.replace("{company_name}", company_name)
    html = html.replace("{tracking_enabled}", "true")
    html = html.replace("{awareness_link}", f"/training/{campaign_id}")

    # Add Microsoft logo (base64 encoded placeholder)
    ms_logo = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
    html = html.replace("{ms_logo}", ms_logo)

    return html

def generate_campaign_recommendations(stats: Dict, total_sent: int) -> List[str]:
    """Generate campaign recommendations"""
    recommendations = []

    if total_sent == 0:
        return ["📧 Start by sending test emails to measure awareness levels"]

    click_rate = (stats["links_clicked"] / total_sent * 100) if total_sent > 0 else 0
    success_rate = (stats["credentials_submitted"] / total_sent * 100) if total_sent > 0 else 0

    if success_rate > 20:
        recommendations.append("🚨 HIGH RISK: >20% of users submitted credentials - immediate training needed")
    elif success_rate > 10:
        recommendations.append("⚠️ MEDIUM RISK: >10% susceptible - additional awareness training recommended")
    elif success_rate > 5:
        recommendations.append("✅ GOOD: <5% fell for phishing - maintain current training")
    else:
        recommendations.append("🏆 EXCELLENT: Very low susceptibility rate")

    if click_rate > 30:
        recommendations.append("📚 Focus on email security awareness training")
    if stats["awareness_completed"] < stats["links_clicked"]:
        recommendations.append("🎯 Encourage more users to complete awareness training")

    recommendations.append("📊 Run quarterly campaigns to maintain awareness")

    return recommendations

@app.get("/templates/email")
async def get_email_templates():
    """Get available email templates"""
    return {
        "default_templates": DEFAULT_TEMPLATES,
        "custom_templates": email_templates,
        "total": len(DEFAULT_TEMPLATES) + len(email_templates)
    }

@app.post("/templates/email")
async def create_email_template(template: EmailTemplate):
    """Create custom email template"""
    template_id = f"custom_{int(datetime.now().timestamp())}"
    email_templates[template_id] = template.dict()

    return {
        "message": "Email template created successfully",
        "template_id": template_id,
        "template": template.dict()
    }

@app.get("/templates/landing-pages")
async def get_landing_page_templates():
    """Get available landing page templates"""
    return {
        "templates": {k: {"name": v["name"]} for k, v in LANDING_PAGE_TEMPLATES.items()},
        "total": len(LANDING_PAGE_TEMPLATES)
    }

@app.get("/training/{campaign_id}")
async def serve_awareness_training(campaign_id: str):
    """Serve awareness training content"""
    if campaign_id not in campaigns:
        raise HTTPException(status_code=404, detail="Campaign not found")

    training_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Security Awareness Training</title>
        <style>
            body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; background: #f8f9fa; }
            .container { max-width: 800px; margin: 50px auto; background: white; padding: 40px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            .header { text-align: center; margin-bottom: 30px; }
            .success { background: #d4edda; border: 1px solid #c3e6cb; padding: 15px; border-radius: 5px; margin-bottom: 20px; color: #155724; }
            .tips { background: #e7f3ff; border: 1px solid #bee5eb; padding: 20px; border-radius: 5px; margin: 20px 0; }
            .tip-item { margin: 10px 0; padding-left: 20px; }
            .btn { background: #007bff; color: white; border: none; padding: 12px 24px; border-radius: 5px; cursor: pointer; text-decoration: none; display: inline-block; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🛡️ Security Awareness Training</h1>
                <p>Learn how to identify and prevent phishing attacks</p>
            </div>

            <div class="success">
                <strong>✅ Great job!</strong> You've completed this security awareness exercise.
                This helps improve our organization's security posture.
            </div>

            <div class="tips">
                <h3>🎯 How to Spot Phishing Emails:</h3>
                <div class="tip-item">• Check the sender's email address carefully</div>
                <div class="tip-item">• Look for urgent language or threats</div>
                <div class="tip-item">• Hover over links to see the real destination</div>
                <div class="tip-item">• Be suspicious of unexpected attachments</div>
                <div class="tip-item">• Verify requests through other channels</div>
            </div>

            <div class="tips">
                <h3>🔐 Best Security Practices:</h3>
                <div class="tip-item">• Use strong, unique passwords</div>
                <div class="tip-item">• Enable two-factor authentication</div>
                <div class="tip-item">• Keep software updated</div>
                <div class="tip-item">• Report suspicious emails to IT</div>
                <div class="tip-item">• Never share credentials</div>
            </div>

            <div style="text-align: center; margin-top: 30px;">
                <a href="#" class="btn" onclick="completeTraining()">Mark Training Complete</a>
            </div>
        </div>

        <script>
            function completeTraining() {
                fetch('/track-interaction', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        campaign_id: '""" + campaign_id + """',
                        action: 'awareness_completed',
                        timestamp: new Date().toISOString()
                    })
                }).then(() => {
                    alert('Training completed! Thank you for improving our security.');
                });
            }
        </script>
    </body>
    </html>
    """

    return training_html

@app.get("/campaigns")
async def list_campaigns():
    """List all campaigns"""
    return {
        "campaigns": list(campaigns.values()),
        "total": len(campaigns)
    }

@app.delete("/campaigns/{campaign_id}")
async def delete_campaign(campaign_id: str):
    """Delete a campaign"""
    if campaign_id not in campaigns:
        raise HTTPException(status_code=404, detail="Campaign not found")

    del campaigns[campaign_id]
    if campaign_id in landing_pages:
        del landing_pages[campaign_id]

    return {"message": "Campaign deleted successfully"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=80)