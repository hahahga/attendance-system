"""
生产环境配置
"""

import os
from .settings import Settings


class ProductionSettings(Settings):
    """生产环境配置"""
    
    # 应用基础配置
    DEBUG: bool = False
    ENVIRONMENT: str = "production"
    
    # 数据库配置 - 生产环境应使用PostgreSQL或MySQL
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/attendance_db")
    
    # 日志配置
    LOG_LEVEL: str = "WARNING"
    
    # 安全配置 - 生产环境必须设置强密钥
    SECRET_KEY: str = os.getenv("SECRET_KEY", "change-me-in-production")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS配置 - 生产环境应限制允许的来源
    BACKEND_CORS_ORIGINS: list = os.getenv(
        "BACKEND_CORS_ORIGINS", 
        "https://yourdomain.com"
    ).split(",")
    
    # 自动重载配置 - 生产环境关闭
    AUTO_RELOAD: bool = False
    
    # 邮件配置 - 生产环境应使用真实SMTP服务器
    SMTP_HOST: str = os.getenv("SMTP_HOST", "")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    EMAILS_FROM_EMAIL: str = os.getenv("EMAILS_FROM_EMAIL", "noreply@yourdomain.com")
    EMAILS_FROM_NAME: str = os.getenv("EMAILS_FROM_NAME", "员工考勤管理系统")
    
    # 数据备份配置 - 生产环境启用自动备份
    AUTO_BACKUP_ENABLED: bool = True
    BACKUP_RETENTION_DAYS: int = 90
    
    # 文件上传配置 - 生产环境限制更严格
    MAX_UPLOAD_SIZE: int = 5 * 1024 * 1024  # 5MB
    
    # 安全头部配置
    SECURITY_HEADERS: dict = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    }