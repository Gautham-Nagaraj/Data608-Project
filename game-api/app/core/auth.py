import base64
import json
from typing import Any, Dict, Optional

from itsdangerous import Signer, BadSignature
from passlib.context import CryptContext

from app.core.config import settings

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# Hash and verify passwords

def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


# Signed cookie management
_signer = Signer(settings.SECRET_KEY)


def create_signed_cookie(data: Dict[str, Any]) -> str:
    payload = json.dumps(data)
    signed = _signer.sign(payload.encode())
    return base64.urlsafe_b64encode(signed).decode()


def validate_signed_cookie(cookie_val: str) -> Optional[Dict[str, Any]]:
    """
    Validate a signed cookie and return its contents.
    Returns None if the cookie is invalid or malformed.
    """
    try:
        signed = base64.urlsafe_b64decode(cookie_val.encode())
        unsigned = _signer.unsign(signed)
        return json.loads(unsigned.decode())
    except (ValueError, BadSignature, json.JSONDecodeError, Exception):
        # Return None for any invalid cookie format
        return None
