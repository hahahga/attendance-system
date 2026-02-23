"""
用户服务模块
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, date
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from fastapi import HTTPException, status, UploadFile
import os
import uuid
import json

from app.core.config import get_settings
from app.models.user import User, UserRole, UserStatus
from app.models.department import Department
from app.schemas.user import UserCreate, UserUpdate, UserFaceData
from app.services.system_log_service import SystemLogService

settings = get_settings()


class UserService:
    """
    用户服务类
    """
    
    @staticmethod
    def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
        """
        根据ID获取用户
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            
        Returns:
            用户对象，不存在返回None
        """
        return db.query(User).filter(User.id == user_id).first()
    
    @staticmethod
    def get_user_by_username(db: Session, username: str) -> Optional[User]:
        """
        根据用户名获取用户
        
        Args:
            db: 数据库会话
            username: 用户名
            
        Returns:
            用户对象，不存在返回None
        """
        return db.query(User).filter(User.username == username).first()
    
    @staticmethod
    def get_user_by_email(db: Session, email: str) -> Optional[User]:
        """
        根据邮箱获取用户
        
        Args:
            db: 数据库会话
            email: 邮箱
            
        Returns:
            用户对象，不存在返回None
        """
        return db.query(User).filter(User.email == email).first()
    
    @staticmethod
    def get_users(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        department_id: Optional[int] = None,
        role: Optional[UserRole] = None,
        status: Optional[UserStatus] = None,
        search: Optional[str] = None
    ) -> List[User]:
        """
        获取用户列表
        
        Args:
            db: 数据库会话
            skip: 跳过记录数
            limit: 返回记录数
            department_id: 部门ID
            role: 用户角色
            status: 用户状态
            search: 搜索关键词
            
        Returns:
            用户列表
        """
        query = db.query(User)
        
        if department_id:
            query = query.filter(User.department_id == department_id)
        
        if role:
            query = query.filter(User.role == role)
        
        if status:
            query = query.filter(User.status == status)
        
        if search:
            query = query.filter(
                or_(
                    User.username.ilike(f"%{search}%"),
                    User.full_name.ilike(f"%{search}%"),
                    User.email.ilike(f"%{search}%"),
                    User.employee_id.ilike(f"%{search}%")
                )
            )
        
        return query.offset(skip).limit(limit).all()
    
    @staticmethod
    def count_users(
        db: Session,
        department_id: Optional[int] = None,
        role: Optional[UserRole] = None,
        status: Optional[UserStatus] = None,
        search: Optional[str] = None
    ) -> int:
        """
        统计用户数量
        
        Args:
            db: 数据库会话
            department_id: 部门ID
            role: 用户角色
            status: 用户状态
            search: 搜索关键词
            
        Returns:
            用户数量
        """
        query = db.query(User)
        
        if department_id:
            query = query.filter(User.department_id == department_id)
        
        if role:
            query = query.filter(User.role == role)
        
        if status:
            query = query.filter(User.status == status)
        
        if search:
            query = query.filter(
                or_(
                    User.username.ilike(f"%{search}%"),
                    User.full_name.ilike(f"%{search}%"),
                    User.email.ilike(f"%{search}%"),
                    User.employee_id.ilike(f"%{search}%")
                )
            )
        
        return query.count()
    
    @staticmethod
    def create_user(db: Session, user: UserCreate) -> User:
        """
        创建用户
        
        Args:
            db: 数据库会话
            user: 用户创建数据
            
        Returns:
            创建的用户对象
            
        Raises:
            HTTPException: 用户名或邮箱已存在时抛出异常
        """
        # 检查用户名是否已存在
        db_user = db.query(User).filter(User.username == user.username).first()
        if db_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户名已存在"
            )
        
        # 检查邮箱是否已存在
        db_user = db.query(User).filter(User.email == user.email).first()
        if db_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="邮箱已存在"
            )
        
        # 检查员工ID是否已存在
        if user.employee_id:
            db_user = db.query(User).filter(User.employee_id == user.employee_id).first()
            if db_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="员工ID已存在"
                )
        
        # 创建新用户
        from app.core.security import get_password_hash
        hashed_password = get_password_hash(user.password)
        
        db_user = User(
            username=user.username,
            email=user.email,
            hashed_password=hashed_password,
            full_name=user.full_name,
            employee_id=user.employee_id,
            department_id=user.department_id,
            position=user.position,
            role=user.role if user.role else UserRole.EMPLOYEE,
            status=user.status if user.status else UserStatus.ACTIVE,
            phone=user.phone,
            hire_date=user.hire_date
        )
        
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        # 记录系统日志
        SystemLogService.log_user_action(
            db=db,
            user_id=db_user.id,
            action="创建用户",
            details=f"创建用户: {user.username}"
        )
        
        return db_user
    
    @staticmethod
    def update_user(db: Session, user_id: int, user: UserUpdate) -> User:
        """
        更新用户
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            user: 用户更新数据
            
        Returns:
            更新后的用户对象
            
        Raises:
            HTTPException: 用户不存在时抛出异常
        """
        db_user = db.query(User).filter(User.id == user_id).first()
        if not db_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        # 更新用户信息
        update_data = user.dict(exclude_unset=True)
        
        # 检查邮箱是否已存在（排除当前用户）
        if "email" in update_data and update_data["email"] != db_user.email:
            existing_user = db.query(User).filter(User.email == update_data["email"]).first()
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="邮箱已存在"
                )
        
        # 检查员工ID是否已存在（排除当前用户）
        if "employee_id" in update_data and update_data["employee_id"] != db_user.employee_id:
            existing_user = db.query(User).filter(User.employee_id == update_data["employee_id"]).first()
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="员工ID已存在"
                )
        
        for field, value in update_data.items():
            setattr(db_user, field, value)
        
        db_user.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(db_user)
        
        # 记录系统日志
        SystemLogService.log_user_action(
            db=db,
            user_id=user_id,
            action="更新用户",
            details=f"更新用户信息: {db_user.username}"
        )
        
        return db_user
    
    @staticmethod
    def delete_user(db: Session, user_id: int) -> bool:
        """
        删除用户
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            
        Returns:
            删除成功返回True
            
        Raises:
            HTTPException: 用户不存在时抛出异常
        """
        db_user = db.query(User).filter(User.id == user_id).first()
        if not db_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        # 记录用户名用于日志
        username = db_user.username
        
        db.delete(db_user)
        db.commit()
        
        # 记录系统日志
        SystemLogService.log_user_action(
            db=db,
            user_id=user_id,
            action="删除用户",
            details=f"删除用户: {username}"
        )
        
        return True
    
    @staticmethod
    def update_user_face_data(db: Session, user_id: int, face_data: UserFaceData) -> User:
        """
        更新用户人脸数据
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            face_data: 人脸数据
            
        Returns:
            更新后的用户对象
            
        Raises:
            HTTPException: 用户不存在时抛出异常
        """
        db_user = db.query(User).filter(User.id == user_id).first()
        if not db_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        # 更新人脸数据
        db_user.face_encoding = json.dumps(face_data.face_encoding)
        db_user.face_image_path = face_data.face_image_path
        db_user.face_registered = True
        db_user.face_registered_at = datetime.utcnow()
        db_user.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(db_user)
        
        # 记录系统日志
        SystemLogService.log_user_action(
            db=db,
            user_id=user_id,
            action="注册人脸",
            details=f"用户 {db_user.username} 注册人脸成功"
        )
        
        return db_user
    
    @staticmethod
    def save_face_image(db: Session, user_id: int, file: UploadFile) -> bool:
        """
        保存人脸图像
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            file: 上传的文件
            
        Returns:
            保存成功返回True
            
        Raises:
            HTTPException: 文件类型不支持时抛出异常
        """
        # 检查文件类型
        if not file.content_type.startswith("image/"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="只支持图像文件"
            )
        
        # 创建目录（如果不存在）
        upload_dir = os.path.join(settings.UPLOAD_DIR, "faces")
        os.makedirs(upload_dir, exist_ok=True)
        
        # 生成唯一文件名
        file_extension = file.filename.split(".")[-1] if "." in file.filename else "jpg"
        unique_filename = f"{uuid.uuid4().hex}.{file_extension}"
        file_path = os.path.join(upload_dir, unique_filename)
        
        # 保存文件
        with open(file_path, "wb") as buffer:
            content = file.file.read()
            buffer.write(content)
        
        # 返回相对路径
        relative_path = os.path.join("uploads", "faces", unique_filename)
        
        # 提取人脸编码
        from app.utils.face_utils import face_recognition_utils
        face_encoding = face_recognition_utils.extract_face_encoding(file_path)
        
        if face_encoding is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="未检测到人脸，请上传包含清晰人脸的图像"
            )
        
        # 获取用户信息
        db_user = db.query(User).filter(User.id == user_id).first()
        if not db_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        # 更新用户人脸数据
        db_user.face_encoding = json.dumps(face_encoding.tolist())
        db_user.face_image_path = relative_path
        db_user.face_registered = True
        db_user.face_registered_at = datetime.utcnow()
        db_user.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(db_user)
        
        # 添加到人脸识别库
        face_recognition_utils.add_face(str(user_id), file_path)
        
        # 记录系统日志
        SystemLogService.log_user_action(
            db=db,
            user_id=user_id,
            action="上传人脸图像",
            details=f"用户 {db_user.username} 上传人脸图像成功"
        )
        
        return True
    
    @staticmethod
    def delete_face_image(db: Session, user_id: int) -> bool:
        """
        删除用户人脸图像
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            
        Returns:
            删除成功返回True
            
        Raises:
            HTTPException: 用户不存在或未注册人脸时抛出异常
        """
        # 获取用户信息
        db_user = db.query(User).filter(User.id == user_id).first()
        if not db_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        # 检查用户是否已注册人脸
        if not db_user.face_registered or not db_user.face_image_path:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="人脸图像不存在"
            )
        
        # 记录人脸图像路径用于日志
        face_image_path = db_user.face_image_path
        
        # 删除人脸图像文件
        try:
            # 构建完整路径
            full_path = os.path.join(settings.BASE_DIR, db_user.face_image_path)
            if os.path.exists(full_path):
                os.remove(full_path)
        except Exception as e:
            # 记录错误但不中断流程
            print(f"删除人脸图像文件失败: {str(e)}")
        
        # 从人脸识别库中移除
        try:
            from app.utils.face_utils import face_recognition_utils
            face_recognition_utils.remove_face(str(user_id))
        except Exception as e:
            # 记录错误但不中断流程
            print(f"从人脸识别库移除失败: {str(e)}")
        
        # 清空用户人脸数据
        db_user.face_encoding = None
        db_user.face_image_path = None
        db_user.face_registered = False
        db_user.face_registered_at = None
        db_user.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(db_user)
        
        # 记录系统日志
        SystemLogService.log_user_action(
            db=db,
            user_id=user_id,
            action="删除人脸图像",
            details=f"用户 {db_user.username} 删除人脸图像成功"
        )
        
        return True
    
    @staticmethod
    def get_user_statistics(db: Session) -> Dict[str, Any]:
        """
        获取用户统计信息
        
        Args:
            db: 数据库会话
            
        Returns:
            用户统计信息字典
        """
        # 总用户数
        total_users = db.query(User).count()
        
        # 按角色统计
        role_stats = db.query(
            User.role,
            func.count(User.id).label("count")
        ).group_by(User.role).all()
        
        # 按状态统计
        status_stats = db.query(
            User.status,
            func.count(User.id).label("count")
        ).group_by(User.status).all()
        
        # 按部门统计
        department_stats = db.query(
            Department.name,
            func.count(User.id).label("count")
        ).join(User, Department.id == User.department_id).group_by(Department.name).all()
        
        # 本月新增用户
        current_month = date.today().replace(day=1)
        new_users_this_month = db.query(User).filter(User.created_at >= current_month).count()
        
        return {
            "total_users": total_users,
            "role_stats": {role.value: count for role, count in role_stats},
            "status_stats": {status.value: count for status, count in status_stats},
            "department_stats": {name: count for name, count in department_stats},
            "new_users_this_month": new_users_this_month
        }