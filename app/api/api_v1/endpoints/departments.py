"""
部门API接口
"""

from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import schemas
from app.api import deps
from app.services.department_service import DepartmentService

router = APIRouter()


@router.get("/", response_model=List[schemas.DepartmentListResponse])
def read_departments(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    parent_id: Optional[int] = None,
    is_active: Optional[bool] = None,
    search: Optional[str] = None,
    current_user: schemas.UserResponse = Depends(deps.get_current_active_user)
) -> Any:
    """
    获取部门列表
    """
    departments = DepartmentService.get_departments(
        db=db,
        skip=skip,
        limit=limit,
        parent_id=parent_id,
        is_active=is_active,
        search=search
    )
    return departments


@router.post("/", response_model=schemas.DepartmentResponse)
def create_department(
    *,
    db: Session = Depends(deps.get_db),
    department_in: schemas.DepartmentCreate,
    current_user: schemas.UserResponse = Depends(deps.get_current_active_superuser)
) -> Any:
    """
    创建新部门（仅管理员）
    """
    department = DepartmentService.create_department(db=db, department=department_in)
    return department


@router.put("/{department_id}", response_model=schemas.DepartmentResponse)
def update_department(
    *,
    db: Session = Depends(deps.get_db),
    department_id: int,
    department_in: schemas.DepartmentUpdate,
    current_user: schemas.UserResponse = Depends(deps.get_current_active_superuser)
) -> Any:
    """
    更新部门信息（仅管理员）
    """
    department = DepartmentService.update_department(
        db=db, department_id=department_id, department=department_in
    )
    return department


@router.get("/{department_id}", response_model=schemas.DepartmentDetailResponse)
def read_department(
    department_id: int,
    db: Session = Depends(deps.get_db),
    current_user: schemas.UserResponse = Depends(deps.get_current_active_user)
) -> Any:
    """
    获取部门详细信息
    """
    department = DepartmentService.get_department_by_id(db, department_id=department_id)
    if not department:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="部门不存在"
        )
    
    return department


@router.delete("/{department_id}", response_model=schemas.Msg)
def delete_department(
    *,
    db: Session = Depends(deps.get_db),
    department_id: int,
    current_user: schemas.UserResponse = Depends(deps.get_current_active_superuser)
) -> Any:
    """
    删除部门（仅管理员）
    """
    success = DepartmentService.delete_department(db=db, department_id=department_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="删除部门失败"
        )
    
    return {"msg": "部门删除成功"}


@router.get("/tree", response_model=List[schemas.DepartmentTreeResponse])
def read_department_tree(
    parent_id: Optional[int] = None,
    db: Session = Depends(deps.get_db),
    current_user: schemas.UserResponse = Depends(deps.get_current_active_user)
) -> Any:
    """
    获取部门树结构
    """
    tree = DepartmentService.get_department_tree(db=db, parent_id=parent_id)
    return tree


@router.get("/{department_id}/children", response_model=List[schemas.DepartmentListResponse])
def read_department_children(
    department_id: int,
    db: Session = Depends(deps.get_db),
    current_user: schemas.UserResponse = Depends(deps.get_current_active_user)
) -> Any:
    """
    获取部门的所有子部门
    """
    children = DepartmentService.get_all_children(db=db, department_id=department_id)
    return children


@router.get("/{department_id}/path", response_model=List[schemas.DepartmentListResponse])
def read_department_path(
    department_id: int,
    db: Session = Depends(deps.get_db),
    current_user: schemas.UserResponse = Depends(deps.get_current_active_user)
) -> Any:
    """
    获取部门路径（从根部门到当前部门）
    """
    path = DepartmentService.get_department_path(db=db, department_id=department_id)
    return path


@router.get("/statistics/overview", response_model=schemas.DepartmentStatistics)
def get_department_statistics(
    db: Session = Depends(deps.get_db),
    current_user: schemas.UserResponse = Depends(deps.get_current_active_user)
) -> Any:
    """
    获取部门统计信息
    """
    stats = DepartmentService.get_department_statistics(db=db)
    return stats


@router.get("/{department_id}/statistics", response_model=schemas.DepartmentStatistics)
def get_single_department_statistics(
    department_id: int,
    db: Session = Depends(deps.get_db),
    current_user: schemas.UserResponse = Depends(deps.get_current_active_user)
) -> Any:
    """
    获取单个部门的统计信息
    """
    # 检查部门是否存在
    department = DepartmentService.get_department_by_id(db, department_id=department_id)
    if not department:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="部门不存在"
        )
    
    stats = DepartmentService.get_department_statistics(db=db, department_id=department_id)
    return stats