"""
用户数据模型
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Enum
from sqlalchemy.orm import relationship
import enum

from .base import BaseModel


class UserRole(enum.Enum):
    """用户角色枚举"""
    ADMIN = "admin"           # 系统管理员
    HR = "hr"                 # 人事管理员
    MANAGER = "manager"       # 部门主管
    EMPLOYEE = "employee"     # 普通员工


class UserStatus(enum.Enum):
    """用户状态枚举"""
    ACTIVE = "active"         # 活跃
    INACTIVE = "inactive"     # 非活跃
    SUSPENDED = "suspended"   # 暂停
    TERMINATED = "terminated" # 已离职


class User(BaseModel):
    """
    用户模型
    """
    __tablename__ = "users"
    
    # 基本信息
    username = Column(String(50), unique=True, index=True, nullable=False, comment="用户名")
    email = Column(String(100), unique=True, index=True, nullable=False, comment="邮箱")
    password_hash = Column(String(255), nullable=False, comment="密码哈希")
    
    # 个人信息
    first_name = Column(String(50), nullable=False, comment="名")
    last_name = Column(String(50), nullable=False, comment="姓")
    full_name = Column(String(100), nullable=False, comment="全名")
    phone = Column(String(20), nullable=True, comment="电话号码")
    avatar = Column(String(255), nullable=True, comment="头像URL")
    
    # 工作信息
    employee_id = Column(String(20), unique=True, index=True, nullable=True, comment="员工编号")
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True, comment="部门ID")
    position = Column(String(100), nullable=True, comment="职位")
    role = Column(Enum(UserRole), default=UserRole.EMPLOYEE, nullable=False, comment="角色")
    status = Column(Enum(UserStatus), default=UserStatus.ACTIVE, nullable=False, comment="状态")
    
    # 权限信息
    is_active = Column(Boolean, default=True, nullable=False, comment="是否激活")
    is_superuser = Column(Boolean, default=False, nullable=False, comment="是否超级用户")
    
    # 安全信息
    last_login = Column(DateTime, nullable=True, comment="最后登录时间")
    failed_login_attempts = Column(Integer, default=0, nullable=False, comment="失败登录次数")
    locked_until = Column(DateTime, nullable=True, comment="锁定到期时间")
    
    # 人脸识别信息
    face_encoding = Column(Text, nullable=True, comment="人脸编码数据")
    face_image_path = Column(String(255), nullable=True, comment="人脸图像路径")
    
    # 其他信息
    notes = Column(Text, nullable=True, comment="备注")
    
    # 关系
    department = relationship("Department", foreign_keys=[department_id], back_populates="users")
    attendances = relationship("Attendance", foreign_keys="Attendance.user_id", back_populates="user")
    leaves = relationship("Leave", foreign_keys="Leave.user_id", back_populates="user")
    
    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"
    
    @property
    def display_name(self) -> str:
        """显示名称"""
        return self.full_name or self.username
    
    @property
    def is_locked(self) -> bool:
        """检查账户是否被锁定"""
        if self.locked_until is None:
            return False
        return datetime.utcnow() < self.locked_until
    
    def unlock(self):
        """解锁账户"""
        self.failed_login_attempts = 0
        self.locked_until = None
    
    def lock(self, hours: int = 24):
        """锁定账户"""
        self.locked_until = datetime.utcnow() + datetime.timedelta(hours=hours)
    
    def set_password(self, password: str):
        """设置密码"""
        from werkzeug.security import generate_password_hash
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password: str) -> bool:
        """验证密码"""
        from werkzeug.security import check_password_hash
        return check_password_hash(self.password_hash, password)