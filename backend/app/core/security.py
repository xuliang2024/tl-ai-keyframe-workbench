import base64
from datetime import UTC, datetime, timedelta
import hashlib
import hmac
import json
import secrets
from typing import Any

from app.core.config import settings


def mask_secret(value: str) -> str:
    if not value:
        return ""
    if len(value) <= 8:
        return "****"
    return f"{value[:4]}****{value[-4:]}"


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 210_000)
    return f"pbkdf2_sha256$210000${_b64url_encode(salt)}${_b64url_encode(digest)}"


def verify_password(password: str, password_hash: str) -> bool:
    try:
        algorithm, iterations, salt, expected = password_hash.split("$", 3)
    except ValueError:
        return False
    if algorithm != "pbkdf2_sha256":
        return False

    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        _b64url_decode(salt),
        int(iterations),
    )
    return hmac.compare_digest(_b64url_encode(digest), expected)


def create_access_token(*, subject: str) -> str:
    now = datetime.now(UTC)
    expires_at = now + timedelta(minutes=settings.auth_access_token_expires_minutes)
    return _encode_token(
        {
            "sub": subject,
            "type": "access",
            "iat": int(now.timestamp()),
            "exp": int(expires_at.timestamp()),
        }
    )


def decode_access_token(token: str) -> dict[str, Any] | None:
    payload = _decode_token(token)
    if not payload or payload.get("type") != "access":
        return None
    return payload


def create_refresh_token() -> str:
    return secrets.token_urlsafe(48)


def create_mcp_token() -> str:
    return f"mcp_{secrets.token_urlsafe(48)}"


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def refresh_token_expires_at() -> datetime:
    return datetime.now(UTC) + timedelta(days=settings.auth_refresh_token_expires_days)


def _encode_token(payload: dict[str, Any]) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    header_part = _b64url_json(header)
    payload_part = _b64url_json(payload)
    signature = _sign(f"{header_part}.{payload_part}")
    return f"{header_part}.{payload_part}.{signature}"


def _decode_token(token: str) -> dict[str, Any] | None:
    parts = token.split(".")
    if len(parts) != 3:
        return None

    signing_input = f"{parts[0]}.{parts[1]}"
    expected_signature = _sign(signing_input)
    if not hmac.compare_digest(expected_signature, parts[2]):
        return None

    try:
        payload = json.loads(_b64url_decode(parts[1]))
    except (ValueError, json.JSONDecodeError):
        return None

    exp = payload.get("exp")
    if not isinstance(exp, int) or exp <= int(datetime.now(UTC).timestamp()):
        return None
    return payload


def _sign(value: str) -> str:
    digest = hmac.new(
        settings.auth_secret_key.encode("utf-8"),
        value.encode("utf-8"),
        hashlib.sha256,
    ).digest()
    return _b64url_encode(digest)


def _b64url_json(value: dict[str, Any]) -> str:
    return _b64url_encode(json.dumps(value, separators=(",", ":")).encode("utf-8"))


def _b64url_encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _b64url_decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)
