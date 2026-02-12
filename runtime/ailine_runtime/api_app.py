"""DEPRECATED: Legacy monolith API. Use api.app.create_app() instead.

This file is kept only for backward compatibility during migration.
All functionality has been moved to the api/ package with proper routers.
"""

from __future__ import annotations

# Re-export for any remaining references
from .api.app import create_app

app = create_app()
