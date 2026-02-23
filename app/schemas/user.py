"""
用户相关的Pydantic模式
"""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, EmailStr, validator


class UserBase(BaseModel):
    """
    用户基础模式
    """
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    email: EmailStr = Field(..., description="邮箱")
    first_name: str = Field(..., min_length=1, max_length=50, description="名")
    last_name: str = Field(..., min_length=1, max_length=50, description="姓")
    phone: Optional[str] = Field(None, max_length=20, description="电话号码")
    employee_id: Optional[str] = Field(None, max_length=20, description="员工编号")
    department_id: Optional[int] = Field(None, description="部门ID")
    position: Optional[str] = Field(None, max_length=100, description="职位")
    role: Optional[str] = Field("employee", description="角色")
    is_active: Optional[bool] = Field(True, description="是否激活")
    
    @validator('full_name', pre=True, always=True)
    def set_full_name(cls, v, values):
        if 'first_name' in values and 'last_name' in values:
            return f"{values['first_name']} {values['last_name']}"
        return v


class UserCreate(UserBase):
    """
    用户创建模式
    """
    password: str = Field(..., min_length=6, max_length=100, description="密码")
    confirm_password: str = Field(..., description="确认密码")
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'password' in values and v != values['password']:
            raise ValueError('密码不匹配')
        return v


class UserRegister(BaseModel):
    """
    用户注册模式
    """
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    email: EmailStr = Field(..., description="邮箱")
    password: str = Field(..., min_length=6, max_length=100, description="密码")
    confirm_password: str = Field(..., description="确认密码")
    first_name: str = Field(..., min_length=1, max_length=50, description="名")
    last_name: str = Field(..., min_length=1, max_length=50, description="姓")
    phone: Optional[str] = Field(None, max_length=20, description="电话号码")
    employee_id: Optional[str] = Field(None, max_length=20, description="员工编号")
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'password' in values and v != values['password']:
            raise ValueError('密码不匹配')
        return v
    
    @validator('full_name', pre=True, always=True)
    def set_full_name(cls, v, values):
        if 'first_name' in values and 'last_name' in values:
            return f"{values['first_name']} {values['last_name']}"
        return v


class UserUpdate(BaseModel):
    """
    用户更新模式
    """
    email: Optional[EmailStr] = Field(None, description="邮箱")
    first_name: Optional[str] = Field(None, min_length=1, max_length=50, description="名")
    last_name: Optional[str] = Field(None, min_length=1, max_length=50, description="姓")
    phone: Optional[str] = Field(None, max_length=20, description="电话号码")
    department_id: Optional[int] = Field(None, description="部门ID")
    position: Optional[str] = Field(None, max_length=100, description="职位")
    role: Optional[str] = Field(None, description="角色")
    is_active: Optional[bool] = Field(None, description="是否激活")
    avatar: Optional[str] = Field(None, description="头像URL")
    notes: Optional[str] = Field(None, description="备注")


class UserChangePassword(BaseModel):
    """
    用户修改密码模式
    """
    current_password: str = Field(..., description="当前密码")
    new_password: str = Field(..., min_length=6, max_length=100, description="新密码")
    confirm_password: str = Field(..., description="确认新密码")
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('密码不匹配')
        return v


class UserLogin(BaseModel):
    """
    用户登录模式
    """
    username: str = Field(..., description="用户名或邮箱")
    password: str = Field(..., description="密码")
    remember_me: Optional[bool] = Field(False, description="记住我")


class UserFaceData(BaseModel):
    """
    用户人脸数据模式
    """
    face_image: str = Field(..., description="人脸图像Base64编码")
    face_encoding: Optional[str] = Field(None, description="人脸编码数据")


class UserResponse(UserBase):
    """
    用户响应模式
    """
    id: int = Field(..., description="用户ID")
    full_name: str = Field(..., description="全名")
    avatar: Optional[str] = Field(None, description="头像URL")
    status: Optional[str] = Field(None, description="状态")
    last_login: Optional[datetime] = Field(None, description="最后登录时间")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    class Config:
        orm_mode = True


class UserDetailResponse(UserResponse):
    """
    用户详情响应模式
    """
    department: Optional[dict] = Field(None, description="部门信息")
    failed_login_attempts: Optional[int] = Field(None, description="失败登录次数")
    locked_until: Optional[datetime] = Field(None, description="锁定到期时间")
    face_image_path: Optional[str] = Field(None, description="人脸图像路径")
    notes: Optional[str] = Field(None, description="备注")


class UserListResponse(BaseModel):
    """
    用户列表响应模式
    """
    users: List[UserResponse] = Field(..., description="用户列表")
    total: int = Field(..., description="总数量")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页数量")
    total_pages: int = Field(..., description="总页数")