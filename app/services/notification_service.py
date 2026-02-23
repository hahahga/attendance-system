"""
通知服务模块
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, date, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

from app.models.user import User
from app.models.notification import Notification, NotificationType


class NotificationService:
    """
    通知服务类
    """
    
    @staticmethod
    def get_notification_by_id(db: Session, notification_id: int) -> Optional[Notification]:
        """
        根据ID获取通知
        
        Args:
            db: 数据库会话
            notification_id: 通知ID
            
        Returns:
            通知对象，不存在返回None
        """
        return db.query(Notification).filter(Notification.id == notification_id).first()
    
    @staticmethod
    def get_notifications(
        db: Session,
        user_id: int,
        skip: int = 0,
        limit: int = 20,
        is_read: Optional[bool] = None,
        notification_type: Optional[NotificationType] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[Notification]:
        """
        获取用户通知列表
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            skip: 跳过记录数
            limit: 返回记录数
            is_read: 是否已读
            notification_type: 通知类型
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            通知列表
        """
        query = db.query(Notification).filter(Notification.user_id == user_id)
        
        if is_read is not None:
            query = query.filter(Notification.is_read == is_read)
        
        if notification_type:
            query = query.filter(Notification.type == notification_type)
        
        if start_date:
            query = query.filter(Notification.created_at >= start_date)
        
        if end_date:
            query = query.filter(Notification.created_at <= end_date)
        
        return query.order_by(Notification.created_at.desc()).offset(skip).limit(limit).all()
    
    @staticmethod
    def count_notifications(
        db: Session,
        user_id: int,
        is_read: Optional[bool] = None,
        notification_type: Optional[NotificationType] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> int:
        """
        统计用户通知数量
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            is_read: 是否已读
            notification_type: 通知类型
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            通知数量
        """
        query = db.query(Notification).filter(Notification.user_id == user_id)
        
        if is_read is not None:
            query = query.filter(Notification.is_read == is_read)
        
        if notification_type:
            query = query.filter(Notification.type == notification_type)
        
        if start_date:
            query = query.filter(Notification.created_at >= start_date)
        
        if end_date:
            query = query.filter(Notification.created_at <= end_date)
        
        return query.count()
    
    @staticmethod
    def create_notification(
        db: Session,
        user_id: int,
        title: str,
        content: str,
        notification_type: NotificationType,
        related_id: Optional[int] = None,
        related_type: Optional[str] = None
    ) -> Notification:
        """
        创建通知
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            title: 通知标题
            content: 通知内容
            notification_type: 通知类型
            related_id: 关联ID
            related_type: 关联类型
            
        Returns:
            创建的通知对象
        """
        db_notification = Notification(
            user_id=user_id,
            title=title,
            content=content,
            type=notification_type,
            related_id=related_id,
            related_type=related_type
        )
        
        db.add(db_notification)
        db.commit()
        db.refresh(db_notification)
        
        return db_notification
    
    @staticmethod
    def mark_as_read(db: Session, notification_id: int, user_id: int) -> Notification:
        """
        标记通知为已读
        
        Args:
            db: 数据库会话
            notification_id: 通知ID
            user_id: 用户ID
            
        Returns:
            更新后的通知对象
            
        Raises:
            ValueError: 通知不存在或不属于当前用户时抛出异常
        """
        db_notification = db.query(Notification).filter(
            and_(Notification.id == notification_id, Notification.user_id == user_id)
        ).first()
        
        if not db_notification:
            raise ValueError("通知不存在或不属于当前用户")
        
        db_notification.is_read = True
        db_notification.read_at = datetime.utcnow()
        
        db.commit()
        db.refresh(db_notification)
        
        return db_notification
    
    @staticmethod
    def mark_all_as_read(db: Session, user_id: int) -> int:
        """
        标记用户所有通知为已读
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            
        Returns:
            更新的通知数量
        """
        count = db.query(Notification).filter(
            and_(Notification.user_id == user_id, Notification.is_read == False)
        ).update(
            {
                "is_read": True,
                "read_at": datetime.utcnow()
            },
            synchronize_session=False
        )
        
        db.commit()
        
        return count
    
    @staticmethod
    def delete_notification(db: Session, notification_id: int, user_id: int) -> bool:
        """
        删除通知
        
        Args:
            db: 数据库会话
            notification_id: 通知ID
            user_id: 用户ID
            
        Returns:
            删除成功返回True
            
        Raises:
            ValueError: 通知不存在或不属于当前用户时抛出异常
        """
        db_notification = db.query(Notification).filter(
            and_(Notification.id == notification_id, Notification.user_id == user_id)
        ).first()
        
        if not db_notification:
            raise ValueError("通知不存在或不属于当前用户")
        
        db.delete(db_notification)
        db.commit()
        
        return True
    
    @staticmethod
    def cleanup_old_notifications(db: Session, days_to_keep: int = 30) -> int:
        """
        清理旧通知（已读且超过指定天数）
        
        Args:
            db: 数据库会话
            days_to_keep: 保留天数
            
        Returns:
            删除的通知数量
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        
        # 删除已读且超过保留天数的通知
        deleted_count = db.query(Notification).filter(
            and_(
                Notification.is_read == True,
                Notification.read_at < cutoff_date
            )
        ).delete()
        
        db.commit()
        
        return deleted_count
    
    @staticmethod
    def send_attendance_notification(
        db: Session,
        user_id: int,
        title: str,
        content: str,
        attendance_id: Optional[int] = None
    ) -> Notification:
        """
        发送考勤相关通知
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            title: 通知标题
            content: 通知内容
            attendance_id: 考勤记录ID
            
        Returns:
            创建的通知对象
        """
        return NotificationService.create_notification(
            db=db,
            user_id=user_id,
            title=title,
            content=content,
            notification_type=NotificationType.ATTENDANCE,
            related_id=attendance_id,
            related_type="attendance"
        )
    
    @staticmethod
    def send_leave_notification(
        db: Session,
        user_id: int,
        title: str,
        content: str,
        leave_id: Optional[int] = None
    ) -> Notification:
        """
        发送请假相关通知
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            title: 通知标题
            content: 通知内容
            leave_id: 请假记录ID
            
        Returns:
            创建的通知对象
        """
        return NotificationService.create_notification(
            db=db,
            user_id=user_id,
            title=title,
            content=content,
            notification_type=NotificationType.LEAVE,
            related_id=leave_id,
            related_type="leave"
        )
    
    @staticmethod
    def send_system_notification(
        db: Session,
        user_id: int,
        title: str,
        content: str
    ) -> Notification:
        """
        发送系统通知
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            title: 通知标题
            content: 通知内容
            
        Returns:
            创建的通知对象
        """
        return NotificationService.create_notification(
            db=db,
            user_id=user_id,
            title=title,
            content=content,
            notification_type=NotificationType.SYSTEM
        )
    
    @staticmethod
    def broadcast_notification(
        db: Session,
        title: str,
        content: str,
        notification_type: NotificationType,
        user_ids: Optional[List[int]] = None,
        department_id: Optional[int] = None,
        role: Optional[str] = None
    ) -> List[Notification]:
        """
        广播通知
        
        Args:
            db: 数据库会话
            title: 通知标题
            content: 通知内容
            notification_type: 通知类型
            user_ids: 用户ID列表
            department_id: 部门ID
            role: 用户角色
            
        Returns:
            创建的通知列表
        """
        # 确定接收通知的用户
        query = db.query(User).filter(User.is_active == True)
        
        if user_ids:
            query = query.filter(User.id.in_(user_ids))
        
        if department_id:
            query = query.filter(User.department_id == department_id)
        
        if role:
            query = query.filter(User.role == role)
        
        users = query.all()
        
        # 为每个用户创建通知
        notifications = []
        for user in users:
            notification = NotificationService.create_notification(
                db=db,
                user_id=user.id,
                title=title,
                content=content,
                notification_type=notification_type
            )
            notifications.append(notification)
        
        return notifications
    
    @staticmethod
    def get_unread_count(db: Session, user_id: int) -> int:
        """
        获取用户未读通知数量
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            
        Returns:
            未读通知数量
        """
        return db.query(Notification).filter(
            and_(Notification.user_id == user_id, Notification.is_read == False)
        ).count()
    
    @staticmethod
    def get_notification_statistics(
        db: Session,
        user_id: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        获取通知统计信息
        
        Args:
            db: 数据库会话
            user_id: 用户ID，None表示获取所有用户统计
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            通知统计信息字典
        """
        query = db.query(Notification)
        
        if user_id:
            query = query.filter(Notification.user_id == user_id)
        
        if start_date:
            query = query.filter(Notification.created_at >= start_date)
        
        if end_date:
            query = query.filter(Notification.created_at <= end_date)
        
        # 总通知数
        total_notifications = query.count()
        
        # 已读通知数
        read_notifications = query.filter(Notification.is_read == True).count()
        
        # 未读通知数
        unread_notifications = total_notifications - read_notifications
        
        # 按类型统计
        type_stats = query.with_entities(
            Notification.type,
            func.count(Notification.id).label("count")
        ).group_by(Notification.type).all()
        
        # 按日期统计（最近7天）
        seven_days_ago = date.today() - timedelta(days=7)
        daily_stats = query.filter(
            Notification.created_at >= seven_days_ago
        ).with_entities(
            func.date(Notification.created_at).label("date"),
            func.count(Notification.id).label("count")
        ).group_by(
            func.date(Notification.created_at)
        ).order_by(
            func.date(Notification.created_at)
        ).all()
        
        return {
            "total_notifications": total_notifications,
            "read_notifications": read_notifications,
            "unread_notifications": unread_notifications,
            "type_stats": {type_.value: count for type_, count in type_stats},
            "daily_stats": {str(date_obj): count for date_obj, count in daily_stats}
        }