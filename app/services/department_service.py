"""
部门服务模块
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

from app.models.user import User
from app.models.department import Department
from app.schemas.department import DepartmentCreate, DepartmentUpdate


class DepartmentService:
    """
    部门服务类
    """
    
    @staticmethod
    def get_department_by_id(db: Session, department_id: int) -> Optional[Department]:
        """
        根据ID获取部门
        
        Args:
            db: 数据库会话
            department_id: 部门ID
            
        Returns:
            部门对象，不存在返回None
        """
        return db.query(Department).filter(Department.id == department_id).first()
    
    @staticmethod
    def get_department_by_name(db: Session, name: str) -> Optional[Department]:
        """
        根据名称获取部门
        
        Args:
            db: 数据库会话
            name: 部门名称
            
        Returns:
            部门对象，不存在返回None
        """
        return db.query(Department).filter(Department.name == name).first()
    
    @staticmethod
    def get_departments(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        parent_id: Optional[int] = None,
        is_active: Optional[bool] = None,
        search: Optional[str] = None
    ) -> List[Department]:
        """
        获取部门列表
        
        Args:
            db: 数据库会话
            skip: 跳过记录数
            limit: 返回记录数
            parent_id: 父部门ID
            is_active: 是否激活
            search: 搜索关键词
            
        Returns:
            部门列表
        """
        query = db.query(Department)
        
        if parent_id is not None:
            query = query.filter(Department.parent_id == parent_id)
        
        if is_active is not None:
            query = query.filter(Department.is_active == is_active)
        
        if search:
            query = query.filter(
                or_(
                    Department.name.ilike(f"%{search}%"),
                    Department.description.ilike(f"%{search}%")
                )
            )
        
        return query.order_by(Department.sort_order.asc(), Department.name.asc()).offset(skip).limit(limit).all()
    
    @staticmethod
    def count_departments(
        db: Session,
        parent_id: Optional[int] = None,
        is_active: Optional[bool] = None,
        search: Optional[str] = None
    ) -> int:
        """
        统计部门数量
        
        Args:
            db: 数据库会话
            parent_id: 父部门ID
            is_active: 是否激活
            search: 搜索关键词
            
        Returns:
            部门数量
        """
        query = db.query(Department)
        
        if parent_id is not None:
            query = query.filter(Department.parent_id == parent_id)
        
        if is_active is not None:
            query = query.filter(Department.is_active == is_active)
        
        if search:
            query = query.filter(
                or_(
                    Department.name.ilike(f"%{search}%"),
                    Department.description.ilike(f"%{search}%")
                )
            )
        
        return query.count()
    
    @staticmethod
    def create_department(db: Session, department: DepartmentCreate) -> Department:
        """
        创建部门
        
        Args:
            db: 数据库会话
            department: 部门创建数据
            
        Returns:
            创建的部门对象
            
        Raises:
            ValueError: 部门名称已存在时抛出异常
        """
        # 检查部门名称是否已存在
        existing = DepartmentService.get_department_by_name(db, department.name)
        if existing:
            raise ValueError("部门名称已存在")
        
        # 如果有父部门，检查父部门是否存在
        if department.parent_id:
            parent = DepartmentService.get_department_by_id(db, department.parent_id)
            if not parent:
                raise ValueError("父部门不存在")
        
        db_department = Department(
            name=department.name,
            description=department.description,
            parent_id=department.parent_id,
            sort_order=department.sort_order or 0,
            is_active=department.is_active if department.is_active is not None else True
        )
        
        db.add(db_department)
        db.commit()
        db.refresh(db_department)
        
        return db_department
    
    @staticmethod
    def update_department(db: Session, department_id: int, department: DepartmentUpdate) -> Department:
        """
        更新部门
        
        Args:
            db: 数据库会话
            department_id: 部门ID
            department: 部门更新数据
            
        Returns:
            更新后的部门对象
            
        Raises:
            ValueError: 部门名称已存在或父部门不存在时抛出异常
        """
        db_department = DepartmentService.get_department_by_id(db, department_id)
        if not db_department:
            raise ValueError("部门不存在")
        
        # 检查部门名称是否已存在（排除当前部门）
        if department.name and department.name != db_department.name:
            existing = DepartmentService.get_department_by_name(db, department.name)
            if existing and existing.id != department_id:
                raise ValueError("部门名称已存在")
        
        # 如果有父部门，检查父部门是否存在且不是当前部门或其子部门
        if department.parent_id is not None:
            if department.parent_id == department_id:
                raise ValueError("不能将部门设置为自己的父部门")
            
            parent = DepartmentService.get_department_by_id(db, department.parent_id)
            if not parent:
                raise ValueError("父部门不存在")
            
            # 检查是否会造成循环引用
            if DepartmentService.is_child_department(db, department_id, department.parent_id):
                raise ValueError("不能将部门设置为自己的子部门的父部门")
        
        # 更新部门信息
        update_data = department.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_department, field, value)
        
        db.commit()
        db.refresh(db_department)
        
        return db_department
    
    @staticmethod
    def delete_department(db: Session, department_id: int) -> bool:
        """
        删除部门
        
        Args:
            db: 数据库会话
            department_id: 部门ID
            
        Returns:
            删除成功返回True
            
        Raises:
            ValueError: 部门不存在或有子部门或关联用户时抛出异常
        """
        db_department = DepartmentService.get_department_by_id(db, department_id)
        if not db_department:
            raise ValueError("部门不存在")
        
        # 检查是否有子部门
        children = DepartmentService.get_departments(db, parent_id=department_id)
        if children:
            raise ValueError("存在子部门，无法删除")
        
        # 检查是否有关联用户
        users = db.query(User).filter(User.department_id == department_id).count()
        if users > 0:
            raise ValueError("存在关联用户，无法删除")
        
        db.delete(db_department)
        db.commit()
        
        return True
    
    @staticmethod
    def is_child_department(db: Session, parent_id: int, child_id: int) -> bool:
        """
        检查一个部门是否是另一个部门的子部门
        
        Args:
            db: 数据库会话
            parent_id: 父部门ID
            child_id: 子部门ID
            
        Returns:
            是子部门返回True，否则返回False
        """
        # 直接子部门
        child = db.query(Department).filter(
            and_(Department.parent_id == parent_id, Department.id == child_id)
        ).first()
        
        if child:
            return True
        
        # 递归检查子部门的子部门
        children = db.query(Department).filter(Department.parent_id == parent_id).all()
        for dept in children:
            if DepartmentService.is_child_department(db, dept.id, child_id):
                return True
        
        return False
    
    @staticmethod
    def get_department_tree(db: Session, parent_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        获取部门树结构
        
        Args:
            db: 数据库会话
            parent_id: 父部门ID，None表示获取根部门
            
        Returns:
            部门树结构列表
        """
        departments = DepartmentService.get_departments(
            db, parent_id=parent_id, is_active=True
        )
        
        tree = []
        for dept in departments:
            # 获取子部门
            children = DepartmentService.get_department_tree(db, dept.id)
            
            # 获取部门用户数量
            user_count = db.query(User).filter(User.department_id == dept.id).count()
            
            tree.append({
                "id": dept.id,
                "name": dept.name,
                "description": dept.description,
                "parent_id": dept.parent_id,
                "sort_order": dept.sort_order,
                "is_active": dept.is_active,
                "user_count": user_count,
                "children": children
            })
        
        return tree
    
    @staticmethod
    def get_all_children(db: Session, department_id: int) -> List[Department]:
        """
        获取所有子部门（包括子部门的子部门）
        
        Args:
            db: 数据库会话
            department_id: 部门ID
            
        Returns:
            所有子部门列表
        """
        children = []
        direct_children = DepartmentService.get_departments(db, parent_id=department_id)
        
        for child in direct_children:
            children.append(child)
            # 递归获取子部门的子部门
            children.extend(DepartmentService.get_all_children(db, child.id))
        
        return children
    
    @staticmethod
    def get_department_path(db: Session, department_id: int) -> List[Department]:
        """
        获取部门路径（从根部门到当前部门）
        
        Args:
            db: 数据库会话
            department_id: 部门ID
            
        Returns:
            部门路径列表
        """
        department = DepartmentService.get_department_by_id(db, department_id)
        if not department:
            return []
        
        path = [department]
        
        # 递归获取父部门
        if department.parent_id:
            parent_path = DepartmentService.get_department_path(db, department.parent_id)
            path = parent_path + path
        
        return path
    
    @staticmethod
    def get_department_statistics(db: Session, department_id: Optional[int] = None) -> Dict[str, Any]:
        """
        获取部门统计信息
        
        Args:
            db: 数据库会话
            department_id: 部门ID，None表示获取所有部门统计
            
        Returns:
            部门统计信息字典
        """
        query = db.query(Department)
        
        if department_id:
            query = query.filter(Department.id == department_id)
        
        # 总部门数
        total_departments = query.count()
        
        # 激活部门数
        active_departments = query.filter(Department.is_active == True).count()
        
        # 根部门数
        root_departments = query.filter(Department.parent_id.is_(None)).count()
        
        # 最大层级数
        max_level = 0
        if not department_id:
            # 计算所有部门的最大层级
            root_departments = query.filter(Department.parent_id.is_(None)).all()
            for root in root_departments:
                level = DepartmentService._calculate_department_level(db, root.id)
                max_level = max(max_level, level)
        else:
            # 计算指定部门的层级
            max_level = DepartmentService._calculate_department_level(db, department_id)
        
        # 用户统计
        if department_id:
            # 获取部门及其所有子部门
            dept_ids = [department_id]
            children = DepartmentService.get_all_children(db, department_id)
            dept_ids.extend([child.id for child in children])
            
            user_count = db.query(User).filter(User.department_id.in_(dept_ids)).count()
        else:
            user_count = db.query(User).count()
        
        return {
            "total_departments": total_departments,
            "active_departments": active_departments,
            "root_departments": root_departments,
            "max_level": max_level,
            "user_count": user_count
        }
    
    @staticmethod
    def _calculate_department_level(db: Session, department_id: int, level: int = 0) -> int:
        """
        计算部门层级
        
        Args:
            db: 数据库会话
            department_id: 部门ID
            level: 当前层级
            
        Returns:
            部门层级
        """
        department = DepartmentService.get_department_by_id(db, department_id)
        if not department:
            return level
        
        if department.parent_id:
            return DepartmentService._calculate_department_level(db, department.parent_id, level + 1)
        
        return level