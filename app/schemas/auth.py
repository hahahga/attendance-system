"""
认证相关的Pydantic模式
"""

from typing import Optional
from pydantic import BaseModel, Field


class Token(BaseModel):
    """
    令牌模式
    """
    access_token: str = Field(..., description="访问令牌")
    refresh_token: str = Field(..., description="刷新令牌")
    token_type: str = Field(default="bearer", description="令牌类型")
    expires_in: int = Field(..., description="令牌过期时间（秒）")


class TokenData(BaseModel):
    """
    令牌数据模式
    """
    username: Optional[str] = Field(None, description="用户名")
    user_id: Optional[int] = Field(None, description="用户ID")
    role: Optional[str] = Field(None, description="用户角色")


class RefreshToken(BaseModel):
    """
    刷新令牌模式
    """
    refresh_token: str = Field(..., description="刷新令牌")