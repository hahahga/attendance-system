"""
考勤服务模块
"""

from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, date, time, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, extract
from fastapi import HTTPException, status
import face_recognition
import numpy as np
import json
import os

from app.core.config import get_settings
from app.models.user import User
from app.models.attendance import Attendance, AttendanceStatus, AttendanceType
from app.schemas.attendance import AttendanceCreate, AttendanceUpdate
from app.services.system_log_service import SystemLogService

settings = get_settings()


class AttendanceService:
    """
    考勤服务类
    """
    
    @staticmethod
    def get_attendance_by_id(db: Session, attendance_id: int) -> Optional[Attendance]:
        """
        根据ID获取考勤记录
        
        Args:
            db: 数据库会话
            attendance_id: 考勤记录ID
            
        Returns:
            考勤记录对象，不存在返回None
        """
        return db.query(Attendance).filter(Attendance.id == attendance_id).first()
    
    @staticmethod
    def get_attendances(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        user_id: Optional[int] = None,
        department_id: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        status: Optional[AttendanceStatus] = None,
        search: Optional[str] = None
    ) -> List[Attendance]:
        """
        获取考勤记录列表
        
        Args:
            db: 数据库会话
            skip: 跳过记录数
            limit: 返回记录数
            user_id: 用户ID
            department_id: 部门ID
            start_date: 开始日期
            end_date: 结束日期
            status: 考勤状态
            search: 搜索关键词
            
        Returns:
            考勤记录列表
        """
        query = db.query(Attendance).join(User)
        
        if user_id:
            query = query.filter(Attendance.user_id == user_id)
        
        if department_id:
            query = query.filter(User.department_id == department_id)
        
        if start_date:
            query = query.filter(Attendance.date >= start_date)
        
        if end_date:
            query = query.filter(Attendance.date <= end_date)
        
        if status:
            query = query.filter(Attendance.status == status)
        
        if search:
            query = query.filter(
                or_(
                    User.username.ilike(f"%{search}%"),
                    User.full_name.ilike(f"%{search}%"),
                    User.employee_id.ilike(f"%{search}%")
                )
            )
        
        return query.order_by(Attendance.date.desc(), Attendance.clock_in_time.desc()).offset(skip).limit(limit).all()
    
    @staticmethod
    def count_attendances(
        db: Session,
        user_id: Optional[int] = None,
        department_id: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        status: Optional[AttendanceStatus] = None,
        search: Optional[str] = None
    ) -> int:
        """
        统计考勤记录数量
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            department_id: 部门ID
            start_date: 开始日期
            end_date: 结束日期
            status: 考勤状态
            search: 搜索关键词
            
        Returns:
            考勤记录数量
        """
        query = db.query(Attendance).join(User)
        
        if user_id:
            query = query.filter(Attendance.user_id == user_id)
        
        if department_id:
            query = query.filter(User.department_id == department_id)
        
        if start_date:
            query = query.filter(Attendance.date >= start_date)
        
        if end_date:
            query = query.filter(Attendance.date <= end_date)
        
        if status:
            query = query.filter(Attendance.status == status)
        
        if search:
            query = query.filter(
                or_(
                    User.username.ilike(f"%{search}%"),
                    User.full_name.ilike(f"%{search}%"),
                    User.employee_id.ilike(f"%{search}%")
                )
            )
        
        return query.count()
    
    @staticmethod
    def clock_in(db: Session, user_id: int, clock_in_time: datetime, location: Optional[str] = None) -> Attendance:
        """
        上班打卡
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            clock_in_time: 打卡时间
            location: 打卡位置
            
        Returns:
            考勤记录对象
            
        Raises:
            HTTPException: 已打卡时抛出异常
        """
        # 检查今天是否已经打卡
        today = clock_in_time.date()
        existing_attendance = db.query(Attendance).filter(
            and_(
                Attendance.user_id == user_id,
                Attendance.date == today
            )
        ).first()
        
        if existing_attendance and existing_attendance.clock_in_time:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="今日已打卡上班"
            )
        
        # 如果已有记录但未打卡上班，更新记录
        if existing_attendance:
            existing_attendance.clock_in_time = clock_in_time.time()
            existing_attendance.clock_in_location = location
            existing_attendance.status = AttendanceStatus.PRESENT
            existing_attendance.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(existing_attendance)
            
            # 记录系统日志
            SystemLogService.log_user_action(
                db=db,
                user_id=user_id,
                action="上班打卡",
                details=f"用户 {user_id} 上班打卡成功"
            )
            
            return existing_attendance
        
        # 创建新的考勤记录
        attendance = Attendance(
            user_id=user_id,
            date=today,
            clock_in_time=clock_in_time.time(),
            clock_in_location=location,
            status=AttendanceStatus.PRESENT
        )
        
        db.add(attendance)
        db.commit()
        db.refresh(attendance)
        
        # 记录系统日志
        SystemLogService.log_user_action(
            db=db,
            user_id=user_id,
            action="上班打卡",
            details=f"用户 {user_id} 上班打卡成功"
        )
        
        return attendance
    
    @staticmethod
    def clock_out(db: Session, user_id: int, clock_out_time: datetime, location: Optional[str] = None) -> Attendance:
        """
        下班打卡
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            clock_out_time: 打卡时间
            location: 打卡位置
            
        Returns:
            考勤记录对象
            
        Raises:
            HTTPException: 未打卡上班或已打卡下班时抛出异常
        """
        # 检查今天是否已经打卡上班
        today = clock_out_time.date()
        attendance = db.query(Attendance).filter(
            and_(
                Attendance.user_id == user_id,
                Attendance.date == today
            )
        ).first()
        
        if not attendance or not attendance.clock_in_time:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="请先打卡上班"
            )
        
        if attendance.clock_out_time:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="今日已打卡下班"
            )
        
        # 更新下班打卡信息
        attendance.clock_out_time = clock_out_time.time()
        attendance.clock_out_location = location
        
        # 计算工作时长
        clock_in_datetime = datetime.combine(today, attendance.clock_in_time)
        clock_out_datetime = datetime.combine(today, attendance.clock_out_time)
        
        # 如果下班时间小于上班时间，说明跨天了
        if clock_out_datetime < clock_in_datetime:
            clock_out_datetime += timedelta(days=1)
        
        work_hours = (clock_out_datetime - clock_in_datetime).total_seconds() / 3600
        attendance.work_hours = round(work_hours, 2)
        
        # 更新考勤状态
        user = db.query(User).filter(User.id == user_id).first()
        if user and user.work_end_time and attendance.clock_out_time > user.work_end_time:
            attendance.status = AttendanceStatus.OVERTIME
        else:
            attendance.status = AttendanceStatus.PRESENT
        
        attendance.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(attendance)
        
        # 记录系统日志
        SystemLogService.log_user_action(
            db=db,
            user_id=user_id,
            action="下班打卡",
            details=f"用户 {user_id} 下班打卡成功，工作时长: {attendance.work_hours}小时"
        )
        
        return attendance
    
    @staticmethod
    def clock_in_by_face(db: Session, user_id: int, face_image_path: str) -> Attendance:
        """
        人脸识别上班打卡
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            face_image_path: 人脸图像路径
            
        Returns:
            考勤记录对象
            
        Raises:
            HTTPException: 人脸识别失败时抛出异常
        """
        # 获取用户信息
        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.face_encoding:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户不存在或未注册人脸"
            )
        
        # 加载人脸编码
        known_face_encoding = json.loads(user.face_encoding)
        known_face_encoding = np.array(known_face_encoding)
        
        # 加载上传的人脸图像
        unknown_image = face_recognition.load_image_file(face_image_path)
        unknown_face_encodings = face_recognition.face_encodings(unknown_image)
        
        if not unknown_face_encodings:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="未检测到人脸"
            )
        
        # 比较人脸
        unknown_face_encoding = unknown_face_encodings[0]
        face_distances = face_recognition.face_distance([known_face_encoding], unknown_face_encoding)
        face_match_percentage = (1 - face_distances[0]) * 100
        
        # 设置人脸识别阈值
        if face_match_percentage < settings.FACE_RECOGNITION_THRESHOLD:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"人脸识别失败，匹配度: {face_match_percentage:.2f}%"
            )
        
        # 人脸识别成功，执行打卡
        now = datetime.utcnow()
        return AttendanceService.clock_in(db, user_id, now)
    
    @staticmethod
    def clock_out_by_face(db: Session, user_id: int, face_image_path: str) -> Attendance:
        """
        人脸识别下班打卡
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            face_image_path: 人脸图像路径
            
        Returns:
            考勤记录对象
            
        Raises:
            HTTPException: 人脸识别失败时抛出异常
        """
        # 获取用户信息
        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.face_encoding:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户不存在或未注册人脸"
            )
        
        # 加载人脸编码
        known_face_encoding = json.loads(user.face_encoding)
        known_face_encoding = np.array(known_face_encoding)
        
        # 加载上传的人脸图像
        unknown_image = face_recognition.load_image_file(face_image_path)
        unknown_face_encodings = face_recognition.face_encodings(unknown_image)
        
        if not unknown_face_encodings:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="未检测到人脸"
            )
        
        # 比较人脸
        unknown_face_encoding = unknown_face_encodings[0]
        face_distances = face_recognition.face_distance([known_face_encoding], unknown_face_encoding)
        face_match_percentage = (1 - face_distances[0]) * 100
        
        # 设置人脸识别阈值
        if face_match_percentage < settings.FACE_RECOGNITION_THRESHOLD:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"人脸识别失败，匹配度: {face_match_percentage:.2f}%"
            )
        
        # 人脸识别成功，执行打卡
        now = datetime.utcnow()
        return AttendanceService.clock_out(db, user_id, now)
    
    @staticmethod
    def update_attendance(db: Session, attendance_id: int, attendance: AttendanceUpdate) -> Attendance:
        """
        更新考勤记录
        
        Args:
            db: 数据库会话
            attendance_id: 考勤记录ID
            attendance: 考勤更新数据
            
        Returns:
            更新后的考勤记录对象
            
        Raises:
            HTTPException: 考勤记录不存在时抛出异常
        """
        db_attendance = db.query(Attendance).filter(Attendance.id == attendance_id).first()
        if not db_attendance:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="考勤记录不存在"
            )
        
        # 更新考勤记录
        update_data = attendance.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_attendance, field, value)
        
        db_attendance.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(db_attendance)
        
        # 记录系统日志
        SystemLogService.log_user_action(
            db=db,
            user_id=db_attendance.user_id,
            action="更新考勤记录",
            details=f"更新考勤记录ID: {attendance_id}"
        )
        
        return db_attendance
    
    @staticmethod
    def delete_attendance(db: Session, attendance_id: int) -> bool:
        """
        删除考勤记录
        
        Args:
            db: 数据库会话
            attendance_id: 考勤记录ID
            
        Returns:
            删除成功返回True
            
        Raises:
            HTTPException: 考勤记录不存在时抛出异常
        """
        db_attendance = db.query(Attendance).filter(Attendance.id == attendance_id).first()
        if not db_attendance:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="考勤记录不存在"
            )
        
        # 记录用户ID用于日志
        user_id = db_attendance.user_id
        
        db.delete(db_attendance)
        db.commit()
        
        # 记录系统日志
        SystemLogService.log_user_action(
            db=db,
            user_id=user_id,
            action="删除考勤记录",
            details=f"删除考勤记录ID: {attendance_id}"
        )
        
        return True
    
    @staticmethod
    def get_attendance_statistics(
        db: Session,
        user_id: Optional[int] = None,
        department_id: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        获取考勤统计信息
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            department_id: 部门ID
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            考勤统计信息字典
        """
        query = db.query(Attendance).join(User)
        
        if user_id:
            query = query.filter(Attendance.user_id == user_id)
        
        if department_id:
            query = query.filter(User.department_id == department_id)
        
        if start_date:
            query = query.filter(Attendance.date >= start_date)
        
        if end_date:
            query = query.filter(Attendance.date <= end_date)
        
        # 总打卡天数
        total_days = query.count()
        
        # 按状态统计
        status_stats = query.with_entities(
            Attendance.status,
            func.count(Attendance.id).label("count")
        ).group_by(Attendance.status).all()
        
        # 平均工作时长
        avg_work_hours = query.filter(Attendance.work_hours.isnot(None)).with_entities(
            func.avg(Attendance.work_hours)
        ).scalar()
        avg_work_hours = round(avg_work_hours, 2) if avg_work_hours else 0
        
        # 总工作时长
        total_work_hours = query.filter(Attendance.work_hours.isnot(None)).with_entities(
            func.sum(Attendance.work_hours)
        ).scalar()
        total_work_hours = round(total_work_hours, 2) if total_work_hours else 0
        
        # 迟到次数
        late_count = query.filter(Attendance.is_late == True).count()
        
        # 早退次数
        early_leave_count = query.filter(Attendance.is_early_leave == True).count()
        
        return {
            "total_days": total_days,
            "status_stats": {status.value: count for status, count in status_stats},
            "avg_work_hours": avg_work_hours,
            "total_work_hours": total_work_hours,
            "late_count": late_count,
            "early_leave_count": early_leave_count
        }
    
    @staticmethod
    def get_monthly_attendance_report(
        db: Session,
        user_id: Optional[int] = None,
        department_id: Optional[int] = None,
        year: int = None,
        month: int = None
    ) -> List[Dict[str, Any]]:
        """
        获取月度考勤报告
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            department_id: 部门ID
            year: 年份
            month: 月份
            
        Returns:
            月度考勤报告列表
        """
        if not year:
            year = date.today().year
        if not month:
            month = date.today().month
        
        # 构建查询
        query = db.query(
            User.id.label("user_id"),
            User.username,
            User.full_name,
            User.employee_id,
            Department.name.label("department_name"),
            func.count(Attendance.id).label("total_days"),
            func.sum(func.case([(Attendance.status == AttendanceStatus.PRESENT, 1)], else_=0)).label("present_days"),
            func.sum(func.case([(Attendance.status == AttendanceStatus.ABSENT, 1)], else_=0)).label("absent_days"),
            func.sum(func.case([(Attendance.status == AttendanceStatus.LEAVE, 1)], else_=0)).label("leave_days"),
            func.sum(func.case([(Attendance.status == AttendanceStatus.HOLIDAY, 1)], else_=0)).label("holiday_days"),
            func.sum(func.case([(Attendance.status == AttendanceStatus.WEEKEND, 1)], else_=0)).label("weekend_days"),
            func.sum(func.case([(Attendance.is_late == True, 1)], else_=0)).label("late_days"),
            func.sum(func.case([(Attendance.is_early_leave == True, 1)], else_=0)).label("early_leave_days"),
            func.avg(Attendance.work_hours).label("avg_work_hours"),
            func.sum(Attendance.work_hours).label("total_work_hours")
        ).join(
            Attendance, User.id == Attendance.user_id
        ).join(
            Department, User.department_id == Department.id
        ).filter(
            extract('year', Attendance.date) == year,
            extract('month', Attendance.date) == month
        )
        
        if user_id:
            query = query.filter(User.id == user_id)
        
        if department_id:
            query = query.filter(User.department_id == department_id)
        
        results = query.group_by(
            User.id, User.username, User.full_name, User.employee_id, Department.name
        ).all()
        
        # 转换结果为字典列表
        reports = []
        for result in results:
            report = {
                "user_id": result.user_id,
                "username": result.username,
                "full_name": result.full_name,
                "employee_id": result.employee_id,
                "department_name": result.department_name,
                "total_days": result.total_days,
                "present_days": result.present_days or 0,
                "absent_days": result.absent_days or 0,
                "leave_days": result.leave_days or 0,
                "holiday_days": result.holiday_days or 0,
                "weekend_days": result.weekend_days or 0,
                "late_days": result.late_days or 0,
                "early_leave_days": result.early_leave_days or 0,
                "avg_work_hours": round(result.avg_work_hours, 2) if result.avg_work_hours else 0,
                "total_work_hours": round(result.total_work_hours, 2) if result.total_work_hours else 0
            }
            reports.append(report)
        
        return reports