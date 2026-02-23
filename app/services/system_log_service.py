"""
系统日志服务模块
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, date
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, extract
from fastapi import HTTPException, status

from app.models.user import User
from app.models.system_log import SystemLog, LogLevel, LogCategory
from app.schemas.system_log import SystemLogCreate, SystemLogUpdate


class SystemLogService:
    """
    系统日志服务类
    """
    
    @staticmethod
    def get_log_by_id(db: Session, log_id: int) -> Optional[SystemLog]:
        """
        根据ID获取系统日志
        
        Args:
            db: 数据库会话
            log_id: 日志ID
            
        Returns:
            系统日志对象，不存在返回None
        """
        return db.query(SystemLog).filter(SystemLog.id == log_id).first()
    
    @staticmethod
    def get_logs(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        user_id: Optional[int] = None,
        level: Optional[LogLevel] = None,
        category: Optional[LogCategory] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        search: Optional[str] = None
    ) -> List[SystemLog]:
        """
        获取系统日志列表
        
        Args:
            db: 数据库会话
            skip: 跳过记录数
            limit: 返回记录数
            user_id: 用户ID
            level: 日志级别
            category: 日志分类
            start_date: 开始日期
            end_date: 结束日期
            search: 搜索关键词
            
        Returns:
            系统日志列表
        """
        query = db.query(SystemLog)
        
        if user_id:
            query = query.filter(SystemLog.user_id == user_id)
        
        if level:
            query = query.filter(SystemLog.level == level)
        
        if category:
            query = query.filter(SystemLog.category == category)
        
        if start_date:
            query = query.filter(SystemLog.created_at >= start_date)
        
        if end_date:
            query = query.filter(SystemLog.created_at <= end_date)
        
        if search:
            query = query.filter(
                or_(
                    SystemLog.message.ilike(f"%{search}%"),
                    SystemLog.details.ilike(f"%{search}%"),
                    SystemLog.request_path.ilike(f"%{search}%"),
                    SystemLog.ip_address.ilike(f"%{search}%")
                )
            )
        
        return query.order_by(SystemLog.created_at.desc()).offset(skip).limit(limit).all()
    
    @staticmethod
    def count_logs(
        db: Session,
        user_id: Optional[int] = None,
        level: Optional[LogLevel] = None,
        category: Optional[LogCategory] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        search: Optional[str] = None
    ) -> int:
        """
        统计系统日志数量
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            level: 日志级别
            category: 日志分类
            start_date: 开始日期
            end_date: 结束日期
            search: 搜索关键词
            
        Returns:
            系统日志数量
        """
        query = db.query(SystemLog)
        
        if user_id:
            query = query.filter(SystemLog.user_id == user_id)
        
        if level:
            query = query.filter(SystemLog.level == level)
        
        if category:
            query = query.filter(SystemLog.category == category)
        
        if start_date:
            query = query.filter(SystemLog.created_at >= start_date)
        
        if end_date:
            query = query.filter(SystemLog.created_at <= end_date)
        
        if search:
            query = query.filter(
                or_(
                    SystemLog.message.ilike(f"%{search}%"),
                    SystemLog.details.ilike(f"%{search}%"),
                    SystemLog.request_path.ilike(f"%{search}%"),
                    SystemLog.ip_address.ilike(f"%{search}%")
                )
            )
        
        return query.count()
    
    @staticmethod
    def create_log(db: Session, log: SystemLogCreate) -> SystemLog:
        """
        创建系统日志
        
        Args:
            db: 数据库会话
            log: 日志创建数据
            
        Returns:
            创建的日志对象
        """
        db_log = SystemLog(
            level=log.level,
            category=log.category,
            message=log.message,
            details=log.details,
            user_id=log.user_id,
            request_method=log.request_method,
            request_path=log.request_path,
            request_params=log.request_params,
            ip_address=log.ip_address,
            user_agent=log.user_agent,
            exception_type=log.exception_type,
            exception_message=log.exception_message,
            stack_trace=log.stack_trace
        )
        
        db.add(db_log)
        db.commit()
        db.refresh(db_log)
        
        return db_log
    
    @staticmethod
    def update_log(db: Session, log_id: int, log: SystemLogUpdate) -> SystemLog:
        """
        更新系统日志
        
        Args:
            db: 数据库会话
            log_id: 日志ID
            log: 日志更新数据
            
        Returns:
            更新后的日志对象
            
        Raises:
            HTTPException: 日志不存在时抛出异常
        """
        db_log = db.query(SystemLog).filter(SystemLog.id == log_id).first()
        if not db_log:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="日志记录不存在"
            )
        
        # 更新日志记录
        update_data = log.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_log, field, value)
        
        db_log.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(db_log)
        
        return db_log
    
    @staticmethod
    def delete_log(db: Session, log_id: int) -> bool:
        """
        删除系统日志
        
        Args:
            db: 数据库会话
            log_id: 日志ID
            
        Returns:
            删除成功返回True
            
        Raises:
            HTTPException: 日志不存在时抛出异常
        """
        db_log = db.query(SystemLog).filter(SystemLog.id == log_id).first()
        if not db_log:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="日志记录不存在"
            )
        
        db.delete(db_log)
        db.commit()
        
        return True
    
    @staticmethod
    def log_user_action(
        db: Session,
        user_id: Optional[int],
        action: str,
        details: Optional[str] = None,
        ip_address: Optional[str] = None,
        request_method: Optional[str] = None,
        request_path: Optional[str] = None,
        request_params: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> SystemLog:
        """
        记录用户操作日志
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            action: 操作动作
            details: 操作详情
            ip_address: IP地址
            request_method: 请求方法
            request_path: 请求路径
            request_params: 请求参数
            user_agent: 用户代理
            
        Returns:
            创建的日志对象
        """
        return SystemLogService.create_log(
            db=db,
            log=SystemLogCreate(
                level=LogLevel.INFO,
                category=LogCategory.USER_ACTION,
                message=action,
                details=details,
                user_id=user_id,
                request_method=request_method,
                request_path=request_path,
                request_params=request_params,
                ip_address=ip_address,
                user_agent=user_agent
            )
        )
    
    @staticmethod
    def log_security_event(
        db: Session,
        event: str,
        details: Optional[str] = None,
        user_id: Optional[int] = None,
        ip_address: Optional[str] = None,
        request_method: Optional[str] = None,
        request_path: Optional[str] = None,
        request_params: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> SystemLog:
        """
        记录安全事件日志
        
        Args:
            db: 数据库会话
            event: 安全事件
            details: 事件详情
            user_id: 用户ID
            ip_address: IP地址
            request_method: 请求方法
            request_path: 请求路径
            request_params: 请求参数
            user_agent: 用户代理
            
        Returns:
            创建的日志对象
        """
        return SystemLogService.create_log(
            db=db,
            log=SystemLogCreate(
                level=LogLevel.WARNING,
                category=LogCategory.SECURITY,
                message=event,
                details=details,
                user_id=user_id,
                request_method=request_method,
                request_path=request_path,
                request_params=request_params,
                ip_address=ip_address,
                user_agent=user_agent
            )
        )
    
    @staticmethod
    def log_system_error(
        db: Session,
        error: str,
        exception_type: Optional[str] = None,
        exception_message: Optional[str] = None,
        stack_trace: Optional[str] = None,
        user_id: Optional[int] = None,
        ip_address: Optional[str] = None,
        request_method: Optional[str] = None,
        request_path: Optional[str] = None,
        request_params: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> SystemLog:
        """
        记录系统错误日志
        
        Args:
            db: 数据库会话
            error: 错误描述
            exception_type: 异常类型
            exception_message: 异常消息
            stack_trace: 堆栈跟踪
            user_id: 用户ID
            ip_address: IP地址
            request_method: 请求方法
            request_path: 请求路径
            request_params: 请求参数
            user_agent: 用户代理
            
        Returns:
            创建的日志对象
        """
        return SystemLogService.create_log(
            db=db,
            log=SystemLogCreate(
                level=LogLevel.ERROR,
                category=LogCategory.SYSTEM,
                message=error,
                exception_type=exception_type,
                exception_message=exception_message,
                stack_trace=stack_trace,
                user_id=user_id,
                request_method=request_method,
                request_path=request_path,
                request_params=request_params,
                ip_address=ip_address,
                user_agent=user_agent
            )
        )
    
    @staticmethod
    def log_api_request(
        db: Session,
        method: str,
        path: str,
        status_code: int,
        response_time: float,
        user_id: Optional[int] = None,
        ip_address: Optional[str] = None,
        request_params: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> SystemLog:
        """
        记录API请求日志
        
        Args:
            db: 数据库会话
            method: 请求方法
            path: 请求路径
            status_code: 响应状态码
            response_time: 响应时间（毫秒）
            user_id: 用户ID
            ip_address: IP地址
            request_params: 请求参数
            user_agent: 用户代理
            
        Returns:
            创建的日志对象
        """
        # 根据状态码确定日志级别
        if status_code >= 500:
            level = LogLevel.ERROR
        elif status_code >= 400:
            level = LogLevel.WARNING
        else:
            level = LogLevel.INFO
        
        return SystemLogService.create_log(
            db=db,
            log=SystemLogCreate(
                level=level,
                category=LogCategory.API,
                message=f"{method} {path} - {status_code}",
                details=f"响应时间: {response_time}ms",
                user_id=user_id,
                request_method=method,
                request_path=path,
                request_params=request_params,
                ip_address=ip_address,
                user_agent=user_agent
            )
        )
    
    @staticmethod
    def get_log_statistics(
        db: Session,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        获取日志统计信息
        
        Args:
            db: 数据库会话
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            日志统计信息字典
        """
        query = db.query(SystemLog)
        
        if start_date:
            query = query.filter(SystemLog.created_at >= start_date)
        
        if end_date:
            query = query.filter(SystemLog.created_at <= end_date)
        
        # 总日志数
        total_logs = query.count()
        
        # 按级别统计
        level_stats = query.with_entities(
            SystemLog.level,
            func.count(SystemLog.id).label("count")
        ).group_by(SystemLog.level).all()
        
        # 按分类统计
        category_stats = query.with_entities(
            SystemLog.category,
            func.count(SystemLog.id).label("count")
        ).group_by(SystemLog.category).all()
        
        # 按日期统计（最近7天）
        from datetime import timedelta
        seven_days_ago = date.today() - timedelta(days=7)
        daily_stats = query.filter(
            SystemLog.created_at >= seven_days_ago
        ).with_entities(
            func.date(SystemLog.created_at).label("date"),
            func.count(SystemLog.id).label("count")
        ).group_by(
            func.date(SystemLog.created_at)
        ).order_by(
            func.date(SystemLog.created_at)
        ).all()
        
        return {
            "total_logs": total_logs,
            "level_stats": {level.value: count for level, count in level_stats},
            "category_stats": {category.value: count for category, count in category_stats},
            "daily_stats": {str(date_obj): count for date_obj, count in daily_stats}
        }
    
    @staticmethod
    def cleanup_old_logs(db: Session, days_to_keep: int = 90) -> int:
        """
        清理旧日志
        
        Args:
            db: 数据库会话
            days_to_keep: 保留天数
            
        Returns:
            删除的日志数量
        """
        from datetime import timedelta
        
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        
        # 删除旧日志
        deleted_count = db.query(SystemLog).filter(
            SystemLog.created_at < cutoff_date
        ).delete()
        
        db.commit()
        
        return deleted_count