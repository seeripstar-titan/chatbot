"""
Rate limiting configuration using SlowAPI.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

from backend.config import get_settings

settings = get_settings()

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[
        f"{settings.rate_limit_per_minute}/minute",
        f"{settings.rate_limit_per_hour}/hour",
    ],
    storage_uri=settings.redis_url if settings.is_production else "memory://",
)
