"""
请假数据模型
"""

from datetime import datetime, date, time
from typing import Optional
from sqlalchemy import Column, Integer, String, DateTime, Date, Time, Float, Text, ForeignKey, Enum, Boolean
from sqlalchemy.orm import relationship
import enum

from .base import BaseModel


class LeaveType(enum.Enum):
    """请假类型枚举"""
    ANNUAL = "annual"           # 年假
    SICK = "sick"               # 病假
    PERSONAL = "personal"       # 事假
    MATERNITY = "maternity"     # 产假
    PATERNITY = "paternity"     # 陪产假
    MARRIAGE = "marriage"       # 婚假
    BEREAVEMENT = "bereavement" # 丧假
    COMPENSATORY = "compensatory" # 调休
    UNPAID = "unpaid"           # 无薪假
    OTHER = "other"             # 其他


class LeaveStatus(enum.Enum):
    """请假状态枚举"""
    PENDING = "pending"         # 待审批
    APPROVED = "approved"       # 已批准
    REJECTED = "rejected"       # 已拒绝
    CANCELLED = "cancelled"     # 已取消
    PROCESSING = "processing"   # 审批中


class Leave(BaseModel):
    """
    请假模型
    """
    __tablename__ = "leaves"
    
    # 关联信息
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="用户ID")
    
    # 请假信息
    leave_type = Column(Enum(LeaveType), nullable=False, comment="请假类型")
    start_date = Column(Date, nullable=False, comment="开始日期")
    end_date = Column(Date, nullable=False, comment="结束日期")
    start_time = Column(Time, nullable=True, comment="开始时间")
    end_time = Column(Time, nullable=True, comment="结束时间")
    
    # 请假时长
    days = Column(Float, default=0.0, nullable=False, comment="请假天数")
    hours = Column(Float, default=0.0, nullable=False, comment="请假小时数")
    
    # 状态信息
    status = Column(Enum(LeaveStatus), default=LeaveStatus.PENDING, nullable=False, comment="请假状态")
    
    # 审批信息
    applied_at = Column(DateTime, default=datetime.utcnow, nullable=False, comment="申请时间")
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True, comment="审批人ID")
    approved_at = Column(DateTime, nullable=True, comment="审批时间")
    rejection_reason = Column(Text, nullable=True, comment="拒绝原因")
    
    # 代理人信息
    replacement_user_id = Column(Integer, ForeignKey("users.id"), nullable=True, comment="代理人ID")
    replacement_approved = Column(Boolean, default=False, nullable=False, comment="代理人是否同意")
    replacement_approved_at = Column(DateTime, nullable=True, comment="代理人同意时间")
    
    # 附件信息
    attachment_path = Column(String(255), nullable=True, comment="附件路径")
    
    # 请假原因
    reason = Column(Text, nullable=True, comment="请假原因")
    
    # 审批流程
    current_approver_id = Column(Integer, ForeignKey("users.id"), nullable=True, comment="当前审批人ID")
    next_approver_id = Column(Integer, ForeignKey("users.id"), nullable=True, comment="下一审批人ID")
    
    # 其他信息
    notes = Column(Text, nullable=True, comment="备注")
    
    # 关系
    user = relationship("User", foreign_keys=[user_id], back_populates="leaves")
    approver = relationship("User", foreign_keys=[approved_by])
    replacement = relationship("User", foreign_keys=[replacement_user_id])
    current_approver = relationship("User", foreign_keys=[current_approver_id])
    next_approver = relationship("User", foreign_keys=[next_approver_id])
    
    def __repr__(self):
        return f"<Leave(id={self.id}, user_id={self.user_id}, type={self.leave_type}, status={self.status})>"
    
    @property
    def is_approved(self) -> bool:
        """是否已批准"""
        return self.status == LeaveStatus.APPROVED
    
    @property
    def is_pending(self) -> bool:
        """是否待审批"""
        return self.status == LeaveStatus.PENDING
    
    @property
    def is_rejected(self) -> bool:
        """是否已拒绝"""
        return self.status == LeaveStatus.REJECTED
    
    @property
    def is_cancelled(self) -> bool:
        """是否已取消"""
        return self.status == LeaveStatus.CANCELLED
    
    @property
    def is_processing(self) -> bool:
        """是否审批中"""
        return self.status == LeaveStatus.PROCESSING
    
    def calculate_duration(self):
        """计算请假时长"""
        if self.start_date and self.end_date:
            # 计算天数
            delta = self.end_date - self.start_date
            self.days = delta.days + 1  # 包含开始和结束日期
            
            # 如果有具体时间，计算小时数
            if self.start_time and self.end_time:
                # 如果是同一天
                if self.start_date == self.end_date:
                    start_datetime = datetime.combine(self.start_date, self.start_time)
                    end_datetime = datetime.combine(self.end_date, self.end_time)
                    delta = end_datetime - start_datetime
                    self.hours = delta.total_seconds() / 3600
                else:
                    # 跨天的情况，简化处理，假设每天工作8小时
                    self.hours = self.days * 8
            else:
                # 没有具体时间，假设每天工作8小时
                self.hours = self.days * 8
        else:
            self.days = 0.0
            self.hours = 0.0
    
    def approve(self, approver_id: int):
        """批准请假"""
        self.status = LeaveStatus.APPROVED
        self.approved_by = approver_id
        self.approved_at = datetime.utcnow()
    
    def reject(self, approver_id: int, reason: str):
        """拒绝请假"""
        self.status = LeaveStatus.REJECTED
        self.approved_by = approver_id
        self.approved_at = datetime.utcnow()
        self.rejection_reason = reason
    
    def cancel(self):
        """取消请假"""
        self.status = LeaveStatus.CANCELLED