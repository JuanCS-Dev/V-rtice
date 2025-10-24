#!/usr/bin/env python3
"""
Create superuser for Vértice Auth Service
Usage: python create_superuser.py <email> [password]
"""

import sys
import bcrypt
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, ARRAY
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

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


def create_superuser(username: str, password: str = None):
    """Create a superuser with admin and user roles."""

    # Database connection - maximus-postgres-immunity
    DATABASE_URL = "postgresql://maximus:maximus_immunity_2024@localhost:5434/adaptive_immunity"
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # Create tables if they don't exist
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # Check if user already exists
        existing_user = db.query(User).filter(User.username == username).first()
        if existing_user:
            print(f"❌ User '{username}' already exists!")
            print(f"   Current roles: {existing_user.roles}")

            # Update to superuser if not already
            if "superuser" not in existing_user.roles:
                existing_user.roles = ["superuser", "admin", "user"]
                db.commit()
                print(f"✅ Updated '{username}' to superuser!")
            return

        # Use provided password or generate strong one
        if not password:
            import secrets
            password = secrets.token_urlsafe(16)
            print(f"🔑 Generated password: {password}")
            print(f"   ⚠️  SAVE THIS PASSWORD - it won't be shown again!")

        # Hash password
        hashed_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

        # Create superuser
        superuser = User(
            username=username,
            hashed_password=hashed_password,
            roles=["superuser", "admin", "user"],
            is_active=True
        )

        db.add(superuser)
        db.commit()

        print(f"✅ Superuser '{username}' created successfully!")
        print(f"   Roles: superuser, admin, user")
        print(f"   Active: True")
        print()
        print("📝 Login credentials:")
        print(f"   Username: {username}")
        if password:
            print(f"   Password: {password}")
        print()
        print("🚀 You can now login via:")
        print(f"   vcli auth login --username {username}")

    except Exception as e:
        print(f"❌ Error creating superuser: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python create_superuser.py <email> [password]")
        print()
        print("Examples:")
        print("  python create_superuser.py juan@vertice.ai")
        print("  python create_superuser.py juan@vertice.ai mySecurePass123")
        sys.exit(1)

    username = sys.argv[1]
    password = sys.argv[2] if len(sys.argv) > 2 else None

    create_superuser(username, password)
