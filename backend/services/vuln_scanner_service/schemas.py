
from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime
from models import ScanStatus, Severity

# --- Request Models ---

class VulnScanRequest(BaseModel):
    target: str
    scan_type: str = "comprehensive"  # quick, comprehensive, stealth, aggressive

class WebVulnRequest(BaseModel):
    target: str
    scan_type: str = "full"  # quick, full, sqli, xss, lfi

# --- Response Models ---

class Vulnerability(BaseModel):
    host: str
    port: int
    service: str
    cve_id: Optional[str] = None
    severity: Severity
    description: str
    recommendation: str
    exploit_available: Optional[str] = None

    class Config:
        from_attributes = True

class Scan(BaseModel):
    id: str
    target: str
    scan_type: str
    status: ScanStatus
    created_at: datetime
    completed_at: Optional[datetime] = None
    vulnerabilities: List[Vulnerability] = []

    class Config:
        from_attributes = True

class ScanInitiatedResponse(BaseModel):
    message: str
    scan_id: str
    target: str
