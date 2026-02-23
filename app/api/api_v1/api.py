"""
API v1 路由
"""

from fastapi import APIRouter

from app.api.api_v1.endpoints import (
    auth,
    users,
    departments,
    attendance,
    leave,
    system_logs,
    notifications,
    statistics
)

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["认证"])
api_router.include_router(users.router, prefix="/users", tags=["用户"])
api_router.include_router(departments.router, prefix="/departments", tags=["部门"])
api_router.include_router(attendance.router, prefix="/attendance", tags=["考勤"])
api_router.include_router(leave.router, prefix="/leave", tags=["请假"])
api_router.include_router(system_logs.router, prefix="/system-logs", tags=["系统日志"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["通知"])
api_router.include_router(statistics.router, prefix="/statistics", tags=["统计"])