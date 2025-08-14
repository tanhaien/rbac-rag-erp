from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import jwt
from passlib.context import CryptContext

from ..core.config import get_settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.algorithm = "HS256"
        self.access_token_minutes = 60 * 24  # 24h

    def hash_password(self, password: str) -> str:
        return pwd_context.hash(password)

    def verify_password(self, plain: str, hashed: str) -> bool:
        return pwd_context.verify(plain, hashed)

    def create_access_token(self, subject: str, extra: Optional[dict] = None) -> str:
        now = datetime.now(timezone.utc)
        payload = {
            "sub": subject,
            "iat": int(now.timestamp()),
            "exp": int(
                (now + timedelta(minutes=self.access_token_minutes)).timestamp()
            ),
        }
        if extra:
            payload.update(extra)
        token = jwt.encode(payload, self.settings.secret_key, algorithm=self.algorithm)
        return token

    def generate_refresh_token(self) -> str:
        return secrets.token_urlsafe(48)


auth_service = AuthService()
