"""
Pydantic模式模块
"""

from .user import (
    UserBase, UserCreate, UserUpdate, UserResponse, UserLogin, UserChangePassword,
    UserListResponse, UserDetailResponse, UserRegister, UserFaceData
)
from .auth import Token, TokenData, RefreshToken
from .department import (
    DepartmentBase, DepartmentCreate, DepartmentUpdate, DepartmentResponse,
    DepartmentListResponse, DepartmentTreeResponse
)
from .attendance import (
    AttendanceBase, AttendanceCreate, AttendanceUpdate, AttendanceResponse,
    AttendanceListResponse, AttendanceCheckIn, AttendanceCheckOut, AttendanceCorrection
)
from .leave import (
    LeaveBase, LeaveCreate, LeaveUpdate, LeaveResponse, LeaveListResponse,
    LeaveApproval, LeaveCancel
)

__all__ = [
    # 用户相关
    "UserBase", "UserCreate", "UserUpdate", "UserResponse", "UserLogin", 
    "UserChangePassword", "UserListResponse", "UserDetailResponse", 
    "UserRegister", "UserFaceData",
    
    # 认证相关
    "Token", "TokenData", "RefreshToken",
    
    # 部门相关
    "DepartmentBase", "DepartmentCreate", "DepartmentUpdate", "DepartmentResponse",
    "DepartmentListResponse", "DepartmentTreeResponse",
    
    # 考勤相关
    "AttendanceBase", "AttendanceCreate", "AttendanceUpdate", "AttendanceResponse",
    "AttendanceListResponse", "AttendanceCheckIn", "AttendanceCheckOut", 
    "AttendanceCorrection",
    
    # 请假相关
    "LeaveBase", "LeaveCreate", "LeaveUpdate", "LeaveResponse", "LeaveListResponse",
    "LeaveApproval", "LeaveCancel",
]