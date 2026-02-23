"""
配置核心模块
"""

import os
from typing import Any, Dict, Optional

from config.settings import settings
from config.development import DevelopmentSettings
from config.production import ProductionSettings


def get_settings() -> Any:
    """根据环境变量获取相应的配置对象"""
    env = os.getenv("ENVIRONMENT", "development")
    
    if env == "production":
        return ProductionSettings()
    else:
        return DevelopmentSettings()


def get_app_settings() -> Dict[str, Any]:
    """获取应用配置字典"""
    app_settings = get_settings()
    
    return {
        "app_name": app_settings.APP_NAME,
        "app_version": app_settings.APP_VERSION,
        "debug": app_settings.DEBUG,
        "environment": app_settings.ENVIRONMENT,
        "host": app_settings.HOST,
        "port": app_settings.PORT,
        "database_url": app_settings.DATABASE_URL,
        "redis_url": app_settings.REDIS_URL,
        "secret_key": app_settings.SECRET_KEY,
        "algorithm": app_settings.ALGORITHM,
        "access_token_expire_minutes": app_settings.ACCESS_TOKEN_EXPIRE_MINUTES,
        "upload_dir": app_settings.UPLOAD_DIR,
        "max_upload_size": app_settings.MAX_UPLOAD_SIZE,
        "allowed_extensions": app_settings.ALLOWED_EXTENSIONS,
        "face_recognition_tolerance": app_settings.FACE_RECOGNITION_TOLERANCE,
        "face_detection_model": app_settings.FACE_DETECTION_MODEL,
        "face_data_dir": app_settings.FACE_DATA_DIR,
        "work_start_time": app_settings.WORK_START_TIME,
        "work_end_time": app_settings.WORK_END_TIME,
        "late_threshold_minutes": app_settings.LATE_THRESHOLD_MINUTES,
        "early_leave_threshold_minutes": app_settings.EARLY_LEAVE_THRESHOLD_MINUTES,
        "overtime_threshold_minutes": app_settings.OVERTIME_THRESHOLD_MINUTES,
        "annual_leave_days": app_settings.ANNUAL_LEAVE_DAYS,
        "sick_leave_days": app_settings.SICK_LEAVE_DAYS,
        "personal_leave_days": app_settings.PERSONAL_LEAVE_DAYS,
        "backup_dir": app_settings.BACKUP_DIR,
        "auto_backup_enabled": app_settings.AUTO_BACKUP_ENABLED,
        "backup_retention_days": app_settings.BACKUP_RETENTION_DAYS,
        "log_dir": app_settings.LOG_DIR,
        "log_level": app_settings.LOG_LEVEL,
        "log_max_bytes": app_settings.LOG_MAX_BYTES,
        "log_backup_count": app_settings.LOG_BACKUP_COUNT,
        "default_page_size": app_settings.DEFAULT_PAGE_SIZE,
        "max_page_size": app_settings.MAX_PAGE_SIZE,
        "backend_cors_origins": app_settings.BACKEND_CORS_ORIGINS,
    }


def get_cors_origins() -> Optional[list]:
    """获取CORS允许的来源"""
    app_settings = get_settings()
    return app_settings.BACKEND_CORS_ORIGINS


def get_database_url() -> str:
    """获取数据库连接URL"""
    app_settings = get_settings()
    return app_settings.DATABASE_URL


def get_redis_url() -> str:
    """获取Redis连接URL"""
    app_settings = get_settings()
    return app_settings.REDIS_URL


def get_secret_key() -> str:
    """获取应用密钥"""
    app_settings = get_settings()
    return app_settings.SECRET_KEY


def get_jwt_algorithm() -> str:
    """获取JWT算法"""
    app_settings = get_settings()
    return app_settings.ALGORITHM


def get_token_expire_minutes() -> int:
    """获取令牌过期时间（分钟）"""
    app_settings = get_settings()
    return app_settings.ACCESS_TOKEN_EXPIRE_MINUTES


def is_debug_mode() -> bool:
    """检查是否为调试模式"""
    app_settings = get_settings()
    return app_settings.DEBUG


def get_upload_config() -> Dict[str, Any]:
    """获取文件上传配置"""
    app_settings = get_settings()
    
    return {
        "upload_dir": app_settings.UPLOAD_DIR,
        "max_upload_size": app_settings.MAX_UPLOAD_SIZE,
        "allowed_extensions": app_settings.ALLOWED_EXTENSIONS,
    }


def get_face_recognition_config() -> Dict[str, Any]:
    """获取人脸识别配置"""
    app_settings = get_settings()
    
    return {
        "tolerance": app_settings.FACE_RECOGNITION_TOLERANCE,
        "detection_model": app_settings.FACE_DETECTION_MODEL,
        "data_dir": app_settings.FACE_DATA_DIR,
    }


def get_attendance_rules() -> Dict[str, Any]:
    """获取考勤规则配置"""
    app_settings = get_settings()
    
    return {
        "work_start_time": app_settings.WORK_START_TIME,
        "work_end_time": app_settings.WORK_END_TIME,
        "late_threshold_minutes": app_settings.LATE_THRESHOLD_MINUTES,
        "early_leave_threshold_minutes": app_settings.EARLY_LEAVE_THRESHOLD_MINUTES,
        "overtime_threshold_minutes": app_settings.OVERTIME_THRESHOLD_MINUTES,
    }


def get_leave_rules() -> Dict[str, Any]:
    """获取请假规则配置"""
    app_settings = get_settings()
    
    return {
        "annual_leave_days": app_settings.ANNUAL_LEAVE_DAYS,
        "sick_leave_days": app_settings.SICK_LEAVE_DAYS,
        "personal_leave_days": app_settings.PERSONAL_LEAVE_DAYS,
    }


def get_backup_config() -> Dict[str, Any]:
    """获取备份配置"""
    app_settings = get_settings()
    
    return {
        "backup_dir": app_settings.BACKUP_DIR,
        "auto_backup_enabled": app_settings.AUTO_BACKUP_ENABLED,
        "backup_retention_days": app_settings.BACKUP_RETENTION_DAYS,
    }


def get_log_config() -> Dict[str, Any]:
    """获取日志配置"""
    app_settings = get_settings()
    
    return {
        "log_dir": app_settings.LOG_DIR,
        "log_level": app_settings.LOG_LEVEL,
        "log_max_bytes": app_settings.LOG_MAX_BYTES,
        "log_backup_count": app_settings.LOG_BACKUP_COUNT,
    }