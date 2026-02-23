"""
请假API接口
"""

from typing import Any, List, Optional
from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session

from app import schemas
from app.api import deps
from app.services.leave_service import LeaveService

router = APIRouter()


@router.get("/", response_model=List[schemas.LeaveListResponse])
def read_leaves(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    user_id: Optional[int] = None,
    department_id: Optional[int] = None,
    leave_type: Optional[str] = None,
    status: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_user: schemas.UserResponse = Depends(deps.get_current_active_user)
) -> Any:
    """
    获取请假记录列表
    """
    # 普通用户只能查看自己的请假记录
    if current_user.role not in ["admin", "hr", "manager"]:
        user_id = current_user.id
    
    leaves = LeaveService.get_leaves(
        db=db,
        skip=skip,
        limit=limit,
        user_id=user_id,
        department_id=department_id,
        leave_type=leave_type,
        status=status,
        start_date=start_date,
        end_date=end_date
    )
    return leaves


@router.get("/{leave_id}", response_model=schemas.LeaveDetailResponse)
def read_leave(
    leave_id: int,
    db: Session = Depends(deps.get_db),
    current_user: schemas.UserResponse = Depends(deps.get_current_active_user)
) -> Any:
    """
    获取请假记录详细信息
    """
    leave = LeaveService.get_leave_by_id(db, leave_id=leave_id)
    if not leave:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="请假记录不存在"
        )
    
    # 检查权限
    if current_user.role not in ["admin", "hr", "manager"] and current_user.id != leave.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="没有权限访问此请假记录"
        )
    
    return leave


@router.post("/", response_model=schemas.LeaveResponse)
def create_leave(
    *,
    db: Session = Depends(deps.get_db),
    leave_in: schemas.LeaveCreate,
    current_user: schemas.UserResponse = Depends(deps.get_current_active_user)
) -> Any:
    """
    创建请假申请
    """
    # 普通用户只能为自己申请请假
    if current_user.role not in ["admin", "hr", "manager"] and current_user.id != leave_in.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="没有权限为其他用户申请请假"
        )
    
    leave = LeaveService.create_leave(db=db, leave=leave_in)
    return leave


@router.put("/{leave_id}", response_model=schemas.LeaveResponse)
def update_leave(
    *,
    db: Session = Depends(deps.get_db),
    leave_id: int,
    leave_in: schemas.LeaveUpdate,
    current_user: schemas.UserResponse = Depends(deps.get_current_active_user)
) -> Any:
    """
    更新请假申请
    """
    # 检查请假记录是否存在
    leave = LeaveService.get_leave_by_id(db, leave_id=leave_id)
    if not leave:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="请假记录不存在"
        )
    
    # 检查权限
    if current_user.role not in ["admin", "hr", "manager"] and current_user.id != leave.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="没有权限修改此请假记录"
        )
    
    # 已审批的请假记录不能修改
    if leave.status in ["approved", "rejected"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="已审批的请假记录不能修改"
        )
    
    leave = LeaveService.update_leave(db=db, leave_id=leave_id, leave=leave_in)
    return leave


@router.post("/{leave_id}/approve", response_model=schemas.LeaveResponse)
def approve_leave(
    *,
    db: Session = Depends(deps.get_db),
    leave_id: int,
    approval_in: schemas.LeaveApproval,
    current_user: schemas.UserResponse = Depends(deps.get_current_active_user)
) -> Any:
    """
    审批请假申请
    """
    # 检查权限
    if current_user.role not in ["admin", "hr", "manager"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="没有权限审批请假申请"
        )
    
    # 检查请假记录是否存在
    leave = LeaveService.get_leave_by_id(db, leave_id=leave_id)
    if not leave:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="请假记录不存在"
        )
    
    # 已审批的请假记录不能再次审批
    if leave.status in ["approved", "rejected"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="请假记录已被审批"
        )
    
    leave = LeaveService.approve_leave(
        db=db,
        leave_id=leave_id,
        approver_id=current_user.id,
        approval=approval_in.approval,
        comment=approval_in.comment
    )
    return leave


@router.post("/{leave_id}/cancel", response_model=schemas.LeaveResponse)
def cancel_leave(
    *,
    db: Session = Depends(deps.get_db),
    leave_id: int,
    current_user: schemas.UserResponse = Depends(deps.get_current_active_user)
) -> Any:
    """
    取消请假申请
    """
    # 检查请假记录是否存在
    leave = LeaveService.get_leave_by_id(db, leave_id=leave_id)
    if not leave:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="请假记录不存在"
        )
    
    # 检查权限
    if current_user.role not in ["admin", "hr", "manager"] and current_user.id != leave.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="没有权限取消此请假记录"
        )
    
    # 已审批的请假记录不能取消
    if leave.status in ["approved", "rejected"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="已审批的请假记录不能取消"
        )
    
    leave = LeaveService.cancel_leave(db=db, leave_id=leave_id)
    return leave


@router.delete("/{leave_id}", response_model=schemas.Msg)
def delete_leave(
    *,
    db: Session = Depends(deps.get_db),
    leave_id: int,
    current_user: schemas.UserResponse = Depends(deps.get_current_active_superuser)
) -> Any:
    """
    删除请假记录（仅管理员）
    """
    success = LeaveService.delete_leave(db=db, leave_id=leave_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="请假记录不存在"
        )
    
    return {"msg": "请假记录删除成功"}


@router.get("/balance/{user_id}", response_model=schemas.LeaveBalanceResponse)
def get_leave_balance(
    user_id: int,
    db: Session = Depends(deps.get_db),
    current_user: schemas.UserResponse = Depends(deps.get_current_active_user)
) -> Any:
    """
    获取用户请假余额
    """
    # 检查权限
    if current_user.role not in ["admin", "hr", "manager"] and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="没有权限查看此用户的请假余额"
        )
    
    balance = LeaveService.get_leave_balance(db=db, user_id=user_id)
    return balance


@router.get("/statistics/overview", response_model=schemas.LeaveStatistics)
def get_leave_statistics(
    db: Session = Depends(deps.get_db),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    department_id: Optional[int] = None,
    current_user: schemas.UserResponse = Depends(deps.get_current_active_user)
) -> Any:
    """
    获取请假统计信息
    """
    # 普通用户只能查看自己的请假统计
    user_id = None
    if current_user.role not in ["admin", "hr", "manager"]:
        user_id = current_user.id
    
    stats = LeaveService.get_leave_statistics(
        db=db,
        user_id=user_id,
        department_id=department_id,
        start_date=start_date,
        end_date=end_date
    )
    return stats


@router.get("/statistics/user/{user_id}", response_model=schemas.LeaveStatistics)
def get_user_leave_statistics(
    user_id: int,
    db: Session = Depends(deps.get_db),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_user: schemas.UserResponse = Depends(deps.get_current_active_user)
) -> Any:
    """
    获取用户请假统计信息
    """
    # 检查权限
    if current_user.role not in ["admin", "hr", "manager"] and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="没有权限查看此用户的请假统计"
        )
    
    stats = LeaveService.get_leave_statistics(
        db=db,
        user_id=user_id,
        start_date=start_date,
        end_date=end_date
    )
    return stats


@router.get("/statistics/monthly/{year}/{month}", response_model=schemas.MonthlyLeaveStatistics)
def get_monthly_leave_statistics(
    year: int,
    month: int,
    db: Session = Depends(deps.get_db),
    department_id: Optional[int] = None,
    current_user: schemas.UserResponse = Depends(deps.get_current_active_user)
) -> Any:
    """
    获取月度请假统计信息
    """
    # 普通用户只能查看自己的请假统计
    user_id = None
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


@router.post("/export", response_model=schemas.Msg)
def export_leaves(
    *,
    db: Session = Depends(deps.get_db),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    department_id: Optional[int] = None,
    user_id: Optional[int] = None,
    current_user: schemas.UserResponse = Depends(deps.get_current_active_user)
) -> Any:
    """
    导出请假数据
    """
    # 普通用户只能导出自己的请假数据
    if current_user.role not in ["admin", "hr", "manager"]:
        user_id = current_user.id
    
    file_path = LeaveService.export_leaves_to_excel(
        db=db,
        start_date=start_date,
        end_date=end_date,
        department_id=department_id,
        user_id=user_id
    )
    
    if not file_path:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="导出请假数据失败"
        )
    
    return {"msg": f"请假数据导出成功，文件保存在: {file_path}"}