"""
考勤相关的Pydantic模式
"""

from typing import Optional, List
from datetime import datetime, date, time
from pydantic import BaseModel, Field, validator


class AttendanceBase(BaseModel):
    """
    考勤基础模式
    """
    user_id: int = Field(..., description="用户ID")
    date: date = Field(..., description="考勤日期")
    check_in_time: Optional[datetime] = Field(None, description="上班打卡时间")
    check_out_time: Optional[datetime] = Field(None, description="下班打卡时间")
    work_hours: Optional[float] = Field(0.0, description="工作时长（小时）")
    overtime_hours: Optional[float] = Field(0.0, description="加班时长（小时）")
    status: Optional[str] = Field("present", description="考勤状态")
    type: Optional[str] = Field("check_in", description="考勤类型")
    check_in_location: Optional[str] = Field(None, description="上班打卡位置")
    check_out_location: Optional[str] = Field(None, description="下班打卡位置")
    check_in_device: Optional[str] = Field(None, description="上班打卡设备")
    check_out_device: Optional[str] = Field(None, description="下班打卡设备")
    check_in_face_match: Optional[float] = Field(None, description="上班人脸匹配度")
    check_out_face_match: Optional[float] = Field(None, description="下班人脸匹配度")
    notes: Optional[str] = Field(None, description="备注")


class AttendanceCreate(AttendanceBase):
    """
    考勤创建模式
    """
    pass


class AttendanceUpdate(BaseModel):
    """
    考勤更新模式
    """
    check_in_time: Optional[datetime] = Field(None, description="上班打卡时间")
    check_out_time: Optional[datetime] = Field(None, description="下班打卡时间")
    work_hours: Optional[float] = Field(None, description="工作时长（小时）")
    overtime_hours: Optional[float] = Field(None, description="加班时长（小时）")
    status: Optional[str] = Field(None, description="考勤状态")
    type: Optional[str] = Field(None, description="考勤类型")
    check_in_location: Optional[str] = Field(None, description="上班打卡位置")
    check_out_location: Optional[str] = Field(None, description="下班打卡位置")
    check_in_device: Optional[str] = Field(None, description="上班打卡设备")
    check_out_device: Optional[str] = Field(None, description="下班打卡设备")
    check_in_face_match: Optional[float] = Field(None, description="上班人脸匹配度")
    check_out_face_match: Optional[float] = Field(None, description="下班人脸匹配度")
    is_approved: Optional[bool] = Field(None, description="是否已审核")
    approval_notes: Optional[str] = Field(None, description="审核备注")
    is_abnormal: Optional[bool] = Field(None, description="是否异常")
    abnormal_reason: Optional[str] = Field(None, description="异常原因")
    notes: Optional[str] = Field(None, description="备注")


class AttendanceCheckIn(BaseModel):
    """
    上班打卡模式
    """
    location: Optional[str] = Field(None, description="打卡位置")
    device: Optional[str] = Field(None, description="打卡设备")
    face_image: Optional[str] = Field(None, description="人脸图像Base64编码")
    notes: Optional[str] = Field(None, description="备注")


class AttendanceCheckOut(BaseModel):
    """
    下班打卡模式
    """
    location: Optional[str] = Field(None, description="打卡位置")
    device: Optional[str] = Field(None, description="打卡设备")
    face_image: Optional[str] = Field(None, description="人脸图像Base64编码")
    notes: Optional[str] = Field(None, description="备注")


class AttendanceCorrection(BaseModel):
    """
    考勤修正模式
    """
    attendance_id: int = Field(..., description="考勤记录ID")
    check_in_time: Optional[datetime] = Field(None, description="修正后上班打卡时间")
    check_out_time: Optional[datetime] = Field(None, description="修正后下班打卡时间")
    reason: str = Field(..., description="修正原因")


class AttendanceResponse(AttendanceBase):
    """
    考勤响应模式
    """
    id: int = Field(..., description="考勤记录ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    is_approved: Optional[bool] = Field(None, description="是否已审核")
    approved_by: Optional[int] = Field(None, description="审核人ID")
    approved_at: Optional[datetime] = Field(None, description="审核时间")
    approval_notes: Optional[str] = Field(None, description="审核备注")
    is_abnormal: Optional[bool] = Field(None, description="是否异常")
    abnormal_reason: Optional[str] = Field(None, description="异常原因")
    is_corrected: Optional[bool] = Field(None, description="是否已修正")
    corrected_by: Optional[int] = Field(None, description="修正人ID")
    corrected_at: Optional[datetime] = Field(None, description="修正时间")
    original_check_in: Optional[datetime] = Field(None, description="原始上班打卡时间")
    original_check_out: Optional[datetime] = Field(None, description="原始下班打卡时间")
    
    class Config:
        orm_mode = True


class AttendanceDetailResponse(AttendanceResponse):
    """
    考勤详情响应模式
    """
    user: Optional[dict] = Field(None, description="用户信息")
    approver: Optional[dict] = Field(None, description="审核人信息")
    corrector: Optional[dict] = Field(None, description="修正人信息")


class AttendanceListResponse(BaseModel):
    """
    考勤列表响应模式
    """
    attendances: List[AttendanceResponse] = Field(..., description="考勤记录列表")
    total: int = Field(..., description="总数量")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页数量")
    total_pages: int = Field(..., description="总页数")


class AttendanceStatisticsResponse(BaseModel):
    """
    考勤统计响应模式
    """
    user_id: int = Field(..., description="用户ID")
    period: str = Field(..., description="统计周期")
    total_days: int = Field(..., description="总天数")
    present_days: int = Field(..., description="出勤天数")
    absent_days: int = Field(..., description="缺勤天数")
    late_days: int = Field(..., description="迟到天数")
    early_leave_days: int = Field(..., description="早退天数")
    leave_days: int = Field(..., description="请假天数")
    overtime_hours: float = Field(..., description="加班时长")
    work_hours: float = Field(..., description="工作时长")
    attendance_rate: float = Field(..., description="出勤率")


class AttendanceMonthlyReportResponse(BaseModel):
    """
    考勤月报响应模式
    """
    year: int = Field(..., description="年份")
    month: int = Field(..., description="月份")
    user_id: int = Field(..., description="用户ID")
    user_name: str = Field(..., description="用户姓名")
    department_name: Optional[str] = Field(None, description="部门名称")
    work_days: int = Field(..., description="工作天数")
    actual_days: int = Field(..., description="实际出勤天数")
    leave_days: int = Field(..., description="请假天数")
    absent_days: int = Field(..., description="缺勤天数")
    late_count: int = Field(..., description="迟到次数")
    early_leave_count: int = Field(..., description="早退次数")
    overtime_hours: float = Field(..., description="加班时长")
    work_hours: float = Field(..., description="工作时长")
    attendance_rate: float = Field(..., description="出勤率")