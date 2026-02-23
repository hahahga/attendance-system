"""
统计API接口
"""

from typing import Any, List, Optional
from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import schemas
from app.api import deps
from app.services.attendance_service import AttendanceService
from app.services.leave_service import LeaveService
from app.services.user_service import UserService

router = APIRouter()


@router.get("/dashboard", response_model=schemas.DashboardStatistics)
def get_dashboard_statistics(
    db: Session = Depends(deps.get_db),
    department_id: Optional[int] = None,
    current_user: schemas.UserResponse = Depends(deps.get_current_active_user)
) -> Any:
    """
    获取仪表盘统计信息
    """
    # 普通用户只能查看自己的统计信息
    user_id = None
    if current_user.role not in ["admin", "hr", "manager"]:
        user_id = current_user.id
    
    # 获取用户统计
    user_stats = UserService.get_user_statistics(
        db=db,
        department_id=department_id
    )
    
    # 获取考勤统计
    attendance_stats = AttendanceService.get_attendance_statistics(
        db=db,
        user_id=user_id,
        department_id=department_id
    )
    
    # 获取请假统计
    leave_stats = LeaveService.get_leave_statistics(
        db=db,
        user_id=user_id,
        department_id=department_id
    )
    
    # 获取今日考勤情况
    today_attendance = AttendanceService.get_today_attendance_status(
        db=db,
        department_id=department_id
    )
    
    # 获取本月请假情况
    current_date = date.today()
    month_leave = LeaveService.get_monthly_leave_statistics(
        db=db,
        year=current_date.year,
        month=current_date.month,
        user_id=user_id,
        department_id=department_id
    )
    
    return schemas.DashboardStatistics(
        total_users=user_stats.total_users,
        active_users=user_stats.active_users,
        total_attendances=attendance_stats.total_attendances,
        attendance_rate=attendance_stats.attendance_rate,
        total_leaves=leave_stats.total_leaves,
        pending_leaves=leave_stats.pending_leaves,
        today_present=today_attendance.present,
        today_absent=today_attendance.absent,
        today_late=today_attendance.late,
        month_leave_days=month_leave.total_days
    )


@router.get("/attendance/monthly/{year}/{month}", response_model=schemas.MonthlyAttendanceStatistics)
def get_monthly_attendance_statistics(
    year: int,
    month: int,
    db: Session = Depends(deps.get_db),
    department_id: Optional[int] = None,
    user_id: Optional[int] = None,
    current_user: schemas.UserResponse = Depends(deps.get_current_active_user)
) -> Any:
    """
    获取月度考勤统计
    """
    # 普通用户只能查看自己的统计信息
    if current_user.role not in ["admin", "hr", "manager"]:
        user_id = current_user.id
    
    stats = AttendanceService.get_monthly_attendance_statistics(
        db=db,
        year=year,
        month=month,
        user_id=user_id,
        department_id=department_id
    )
    return stats


@router.get("/attendance/daily/{date}", response_model=schemas.DailyAttendanceStatistics)
def get_daily_attendance_statistics(
    date: date,
    db: Session = Depends(deps.get_db),
    department_id: Optional[int] = None,
    current_user: schemas.UserResponse = Depends(deps.get_current_active_user)
) -> Any:
    """
    获取日考勤统计
    """
    # 普通用户只能查看自己的统计信息
    user_id = None
    if current_user.role not in ["admin", "hr", "manager"]:
        user_id = current_user.id
    
    stats = AttendanceService.get_daily_attendance_statistics(
        db=db,
        date=date,
        user_id=user_id,
        department_id=department_id
    )
    return stats


@router.get("/leave/monthly/{year}/{month}", response_model=schemas.MonthlyLeaveStatistics)
def get_monthly_leave_statistics(
    year: int,
    month: int,
    db: Session = Depends(deps.get_db),
    department_id: Optional[int] = None,
    user_id: Optional[int] = None,
    current_user: schemas.UserResponse = Depends(deps.get_current_active_user)
) -> Any:
    """
    获取月度请假统计
    """
    # 普通用户只能查看自己的统计信息
    if current_user.role not in ["admin", "hr", "manager"]:
        user_id = current_user.id
    
    stats = LeaveService.get_monthly_leave_statistics(
        db=db,
        year=year,
        month=month,
        user_id=user_id,
        department_id=department_id
    )
    return stats


@router.get("/leave/annual/{year}", response_model=schemas.AnnualLeaveStatistics)
def get_annual_leave_statistics(
    year: int,
    db: Session = Depends(deps.get_db),
    department_id: Optional[int] = None,
    user_id: Optional[int] = None,
    current_user: schemas.UserResponse = Depends(deps.get_current_active_user)
) -> Any:
    """
    获取年度请假统计
    """
    # 普通用户只能查看自己的统计信息
    if current_user.role not in ["admin", "hr", "manager"]:
        user_id = current_user.id
    
    # 获取年度请假统计
    monthly_stats = []
    for month in range(1, 13):
        month_stats = LeaveService.get_monthly_leave_statistics(
            db=db,
            year=year,
            month=month,
            user_id=user_id,
            department_id=department_id
        )
        monthly_stats.append(month_stats)
    
    # 计算年度总计
    total_days = sum(stats.total_days for stats in monthly_stats)
    total_leaves = sum(stats.total_leaves for stats in monthly_stats)
    
    # 按请假类型统计
    leave_types = {}
    for stats in monthly_stats:
        for leave_type, days in stats.leave_types.items():
            leave_types[leave_type] = leave_types.get(leave_type, 0) + days
    
    return schemas.AnnualLeaveStatistics(
        year=year,
        total_days=total_days,
        total_leaves=total_leaves,
        monthly_statistics=monthly_stats,
        leave_types=leave_types
    )


@router.get("/user/{user_id}/attendance", response_model=schemas.UserAttendanceStatistics)
def get_user_attendance_statistics(
    user_id: int,
    db: Session = Depends(deps.get_db),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_user: schemas.UserResponse = Depends(deps.get_current_active_user)
) -> Any:
    """
    获取用户考勤统计
    """
    # 检查权限
    if current_user.role not in ["admin", "hr", "manager"] and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="没有权限查看此用户的考勤统计"
        )
    
    # 获取用户基本信息
    user = UserService.get_user_by_id(db, user_id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 获取考勤统计
    attendance_stats = AttendanceService.get_attendance_statistics(
        db=db,
        user_id=user_id,
        start_date=start_date,
        end_date=end_date
    )
    
    # 获取请假统计
    leave_stats = LeaveService.get_leave_statistics(
        db=db,
        user_id=user_id,
        start_date=start_date,
        end_date=end_date
    )
    
    return schemas.UserAttendanceStatistics(
        user_id=user_id,
        username=user.username,
        full_name=user.full_name,
        total_attendances=attendance_stats.total_attendances,
        present_days=attendance_stats.present_days,
        absent_days=attendance_stats.absent_days,
        late_days=attendance_stats.late_days,
        early_leave_days=attendance_stats.early_leave_days,
        attendance_rate=attendance_stats.attendance_rate,
        total_leave_days=leave_stats.total_days,
        sick_leave_days=leave_stats.leave_types.get("sick", 0),
        personal_leave_days=leave_stats.leave_types.get("personal", 0),
        annual_leave_days=leave_stats.leave_types.get("annual", 0),
        other_leave_days=leave_stats.leave_types.get("other", 0)
    )


@router.get("/department/{department_id}/attendance", response_model=schemas.DepartmentAttendanceStatistics)
def get_department_attendance_statistics(
    department_id: int,
    db: Session = Depends(deps.get_db),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_user: schemas.UserResponse = Depends(deps.get_current_active_user)
) -> Any:
    """
    获取部门考勤统计
    """
    # 检查权限
    if current_user.role not in ["admin", "hr", "manager"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="没有权限查看部门考勤统计"
        )
    
    # 获取部门基本信息
    from app.services.department_service import DepartmentService
    department = DepartmentService.get_department_by_id(db, department_id=department_id)
    if not department:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="部门不存在"
        )
    
    # 获取部门用户统计
    user_stats = UserService.get_user_statistics(db=db, department_id=department_id)
    
    # 获取部门考勤统计
    attendance_stats = AttendanceService.get_attendance_statistics(
        db=db,
        department_id=department_id,
        start_date=start_date,
        end_date=end_date
    )
    
    # 获取部门请假统计
    leave_stats = LeaveService.get_leave_statistics(
        db=db,
        department_id=department_id,
        start_date=start_date,
        end_date=end_date
    )
    
    return schemas.DepartmentAttendanceStatistics(
        department_id=department_id,
        department_name=department.name,
        total_users=user_stats.total_users,
        active_users=user_stats.active_users,
        total_attendances=attendance_stats.total_attendances,
        present_days=attendance_stats.present_days,
        absent_days=attendance_stats.absent_days,
        late_days=attendance_stats.late_days,
        early_leave_days=attendance_stats.early_leave_days,
        attendance_rate=attendance_stats.attendance_rate,
        total_leave_days=leave_stats.total_days,
        sick_leave_days=leave_stats.leave_types.get("sick", 0),
        personal_leave_days=leave_stats.leave_types.get("personal", 0),
        annual_leave_days=leave_stats.leave_types.get("annual", 0),
        other_leave_days=leave_stats.leave_types.get("other", 0)
    )


@router.get("/export/attendance", response_model=schemas.Msg)
def export_attendance_statistics(
    *,
    db: Session = Depends(deps.get_db),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    department_id: Optional[int] = None,
    user_id: Optional[int] = None,
    format: str = "excel",
    current_user: schemas.UserResponse = Depends(deps.get_current_active_user)
) -> Any:
    """
    导出考勤统计数据
    """
    # 普通用户只能导出自己的统计数据
    if current_user.role not in ["admin", "hr", "manager"]:
        user_id = current_user.id
    
    file_path = AttendanceService.export_attendance_statistics(
        db=db,
        start_date=start_date,
        end_date=end_date,
        department_id=department_id,
        user_id=user_id,
        format=format
    )
    
    if not file_path:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="导出考勤统计数据失败"
        )
    
    return {"msg": f"考勤统计数据导出成功，文件保存在: {file_path}"}


@router.get("/export/leave", response_model=schemas.Msg)
def export_leave_statistics(
    *,
    db: Session = Depends(deps.get_db),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    department_id: Optional[int] = None,
    user_id: Optional[int] = None,
    format: str = "excel",
    current_user: schemas.UserResponse = Depends(deps.get_current_active_user)
) -> Any:
    """
    导出请假统计数据
    """
    # 普通用户只能导出自己的统计数据
    if current_user.role not in ["admin", "hr", "manager"]:
        user_id = current_user.id
    
    file_path = LeaveService.export_leave_statistics(
        db=db,
        start_date=start_date,
        end_date=end_date,
        department_id=department_id,
        user_id=user_id,
        format=format
    )
    
    if not file_path:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="导出请假统计数据失败"
        )
    
    return {"msg": f"请假统计数据导出成功，文件保存在: {file_path}"}