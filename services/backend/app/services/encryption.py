import base64
import hashlib
from cryptography.fernet import Fernet
from app.config import settings

def _get_fernet_instance() -> Fernet:
    key_str = settings.FERNET_KEY
    try:
        key_bytes = key_str.encode('utf-8')
        # Validate Fernet key format (must be 32 bytes base64 decoded)
        decoded = base64.urlsafe_b64decode(key_bytes)
        if len(decoded) != 32:
            raise ValueError(f"Fernet key must decode to 32 bytes, got {len(decoded)}")
        return Fernet(key_bytes)
    except Exception as e:
        if settings.ENV == "prod":
            raise RuntimeError(f"CRITICAL: Invalid FERNET_KEY in production environment: {e}")
        # Fallback for dev mode
        key_bytes = hashlib.sha256(settings.SECRET_KEY.encode('utf-8')).digest()
        base64_key = base64.urlsafe_b64encode(key_bytes)
        return Fernet(base64_key)

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
