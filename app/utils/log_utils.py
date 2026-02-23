"""
日志处理相关工具函数
"""

import logging
import os
import sys
from datetime import datetime
from typing import Optional

from core.config import settings


def setup_logger(
    name: str,
    log_file: Optional[str] = None,
    level: str = None,
    format_string: Optional[str] = None
) -> logging.Logger:
    """
    设置日志记录器
    
    Args:
        name: 日志记录器名称
        log_file: 日志文件路径，如果不提供则使用配置中的日志文件
        level: 日志级别，如果不提供则使用配置中的日志级别
        format_string: 日志格式字符串
        
    Returns:
        配置好的日志记录器
    """
    # 创建日志记录器
    logger = logging.getLogger(name)
    
    # 避免重复添加处理器
    if logger.handlers:
        return logger
    
    # 设置日志级别
    log_level = level or settings.LOG_LEVEL.upper()
    logger.setLevel(getattr(logging, log_level))
    
    # 设置日志格式
    if format_string is None:
        format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    formatter = logging.Formatter(format_string)
    
    # 添加控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 添加文件处理器
    file_path = log_file or settings.LOG_FILE
    if file_path:
        # 确保日志目录存在
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        file_handler = logging.FileHandler(file_path, encoding='utf-8')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def log_user_action(
    user_id: str,
    action: str,
    details: str = "",
    ip_address: str = "",
    user_agent: str = ""
) -> None:
    """
    记录用户操作日志
    
    Args:
        user_id: 用户ID
        action: 操作类型
        details: 操作详情
        ip_address: IP地址
        user_agent: 用户代理
    """
    logger = setup_logger("user_actions")
    message = f"用户ID: {user_id}, 操作: {action}"
    
    if details:
        message += f", 详情: {details}"
    
    if ip_address:
        message += f", IP: {ip_address}"
    
    if user_agent:
        message += f", User-Agent: {user_agent}"
    
    logger.info(message)


def log_system_event(
    event_type: str,
    details: str,
    level: str = "info"
) -> None:
    """
    记录系统事件日志
    
    Args:
        event_type: 事件类型
        details: 事件详情
        level: 日志级别
    """
    logger = setup_logger("system_events")
    
    message = f"事件类型: {event_type}, 详情: {details}"
    
    log_method = getattr(logger, level.lower(), logger.info)
    log_method(message)


def log_security_event(
    event_type: str,
    details: str,
    user_id: str = "",
    ip_address: str = ""
) -> None:
    """
    记录安全事件日志
    
    Args:
        event_type: 事件类型
        details: 事件详情
        user_id: 用户ID
        ip_address: IP地址
    """
    logger = setup_logger("security_events")
    message = f"安全事件: {event_type}, 详情: {details}"
    
    if user_id:
        message += f", 用户ID: {user_id}"
    
    if ip_address:
        message += f", IP: {ip_address}"
    
    logger.warning(message)


def log_error(
    error_type: str,
    error_message: str,
    traceback: str = "",
    user_id: str = "",
    request_id: str = ""
) -> None:
    """
    记录错误日志
    
    Args:
        error_type: 错误类型
        error_message: 错误消息
        traceback: 错误堆栈
        user_id: 用户ID
        request_id: 请求ID
    """
    logger = setup_logger("errors")
    message = f"错误类型: {error_type}, 错误消息: {error_message}"
    
    if user_id:
        message += f", 用户ID: {user_id}"
    
    if request_id:
        message += f", 请求ID: {request_id}"
    
    if traceback:
        message += f", 堆栈: {traceback}"
    
    logger.error(message)


def log_api_request(
    method: str,
    endpoint: str,
    status_code: int,
    response_time: float,
    user_id: str = "",
    ip_address: str = ""
) -> None:
    """
    记录API请求日志
    
    Args:
        method: HTTP方法
        endpoint: API端点
        status_code: 响应状态码
        response_time: 响应时间（毫秒）
        user_id: 用户ID
        ip_address: IP地址
    """
    logger = setup_logger("api_requests")
    message = f"{method} {endpoint} - {status_code} - {response_time:.2f}ms"
    
    if user_id:
        message += f", 用户ID: {user_id}"
    
    if ip_address:
        message += f", IP: {ip_address}"
    
    logger.info(message)


def log_database_operation(
    operation: str,
    table: str,
    details: str = "",
    execution_time: float = 0.0
) -> None:
    """
    记录数据库操作日志
    
    Args:
        operation: 操作类型（SELECT, INSERT, UPDATE, DELETE等）
        table: 表名
        details: 操作详情
        execution_time: 执行时间（毫秒）
    """
    logger = setup_logger("database_operations")
    message = f"数据库操作: {operation} 表: {table}"
    
    if details:
        message += f", 详情: {details}"
    
    if execution_time > 0:
        message += f", 执行时间: {execution_time:.2f}ms"
    
    logger.debug(message)


def log_email_sent(
    to_emails: list,
    subject: str,
    success: bool,
    error_message: str = ""
) -> None:
    """
    记录邮件发送日志
    
    Args:
        to_emails: 收件人邮箱列表
        subject: 邮件主题
        success: 是否发送成功
        error_message: 错误消息（如果发送失败）
    """
    logger = setup_logger("email_operations")
    
    if success:
        logger.info(f"邮件发送成功 - 收件人: {', '.join(to_emails)}, 主题: {subject}")
    else:
        logger.error(f"邮件发送失败 - 收件人: {', '.join(to_emails)}, 主题: {subject}, 错误: {error_message}")


def log_file_operation(
    operation: str,
    file_path: str,
    success: bool,
    details: str = ""
) -> None:
    """
    记录文件操作日志
    
    Args:
        operation: 操作类型（上传、下载、删除等）
        file_path: 文件路径
        success: 是否操作成功
        details: 操作详情
    """
    logger = setup_logger("file_operations")
    
    message = f"文件操作: {operation} - 路径: {file_path}"
    
    if details:
        message += f", 详情: {details}"
    
    if success:
        logger.info(message)
    else:
        logger.error(message)


def cleanup_old_logs(days_to_keep: int = 30) -> None:
    """
    清理旧的日志文件
    
    Args:
        days_to_keep: 保留天数
    """
    logger = setup_logger("log_cleanup")
    
    log_dir = os.path.dirname(settings.LOG_FILE)
    
    if not os.path.exists(log_dir):
        return
    
    current_time = datetime.now()
    
    for filename in os.listdir(log_dir):
        if not filename.endswith('.log'):
            continue
        
        file_path = os.path.join(log_dir, filename)
        
        # 获取文件修改时间
        file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
        
        # 计算文件天数
        days_old = (current_time - file_time).days
        
        # 如果文件超过保留天数，则删除
        if days_old > days_to_keep:
            try:
                os.remove(file_path)
                logger.info(f"删除旧日志文件: {filename}")
            except Exception as e:
                logger.error(f"删除日志文件失败: {filename}, 错误: {str(e)}")


# 创建默认日志记录器
app_logger = setup_logger("app")
user_logger = setup_logger("user_actions")
system_logger = setup_logger("system_events")
security_logger = setup_logger("security_events")
error_logger = setup_logger("errors")
api_logger = setup_logger("api_requests")
db_logger = setup_logger("database_operations")
email_logger = setup_logger("email_operations")
file_logger = setup_logger("file_operations")