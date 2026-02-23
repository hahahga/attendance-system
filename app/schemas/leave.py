"""
请假相关的Pydantic模式
"""

from typing import Optional, List
from datetime import datetime, date, time
from pydantic import BaseModel, Field, validator


class LeaveBase(BaseModel):
    """
    请假基础模式
    """
    leave_type: str = Field(..., description="请假类型")
    start_date: date = Field(..., description="开始日期")
    end_date: date = Field(..., description="结束日期")
    start_time: Optional[time] = Field(None, description="开始时间")
    end_time: Optional[time] = Field(None, description="结束时间")
    days: Optional[float] = Field(0.0, description="请假天数")
    hours: Optional[float] = Field(0.0, description="请假小时数")
    replacement_user_id: Optional[int] = Field(None, description="代理人ID")
    reason: Optional[str] = Field(None, description="请假原因")
    notes: Optional[str] = Field(None, description="备注")
    
    @validator('end_date')
    def end_date_after_start_date(cls, v, values):
        if 'start_date' in values and v < values['start_date']:
            raise ValueError('结束日期不能早于开始日期')
        return v


class LeaveCreate(LeaveBase):
    """
    请假创建模式
    """
    pass


class LeaveUpdate(BaseModel):
    """
    请假更新模式
    """
    leave_type: Optional[str] = Field(None, description="请假类型")
    start_date: Optional[date] = Field(None, description="开始日期")
    end_date: Optional[date] = Field(None, description="结束日期")
    start_time: Optional[time] = Field(None, description="开始时间")
    end_time: Optional[time] = Field(None, description="结束时间")
    days: Optional[float] = Field(None, description="请假天数")
    hours: Optional[float] = Field(None, description="请假小时数")
    replacement_user_id: Optional[int] = Field(None, description="代理人ID")
    reason: Optional[str] = Field(None, description="请假原因")
    notes: Optional[str] = Field(None, description="备注")
    
    @validator('end_date')
    def end_date_after_start_date(cls, v, values):
        if 'start_date' in values and v and values['start_date'] and v < values['start_date']:
            raise ValueError('结束日期不能早于开始日期')
        return v


class LeaveApproval(BaseModel):
    """
    请假审批模式
    """
    leave_id: int = Field(..., description="请假记录ID")
    action: str = Field(..., description="审批动作 (approve/reject)")
    reason: Optional[str] = Field(None, description="审批意见或拒绝原因")


class LeaveCancel(BaseModel):
    """
    请假取消模式
    """
    leave_id: int = Field(..., description="请假记录ID")
    reason: Optional[str] = Field(None, description="取消原因")


class LeaveResponse(LeaveBase):
    """
    请假响应模式
    """
    id: int = Field(..., description="请假记录ID")
    user_id: int = Field(..., description="用户ID")
    status: str = Field(..., description="请假状态")
    applied_at: datetime = Field(..., description="申请时间")
    approved_by: Optional[int] = Field(None, description="审批人ID")
    approved_at: Optional[datetime] = Field(None, description="审批时间")
    rejection_reason: Optional[str] = Field(None, description="拒绝原因")
    replacement_approved: Optional[bool] = Field(None, description="代理人是否同意")
    replacement_approved_at: Optional[datetime] = Field(None, description="代理人同意时间")
    attachment_path: Optional[str] = Field(None, description="附件路径")
    current_approver_id: Optional[int] = Field(None, description="当前审批人ID")
    next_approver_id: Optional[int] = Field(None, description="下一审批人ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    class Config:
        orm_mode = True


class LeaveDetailResponse(LeaveResponse):
    """
    请假详情响应模式
    """
    user: Optional[dict] = Field(None, description="用户信息")
    approver: Optional[dict] = Field(None, description="审批人信息")
    replacement: Optional[dict] = Field(None, description="代理人信息")
    current_approver: Optional[dict] = Field(None, description="当前审批人信息")
    next_approver: Optional[dict] = Field(None, description="下一审批人信息")


class LeaveListResponse(BaseModel):
    """
    请假列表响应模式
    """
    leaves: List[LeaveResponse] = Field(..., description="请假记录列表")
    total: int = Field(..., description="总数量")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页数量")
    total_pages: int = Field(..., description="总页数")


class LeaveBalanceResponse(BaseModel):
    """
    请假余额响应模式
    """
    user_id: int = Field(..., description="用户ID")
    annual_leave_total: float = Field(..., description="年假总额")
    annual_leave_used: float = Field(..., description="年假已使用")
    annual_leave_remaining: float = Field(..., description="年假剩余")
    sick_leave_total: float = Field(..., description="病假总额")
    sick_leave_used: float = Field(..., description="病假已使用")
    sick_leave_remaining: float = Field(..., description="病假剩余")
    personal_leave_total: float = Field(..., description="事假总额")
    personal_leave_used: float = Field(..., description="事假已使用")
    personal_leave_remaining: float = Field(..., description="事假剩余")


class LeaveStatisticsResponse(BaseModel):
    """
    请假统计响应模式
    """
    user_id: int = Field(..., description="用户ID")
    period: str = Field(..., description="统计周期")
    total_leaves: int = Field(..., description="总请假次数")
    annual_leave_days: float = Field(..., description="年假天数")
    sick_leave_days: float = Field(..., description="病假天数")
    personal_leave_days: float = Field(..., description="事假天数")
    other_leave_days: float = Field(..., description="其他请假天数")
    total_leave_days: float = Field(..., description="总请假天数")
    approved_leaves: int = Field(..., description="已批准请假次数")
    pending_leaves: int = Field(..., description="待审批请假次数")
    rejected_leaves: int = Field(..., description="已拒绝请假次数")


class LeaveMonthlyReportResponse(BaseModel):
    """
    请假月报响应模式
    """
    year: int = Field(..., description="年份")
    month: int = Field(..., description="月份")
    user_id: int = Field(..., description="用户ID")
    user_name: str = Field(..., description="用户姓名")
    department_name: Optional[str] = Field(None, description="部门名称")
    annual_leave_days: float = Field(..., description="年假天数")
    sick_leave_days: float = Field(..., description="病假天数")
    personal_leave_days: float = Field(..., description="事假天数")
    other_leave_days: float = Field(..., description="其他请假天数")
    total_leave_days: float = Field(..., description="总请假天数")
    leave_count: int = Field(..., description="请假次数")