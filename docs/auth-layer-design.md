# Authentication and Authorization Layer Design

## Overview
This document details the authentication and authorization system for the RBAC-RAG application, providing comprehensive security controls while maintaining usability and performance.

## Authentication System

### 1. User Management Schema

```sql
-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    department VARCHAR(100),
    is_active BOOLEAN DEFAULT true,
    is_verified BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    last_login TIMESTAMP,
    failed_login_attempts INTEGER DEFAULT 0,
    locked_until TIMESTAMP
);

-- Roles table
CREATE TABLE roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    permissions JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- User-Role junction table
CREATE TABLE user_roles (
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    role_id UUID REFERENCES roles(id) ON DELETE CASCADE,
    assigned_by UUID REFERENCES users(id),
    assigned_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP,
    PRIMARY KEY (user_id, role_id)
);

-- Sessions table for token management
CREATE TABLE user_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    access_token_jti VARCHAR(255) UNIQUE NOT NULL,
    refresh_token_jti VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP NOT NULL,
    is_active BOOLEAN DEFAULT true,
    ip_address INET,
    user_agent TEXT
);
```

### 2. JWT Token Structure

```python
# Access Token Payload
{
    "sub": "user_id",  # Subject (user ID)
    "email": "user@example.com",
    "username": "john_doe",
    "roles": ["employee", "finance_viewer"],
    "permissions": ["read:documents", "query:rag"],
    "department": "finance",
    "jti": "access_token_id",  # JWT ID
    "iat": 1640995200,  # Issued at
    "exp": 1641081600,  # Expires at (24 hours)
    "iss": "rbac-rag-system",  # Issuer
    "aud": "rbac-rag-api"  # Audience
}

# Refresh Token Payload
{
    "sub": "user_id",
    "type": "refresh",
    "jti": "refresh_token_id",
    "iat": 1640995200,
    "exp": 1643587200,  # 30 days
    "iss": "rbac-rag-system",
    "aud": "rbac-rag-api"
}
```

### 3. Authentication Flow

```python
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
import secrets

app = FastAPI()
security = HTTPBearer()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthService:
    def __init__(self):
        self.secret_key = "your-secret-key-here"  # Use environment variable
        self.algorithm = "HS256"
        self.access_token_expire = timedelta(hours=24)
        self.refresh_token_expire = timedelta(days=30)
    
    def create_access_token(self, user_data: dict) -> str:
        """Create JWT access token"""
        to_encode = user_data.copy()
        expire = datetime.utcnow() + self.access_token_expire
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "jti": secrets.token_urlsafe(32),
            "iss": "rbac-rag-system",
            "aud": "rbac-rag-api"
        })
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
    
    def create_refresh_token(self, user_id: str) -> str:
        """Create JWT refresh token"""
        to_encode = {
            "sub": user_id,
            "type": "refresh",
            "exp": datetime.utcnow() + self.refresh_token_expire,
            "iat": datetime.utcnow(),
            "jti": secrets.token_urlsafe(32),
            "iss": "rbac-rag-system",
            "aud": "rbac-rag-api"
        }
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
    
    def verify_token(self, token: str) -> dict:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )
    
    def get_current_user(self, credentials: HTTPAuthorizationCredentials = Depends(security)):
        """Dependency to get current user from JWT token"""
        token = credentials.credentials
        payload = self.verify_token(token)
        
        # Check token type
        if payload.get("type") == "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )
        
        return payload

auth_service = AuthService()
```

### 4. Password Security

```python
class PasswordService:
    def __init__(self):
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.min_length = 8
        self.require_special = True
        self.require_numeric = True
        self.require_uppercase = True
    
    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        return self.pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        return self.pwd_context.verify(plain_password, hashed_password)
    
    def validate_password(self, password: str) -> bool:
        """Validate password strength"""
        if len(password) < self.min_length:
            return False
        
        if self.require_uppercase and not any(c.isupper() for c in password):
            return False
        
        if self.require_numeric and not any(c.isdigit() for c in password):
            return False
        
        if self.require_special and not any(c in "!@#$%^&*()_+-=" for c in password):
            return False
        
        return True
```

## Authorization System

### 1. Role Definitions

```python
# Role hierarchy and permissions
ROLE_HIERARCHY = {
    "admin": {
        "permissions": ["*"],  # All permissions
        "description": "System administrator with full access",
        "inherits": []
    },
    "manager": {
        "permissions": [
            "read:all_documents",
            "write:department_documents",
            "manage:team_members",
            "query:advanced_rag"
        ],
        "description": "Department manager with team oversight",
        "inherits": ["employee"]
    },
    "employee": {
        "permissions": [
            "read:public_documents",
            "read:department_documents",
            "write:personal_documents",
            "query:basic_rag"
        ],
        "description": "Regular employee with department access",
        "inherits": ["guest"]
    },
    "guest": {
        "permissions": [
            "read:public_documents",
            "query:basic_rag"
        ],
        "description": "Limited access for external users",
        "inherits": []
    }
}

# Document classification system
DOCUMENT_CLASSIFICATIONS = {
    "public": {
        "required_roles": ["*"],
        "description": "Publicly accessible documents"
    },
    "internal": {
        "required_roles": ["employee", "manager", "admin"],
        "description": "Internal company documents"
    },
    "confidential": {
        "required_roles": ["manager", "admin"],
        "description": "Sensitive business information"
    },
    "restricted": {
        "required_roles": ["admin"],
        "description": "Highly sensitive or regulatory documents"
    }
}
```

### 2. Permission-Based Access Control

```python
class AuthorizationService:
    def __init__(self):
        self.role_hierarchy = ROLE_HIERARCHY
        self.document_classifications = DOCUMENT_CLASSIFICATIONS
    
    def get_user_permissions(self, user_roles: list) -> set:
        """Get all permissions for user based on roles"""
        permissions = set()
        
        for role_name in user_roles:
            if role_name in self.role_hierarchy:
                role = self.role_hierarchy[role_name]
                
                # Add direct permissions
                if "*" in role["permissions"]:
                    return {"*"}  # Admin has all permissions
                permissions.update(role["permissions"])
                
                # Add inherited permissions
                for inherited_role in role.get("inherits", []):
                    inherited_perms = self.get_user_permissions([inherited_role])
                    permissions.update(inherited_perms)
        
        return permissions
    
    def check_permission(self, user_permissions: set, required_permission: str) -> bool:
        """Check if user has required permission"""
        if "*" in user_permissions:
            return True
        return required_permission in user_permissions
    
    def can_access_document(self, user_roles: list, document_classification: str, 
                          document_metadata: dict) -> bool:
        """Check if user can access specific document"""
        # Check classification-based access
        classification_config = self.document_classifications.get(document_classification)
        if classification_config:
            required_roles = classification_config["required_roles"]
            if "*" not in required_roles and not any(role in user_roles for role in required_roles):
                return False
        
        # Check metadata-based access (department, tags, etc.)
        document_roles = document_metadata.get("allowed_roles", [])
        if document_roles and "*" not in document_roles:
            if not any(role in user_roles for role in document_roles):
                return False
        
        # Check department-based access
        user_department = document_metadata.get("user_department")
        document_department = document_metadata.get("document_department")
        if document_department and user_department != document_department:
            # Check if user has cross-department access permission
            user_permissions = self.get_user_permissions(user_roles)
            if not self.check_permission(user_permissions, "read:all_departments"):
                return False
        
        return True

authorization_service = AuthorizationService()
```

### 3. Middleware Integration

```python
from functools import wraps
from fastapi import Request

class RBACMiddleware:
    def __init__(self, auth_service: AuthService, authz_service: AuthorizationService):
        self.auth_service = auth_service
        self.authz_service = authz_service
    
    async def __call__(self, request: Request, call_next):
        # Skip auth for public endpoints
        if request.url.path in ["/docs", "/openapi.json", "/health"]:
            response = await call_next(request)
            return response
        
        # Extract and verify token
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Missing or invalid authorization header")
        
        token = auth_header[7:]  # Remove "Bearer " prefix
        user_data = self.auth_service.verify_token(token)
        
        # Add user context to request
        request.state.user = user_data
        request.state.user_permissions = self.authz_service.get_user_permissions(user_data.get("roles", []))
        
        response = await call_next(request)
        return response

def require_permission(required_permission: str):
    """Decorator to require specific permission"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request = kwargs.get("request") or args[0]  # Assume first arg is request
            user_permissions = getattr(request.state, "user_permissions", set())
            
            if not authorization_service.check_permission(user_permissions, required_permission):
                raise HTTPException(
                    status_code=403,
                    detail=f"Insufficient permissions. Required: {required_permission}"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

def require_role(required_roles: list):
    """Decorator to require specific roles"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request = kwargs.get("request") or args[0]
            user_data = getattr(request.state, "user", {})
            user_roles = user_data.get("roles", [])
            
            if not any(role in user_roles for role in required_roles) and "*" not in required_roles:
                raise HTTPException(
                    status_code=403,
                    detail=f"Insufficient role. Required one of: {required_roles}"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator
```

### 4. API Endpoints

```python
from pydantic import BaseModel
from fastapi import APIRouter, Depends, Request

router = APIRouter()

class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int

@router.post("/auth/login", response_model=LoginResponse)
async def login(login_data: LoginRequest):
    """User login endpoint"""
    # Verify credentials (implement user lookup and password verification)
    user = await get_user_by_username(login_data.username)
    if not user or not verify_password(login_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Create tokens
    user_data = {
        "sub": str(user.id),
        "email": user.email,
        "username": user.username,
        "roles": await get_user_roles(user.id),
        "department": user.department
    }
    
    access_token = auth_service.create_access_token(user_data)
    refresh_token = auth_service.create_refresh_token(str(user.id))
    
    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=86400  # 24 hours
    )

@router.post("/auth/refresh")
async def refresh_token(refresh_token: str):
    """Token refresh endpoint"""
    payload = auth_service.verify_token(refresh_token)
    
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid token type")
    
    user_id = payload.get("sub")
    user = await get_user_by_id(user_id)
    
    user_data = {
        "sub": user_id,
        "email": user.email,
        "username": user.username,
        "roles": await get_user_roles(user_id),
        "department": user.department
    }
    
    new_access_token = auth_service.create_access_token(user_data)
    
    return {"access_token": new_access_token, "token_type": "bearer"}

@router.post("/auth/logout")
async def logout(request: Request):
    """User logout endpoint"""
    # Invalidate current session
    user_data = request.state.user
    await invalidate_user_session(user_data.get("jti"))
    
    return {"message": "Successfully logged out"}

@router.get("/auth/me")
async def get_current_user_info(request: Request):
    """Get current user information"""
    return {
        "user": request.state.user,
        "permissions": list(request.state.user_permissions)
    }
```

## Security Considerations

### 1. Token Security
- Use secure, random JWT secrets stored in environment variables
- Implement token rotation and blacklisting
- Set appropriate expiration times (short for access, longer for refresh)
- Store sensitive tokens in secure HTTP-only cookies when possible

### 2. Rate Limiting
```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)

@router.post("/auth/login")
@limiter.limit("5/minute")  # 5 attempts per minute
async def login(request: Request, login_data: LoginRequest):
    # Login implementation
    pass
```

### 3. Account Security
- Implement account lockout after failed attempts
- Require strong passwords
- Log security events
- Monitor for suspicious activities

### 4. Session Management
- Track active sessions per user
- Allow users to view and revoke sessions
- Implement session timeout
- Detect concurrent logins from different locations

This authentication and authorization layer provides comprehensive security while maintaining flexibility and performance for the RBAC-RAG system.