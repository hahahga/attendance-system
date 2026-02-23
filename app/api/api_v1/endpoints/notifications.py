"""
通知API接口
"""

from typing import Any, List, Optional
from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import schemas
from app.api import deps
from app.services.notification_service import NotificationService

router = APIRouter()


@router.get("/", response_model=List[schemas.NotificationListResponse])
def read_notifications(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    user_id: Optional[int] = None,
    is_read: Optional[bool] = None,
    notification_type: Optional[str] = None,
    current_user: schemas.UserResponse = Depends(deps.get_current_active_user)
) -> Any:
    """
    获取通知列表
    """
    # 普通用户只能查看自己的通知
    if current_user.role not in ["admin", "hr", "manager"]:
        user_id = current_user.id
    
    notifications = NotificationService.get_notifications(
        db=db,
        skip=skip,
        limit=limit,
        user_id=user_id,
        is_read=is_read,
        notification_type=notification_type
    )
    return notifications


@router.get("/{notification_id}", response_model=schemas.NotificationResponse)
def read_notification(
    notification_id: int,
    db: Session = Depends(deps.get_db),
    current_user: schemas.UserResponse = Depends(deps.get_current_active_user)
) -> Any:
    """
    获取通知详细信息
    """
    notification = NotificationService.get_notification_by_id(db, notification_id=notification_id)
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="通知不存在"
        )
    
    # 检查权限
    if current_user.role not in ["admin", "hr", "manager"] and current_user.id != notification.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="没有权限访问此通知"
        )
    
    return notification


@router.post("/", response_model=schemas.NotificationResponse)
def create_notification(
    *,
    db: Session = Depends(deps.get_db),
    notification_in: schemas.NotificationCreate,
    current_user: schemas.UserResponse = Depends(deps.get_current_active_user)
) -> Any:
    """
    创建通知
    """
    # 检查权限
    if current_user.role not in ["admin", "hr", "manager"] and current_user.id != notification_in.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="没有权限为其他用户创建通知"
        )
    
    notification = NotificationService.create_notification(db=db, notification=notification_in)
    return notification


@router.put("/{notification_id}/read", response_model=schemas.NotificationResponse)
def mark_notification_as_read(
    *,
    db: Session = Depends(deps.get_db),
    notification_id: int,
    current_user: schemas.UserResponse = Depends(deps.get_current_active_user)
) -> Any:
    """
    标记通知为已读
    """
    # 检查通知是否存在
    notification = NotificationService.get_notification_by_id(db, notification_id=notification_id)
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="通知不存在"
        )
    
    # 检查权限
    if current_user.role not in ["admin", "hr", "manager"] and current_user.id != notification.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="没有权限修改此通知"
        )
    
    notification = NotificationService.mark_as_read(db=db, notification_id=notification_id)
    return notification


@router.put("/read-all", response_model=schemas.Msg)
def mark_all_notifications_as_read(
    *,
    db: Session = Depends(deps.get_db),
    user_id: Optional[int] = None,
    current_user: schemas.UserResponse = Depends(deps.get_current_active_user)
) -> Any:
    """
    标记所有通知为已读
    """
    # 普通用户只能标记自己的通知
    if current_user.role not in ["admin", "hr", "manager"]:
        user_id = current_user.id
    
    count = NotificationService.mark_all_as_read(db=db, user_id=user_id)
    return {"msg": f"已将 {count} 条通知标记为已读"}


@router.delete("/{notification_id}", response_model=schemas.Msg)
def delete_notification(
    *,
    db: Session = Depends(deps.get_db),
    notification_id: int,
    current_user: schemas.UserResponse = Depends(deps.get_current_active_user)
) -> Any:
    """
    删除通知
    """
    # 检查通知是否存在
    notification = NotificationService.get_notification_by_id(db, notification_id=notification_id)
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="通知不存在"
        )
    
    # 检查权限
    if current_user.role not in ["admin", "hr", "manager"] and current_user.id != notification.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="没有权限删除此通知"
        )
    
    success = NotificationService.delete_notification(db=db, notification_id=notification_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="删除通知失败"
        )
    
    return {"msg": "通知删除成功"}


@router.delete("/cleanup", response_model=schemas.Msg)
def cleanup_old_notifications(
    *,
    db: Session = Depends(deps.get_db),
    days: int = 30,
    user_id: Optional[int] = None,
    current_user: schemas.UserResponse = Depends(deps.get_current_active_user)
) -> Any:
    """
    清理旧通知
    """
    # 普通用户只能清理自己的通知
    if current_user.role not in ["admin", "hr", "manager"]:
        user_id = current_user.id
    
    count = NotificationService.cleanup_old_notifications(db=db, days=days, user_id=user_id)
    return {"msg": f"已清理 {count} 条旧通知"}


@router.get("/unread/count", response_model=schemas.UnreadCountResponse)
def get_unread_count(
    *,
    db: Session = Depends(deps.get_db),
    user_id: Optional[int] = None,
    current_user: schemas.UserResponse = Depends(deps.get_current_active_user)
) -> Any:
    """
    获取未读通知数量
    """
    # 普通用户只能查看自己的未读通知
    if current_user.role not in ["admin", "hr", "manager"]:
        user_id = current_user.id
    
    count = NotificationService.get_unread_count(db=db, user_id=user_id)
    return {"count": count}


@router.post("/attendance", response_model=schemas.Msg)
def send_attendance_notification(
    *,
    db: Session = Depends(deps.get_db),
    notification_in: schemas.AttendanceNotification,
    current_user: schemas.UserResponse = Depends(deps.get_current_active_user)
) -> Any:
    """
    发送考勤通知
    """
    # 检查权限
    if current_user.role not in ["admin", "hr", "manager"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="没有权限发送考勤通知"
        )
    
    count = NotificationService.send_attendance_notification(
        db=db,
        user_id=notification_in.user_id,
        message=notification_in.message,
        attendance_id=notification_in.attendance_id
    )
    return {"msg": f"已向 {count} 个用户发送考勤通知"}


@router.post("/leave", response_model=schemas.Msg)
def send_leave_notification(
    *,
    db: Session = Depends(deps.get_db),
    notification_in: schemas.LeaveNotification,
    current_user: schemas.UserResponse = Depends(deps.get_current_active_user)
) -> Any:
    """
    发送请假通知
    """
    # 检查权限
    if current_user.role not in ["admin", "hr", "manager"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="没有权限发送请假通知"
        )
    
    count = NotificationService.send_leave_notification(
        db=db,
        user_id=notification_in.user_id,
        message=notification_in.message,
        leave_id=notification_in.leave_id
    )
    return {"msg": f"已向 {count} 个用户发送请假通知"}


@router.post("/system", response_model=schemas.Msg)
def send_system_notification(
    *,
    db: Session = Depends(deps.get_db),
    notification_in: schemas.SystemNotification,
    current_user: schemas.UserResponse = Depends(deps.get_current_active_superuser)
) -> Any:
    """
    发送系统通知（仅管理员）
    """
    count = NotificationService.send_system_notification(
        db=db,
        message=notification_in.message,
        user_ids=notification_in.user_ids
    )
    return {"msg": f"已向 {count} 个用户发送系统通知"}