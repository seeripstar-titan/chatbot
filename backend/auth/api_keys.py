"""
API key generation and validation utilities.
"""

import hashlib
import secrets


def generate_api_key() -> tuple[str, str, str]:
    """
    Generate a new API key.

    Returns:
        Tuple of (raw_key, key_hash, key_prefix)
        - raw_key: The full API key to give to the tenant (shown only once)
        - key_hash: SHA-256 hash stored in the database
        - key_prefix: First 8 chars for identification in logs/UI
    """
    raw_key = f"cb_{secrets.token_urlsafe(32)}"
    key_hash = hash_api_key(raw_key)
    key_prefix = raw_key[:11]  # "cb_" + first 8 chars
    return raw_key, key_hash, key_prefix


def hash_api_key(raw_key: str) -> str:
    """Hash an API key using SHA-256."""
    return hashlib.sha256(raw_key.encode()).hexdigest()
