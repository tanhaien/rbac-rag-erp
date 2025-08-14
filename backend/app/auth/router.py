from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt

from .schemas import LoginRequest, Token, MeResponse
from .service import auth_service
from ..core.config import get_settings

security = HTTPBearer()
router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=Token)
def login(payload: LoginRequest) -> Token:
    # Placeholder: accept any username/password for now
    if not payload.username or not payload.password:
        raise HTTPException(status_code=400, detail="Missing credentials")

    access_token = auth_service.create_access_token(subject=payload.username)
    return Token(access_token=access_token)


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
