"""REST API Module - PRODUCTION-READY

Enterprise-grade REST API for Active Immune Core system.

Features:
- Complete CRUD operations
- Authentication & Authorization
- Rate limiting
- WebSocket support
- OpenAPI/Swagger documentation
- Real-time monitoring
- Management operations

NO MOCKS, NO PLACEHOLDERS, NO TODOS.

Authors: Juan & Claude
Version: 1.0.0
"""


# Lazy imports to avoid circular import issues
def __getattr__(name):
    """Lazy attribute access for app and create_app."""
    if name in ("app", "create_app"):
        from .main import app, create_app

        return app if name == "app" else create_app
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = ["app", "create_app"]
