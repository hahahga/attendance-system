"""
数据模型模块
"""

from .base import BaseModel
from .user import User
from .department import Department
from .attendance import Attendance
from .leave import Leave
from .system_log import SystemLog
from .system_config import SystemConfig

__all__ = [
    "BaseModel",
    "User",
    "Department",
    "Attendance",
    "Leave",
    "SystemLog",
    "SystemConfig",
]