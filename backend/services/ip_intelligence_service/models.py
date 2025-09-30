
import datetime
from sqlalchemy import (Column, String, DateTime, JSON)
from database import Base

class IPAnalysisCache(Base):
    __tablename__ = "ip_analysis_cache"

    ip = Column(String, primary_key=True, index=True)
    analysis_data = Column(JSON)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
