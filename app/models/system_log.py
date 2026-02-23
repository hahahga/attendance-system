"""
系统日志数据模型
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Enum
from sqlalchemy.orm import relationship
import enum

from .base import BaseModel


class LogLevel(enum.Enum):
    """日志级别枚举"""
    DEBUG = "debug"     # 调试
    INFO = "info"       # 信息
    WARNING = "warning" # 警告
    ERROR = "error"     # 错误
    CRITICAL = "critical" # 严重


class LogCategory(enum.Enum):
    """日志分类枚举"""
    AUTH = "auth"               # 认证
    ATTENDANCE = "attendance"   # 考勤
    LEAVE = "leave"             # 请假
    USER = "user"               # 用户管理
    SYSTEM = "system"           # 系统
    API = "api"                 # API
    DATABASE = "database"       # 数据库
    SECURITY = "security"       # 安全
    BACKUP = "backup"           # 备份
    OTHER = "other"             # 其他


class SystemLog(BaseModel):
    """
    系统日志模型
    """
    __tablename__ = "system_logs"
    
    # 日志信息
    level = Column(Enum(LogLevel), nullable=False, comment="日志级别")
    category = Column(Enum(LogCategory), nullable=False, comment="日志分类")
    message = Column(Text, nullable=False, comment="日志消息")
    details = Column(Text, nullable=True, comment="详细信息")
    
    # 关联信息
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, comment="用户ID")
    ip_address = Column(String(45), nullable=True, comment="IP地址")
    user_agent = Column(String(500), nullable=True, comment="用户代理")
    
    # 请求信息
    request_method = Column(String(10), nullable=True, comment="请求方法")
    request_url = Column(String(500), nullable=True, comment="请求URL")
    request_params = Column(Text, nullable=True, comment="请求参数")
    response_status = Column(Integer, nullable=True, comment="响应状态码")
    
    # 异常信息
    exception_type = Column(String(100), nullable=True, comment="异常类型")
    exception_message = Column(Text, nullable=True, comment="异常消息")
    stack_trace = Column(Text, nullable=True, comment="堆栈跟踪")
    
    # 其他信息
    module = Column(String(100), nullable=True, comment="模块名")
    function = Column(String(100), nullable=True, comment="函数名")
    line_number = Column(Integer, nullable=True, comment="行号")
    execution_time = Column(Integer, nullable=True, comment="执行时间（毫秒）")
    
    # 关系
    user = relationship("User", back_populates="logs")
    
    def __repr__(self):
        return f"<SystemLog(id={self.id}, level={self.level}, category={self.category}, message='{self.message[:50]}...')>"
    
    @property
    def is_error(self) -> bool:
        """是否为错误日志"""
        return self.level in [LogLevel.ERROR, LogLevel.CRITICAL]
    
    @property
    def is_warning(self) -> bool:
        """是否为警告日志"""
        return self.level == LogLevel.WARNING
    
    @property
    def is_info(self) -> bool:
        """是否为信息日志"""
        return self.level == LogLevel.INFO
    
    @property
    def is_debug(self) -> bool:
        """是否为调试日志"""
        return self.level == LogLevel.DEBUG
    
    @property
    def short_message(self) -> str:
        """获取短消息（前100个字符）"""
        if len(self.message) > 100:
            return self.message[:100] + "..."
        return self.message


# 为User模型添加反向关系
from .user import User

# 添加logs关系
User.logs = relationship("SystemLog", back_populates="user")