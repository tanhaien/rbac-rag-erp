from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from ..cerbos.client import cerbos_client
from ..core.config import get_settings
from ..core.db import db_dependency
from .models import RefreshToken, Role, User
from .schemas import (
    LoginRequest,
    MeResponse,
    RegisterRequest,
    RegisterResponse,
    Token,
    TokenPair,
)
from .service import auth_service

security = HTTPBearer()
router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenPair)
def login(
    payload: LoginRequest, db: Session | None = Depends(lambda: None)
) -> TokenPair:
    # Placeholder: accept any username/password for now
    if not payload.username or not payload.password:
        raise HTTPException(status_code=400, detail="Missing credentials")

    claims = {}
    # If DB available, fetch roles for user and include in claims
    if db is not None:
        user = db.query(User).filter(User.username == payload.username).first()
        if user:
            if not auth_service.verify_password(payload.password, user.password_hash):
                raise HTTPException(status_code=401, detail="Invalid credentials")
        if user and user.roles:
            claims["roles"] = [r.name for r in user.roles]

    access_token = auth_service.create_access_token(
        subject=payload.username, extra=claims or None
    )
    refresh_value: str | None = None
    # If DB available, also issue/persist a refresh token
    if db is not None and user:
        rt_value = auth_service.generate_refresh_token()
        rt = RefreshToken(
            user_id=user.id,
            token=rt_value,
            expires_at=datetime.now(timezone.utc) + timedelta(days=14),
        )
        db.add(rt)
        refresh_value = rt_value
    return TokenPair(access_token=access_token, refresh_token=refresh_value)


@router.post("/register", response_model=RegisterResponse)
def register(
    payload: RegisterRequest, db: Session = Depends(db_dependency)
) -> RegisterResponse:
    # Ensure unique username/email
    if (
        db.query(User)
        .filter((User.username == payload.username) | (User.email == payload.email))
        .first()
    ):
        raise HTTPException(status_code=409, detail="User already exists")

    hashed = auth_service.hash_password(payload.password)
    user = User(email=payload.email, username=payload.username, password_hash=hashed)
    # Assign default 'user' role if exists, else create
    role = db.query(Role).filter(Role.name == "user").first()
    if role is None:
        role = Role(name="user", description="Default user role")
        db.add(role)
        db.flush()
    user.roles.append(role)
    db.add(user)
    db.flush()
    return RegisterResponse(id=user.id, email=user.email, username=user.username)


@router.get("/me", response_model=MeResponse)
def me(credentials: HTTPAuthorizationCredentials = Depends(security)) -> MeResponse:
    settings = get_settings()
    token = credentials.credentials
    try:
        data = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )

    username = data.get("sub")
    if not username:
        raise HTTPException(status_code=401, detail="Invalid token subject")

    # Placeholder user profile; in future, fetch from DB
    return MeResponse(id=1, email="user@example.com", username=username)


@router.post("/refresh", response_model=Token)
def refresh(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session | None = Depends(lambda: None),
) -> Token:
    """Issue a new access token from a stored refresh token if DB available; else from access token (legacy)."""
    settings = get_settings()
    raw = credentials.credentials
    if db is not None:
        # Treat provided token as refresh token
        rt = (
            db.query(RefreshToken)
            .filter(RefreshToken.token == raw, RefreshToken.revoked == False)
            .first()
        )
        if not rt:
            raise HTTPException(status_code=401, detail="Invalid refresh token")
        if rt.expires_at < datetime.now(timezone.utc):
            raise HTTPException(status_code=401, detail="Refresh token expired")
        user = db.get(User, rt.user_id)
        claims = (
            {"roles": [r.name for r in user.roles]} if user and user.roles else None
        )
        return Token(
            access_token=auth_service.create_access_token(
                subject=user.username, extra=claims
            )
        )
    # Legacy path: parse as access token
    try:
        data = jwt.decode(raw, settings.secret_key, algorithms=["HS256"])
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )
    sub = data.get("sub")
    if not sub:
        raise HTTPException(status_code=401, detail="Invalid token subject")
    new_token = auth_service.create_access_token(subject=sub)
    return Token(access_token=new_token)


@router.post("/revoke")
def revoke_refresh_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session | None = Depends(lambda: None),
) -> dict:
    """Revoke a refresh token. If DB available, marks token as revoked; else returns success."""
    if db is None:
        # Without DB, we can't track revocation, but return success for compatibility
        return {"message": "Token revoked (no persistence)"}

    raw = credentials.credentials
    rt = db.query(RefreshToken).filter(RefreshToken.token == raw).first()
    if rt:
        rt.revoked = True
        db.commit()
        return {"message": "Token revoked successfully"}
    else:
        # Token not found, but return success to avoid information leakage
        return {"message": "Token revoked successfully"}


@router.get("/demo-protected")
def demo_protected(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    settings = get_settings()
    token = credentials.credentials
    try:
        data = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )

    # roles from claims if present, else heuristic
    username = data.get("sub", "user")
    roles = data.get("roles") or (
        ["admin"] if username.endswith("-admin") else ["user"]
    )
    allowed = cerbos_client.authorize(roles, resource="demo", action="read")
    if not allowed:
        raise HTTPException(status_code=403, detail="Forbidden by policy")
    return {"ok": True, "roles": roles}
