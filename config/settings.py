"""
系统配置管理
"""

import os
from typing import Optional
from pydantic import BaseSettings, validator


class Settings(BaseSettings):
    """系统基础配置"""
    
    # 应用基础配置
    APP_NAME: str = "员工考勤管理系统"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"
    
    # 服务器配置
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    
    # 安全配置
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # 数据库配置
    DATABASE_URL: str = "sqlite:///./data/database/attendance.db"
    
    # Redis配置
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # 邮件配置
    SMTP_TLS: bool = True
    SMTP_PORT: Optional[int] = None
    SMTP_HOST: Optional[str] = None
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAILS_FROM_EMAIL: Optional[str] = None
    EMAILS_FROM_NAME: Optional[str] = None
    
    # 文件上传配置
    UPLOAD_DIR: str = "app/static/uploads"
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS: list = ["jpg", "jpeg", "png", "gif", "pdf", "doc", "docx"]
    
    # 人脸识别配置
    FACE_RECOGNITION_TOLERANCE: float = 0.6
    FACE_DETECTION_MODEL: str = "hog"  # hog or cnn
    FACE_DATA_DIR: str = "app/static/uploads/faces"
    
    # 考勤规则配置
    WORK_START_TIME: str = "09:00"
    WORK_END_TIME: str = "18:00"
    LATE_THRESHOLD_MINUTES: int = 10
    EARLY_LEAVE_THRESHOLD_MINUTES: int = 10
    OVERTIME_THRESHOLD_MINUTES: int = 60
    
    # 请假规则配置
    ANNUAL_LEAVE_DAYS: int = 10
    SICK_LEAVE_DAYS: int = 5
    PERSONAL_LEAVE_DAYS: int = 3
    
    # 数据备份配置
    BACKUP_DIR: str = "data/backups"
    AUTO_BACKUP_ENABLED: bool = True
    BACKUP_RETENTION_DAYS: int = 30
    
    # 日志配置
    LOG_DIR: str = "data/logs"
    LOG_LEVEL: str = "INFO"
    LOG_MAX_BYTES: int = 10 * 1024 * 1024  # 10MB
    LOG_BACKUP_COUNT: int = 5
    
    # 分页配置
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100
    
    # CORS配置
    BACKEND_CORS_ORIGINS: list = ["http://localhost:3000", "http://localhost:8080"]
    
    @validator("DATABASE_URL", pre=True)
    def assemble_db_connection(cls, v: Optional[str], values: dict) -> str:
        """根据环境变量组装数据库连接字符串"""
        if isinstance(v, str):
            return v
        
        # 如果没有显式设置DATABASE_URL，则根据其他数据库配置参数组装
        db_user = values.get("DB_USER", "")
        db_password = values.get("DB_PASSWORD", "")
        db_host = values.get("DB_HOST", "localhost")
        db_port = values.get("DB_PORT", "5432")
        db_name = values.get("DB_NAME", "attendance_db")
        
        if db_user and db_password:
            return f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
        else:
            return f"sqlite:///./data/database/attendance.db"
    
    @validator("ACCESS_TOKEN_EXPIRE_MINUTES", pre=True)
    def validate_token_expire_minutes(cls, v):
        """验证访问令牌过期时间"""
        if v <= 0:
            raise ValueError("访问令牌过期时间必须大于0")
        return v
    
    @validator("MAX_UPLOAD_SIZE", pre=True)
    def validate_max_upload_size(cls, v):
        """验证最大上传文件大小"""
        if v <= 0:
            raise ValueError("最大上传文件大小必须大于0")
        return v
    
    @validator("LATE_THRESHOLD_MINUTES", pre=True)
    def validate_late_threshold(cls, v):
        """验证迟到阈值"""
        if v < 0:
            raise ValueError("迟到阈值不能为负数")
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# 创建全局设置实例
settings = Settings()