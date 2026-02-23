"""
请假服务模块
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, date, time, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, extract
from fastapi import HTTPException, status

from app.models.user import User
from app.models.leave import Leave, LeaveType, LeaveStatus
from app.schemas.leave import LeaveCreate, LeaveUpdate, LeaveApproval
from app.services.system_log_service import SystemLogService


class LeaveService:
    """
    请假服务类
    """
    
    @staticmethod
    def get_leave_by_id(db: Session, leave_id: int) -> Optional[Leave]:
        """
        根据ID获取请假记录
        
        Args:
            db: 数据库会话
            leave_id: 请假记录ID
            
        Returns:
            请假记录对象，不存在返回None
        """
        return db.query(Leave).filter(Leave.id == leave_id).first()
    
    @staticmethod
    def get_leaves(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        user_id: Optional[int] = None,
        department_id: Optional[int] = None,
        leave_type: Optional[LeaveType] = None,
        status: Optional[LeaveStatus] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        search: Optional[str] = None
    ) -> List[Leave]:
        """
        获取请假记录列表
        
        Args:
            db: 数据库会话
            skip: 跳过记录数
            limit: 返回记录数
            user_id: 用户ID
            department_id: 部门ID
            leave_type: 请假类型
            status: 请假状态
            start_date: 开始日期
            end_date: 结束日期
            search: 搜索关键词
            
        Returns:
            请假记录列表
        """
        query = db.query(Leave).join(User)
        
        if user_id:
            query = query.filter(Leave.user_id == user_id)
        
        if department_id:
            query = query.filter(User.department_id == department_id)
        
        if leave_type:
            query = query.filter(Leave.leave_type == leave_type)
        
        if status:
            query = query.filter(Leave.status == status)
        
        if start_date:
            query = query.filter(Leave.start_date >= start_date)
        
        if end_date:
            query = query.filter(Leave.end_date <= end_date)
        
        if search:
            query = query.filter(
                or_(
                    User.username.ilike(f"%{search}%"),
                    User.full_name.ilike(f"%{search}%"),
                    User.employee_id.ilike(f"%{search}%"),
                    Leave.reason.ilike(f"%{search}%")
                )
            )
        
        return query.order_by(Leave.applied_at.desc()).offset(skip).limit(limit).all()
    
    @staticmethod
    def count_leaves(
        db: Session,
        user_id: Optional[int] = None,
        department_id: Optional[int] = None,
        leave_type: Optional[LeaveType] = None,
        status: Optional[LeaveStatus] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        search: Optional[str] = None
    ) -> int:
        """
        统计请假记录数量
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            department_id: 部门ID
            leave_type: 请假类型
            status: 请假状态
            start_date: 开始日期
            end_date: 结束日期
            search: 搜索关键词
            
        Returns:
            请假记录数量
        """
        query = db.query(Leave).join(User)
        
        if user_id:
            query = query.filter(Leave.user_id == user_id)
        
        if department_id:
            query = query.filter(User.department_id == department_id)
        
        if leave_type:
            query = query.filter(Leave.leave_type == leave_type)
        
        if status:
            query = query.filter(Leave.status == status)
        
        if start_date:
            query = query.filter(Leave.start_date >= start_date)
        
        if end_date:
            query = query.filter(Leave.end_date <= end_date)
        
        if search:
            query = query.filter(
                or_(
                    User.username.ilike(f"%{search}%"),
                    User.full_name.ilike(f"%{search}%"),
                    User.employee_id.ilike(f"%{search}%"),
                    Leave.reason.ilike(f"%{search}%")
                )
            )
        
        return query.count()
    
    @staticmethod
    def create_leave(db: Session, user_id: int, leave: LeaveCreate) -> Leave:
        """
        创建请假申请
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            leave: 请假创建数据
            
        Returns:
            创建的请假记录对象
            
        Raises:
            HTTPException: 请假时间冲突时抛出异常
        """
        # 检查请假时间是否冲突
        existing_leave = db.query(Leave).filter(
            and_(
                Leave.user_id == user_id,
                Leave.status.in_([LeaveStatus.PENDING, LeaveStatus.APPROVED]),
                or_(
                    and_(Leave.start_date <= leave.start_date, Leave.end_date >= leave.start_date),
                    and_(Leave.start_date <= leave.end_date, Leave.end_date >= leave.end_date),
                    and_(Leave.start_date >= leave.start_date, Leave.end_date <= leave.end_date)
                )
            )
        ).first()
        
        if existing_leave:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="请假时间与已有请假记录冲突"
            )
        
        # 计算请假天数和小时数
        days, hours = LeaveService._calculate_leave_duration(
            leave.start_date, leave.end_date, leave.start_time, leave.end_time
        )
        
        # 创建请假记录
        db_leave = Leave(
            user_id=user_id,
            leave_type=leave.leave_type,
            start_date=leave.start_date,
            end_date=leave.end_date,
            start_time=leave.start_time,
            end_time=leave.end_time,
            days=days,
            hours=hours,
            replacement_user_id=leave.replacement_user_id,
            reason=leave.reason,
            notes=leave.notes,
            status=LeaveStatus.PENDING
        )
        
        db.add(db_leave)
        db.commit()
        db.refresh(db_leave)
        
        # 记录系统日志
        SystemLogService.log_user_action(
            db=db,
            user_id=user_id,
            action="申请请假",
            details=f"申请请假: {leave.leave_type.value}, 天数: {days}, 小时: {hours}"
        )
        
        return db_leave
    
    @staticmethod
    def update_leave(db: Session, leave_id: int, leave: LeaveUpdate) -> Leave:
        """
        更新请假记录
        
        Args:
            db: 数据库会话
            leave_id: 请假记录ID
            leave: 请假更新数据
            
        Returns:
            更新后的请假记录对象
            
        Raises:
            HTTPException: 请假记录不存在或状态不允许更新时抛出异常
        """
        db_leave = db.query(Leave).filter(Leave.id == leave_id).first()
        if not db_leave:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="请假记录不存在"
            )
        
        # 只有待审批状态才能更新
        if db_leave.status != LeaveStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="只有待审批状态的请假记录才能更新"
            )
        
        # 更新请假记录
        update_data = leave.dict(exclude_unset=True)
        
        # 如果更新了请假时间，重新计算天数和小时数
        if "start_date" in update_data or "end_date" in update_data or "start_time" in update_data or "end_time" in update_data:
            start_date = update_data.get("start_date", db_leave.start_date)
            end_date = update_data.get("end_date", db_leave.end_date)
            start_time = update_data.get("start_time", db_leave.start_time)
            end_time = update_data.get("end_time", db_leave.end_time)
            
            days, hours = LeaveService._calculate_leave_duration(
                start_date, end_date, start_time, end_time
            )
            
            update_data["days"] = days
            update_data["hours"] = hours
        
        for field, value in update_data.items():
            setattr(db_leave, field, value)
        
        db_leave.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(db_leave)
        
        # 记录系统日志
        SystemLogService.log_user_action(
            db=db,
            user_id=db_leave.user_id,
            action="更新请假申请",
            details=f"更新请假记录ID: {leave_id}"
        )
        
        return db_leave
    
    @staticmethod
    def approve_leave(db: Session, leave_id: int, approval: LeaveApproval, approver_id: int) -> Leave:
        """
        审批请假申请
        
        Args:
            db: 数据库会话
            leave_id: 请假记录ID
            approval: 审批数据
            approver_id: 审批人ID
            
        Returns:
            更新后的请假记录对象
            
        Raises:
            HTTPException: 请假记录不存在或状态不允许审批时抛出异常
        """
        db_leave = db.query(Leave).filter(Leave.id == leave_id).first()
        if not db_leave:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="请假记录不存在"
            )
        
        # 只有待审批状态才能审批
        if db_leave.status != LeaveStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="只有待审批状态的请假记录才能审批"
            )
        
        # 更新审批信息
        if approval.action == "approve":
            db_leave.status = LeaveStatus.APPROVED
        else:  # reject
            db_leave.status = LeaveStatus.REJECTED
            db_leave.rejection_reason = approval.reason
        
        db_leave.approved_by = approver_id
        db_leave.approved_at = datetime.utcnow()
        db_leave.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(db_leave)
        
        # 记录系统日志
        action_text = "批准" if approval.action == "approve" else "拒绝"
        SystemLogService.log_user_action(
            db=db,
            user_id=approver_id,
            action=f"{action_text}请假申请",
            details=f"{action_text}请假记录ID: {leave_id}, 原因: {approval.reason or '无'}"
        )
        
        return db_leave
    
    @staticmethod
    def cancel_leave(db: Session, leave_id: int, reason: Optional[str] = None, user_id: Optional[int] = None) -> Leave:
        """
        取消请假申请
        
        Args:
            db: 数据库会话
            leave_id: 请假记录ID
            reason: 取消原因
            user_id: 操作用户ID
            
        Returns:
            更新后的请假记录对象
            
        Raises:
            HTTPException: 请假记录不存在或状态不允许取消时抛出异常
        """
        db_leave = db.query(Leave).filter(Leave.id == leave_id).first()
        if not db_leave:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="请假记录不存在"
            )
        
        # 只有待审批或已批准状态才能取消
        if db_leave.status not in [LeaveStatus.PENDING, LeaveStatus.APPROVED]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="只有待审批或已批准状态的请假记录才能取消"
            )
        
        # 更新取消信息
        db_leave.status = LeaveStatus.CANCELLED
        db_leave.cancelled_by = user_id
        db_leave.cancelled_at = datetime.utcnow()
        db_leave.cancellation_reason = reason
        db_leave.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(db_leave)
        
        # 记录系统日志
        SystemLogService.log_user_action(
            db=db,
            user_id=user_id or db_leave.user_id,
            action="取消请假申请",
            details=f"取消请假记录ID: {leave_id}, 原因: {reason or '无'}"
        )
        
        return db_leave
    
    @staticmethod
    def delete_leave(db: Session, leave_id: int) -> bool:
        """
        删除请假记录
        
        Args:
            db: 数据库会话
            leave_id: 请假记录ID
            
        Returns:
            删除成功返回True
            
        Raises:
            HTTPException: 请假记录不存在时抛出异常
        """
        db_leave = db.query(Leave).filter(Leave.id == leave_id).first()
        if not db_leave:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="请假记录不存在"
            )
        
        # 记录用户ID用于日志
        user_id = db_leave.user_id
        
        db.delete(db_leave)
        db.commit()
        
        # 记录系统日志
        SystemLogService.log_user_action(
            db=db,
            user_id=user_id,
            action="删除请假记录",
            details=f"删除请假记录ID: {leave_id}"
        )
        
        return True
    
    @staticmethod
    def get_leave_balance(db: Session, user_id: int) -> Dict[str, Any]:
        """
        获取用户请假余额
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            
        Returns:
            请假余额字典
        """
        # 获取用户信息
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        # 计算工作年限（用于年假计算）
        hire_date = user.hire_date or date.today()
        years_of_service = (date.today() - hire_date).days // 365
        
        # 年假天数（根据工作年限计算）
        annual_leave_total = 5 + min(years_of_service, 10)  # 5-15天年假
        
        # 病假天数（固定10天）
        sick_leave_total = 10
        
        # 事假天数（固定5天）
        personal_leave_total = 5
        
        # 计算本年度已使用的请假天数
        current_year = date.today().year
        start_of_year = date(current_year, 1, 1)
        
        # 年假已使用
        annual_leave_used = db.query(func.sum(Leave.days)).filter(
            and_(
                Leave.user_id == user_id,
                Leave.leave_type == LeaveType.ANNUAL,
                Leave.status == LeaveStatus.APPROVED,
                Leave.start_date >= start_of_year
            )
        ).scalar() or 0
        
        # 病假已使用
        sick_leave_used = db.query(func.sum(Leave.days)).filter(
            and_(
                Leave.user_id == user_id,
                Leave.leave_type == LeaveType.SICK,
                Leave.status == LeaveStatus.APPROVED,
                Leave.start_date >= start_of_year
            )
        ).scalar() or 0
        
        # 事假已使用
        personal_leave_used = db.query(func.sum(Leave.days)).filter(
            and_(
                Leave.user_id == user_id,
                Leave.leave_type == LeaveType.PERSONAL,
                Leave.status == LeaveStatus.APPROVED,
                Leave.start_date >= start_of_year
            )
        ).scalar() or 0
        
        return {
            "user_id": user_id,
            "annual_leave_total": annual_leave_total,
            "annual_leave_used": round(annual_leave_used, 1),
            "annual_leave_remaining": round(annual_leave_total - annual_leave_used, 1),
            "sick_leave_total": sick_leave_total,
            "sick_leave_used": round(sick_leave_used, 1),
            "sick_leave_remaining": round(sick_leave_total - sick_leave_used, 1),
            "personal_leave_total": personal_leave_total,
            "personal_leave_used": round(personal_leave_used, 1),
            "personal_leave_remaining": round(personal_leave_total - personal_leave_used, 1)
        }
    
    @staticmethod
    def get_leave_statistics(
        db: Session,
        user_id: Optional[int] = None,
        department_id: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        获取请假统计信息
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            department_id: 部门ID
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            请假统计信息字典
        """
        query = db.query(Leave).join(User)
        
        if user_id:
            query = query.filter(Leave.user_id == user_id)
        
        if department_id:
            query = query.filter(User.department_id == department_id)
        
        if start_date:
            query = query.filter(Leave.start_date >= start_date)
        
        if end_date:
            query = query.filter(Leave.end_date <= end_date)
        
        # 总请假次数
        total_leaves = query.count()
        
        # 按类型统计
        type_stats = query.with_entities(
            Leave.leave_type,
            func.count(Leave.id).label("count"),
            func.sum(Leave.days).label("days")
        ).group_by(Leave.leave_type).all()
        
        # 按状态统计
        status_stats = query.with_entities(
            Leave.status,
            func.count(Leave.id).label("count")
        ).group_by(Leave.status).all()
        
        # 总请假天数
        total_leave_days = query.with_entities(
            func.sum(Leave.days)
        ).scalar() or 0
        
        return {
            "total_leaves": total_leaves,
            "type_stats": {
                leave_type.value: {"count": count, "days": round(days, 1) if days else 0}
                for leave_type, count, days in type_stats
            },
            "status_stats": {status.value: count for status, count in status_stats},
            "total_leave_days": round(total_leave_days, 1)
        }
    
    @staticmethod
    def _calculate_leave_duration(
        start_date: date,
        end_date: date,
        start_time: Optional[time] = None,
        end_time: Optional[time] = None
    ) -> tuple[float, float]:
        """
        计算请假天数和小时数
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            start_time: 开始时间
            end_time: 结束时间
            
        Returns:
            (天数, 小时数) 元组
        """
        # 如果没有指定时间，按整天计算
        if not start_time and not end_time:
            days = (end_date - start_date).days + 1
            return days, 0.0
        
        # 如果有指定时间，按小时计算
        start_datetime = datetime.combine(start_date, start_time or time(0, 0))
        end_datetime = datetime.combine(end_date, end_time or time(23, 59))
        
        # 如果结束时间小于开始时间，说明跨天了
        if end_datetime < start_datetime:
            end_datetime += timedelta(days=1)
        
        # 计算总小时数
        total_hours = (end_datetime - start_datetime).total_seconds() / 3600
        
        # 计算天数（按8小时一天计算）
        days = total_hours / 8
        
        return round(days, 1), round(total_hours, 1)