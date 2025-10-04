"""IP Intelligence Service - Database Models.

This module defines the SQLAlchemy ORM model for the IP analysis cache.
"""

import datetime
from sqlalchemy import (Column, String, DateTime, JSON)
from .database import Base

class IPAnalysisCache(Base):
    """SQLAlchemy model for the IP analysis cache table.

    This table stores the JSON results of IP intelligence analyses to reduce
    redundant queries to external APIs.

    Attributes:
        ip (str): The IP address, serving as the primary key.
        analysis_data (JSON): The complete JSON data from the analysis.
        timestamp (DateTime): The timestamp of the last update.
    """
    __tablename__ = "ip_analysis_cache"

    ip = Column(String, primary_key=True, index=True)
    analysis_data = Column(JSON)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)