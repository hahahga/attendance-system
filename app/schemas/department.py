"""
部门相关的Pydantic模式
"""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, validator


class DepartmentBase(BaseModel):
    """
    部门基础模式
    """
    name: str = Field(..., min_length=1, max_length=100, description="部门名称")
    code: str = Field(..., min_length=1, max_length=20, description="部门代码")
    description: Optional[str] = Field(None, description="部门描述")
    parent_id: Optional[int] = Field(None, description="上级部门ID")
    level: Optional[int] = Field(1, description="部门层级")
    sort_order: Optional[int] = Field(0, description="排序顺序")
    is_active: Optional[bool] = Field(True, description="是否激活")
    manager_id: Optional[int] = Field(None, description="部门主管ID")
    phone: Optional[str] = Field(None, max_length=20, description="联系电话")
    email: Optional[str] = Field(None, max_length=100, description="联系邮箱")
    location: Optional[str] = Field(None, max_length=255, description="办公地点")
    notes: Optional[str] = Field(None, description="备注")


class DepartmentCreate(DepartmentBase):
    """
    部门创建模式
    """
    pass


class DepartmentUpdate(BaseModel):
    """
    部门更新模式
    """
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="部门名称")
    code: Optional[str] = Field(None, min_length=1, max_length=20, description="部门代码")
    description: Optional[str] = Field(None, description="部门描述")
    parent_id: Optional[int] = Field(None, description="上级部门ID")
    level: Optional[int] = Field(None, description="部门层级")
    sort_order: Optional[int] = Field(None, description="排序顺序")
    is_active: Optional[bool] = Field(None, description="是否激活")
    manager_id: Optional[int] = Field(None, description="部门主管ID")
    phone: Optional[str] = Field(None, max_length=20, description="联系电话")
    email: Optional[str] = Field(None, max_length=100, description="联系邮箱")
    location: Optional[str] = Field(None, max_length=255, description="办公地点")
    notes: Optional[str] = Field(None, description="备注")


class DepartmentResponse(DepartmentBase):
    """
    部门响应模式
    """
    id: int = Field(..., description="部门ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    class Config:
        orm_mode = True


class DepartmentDetailResponse(DepartmentResponse):
    """
    部门详情响应模式
    """
    parent: Optional[dict] = Field(None, description="上级部门信息")
    children: Optional[List[dict]] = Field(None, description="子部门列表")
    manager: Optional[dict] = Field(None, description="部门主管信息")
    user_count: Optional[int] = Field(None, description="部门用户数量")
    full_name: Optional[str] = Field(None, description="完整部门名称")


class DepartmentTreeResponse(BaseModel):
    """
    部门树响应模式
    """
    id: int = Field(..., description="部门ID")
    name: str = Field(..., description="部门名称")
    code: str = Field(..., description="部门代码")
    level: int = Field(..., description="部门层级")
    is_active: bool = Field(..., description="是否激活")
    children: Optional[List["DepartmentTreeResponse"]] = Field(None, description="子部门列表")
    
    class Config:
        orm_mode = True


# 解决递归引用问题
DepartmentTreeResponse.update_forward_refs()


class DepartmentListResponse(BaseModel):
    """
    部门列表响应模式
    """
    departments: List[DepartmentResponse] = Field(..., description="部门列表")
    total: int = Field(..., description="总数量")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页数量")
    total_pages: int = Field(..., description="总页数")