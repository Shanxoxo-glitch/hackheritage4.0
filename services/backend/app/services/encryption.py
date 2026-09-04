import base64
from cryptography.fernet import Fernet
from app.config import settings

def _get_fernet_instance() -> Fernet:
    try:
        # Check if settings key is valid Fernet key (32 url-safe base64-encoded bytes)
        return Fernet(settings.FERNET_KEY.encode('utf-8'))
    except Exception:
        # Fallback to deterministic key derived from settings.SECRET_KEY
        key_bytes = hashlib.sha256(settings.SECRET_KEY.encode('utf-8')).digest()
        base64_key = base64.urlsafe_b64encode(key_bytes)
        return Fernet(base64_key)

import hashlib
_fernet = _get_fernet_instance()

def encrypt_pii(plain_text: str | None) -> str | None:
    """Encrypts PII text using AES-256 (Fernet symmetric encryption)."""
    if plain_text is None:
        return None
    return _fernet.encrypt(plain_text.encode('utf-8')).decode('utf-8')

def decrypt_pii(cipher_text: str | None) -> str | None:
    """Decrypts PII cipher text back to plain text."""
    if cipher_text is None:
        return None
    try:
        return _fernet.decrypt(cipher_text.encode('utf-8')).decode('utf-8')
    except Exception:
        return "[Decryption Failed]"
