"""
用户API接口
"""

from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session

from app import schemas
from app.api import deps
from app.core.config import settings
from app.services.user_service import UserService

router = APIRouter()


@router.get("/", response_model=List[schemas.UserListResponse])
def read_users(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    department_id: Optional[int] = None,
    role: Optional[str] = None,
    is_active: Optional[bool] = None,
    search: Optional[str] = None,
    current_user: schemas.UserResponse = Depends(deps.get_current_active_superuser)
) -> Any:
    """
    获取用户列表（仅管理员）
    """
    users = UserService.get_users(
        db=db,
        skip=skip,
        limit=limit,
        department_id=department_id,
        role=role,
        is_active=is_active,
        search=search
    )
    return users


@router.post("/", response_model=schemas.UserResponse)
def create_user(
    *,
    db: Session = Depends(deps.get_db),
    user_in: schemas.UserCreate,
    current_user: schemas.UserResponse = Depends(deps.get_current_active_superuser)
) -> Any:
    """
    创建新用户（仅管理员）
    """
    user = UserService.get_user_by_username(db, username=user_in.username)
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在"
        )
    
    user = UserService.get_user_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="邮箱已存在"
        )
    
    user = UserService.create_user(db=db, user=user_in)
    return user


@router.put("/me", response_model=schemas.UserResponse)
def update_user_me(
    *,
    db: Session = Depends(deps.get_db),
    user_in: schemas.UserUpdate,
    current_user: schemas.UserResponse = Depends(deps.get_current_active_user)
) -> Any:
    """
    更新当前用户信息
    """
    user = UserService.update_user(
        db=db, user_id=current_user.id, user=user_in
    )
    return user


@router.get("/me", response_model=schemas.UserDetailResponse)
def read_user_me(
    db: Session = Depends(deps.get_db),
    current_user: schemas.UserResponse = Depends(deps.get_current_active_user)
) -> Any:
    """
    获取当前用户详细信息
    """
    user = UserService.get_user_with_details(db=db, user_id=current_user.id)
    return user


@router.get("/{user_id}", response_model=schemas.UserDetailResponse)
def read_user(
    user_id: int,
    db: Session = Depends(deps.get_db),
    current_user: schemas.UserResponse = Depends(deps.get_current_active_user)
) -> Any:
    """
    获取用户详细信息
    """
    user = UserService.get_user_with_details(db=db, user_id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 普通用户只能查看自己的详细信息
    if current_user.role != "admin" and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="没有权限访问此用户信息"
        )
    
    return user


@router.put("/{user_id}", response_model=schemas.UserResponse)
def update_user(
    *,
    db: Session = Depends(deps.get_db),
    user_id: int,
    user_in: schemas.UserUpdate,
    current_user: schemas.UserResponse = Depends(deps.get_current_active_superuser)
) -> Any:
    """
    更新用户信息（仅管理员）
    """
    user = UserService.get_user_by_id(db, user_id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    user = UserService.update_user(db=db, user_id=user_id, user=user_in)
    return user


@router.delete("/{user_id}", response_model=schemas.Msg)
def delete_user(
    *,
    db: Session = Depends(deps.get_db),
    user_id: int,
    current_user: schemas.UserResponse = Depends(deps.get_current_active_superuser)
) -> Any:
    """
    删除用户（仅管理员）
    """
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能删除自己的账户"
        )
    
    user = UserService.get_user_by_id(db, user_id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    UserService.delete_user(db=db, user_id=user_id)
    return {"msg": "用户删除成功"}


@router.post("/upload-face", response_model=schemas.Msg)
def upload_face_image(
    *,
    db: Session = Depends(deps.get_db),
    file: UploadFile = File(...),
    current_user: schemas.UserResponse = Depends(deps.get_current_active_user)
) -> Any:
    """
    上传人脸图像用于人脸识别
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
    
    # 保存人脸图像
    try:
        UserService.save_face_image(
            db=db, user_id=current_user.id, file=file
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"人脸图像保存失败: {str(e)}"
        )
    
    return {"msg": "人脸图像上传成功"}


@router.delete("/face", response_model=schemas.Msg)
def delete_face_image(
    db: Session = Depends(deps.get_db),
    current_user: schemas.UserResponse = Depends(deps.get_current_active_user)
) -> Any:
    """
    删除人脸图像
    """
    try:
        UserService.delete_face_image(db=db, user_id=current_user.id)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除人脸图像失败: {str(e)}"
        )
    
    return {"msg": "人脸图像删除成功"}


@router.get("/statistics/overview", response_model=schemas.UserStatistics)
def get_user_statistics(
    db: Session = Depends(deps.get_db),
    current_user: schemas.UserResponse = Depends(deps.get_current_active_superuser)
) -> Any:
    """
    获取用户统计信息（仅管理员）
    """
    stats = UserService.get_user_statistics(db=db)
    return stats


@router.get("/statistics/department/{department_id}", response_model=schemas.UserStatistics)
def get_department_user_statistics(
    department_id: int,
    db: Session = Depends(deps.get_db),
    current_user: schemas.UserResponse = Depends(deps.get_current_active_user)
) -> Any:
    """
    获取部门用户统计信息
    """
    # 检查权限
    if current_user.role != "admin" and current_user.department_id != department_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="没有权限访问此部门的统计信息"
        )
    
    stats = UserService.get_user_statistics(db=db, department_id=department_id)
    return stats


@router.post("/export", response_model=schemas.Msg)
def export_users(
    *,
    db: Session = Depends(deps.get_db),
    department_id: Optional[int] = None,
    current_user: schemas.UserResponse = Depends(deps.get_current_active_superuser)
) -> Any:
    """
    导出用户数据（仅管理员）
    """
    file_path = UserService.export_users_to_excel(db=db, department_id=department_id)
    if not file_path:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="导出用户数据失败"
        )
    
    return {"msg": f"用户数据导出成功，文件保存在: {file_path}"}


@router.post("/import", response_model=schemas.Msg)
def import_users(
    *,
    db: Session = Depends(deps.get_db),
    file: UploadFile = File(...),
    current_user: schemas.UserResponse = Depends(deps.get_current_active_superuser)
) -> Any:
    """
    导入用户数据（仅管理员）
    """
    # 检查文件类型
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="上传的文件必须是Excel文件"
        )
    
    # 导入用户数据
    result = UserService.import_users_from_excel(db=db, file=file)
    
    return {
        "msg": f"用户数据导入完成，成功: {result['success']}, 失败: {result['failed']}"
    }