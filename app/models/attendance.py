"""
考勤数据模型
"""

from datetime import datetime, time, date
from typing import Optional
from sqlalchemy import Column, Integer, String, DateTime, Date, Time, Float, Text, ForeignKey, Enum, Boolean
from sqlalchemy.orm import relationship
import enum

from .base import BaseModel


class AttendanceStatus(enum.Enum):
    """考勤状态枚举"""
    PRESENT = "present"         # 出勤
    ABSENT = "absent"           # 缺勤
    LATE = "late"               # 迟到
    EARLY_LEAVE = "early_leave" # 早退
    LEAVE = "leave"             # 请假
    HOLIDAY = "holiday"         # 节假日
    WEEKEND = "weekend"         # 周末
    OVERTIME = "overtime"       # 加班


class AttendanceType(enum.Enum):
    """考勤类型枚举"""
    CHECK_IN = "check_in"       # 上班打卡
    CHECK_OUT = "check_out"     # 下班打卡
    AUTO = "auto"               # 自动记录
    MANUAL = "manual"           # 手动记录
    CORRECTION = "correction"   # 考勤修正


class Attendance(BaseModel):
    """
    考勤模型
    """
    __tablename__ = "attendances"
    
    # 关联信息
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="用户ID")
    date = Column(Date, nullable=False, index=True, comment="考勤日期")
    
    # 打卡时间
    check_in_time = Column(DateTime, nullable=True, comment="上班打卡时间")
    check_out_time = Column(DateTime, nullable=True, comment="下班打卡时间")
    
    # 工作时长
    work_hours = Column(Float, default=0.0, nullable=False, comment="工作时长（小时）")
    overtime_hours = Column(Float, default=0.0, nullable=False, comment="加班时长（小时）")
    
    # 状态信息
    status = Column(Enum(AttendanceStatus), default=AttendanceStatus.PRESENT, nullable=False, comment="考勤状态")
    type = Column(Enum(AttendanceType), default=AttendanceType.CHECK_IN, nullable=False, comment="考勤类型")
    
    # 位置信息
    check_in_location = Column(String(255), nullable=True, comment="上班打卡位置")
    check_out_location = Column(String(255), nullable=True, comment="下班打卡位置")
    
    # 设备信息
    check_in_device = Column(String(100), nullable=True, comment="上班打卡设备")
    check_out_device = Column(String(100), nullable=True, comment="下班打卡设备")
    
    # 人脸识别信息
    check_in_face_match = Column(Float, nullable=True, comment="上班人脸匹配度")
    check_out_face_match = Column(Float, nullable=True, comment="下班人脸匹配度")
    
    # 审核信息
    is_approved = Column(Boolean, default=True, nullable=False, comment="是否已审核")
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True, comment="审核人ID")
    approved_at = Column(DateTime, nullable=True, comment="审核时间")
    approval_notes = Column(Text, nullable=True, comment="审核备注")
    
    # 异常信息
    is_abnormal = Column(Boolean, default=False, nullable=False, comment="是否异常")
    abnormal_reason = Column(Text, nullable=True, comment="异常原因")
    
    # 修正信息
    is_corrected = Column(Boolean, default=False, nullable=False, comment="是否已修正")
    corrected_by = Column(Integer, ForeignKey("users.id"), nullable=True, comment="修正人ID")
    corrected_at = Column(DateTime, nullable=True, comment="修正时间")
    original_check_in = Column(DateTime, nullable=True, comment="原始上班打卡时间")
    original_check_out = Column(DateTime, nullable=True, comment="原始下班打卡时间")
    
    # 其他信息
    notes = Column(Text, nullable=True, comment="备注")
    
    # 关系
    user = relationship("User", foreign_keys=[user_id], back_populates="attendances")
    approver = relationship("User", foreign_keys=[approved_by])
    corrector = relationship("User", foreign_keys=[corrected_by])
    
    def __repr__(self):
        return f"<Attendance(id={self.id}, user_id={self.user_id}, date={self.date}, status={self.status})>"
    
    @property
    def is_late(self) -> bool:
        """是否迟到"""
        if not self.check_in_time:
            return False
        # 这里应该根据公司规定的上班时间判断
        # 简化处理，假设9:00为上班时间
        work_start_time = time(9, 0)
        return self.check_in_time.time() > work_start_time
    
    @property
    def is_early_leave(self) -> bool:
        """是否早退"""
        if not self.check_out_time:
            return False
        # 这里应该根据公司规定的下班时间判断
        # 简化处理，假设18:00为下班时间
        work_end_time = time(18, 0)
        return self.check_out_time.time() < work_end_time
    
    def calculate_work_hours(self):
        """计算工作时长"""
        if self.check_in_time and self.check_out_time:
            # 计算工作时长（小时）
            delta = self.check_out_time - self.check_in_time
            self.work_hours = delta.total_seconds() / 3600
            
            # 计算加班时长（小时）
            # 简化处理，假设超过8小时为加班
            if self.work_hours > 8:
                self.overtime_hours = self.work_hours - 8
            else:
                self.overtime_hours = 0.0
        else:
            self.work_hours = 0.0
            self.overtime_hours = 0.0