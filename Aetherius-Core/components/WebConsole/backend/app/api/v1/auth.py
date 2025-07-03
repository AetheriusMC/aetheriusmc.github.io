"""
Authentication API endpoints.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer
from pydantic import BaseModel, Field, EmailStr

from ...core.container import get_container
from ...utils.security import (
    create_access_token, get_current_user,
    verify_password, get_password_hash
)
from ...models.simple_models import User
from ...services.database import DatabaseService

logger = logging.getLogger(__name__)

router = APIRouter()
security = HTTPBearer()


# Request/Response Models
class LoginRequest(BaseModel):
    """Login request model."""
    username: str = Field(..., description="Username or email")
    password: str = Field(..., description="Password")
    remember_me: bool = Field(False, description="Remember login")


class LoginResponse(BaseModel):
    """Login response model."""
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(..., description="Token type")
    expires_in: int = Field(..., description="Token expiration time in seconds")
    user: Dict[str, Any] = Field(..., description="User information")


class RegisterRequest(BaseModel):
    """Registration request model."""
    username: str = Field(..., min_length=3, max_length=50, description="Username")
    email: EmailStr = Field(..., description="Email address")
    password: str = Field(..., min_length=8, description="Password")
    full_name: Optional[str] = Field(None, max_length=100, description="Full name")


class UserResponse(BaseModel):
    """User response model."""
    id: int = Field(..., description="User ID")
    username: str = Field(..., description="Username")
    email: str = Field(..., description="Email address")
    full_name: Optional[str] = Field(None, description="Full name")
    is_active: bool = Field(..., description="User active status")
    is_admin: bool = Field(..., description="Admin status")
    roles: list = Field(..., description="User roles")
    created_at: str = Field(..., description="Account creation timestamp")
    last_login: Optional[str] = Field(None, description="Last login timestamp")


class PasswordChangeRequest(BaseModel):
    """Password change request model."""
    current_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=8, description="New password")


class ProfileUpdateRequest(BaseModel):
    """Profile update request model."""
    full_name: Optional[str] = Field(None, max_length=100, description="Full name")
    email: Optional[EmailStr] = Field(None, description="Email address")


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """
    用户登录。
    
    验证用户凭据并返回访问令牌。
    """
    try:
        # Get database service
        container = get_container()
        db_service = await container.get_service(DatabaseService)
        
        # Authenticate user and update login time
        async with db_service.session() as session:
            from sqlalchemy import select, or_
            
            # Find user by username or email
            result = await session.execute(
                select(User).where(
                    or_(
                        User.username == request.username,
                        User.email == request.username
                    )
                )
            )
            user = result.scalar_one_or_none()
            
            # Verify user exists and password is correct
            # Handle both BCrypt and SHA256 hashes for backward compatibility
            password_valid = False
            if user:
                try:
                    # Try BCrypt first
                    password_valid = verify_password(request.password, user.password_hash)
                except Exception:
                    # Fallback to SHA256 for compatibility
                    import hashlib
                    sha256_hash = hashlib.sha256(request.password.encode()).hexdigest()
                    password_valid = sha256_hash == user.password_hash
            
            if not user or not password_valid:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="用户名或密码错误",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            if not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="账户已被禁用",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            # Create access token
            expires_delta = timedelta(days=7) if request.remember_me else timedelta(hours=1)
            access_token = create_access_token(
                data={"sub": str(user.id)}, 
                expires_delta=expires_delta
            )
            
            # Update last login time
            user.last_login = datetime.utcnow()
            session.add(user)
            await session.commit()
            
            # Prepare user data for response (simplified to avoid relationship issues)
            user_data = {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role,  # Use simple role field instead of roles relationship
                "is_active": user.is_active,
                "created_at": user.created_at.isoformat(),
                "last_login": user.last_login.isoformat() if user.last_login else None
            }
        
        logger.info(f"User {user_data['username']} logged in successfully")
        
        return LoginResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=int(expires_delta.total_seconds()),
            user=user_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="登录过程中发生错误"
        )


@router.post("/register", response_model=UserResponse)
async def register(request: RegisterRequest):
    """
    用户注册。
    
    创建新用户账户。需要系统允许注册功能。
    """
    try:
        from ...core.config import settings
        
        # Check if registration is enabled
        if not settings.security.allow_registration:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="系统不允许新用户注册"
            )
        
        async with get_async_session() as session:
            # Check if username already exists
            from sqlalchemy import select
            existing_user = await session.execute(
                select(User).where(User.username == request.username)
            )
            if existing_user.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="用户名已存在"
                )
            
            # Check if email already exists
            existing_email = await session.execute(
                select(User).where(User.email == request.email)
            )
            if existing_email.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="邮箱地址已被使用"
                )
            
            # Create new user
            user = User(
                username=request.username,
                email=request.email,
                full_name=request.full_name,
                password_hash=get_password_hash(request.password),
                is_active=True,
                is_admin=False,
                created_at=datetime.utcnow()
            )
            
            session.add(user)
            await session.commit()
            await session.refresh(user)
            
            logger.info(f"New user registered: {user.username}")
            
            return UserResponse(
                id=user.id,
                username=user.username,
                email=user.email,
                full_name=user.full_name,
                is_active=user.is_active,
                is_admin=user.is_admin,
                roles=[],
                created_at=user.created_at.isoformat(),
                last_login=None
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="注册过程中发生错误"
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    获取当前用户信息。
    
    返回当前登录用户的详细信息。
    """
    try:
        return UserResponse(**current_user)
    except Exception as e:
        logger.error(f"Failed to get user info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取用户信息失败"
        )


@router.put("/me", response_model=UserResponse)
async def update_profile(
    request: ProfileUpdateRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    更新用户资料。
    
    允许用户更新自己的基本信息。
    """
    try:
        async with get_async_session() as session:
            from sqlalchemy import select
            
            # Get user from database
            result = await session.execute(
                select(User).where(User.id == current_user["id"])
            )
            user = result.scalar_one_or_none()
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="用户不存在"
                )
            
            # Update user information
            if request.full_name is not None:
                user.full_name = request.full_name
            
            if request.email is not None:
                # Check if email is already used by another user
                existing_email = await session.execute(
                    select(User).where(User.email == request.email, User.id != user.id)
                )
                if existing_email.scalar_one_or_none():
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="邮箱地址已被其他用户使用"
                    )
                user.email = request.email
            
            user.updated_at = datetime.utcnow()
            await session.commit()
            await session.refresh(user)
            
            logger.info(f"User {user.username} updated profile")
            
            return UserResponse(
                id=user.id,
                username=user.username,
                email=user.email,
                full_name=user.full_name,
                is_active=user.is_active,
                is_admin=user.is_admin,
                roles=[role.name for role in user.roles],
                created_at=user.created_at.isoformat(),
                last_login=user.last_login.isoformat() if user.last_login else None
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Profile update failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新资料过程中发生错误"
        )


@router.post("/change-password")
async def change_password(
    request: PasswordChangeRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    修改密码。
    
    用户可以修改自己的登录密码。
    """
    try:
        async with get_async_session() as session:
            from sqlalchemy import select
            
            # Get user from database
            result = await session.execute(
                select(User).where(User.id == current_user["id"])
            )
            user = result.scalar_one_or_none()
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="用户不存在"
                )
            
            # Verify current password
            if not verify_password(request.current_password, user.password_hash):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="当前密码错误"
                )
            
            # Update password
            user.password_hash = get_password_hash(request.new_password)
            user.updated_at = datetime.utcnow()
            await session.commit()
            
            logger.info(f"User {user.username} changed password")
            
            return {
                "success": True,
                "message": "密码修改成功",
                "timestamp": datetime.now().isoformat()
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Password change failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="密码修改过程中发生错误"
        )


@router.post("/logout")
async def logout(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    用户登出。
    
    登出当前用户会话。注意：JWT 令牌在服务端是无状态的，
    客户端需要删除本地存储的令牌。
    """
    try:
        logger.info(f"User {current_user['username']} logged out")
        
        return {
            "success": True,
            "message": "登出成功",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Logout failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="登出过程中发生错误"
        )


@router.post("/refresh")
async def refresh_token(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    刷新访问令牌。
    
    为当前用户生成新的访问令牌。
    """
    try:
        # Create new access token
        access_token = create_access_token(
            data={"sub": str(current_user["id"])},
            expires_delta=timedelta(hours=1)
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": 3600,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Token refresh failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="令牌刷新过程中发生错误"
        )