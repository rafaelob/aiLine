"""Dev-only JWT fallback secret (F-254).

Generated ONCE at import time so that both the auth router (minting)
and the tenant context middleware (verifying) share the same value
within a single process.

**WARNING**: This secret is random per process restart.  In multi-worker
deployments each worker will have a different secret, breaking cross-worker
JWT verification.  Always set AILINE_JWT_SECRET explicitly when running
more than one worker process.
"""

from __future__ import annotations

import logging
import secrets

logger = logging.getLogger("ailine.shared.jwt_dev_secret")

DEV_JWT_SECRET: str = secrets.token_urlsafe(48)

logger.warning(
    "Using auto-generated dev JWT secret. "
    "Set AILINE_JWT_SECRET for multi-worker or production use."
)
