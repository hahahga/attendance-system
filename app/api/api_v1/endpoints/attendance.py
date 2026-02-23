"""
考勤API接口
"""

from typing import Any, List, Optional
from datetime import date, datetime, time

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session

from app import schemas
from app.api import deps
from app.services.attendance_service import AttendanceService
from app.models.user import UserRole

router = APIRouter()


@router.get("/", response_model=List[schemas.AttendanceListResponse])
def read_attendances(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    user_id: Optional[int] = None,
    department_id: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_user: schemas.UserResponse = Depends(deps.get_current_active_user)
) -> Any:
    """
    获取考勤记录列表
    """
    # 普通用户只能查看自己的考勤记录
    if current_user.role not in [UserRole.ADMIN, UserRole.HR]:
        user_id = current_user.id
    
    attendances = AttendanceService.get_attendances(
        db=db,
        skip=skip,
        limit=limit,
        user_id=user_id,
        department_id=department_id,
        start_date=start_date,
        end_date=end_date
    )
    return attendances


@router.get("/{attendance_id}", response_model=schemas.AttendanceDetailResponse)
def read_attendance(
    attendance_id: int,
    db: Session = Depends(deps.get_db),
    current_user: schemas.UserResponse = Depends(deps.get_current_active_user)
) -> Any:
    """
    获取考勤记录详细信息
    """
    attendance = AttendanceService.get_attendance_by_id(db, attendance_id=attendance_id)
    if not attendance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="考勤记录不存在"
        )
    
    # 普通用户只能查看自己的考勤记录
    if current_user.role not in [UserRole.ADMIN, UserRole.HR] and current_user.id != attendance.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="没有权限访问此考勤记录"
        )
    
    return attendance


@router.post("/check-in", response_model=schemas.AttendanceResponse)
def check_in(
    *,
    db: Session = Depends(deps.get_db),
    attendance_in: Optional[schemas.AttendanceCreate] = None,
    location: Optional[str] = None,
    current_user: schemas.UserResponse = Depends(deps.get_current_active_user)
) -> Any:
    """
    打卡签到
    """
    # 如果没有传递attendance_in，则创建一个基本的对象
    if not attendance_in:
        attendance_in = schemas.AttendanceCreate(
            user_id=current_user.id,
            date=datetime.now().date(),
            location=location
        )
    
    # 普通用户只能为自己打卡
    if current_user.role not in [UserRole.ADMIN, UserRole.HR] and current_user.id != attendance_in.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="没有权限为其他用户打卡"
        )
    
    attendance = AttendanceService.clock_in(
        db=db, 
        user_id=attendance_in.user_id, 
        clock_in_time=datetime.now(), 
        location=location or attendance_in.location
    )
    return attendance


@router.post("/check-out", response_model=schemas.AttendanceResponse)
def check_out(
    *,
    db: Session = Depends(deps.get_db),
    attendance_in: Optional[schemas.AttendanceCreate] = None,
    location: Optional[str] = None,
    current_user: schemas.UserResponse = Depends(deps.get_current_active_user)
) -> Any:
    """
    打卡签退
    """
    # 如果没有传递attendance_in，则创建一个基本的对象
    if not attendance_in:
        attendance_in = schemas.AttendanceCreate(
            user_id=current_user.id,
            date=datetime.now().date(),
            location=location
        )
    
    # 普通用户只能为自己打卡
    if current_user.role not in [UserRole.ADMIN, UserRole.HR] and current_user.id != attendance_in.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="没有权限为其他用户打卡"
        )
    
    attendance = AttendanceService.clock_out(
        db=db, 
        user_id=attendance_in.user_id, 
        clock_out_time=datetime.now(), 
        location=location or attendance_in.location
    )
    return attendance


@router.post("/face-check-in", response_model=schemas.AttendanceResponse)
def face_check_in(
    *,
    db: Session = Depends(deps.get_db),
    file: UploadFile = File(...),
    user_id: Optional[int] = None,
    current_user: schemas.UserResponse = Depends(deps.get_current_active_user)
) -> Any:
    """
    人脸识别打卡签到
    """
    # 检查文件类型
    if not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="上传的文件必须是图像"
        )
    
    # 检查文件大小（限制为5MB）
    if file.size and file.size > 5 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="图像文件大小不能超过5MB"
        )
    
    # 确定用户ID
    target_user_id = user_id if user_id else current_user.id
    
    # 普通用户只能为自己打卡
    if current_user.role not in [UserRole.ADMIN, UserRole.HR] and current_user.id != target_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="没有权限为其他用户打卡"
        )
    
    # 保存上传的文件到临时位置
    import tempfile
    import os
    
    with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
        temp_file.write(file.file.read())
        temp_file_path = temp_file.name
    
    try:
        # 进行人脸识别打卡
        attendance = AttendanceService.clock_in_by_face(
            db=db, 
            user_id=target_user_id, 
            face_image_path=temp_file_path
        )
        
        if not attendance:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="人脸识别失败，请确保图像清晰且包含人脸"
            )
        
        return attendance
    finally:
        # 清理临时文件
        os.unlink(temp_file_path)


@router.post("/face-check-out", response_model=schemas.AttendanceResponse)
def face_check_out(
    *,
    db: Session = Depends(deps.get_db),
    file: UploadFile = File(...),
    user_id: Optional[int] = None,
    current_user: schemas.UserResponse = Depends(deps.get_current_active_user)
) -> Any:
    """
    人脸识别打卡签退
    """
    # 检查文件类型
    if not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="上传的文件必须是图像"
        )
    
    # 检查文件大小（限制为5MB）
    if file.size and file.size > 5 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="图像文件大小不能超过5MB"
        )
    
    # 确定用户ID
    target_user_id = user_id if user_id else current_user.id
    
    # 普通用户只能为自己打卡
    if current_user.role not in [UserRole.ADMIN, UserRole.HR] and current_user.id != target_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="没有权限为其他用户打卡"
        )
    
    # 保存上传的文件到临时位置
    import tempfile
    import os
    
    with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
        temp_file.write(file.file.read())
        temp_file_path = temp_file.name
    
    try:
        # 进行人脸识别打卡
        attendance = AttendanceService.clock_out_by_face(
            db=db, 
            user_id=target_user_id, 
            face_image_path=temp_file_path
        )
        
        if not attendance:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="人脸识别失败，请确保图像清晰且包含人脸"
            )
        
        return attendance
    finally:
        # 清理临时文件
        os.unlink(temp_file_path)


@router.put("/{attendance_id}", response_model=schemas.AttendanceResponse)
def update_attendance(
    *,
    db: Session = Depends(deps.get_db),
    attendance_id: int,
    attendance_in: schemas.AttendanceUpdate,
    current_user: schemas.UserResponse = Depends(deps.get_current_active_user)
) -> Any:
    """
    更新考勤记录（仅管理员和HR）
    """
    if current_user.role not in [UserRole.ADMIN, UserRole.HR]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="没有权限修改考勤记录"
        )
    
    attendance = AttendanceService.update_attendance(
        db=db, attendance_id=attendance_id, attendance=attendance_in
    )
    return attendance


@router.delete("/{attendance_id}", response_model=schemas.Msg)
def delete_attendance(
    *,
    db: Session = Depends(deps.get_db),
    attendance_id: int,
    current_user: schemas.UserResponse = Depends(deps.get_current_active_superuser)
) -> Any:
    """
    删除考勤记录（仅管理员）
    """
    success = AttendanceService.delete_attendance(db=db, attendance_id=attendance_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="考勤记录不存在"
        )
    
    return {"msg": "考勤记录删除成功"}


@router.get("/statistics/overview", response_model=schemas.AttendanceStatistics)
def get_attendance_statistics(
    db: Session = Depends(deps.get_db),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    department_id: Optional[int] = None,
    current_user: schemas.UserResponse = Depends(deps.get_current_active_user)
) -> Any:
    """
    获取考勤统计信息
    """
    # 普通用户只能查看自己的考勤统计
    user_id = None
    if current_user.role not in [UserRole.ADMIN, UserRole.HR]:
        user_id = current_user.id
    
    stats = AttendanceService.get_attendance_statistics(
        db=db,
        user_id=user_id,
        department_id=department_id,
        start_date=start_date,
        end_date=end_date
    )
    return stats


@router.get("/statistics/user/{user_id}", response_model=schemas.AttendanceStatistics)
def get_user_attendance_statistics(
    user_id: int,
    db: Session = Depends(deps.get_db),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_user: schemas.UserResponse = Depends(deps.get_current_active_user)
) -> Any:
    """
    获取用户考勤统计信息
    """
    # 普通用户只能查看自己的考勤统计
    if current_user.role not in [UserRole.ADMIN, UserRole.HR] and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="没有权限查看此用户的考勤统计"
        )
    
    stats = AttendanceService.get_attendance_statistics(
        db=db,
        user_id=user_id,
        start_date=start_date,
        end_date=end_date
    )
    return stats


@router.get("/statistics/monthly/{year}/{month}", response_model=schemas.MonthlyAttendanceStatistics)
def get_monthly_attendance_statistics(
    year: int,
    month: int,
    db: Session = Depends(deps.get_db),
    department_id: Optional[int] = None,
    current_user: schemas.UserResponse = Depends(deps.get_current_active_user)
) -> Any:
    """
    获取月度考勤统计信息
    """
    # 普通用户只能查看自己的考勤统计
    user_id = None
    if current_user.role not in [UserRole.ADMIN, UserRole.HR]:
        user_id = current_user.id
    
    stats = AttendanceService.get_monthly_attendance_report(
        db=db,
        year=year,
        month=month,
        user_id=user_id,
        department_id=department_id
    )
    return stats


@router.post("/export", response_model=schemas.Msg)
def export_attendances(
    *,
    db: Session = Depends(deps.get_db),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    department_id: Optional[int] = None,
    user_id: Optional[int] = None,
    current_user: schemas.UserResponse = Depends(deps.get_current_active_user)
) -> Any:
    """
    导出考勤数据
    """
    # 普通用户只能导出自己的考勤数据
    if current_user.role not in [UserRole.ADMIN, UserRole.HR]:
        user_id = current_user.id
    
    # 暂时禁用导出功能，返回提示消息
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="导出功能暂未实现，请稍后再试"
    )