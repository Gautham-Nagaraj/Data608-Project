import base64
import json
import warnings
import sys
import io
import contextlib
from typing import Any, Dict, Optional

from itsdangerous import Signer, BadSignature
from passlib.context import CryptContext

from app.core.config import settings

# Suppress the bcrypt version warning by temporarily redirecting stderr
# This is a known compatibility issue between passlib 1.7.4 and bcrypt 4.x
@contextlib.contextmanager
def suppress_bcrypt_warning():
    original_stderr = sys.stderr
    sys.stderr = io.StringIO()
    try:
        yield
    finally:
        sys.stderr = original_stderr

# Initialize password context with warning suppression
with suppress_bcrypt_warning():
    pwd_context = CryptContext(
        schemes=["bcrypt"], 
        deprecated="auto",
        bcrypt__rounds=12
    )


# Hash and verify passwords

def hash_password(password: str) -> str:
    with suppress_bcrypt_warning():
        return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    with suppress_bcrypt_warning():
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
