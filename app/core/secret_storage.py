import base64
import hashlib
import json

from cryptography.fernet import Fernet

from app.core.config import settings


def _cipher() -> Fernet:
    key = base64.urlsafe_b64encode(hashlib.sha256(settings.SECRET_KEY.encode()).digest())
    return Fernet(key)


def encrypt_json(value: dict) -> str:
    payload = json.dumps(value, separators=(",", ":")).encode()
    return _cipher().encrypt(payload).decode()


def decrypt_json(value: str) -> dict:
    return json.loads(_cipher().decrypt(value.encode()).decode())
