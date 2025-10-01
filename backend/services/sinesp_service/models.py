from pydantic import BaseModel
from typing import List, Dict
from datetime import datetime

class SinespQueryInput(BaseModel):
    plate: str
    request_context: Dict | None = None
    deep_analysis: bool = False

class SinespAnalysisReport(BaseModel):
    plate_details: Dict
    threat_score: int
    risk_level: str
    summary: str
    reasoning_chain: List[str]
    correlated_events: List[Dict]
    recommended_actions: List[str]
    confidence_score: float
    timestamp: datetime
