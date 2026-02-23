"""
部门数据模型
"""

from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship

from .base import BaseModel


class Department(BaseModel):
    """
    部门模型
    """
    __tablename__ = "departments"
    
    # 基本信息
    name = Column(String(100), unique=True, index=True, nullable=False, comment="部门名称")
    code = Column(String(20), unique=True, index=True, nullable=False, comment="部门代码")
    description = Column(Text, nullable=True, comment="部门描述")
    
    # 层级关系
    parent_id = Column(Integer, ForeignKey("departments.id"), nullable=True, comment="上级部门ID")
    level = Column(Integer, default=1, nullable=False, comment="部门层级")
    sort_order = Column(Integer, default=0, nullable=False, comment="排序顺序")
    
    # 状态信息
    is_active = Column(Integer, default=1, nullable=False, comment="是否激活 (1:激活, 0:禁用)")
    
    # 联系信息
    manager_id = Column(Integer, ForeignKey("users.id"), nullable=True, comment="部门主管ID")
    phone = Column(String(20), nullable=True, comment="联系电话")
    email = Column(String(100), nullable=True, comment="联系邮箱")
    location = Column(String(255), nullable=True, comment="办公地点")
    
    # 其他信息
    notes = Column(Text, nullable=True, comment="备注")
    
    # 关系
    parent = relationship("Department", remote_side="Department.id", back_populates="children")
    children = relationship("Department", back_populates="parent")
    manager = relationship("User", foreign_keys=[manager_id])
    users = relationship("User", foreign_keys="User.department_id", back_populates="department")
    
    def __repr__(self):
        return f"<Department(id={self.id}, name='{self.name}', code='{self.code}')>"
    
    @property
    def full_name(self) -> str:
        """获取完整部门名称（包含上级部门）"""
        if self.parent:
            return f"{self.parent.full_name} > {self.name}"
        return self.name
    
    @property
    def is_leaf(self) -> bool:
        """是否为叶子节点（无子部门）"""
        return len(self.children) == 0
    
    def get_all_children_ids(self):
        """获取所有子部门ID（包括子部门的子部门）"""
        ids = []
        for child in self.children:
            ids.append(child.id)
            ids.extend(child.get_all_children_ids())
        return ids
    
    def get_all_parent_ids(self):
        """获取所有上级部门ID"""
        ids = []
        if self.parent:
            ids.append(self.parent.id)
            ids.extend(self.parent.get_all_parent_ids())
        return ids