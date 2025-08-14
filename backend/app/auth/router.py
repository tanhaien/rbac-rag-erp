from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt

from sqlalchemy.orm import Session

from .schemas import LoginRequest, Token, MeResponse, RegisterRequest, RegisterResponse
from .service import auth_service
from ..core.config import get_settings
from ..core.db import db_dependency
from .models import User

security = HTTPBearer()
router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=Token)
def login(payload: LoginRequest) -> Token:
    # Placeholder: accept any username/password for now
    if not payload.username or not payload.password:
        raise HTTPException(status_code=400, detail="Missing credentials")

    access_token = auth_service.create_access_token(subject=payload.username)
    return Token(access_token=access_token)


@router.post("/register", response_model=RegisterResponse)
def register(payload: RegisterRequest, db: Session = Depends(db_dependency)) -> RegisterResponse:
    # Ensure unique username/email
    if db.query(User).filter((User.username == payload.username) | (User.email == payload.email)).first():
        raise HTTPException(status_code=409, detail="User already exists")

    hashed = auth_service.hash_password(payload.password)
    user = User(email=payload.email, username=payload.username, password_hash=hashed)
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
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    username = data.get("sub")
    if not username:
        raise HTTPException(status_code=401, detail="Invalid token subject")

    # Placeholder user profile; in future, fetch from DB
    return MeResponse(id=1, email="user@example.com", username=username)


@router.post("/refresh", response_model=Token)
def refresh(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Token:
    """Issue a new access token from a valid (but soon-to-expire) access token.
    In future, switch to long-lived refresh tokens persisted in DB.
    """
    settings = get_settings()
    token = credentials.credentials
    try:
        data = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    sub = data.get("sub")
    if not sub:
        raise HTTPException(status_code=401, detail="Invalid token subject")

    new_token = auth_service.create_access_token(subject=sub)
    return Token(access_token=new_token)
