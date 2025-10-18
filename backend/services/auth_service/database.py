"""Database models and connection for Auth Service."""

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, Column, DateTime, Integer, String, create_engine
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()


class User(Base):
    """User model for authentication."""
    
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    roles = Column(ARRAY(String), nullable=False, default=["user"])
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


# Database connection
DATABASE_URL = "postgresql://postgres:postgres@postgres:5432/vertice_auth"

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Dependency for database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables and seed default users."""
    import bcrypt
    
    Base.metadata.create_all(bind=engine)
    
    # Seed default users
    db = SessionLocal()
    try:
        # Check if users exist
        existing_admin = db.query(User).filter(User.username == "maximus_admin").first()
        if not existing_admin:
            admin_user = User(
                username="maximus_admin",
                hashed_password=bcrypt.hashpw("adminpass".encode("utf-8"), bcrypt.gensalt()).decode("utf-8"),
                roles=["admin", "user"],
                is_active=True
            )
            db.add(admin_user)
        
        existing_user = db.query(User).filter(User.username == "maximus_user").first()
        if not existing_user:
            regular_user = User(
                username="maximus_user",
                hashed_password=bcrypt.hashpw("userpass".encode("utf-8"), bcrypt.gensalt()).decode("utf-8"),
                roles=["user"],
                is_active=True
            )
            db.add(regular_user)
        
        db.commit()
    finally:
        db.close()
