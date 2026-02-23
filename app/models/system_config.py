"""
系统配置数据模型
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, Float

from .base import BaseModel


class SystemConfig(BaseModel):
    """
    系统配置模型
    """
    __tablename__ = "system_configs"
    
    # 基本信息
    system_name = Column(String(100), nullable=False, default="考勤管理系统", comment="系统名称")
    company_name = Column(String(100), nullable=False, default="示例公司", comment="公司名称")
    
    # 工作时间配置
    work_start_time = Column(String(5), nullable=False, default="09:00", comment="上班时间")
    work_end_time = Column(String(5), nullable=False, default="18:00", comment="下班时间")
    work_days = Column(String(20), nullable=False, default="1,2,3,4,5", comment="工作日")
    
    # 考勤规则配置
    late_threshold = Column(Integer, nullable=False, default=10, comment="迟到阈值（分钟）")
    early_threshold = Column(Integer, nullable=False, default=10, comment="早退阈值（分钟）")
    overtime_threshold = Column(Integer, nullable=False, default=60, comment="加班阈值（分钟）")
    
    # 请假规则配置
    annual_leave_days = Column(Integer, nullable=False, default=10, comment="年假天数")
    sick_leave_days = Column(Integer, nullable=False, default=5, comment="病假天数")
    personal_leave_days = Column(Integer, nullable=False, default=3, comment="事假天数")
    
    # 功能开关
    allow_face_recognition = Column(Boolean, nullable=False, default=True, comment="允许人脸识别")
    allow_leave = Column(Boolean, nullable=False, default=True, comment="允许请假")
    allow_overtime = Column(Boolean, nullable=False, default=True, comment="允许加班")
    
    # 通知配置
    notification_enabled = Column(Boolean, nullable=False, default=True, comment="启用通知")
    email_enabled = Column(Boolean, nullable=False, default=False, comment="启用邮件通知")
    sms_enabled = Column(Boolean, nullable=False, default=False, comment="启用短信通知")
    
    # 备份配置
    auto_backup = Column(Boolean, nullable=False, default=True, comment="自动备份")
    backup_retention_days = Column(Integer, nullable=False, default=30, comment="备份保留天数")
    
    # 人脸识别配置
    face_recognition_tolerance = Column(Float, nullable=False, default=0.6, comment="人脸识别容差")
    
    # 其他配置
    timezone = Column(String(50), nullable=False, default="Asia/Shanghai", comment="时区")
    language = Column(String(10), nullable=False, default="zh-CN", comment="语言")
    
    def __repr__(self):
        return f"<SystemConfig(id={self.id}, system_name='{self.system_name}')>"