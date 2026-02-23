"""
认证服务模块
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
import secrets

from app.core.config import get_settings
from app.core.security import verify_password, get_password_hash
from app.models.user import User, UserRole, UserStatus
from app.schemas.auth import TokenData
from app.schemas.user import UserCreate, UserLogin, UserChangePassword
from app.services.system_log_service import SystemLogService

settings = get_settings()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    """
    认证服务类
    """
    
    @staticmethod
    def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
        """
        验证用户凭据
        
        Args:
            db: 数据库会话
            username: 用户名
            password: 密码
            
        Returns:
            验证成功返回用户对象，失败返回None
        """
        user = db.query(User).filter(User.username == username).first()
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        if user.status != UserStatus.ACTIVE:
            return None
        return user
    
    @staticmethod
    def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """
        创建访问令牌
        
        Args:
            data: 令牌数据
            expires_delta: 过期时间增量
            
        Returns:
            JWT访问令牌
        """
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def create_refresh_token(data: Dict[str, Any]) -> str:
        """
        创建刷新令牌
        
        Args:
            data: 令牌数据
            
        Returns:
            JWT刷新令牌
        """
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        to_encode.update({"exp": expire, "type": "refresh"})
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def verify_token(token: str) -> Optional[TokenData]:
        """
        验证令牌
        
        Args:
            token: JWT令牌
            
        Returns:
            令牌数据，验证失败返回None
        """
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            username: str = payload.get("sub")
            if username is None:
                return None
            token_data = TokenData(username=username)
            return token_data
        except JWTError:
            return None
    
    @staticmethod
    def get_current_user(db: Session, token: str) -> User:
        """
        获取当前用户
        
        Args:
            db: 数据库会话
            token: JWT令牌
            
        Returns:
            当前用户对象
            
        Raises:
            HTTPException: 认证失败时抛出异常
        """
        token_data = AuthService.verify_token(token)
        if token_data is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的认证凭据",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        user = db.query(User).filter(User.username == token_data.username).first()
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户不存在",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user
    
    @staticmethod
    def get_current_active_user(current_user: User) -> User:
        """
        获取当前活跃用户
        
        Args:
            current_user: 当前用户
            
        Returns:
            当前活跃用户对象
            
        Raises:
            HTTPException: 用户未激活时抛出异常
        """
        if current_user.status != UserStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户账户未激活"
            )
        return current_user
    
    @staticmethod
    def register_user(db: Session, user: UserCreate) -> User:
        """
        用户注册
        
        Args:
            db: 数据库会话
            user: 用户创建数据
            
        Returns:
            创建的用户对象
            
        Raises:
            HTTPException: 用户名已存在时抛出异常
        """
        # 检查用户名是否已存在
        db_user = db.query(User).filter(User.username == user.username).first()
        if db_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户名已存在"
            )
        
        # 检查邮箱是否已存在
        db_user = db.query(User).filter(User.email == user.email).first()
        if db_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="邮箱已存在"
            )
        
        # 创建新用户
        hashed_password = get_password_hash(user.password)
        db_user = User(
            username=user.username,
            email=user.email,
            hashed_password=hashed_password,
            full_name=user.full_name,
            role=user.role if user.role else UserRole.EMPLOYEE,
            status=UserStatus.ACTIVE
        )
        
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        # 记录系统日志
        SystemLogService.log_user_action(
            db=db,
            user_id=db_user.id,
            action="用户注册",
            details=f"用户 {user.username} 注册成功"
        )
        
        return db_user
    
    @staticmethod
    def login_user(db: Session, user_login: UserLogin) -> Dict[str, Any]:
        """
        用户登录
        
        Args:
            db: 数据库会话
            user_login: 用户登录数据
            
        Returns:
            包含访问令牌和刷新令牌的字典
            
        Raises:
            HTTPException: 登录失败时抛出异常
        """
        user = AuthService.authenticate_user(db, user_login.username, user_login.password)
        if not user:
            # 记录登录失败
            SystemLogService.log_security_event(
                db=db,
                event="登录失败",
                details=f"用户名: {user_login.username}, IP地址: {user_login.ip_address}"
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名或密码错误",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # 创建访问令牌和刷新令牌
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = AuthService.create_access_token(
            data={"sub": user.username}, expires_delta=access_token_expires
        )
        refresh_token = AuthService.create_refresh_token(data={"sub": user.username})
        
        # 更新用户最后登录时间
        user.last_login_at = datetime.utcnow()
        db.commit()
        
        # 记录登录成功
        SystemLogService.log_user_action(
            db=db,
            user_id=user.id,
            action="用户登录",
            details=f"用户 {user.username} 登录成功"
        )
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        }
    
    @staticmethod
    def refresh_access_token(refresh_token: str) -> Dict[str, Any]:
        """
        刷新访问令牌
        
        Args:
            refresh_token: 刷新令牌
            
        Returns:
            包含新访问令牌的字典
            
        Raises:
            HTTPException: 刷新令牌无效时抛出异常
        """
        try:
            payload = jwt.decode(refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            username: str = payload.get("sub")
            token_type: str = payload.get("type")
            
            if username is None or token_type != "refresh":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="无效的刷新令牌"
                )
            
            # 创建新的访问令牌
            access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
            access_token = AuthService.create_access_token(
                data={"sub": username}, expires_delta=access_token_expires
            )
            
            return {
                "access_token": access_token,
                "token_type": "bearer",
                "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
            }
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的刷新令牌"
            )
    
    @staticmethod
    def change_password(db: Session, user_id: int, password_data: UserChangePassword) -> bool:
        """
        修改密码
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            password_data: 密码修改数据
            
        Returns:
            修改成功返回True
            
        Raises:
            HTTPException: 原密码错误时抛出异常
        """
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        # 验证原密码
        if not verify_password(password_data.old_password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="原密码错误"
            )
        
        # 更新密码
        user.hashed_password = get_password_hash(password_data.new_password)
        user.password_changed_at = datetime.utcnow()
        db.commit()
        
        # 记录系统日志
        SystemLogService.log_user_action(
            db=db,
            user_id=user_id,
            action="修改密码",
            details="用户成功修改密码"
        )
        
        return True
    
    @staticmethod
    def reset_password(db: Session, email: str) -> bool:
        """
        重置密码
        
        Args:
            db: 数据库会话
            email: 用户邮箱
            
        Returns:
            重置成功返回True
            
        Raises:
            HTTPException: 用户不存在时抛出异常
        """
        user = db.query(User).filter(User.email == email).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        # 生成临时密码
        temp_password = secrets.token_urlsafe(12)
        user.hashed_password = get_password_hash(temp_password)
        user.password_changed_at = datetime.utcnow()
        db.commit()
        
        # 记录系统日志
        SystemLogService.log_user_action(
            db=db,
            user_id=user.id,
            action="重置密码",
            details=f"用户密码已重置，临时密码: {temp_password}"
        )
        
        # 这里应该发送邮件通知用户临时密码
        # TODO: 实现邮件发送功能
        
        return True