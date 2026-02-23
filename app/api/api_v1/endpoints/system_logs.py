"""
系统日志API接口
"""

from typing import Any, List, Optional
from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import schemas
from app.api import deps
from app.services.system_log_service import SystemLogService

router = APIRouter()


@router.get("/", response_model=List[schemas.SystemLogListResponse])
def read_logs(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    user_id: Optional[int] = None,
    action: Optional[str] = None,
    resource: Optional[str] = None,
    ip_address: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_user: schemas.UserResponse = Depends(deps.get_current_active_superuser)
) -> Any:
    """
    获取系统日志列表（仅管理员）
    """
    logs = SystemLogService.get_logs(
        db=db,
        skip=skip,
        limit=limit,
        user_id=user_id,
        action=action,
        resource=resource,
        ip_address=ip_address,
        start_date=start_date,
        end_date=end_date
    )
    return logs


@router.get("/{log_id}", response_model=schemas.SystemLogResponse)
def read_log(
    log_id: int,
    db: Session = Depends(deps.get_db),
    current_user: schemas.UserResponse = Depends(deps.get_current_active_superuser)
) -> Any:
    """
    获取系统日志详细信息（仅管理员）
    """
    log = SystemLogService.get_log_by_id(db, log_id=log_id)
    if not log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="系统日志不存在"
        )
    return log


@router.get("/statistics/overview", response_model=schemas.LogStatistics)
def get_log_statistics(
    db: Session = Depends(deps.get_db),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_user: schemas.UserResponse = Depends(deps.get_current_active_superuser)
) -> Any:
    """
    获取系统日志统计信息（仅管理员）
    """
    stats = SystemLogService.get_log_statistics(
        db=db,
        start_date=start_date,
        end_date=end_date
    )
    return stats


@router.get("/statistics/actions", response_model=List[schemas.ActionStatistics])
def get_action_statistics(
    db: Session = Depends(deps.get_db),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_user: schemas.UserResponse = Depends(deps.get_current_active_superuser)
) -> Any:
    """
    获取操作类型统计（仅管理员）
    """
    stats = SystemLogService.get_action_statistics(
        db=db,
        start_date=start_date,
        end_date=end_date
    )
    return stats


@router.get("/statistics/users", response_model=List[schemas.UserLogStatistics])
def get_user_log_statistics(
    db: Session = Depends(deps.get_db),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_user: schemas.UserResponse = Depends(deps.get_current_active_superuser)
) -> Any:
    """
    获取用户操作统计（仅管理员）
    """
    stats = SystemLogService.get_user_log_statistics(
        db=db,
        start_date=start_date,
        end_date=end_date
    )
    return stats


@router.get("/statistics/hourly", response_model=List[schemas.HourlyLogStatistics])
def get_hourly_log_statistics(
    db: Session = Depends(deps.get_db),
    date: Optional[date] = None,
    current_user: schemas.UserResponse = Depends(deps.get_current_active_superuser)
) -> Any:
    """
    获取小时级日志统计（仅管理员）
    """
    stats = SystemLogService.get_hourly_log_statistics(
        db=db,
        date=date
    )
    return stats


@router.delete("/{log_id}", response_model=schemas.Msg)
def delete_log(
    *,
    db: Session = Depends(deps.get_db),
    log_id: int,
    current_user: schemas.UserResponse = Depends(deps.get_current_active_superuser)
) -> Any:
    """
    删除系统日志（仅管理员）
    """
    success = SystemLogService.delete_log(db=db, log_id=log_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="系统日志不存在"
        )
    
    return {"msg": "系统日志删除成功"}


@router.delete("/cleanup", response_model=schemas.Msg)
def cleanup_old_logs(
    *,
    db: Session = Depends(deps.get_db),
    days: int = 90,
    current_user: schemas.UserResponse = Depends(deps.get_current_active_superuser)
) -> Any:
    """
    清理旧日志（仅管理员）
    """
    count = SystemLogService.cleanup_old_logs(db=db, days=days)
    return {"msg": f"已清理 {count} 条旧日志记录"}