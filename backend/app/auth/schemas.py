from pydantic import BaseModel, EmailStr


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str | None = None
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    username: str
    password: str


class MeResponse(BaseModel):
    id: int
    email: EmailStr
    username: str


class RegisterRequest(BaseModel):
    email: EmailStr
    username: str
    password: str


class RegisterResponse(BaseModel):
    id: int
    email: EmailStr
    username: str
