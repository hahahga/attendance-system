"""
开发环境配置
"""

from .settings import Settings


class DevelopmentSettings(Settings):
    """开发环境配置"""
    
    # 应用基础配置
    DEBUG: bool = True
    ENVIRONMENT: str = "development"
    
    # 数据库配置
    DATABASE_URL: str = "mysql://root:YYH.204113@localhost:3306/mysql"
    
    # 日志配置
    LOG_LEVEL: str = "DEBUG"
    
    # 安全配置
    SECRET_KEY: str = "dev-secret-key-not-for-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 开发环境令牌有效期更长
    
    # CORS配置 - 开发环境允许所有来源
    BACKEND_CORS_ORIGINS: list = [
        "http://localhost:3000",
        "http://localhost:8080",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8080",
    ]
    
    # 自动重载配置
    AUTO_RELOAD: bool = True
    
    # 邮件配置 - 开发环境使用控制台输出
    SMTP_HOST: str = "localhost"
    SMTP_PORT: int = 1025
    EMAILS_FROM_EMAIL: str = "dev@attendance-system.local"
    EMAILS_FROM_NAME: str = "考勤系统(开发环境)"