"""Role-Based Access Control for Vertice CLI."""

import os
from typing import Dict, List, Any

# Load from env or use a default
SUPER_ADMIN = os.getenv("SUPER_ADMIN_EMAIL", "juan.brainfarma@gmail.com")

ROLES: Dict[str, Dict[str, Any]] = {
    "super_admin": {"permissions": ["*"], "level": 100},  # All permissions
    "admin": {"permissions": ["read", "write", "execute", "manage_users"], "level": 80},
    "analyst": {"permissions": ["read", "write", "execute"], "level": 50},
    "viewer": {"permissions": ["read"], "level": 10},
}


class PermissionManager:
    """Manages permissions and roles."""

    @staticmethod
    def get_user_role(email: str) -> str:
        """Determine user role based on email."""
        if email == SUPER_ADMIN:
            return "super_admin"
        # In a real scenario, this would be loaded from a database or user profile
        return "analyst"  # Default role for now

    @staticmethod
    def has_permission(email: str, permission: str) -> bool:
        """Check if user has a specific permission."""
        role = PermissionManager.get_user_role(email)
        role_data = ROLES.get(role, ROLES["viewer"])
        permissions: List[str] = role_data.get("permissions", [])

        # Super admin has all permissions
        if "*" in permissions:
            return True

        return permission in permissions
