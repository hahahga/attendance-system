"""
认证API接口
"""

from datetime import timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app import schemas
from app.api import deps
from app.core import security
from app.core.config import settings
from app.services.auth_service import AuthService

router = APIRouter()


@router.post("/login", response_model=schemas.Token)
def login_for_access_token(
    db: Session = Depends(deps.get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """
    OAuth2兼容的令牌登录接口，获取访问令牌
    """
    user = AuthService.authenticate(
        db, username=form_data.username, password=form_data.password
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码不正确",
            headers={"WWW-Authenticate": "Bearer"},
        )
    elif not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户账户已被禁用"
        )

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    access_token = security.create_access_token(
        subject=user.id, expires_delta=access_token_expires
    )
    refresh_token = security.create_refresh_token(
        subject=user.id, expires_delta=refresh_token_expires
    )

    # 记录登录日志
    AuthService.log_login(db, user.id, "用户登录")

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }


@router.post("/refresh", response_model=schemas.Token)
def refresh_access_token(
    refresh_data: schemas.RefreshToken,
    db: Session = Depends(deps.get_db)
) -> Any:
    """
    使用刷新令牌获取新的访问令牌
    """
    try:
        payload = security.decode_refresh_token(refresh_data.refresh_token)
        user_id: int = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的刷新令牌"
            )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的刷新令牌"
        )

    user = AuthService.get_user_by_id(db, user_id=user_id)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在或已被禁用"
        )

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        subject=user.id, expires_delta=access_token_expires
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_data.refresh_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }


@router.post("/register", response_model=schemas.UserResponse)
def register(
    *,
    db: Session = Depends(deps.get_db),
    user_in: schemas.UserRegister
) -> Any:
    """
    用户注册接口
    """
    user = AuthService.get_user_by_username(db, username=user_in.username)
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在"
        )
    
    user = AuthService.get_user_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="邮箱已存在"
        )
    
    user = AuthService.register(db, user_in)
    
    # 记录注册日志
    AuthService.log_register(db, user.id, "用户注册")
    
    return user


@router.post("/change-password", response_model=schemas.Msg)
def change_password(
    *,
    db: Session = Depends(deps.get_db),
    password_data: schemas.UserChangePassword,
    current_user: schemas.UserResponse = Depends(deps.get_current_active_user)
) -> Any:
    """
    修改密码接口
    """
    if not AuthService.verify_password(
        password_data.current_password, current_user.hashed_password
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="当前密码不正确"
        )
    
    if password_data.new_password != password_data.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="新密码与确认密码不匹配"
        )
    
    AuthService.change_password(
        db, user_id=current_user.id, new_password=password_data.new_password
    )
    
    # 记录修改密码日志
    AuthService.log_password_change(db, current_user.id, "用户修改密码")
    
    return {"msg": "密码修改成功"}


@router.post("/reset-password", response_model=schemas.Msg)
def reset_password(
    *,
    db: Session = Depends(deps.get_db),
    email_data: schemas.UserResetPassword
) -> Any:
    """
    重置密码接口
    """
    user = AuthService.get_user_by_email(db, email=email_data.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 生成重置令牌
    reset_token = AuthService.generate_password_reset_token(email=email_data.email)
    
    # 发送重置密码邮件
    AuthService.send_password_reset_email(
        email_to=email_data.email, token=reset_token
    )
    
    # 记录重置密码请求日志
    AuthService.log_password_reset_request(db, user.id, "用户请求重置密码")
    
    return {"msg": "重置密码链接已发送到您的邮箱"}


@router.post("/confirm-reset-password", response_model=schemas.Msg)
def confirm_reset_password(
    *,
    db: Session = Depends(deps.get_db),
    reset_data: schemas.UserConfirmResetPassword
) -> Any:
    """
    确认重置密码接口
    """
    email = AuthService.verify_password_reset_token(reset_data.token)
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效或已过期的重置令牌"
        )
    
    user = AuthService.get_user_by_email(db, email=email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    if reset_data.new_password != reset_data.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="新密码与确认密码不匹配"
        )
    
    AuthService.change_password(
        db, user_id=user.id, new_password=reset_data.new_password
    )
    
    # 记录重置密码确认日志
    AuthService.log_password_reset_confirm(db, user.id, "用户确认重置密码")
    
    return {"msg": "密码重置成功"}


@router.get("/me", response_model=schemas.UserResponse)
def read_current_user(
    current_user: schemas.UserResponse = Depends(deps.get_current_active_user)
) -> Any:
    """
    获取当前用户信息
    """
    return current_user


@router.post("/logout", response_model=schemas.Msg)
def logout(
    current_user: schemas.UserResponse = Depends(deps.get_current_active_user),
    db: Session = Depends(deps.get_db)
) -> Any:
    """
    用户登出接口
    """
    # 记录登出日志
    AuthService.log_logout(db, current_user.id, "用户登出")
    
    return {"msg": "登出成功"}