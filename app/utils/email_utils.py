"""
邮件发送相关工具函数
"""

import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from typing import List, Optional, Dict, Any

from jinja2 import Template

from core.config import settings


class EmailSender:
    """邮件发送工具类"""
    
    def __init__(
        self,
        smtp_server: str = None,
        smtp_port: int = None,
        username: str = None,
        password: str = None,
        use_tls: bool = True
    ):
        """
        初始化邮件发送器
        
        Args:
            smtp_server: SMTP服务器地址
            smtp_port: SMTP服务器端口
            username: 邮箱用户名
            password: 邮箱密码
            use_tls: 是否使用TLS加密
        """
        self.smtp_server = smtp_server or settings.SMTP_SERVER
        self.smtp_port = smtp_port or settings.SMTP_PORT
        self.username = username or settings.SMTP_USERNAME
        self.password = password or settings.SMTP_PASSWORD
        self.use_tls = use_tls
    
    def send_email(
        self,
        to_emails: List[str],
        subject: str,
        body: str,
        is_html: bool = False,
        cc_emails: List[str] = None,
        bcc_emails: List[str] = None,
        attachments: List[str] = None,
        reply_to: str = None
    ) -> bool:
        """
        发送邮件
        
        Args:
            to_emails: 收件人邮箱列表
            subject: 邮件主题
            body: 邮件正文
            is_html: 是否为HTML格式
            cc_emails: 抄送邮箱列表
            bcc_emails: 密送邮箱列表
            attachments: 附件路径列表
            reply_to: 回复邮箱
            
        Returns:
            是否发送成功
        """
        try:
            # 创建邮件对象
            msg = MIMEMultipart()
            msg["From"] = self.username
            msg["To"] = ", ".join(to_emails)
            msg["Subject"] = subject
            
            if cc_emails:
                msg["Cc"] = ", ".join(cc_emails)
            
            if reply_to:
                msg["Reply-To"] = reply_to
            
            # 添加邮件正文
            if is_html:
                msg.attach(MIMEText(body, "html"))
            else:
                msg.attach(MIMEText(body, "plain"))
            
            # 添加附件
            if attachments:
                for file_path in attachments:
                    if os.path.exists(file_path):
                        with open(file_path, "rb") as attachment:
                            part = MIMEBase("application", "octet-stream")
                            part.set_payload(attachment.read())
                            encoders.encode_base64(part)
                            part.add_header(
                                "Content-Disposition",
                                f"attachment; filename= {os.path.basename(file_path)}"
                            )
                            msg.attach(part)
            
            # 创建所有收件人列表（包括抄送和密送）
            all_recipients = to_emails.copy()
            if cc_emails:
                all_recipients.extend(cc_emails)
            if bcc_emails:
                all_recipients.extend(bcc_emails)
            
            # 连接SMTP服务器并发送邮件
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                if self.use_tls:
                    server.starttls()
                
                if self.username and self.password:
                    server.login(self.username, self.password)
                
                server.send_message(msg, to_addrs=all_recipients)
            
            return True
        except Exception as e:
            print(f"发送邮件失败: {str(e)}")
            return False
    
    def send_template_email(
        self,
        to_emails: List[str],
        subject: str,
        template_path: str,
        template_data: Dict[str, Any],
        is_html: bool = True,
        cc_emails: List[str] = None,
        bcc_emails: List[str] = None,
        attachments: List[str] = None,
        reply_to: str = None
    ) -> bool:
        """
        发送模板邮件
        
        Args:
            to_emails: 收件人邮箱列表
            subject: 邮件主题
            template_path: 模板文件路径
            template_data: 模板数据
            is_html: 是否为HTML格式
            cc_emails: 抄送邮箱列表
            bcc_emails: 密送邮箱列表
            attachments: 附件路径列表
            reply_to: 回复邮箱
            
        Returns:
            是否发送成功
        """
        try:
            # 读取模板文件
            with open(template_path, "r", encoding="utf-8") as f:
                template_content = f.read()
            
            # 渲染模板
            template = Template(template_content)
            body = template.render(**template_data)
            
            # 发送邮件
            return self.send_email(
                to_emails=to_emails,
                subject=subject,
                body=body,
                is_html=is_html,
                cc_emails=cc_emails,
                bcc_emails=bcc_emails,
                attachments=attachments,
                reply_to=reply_to
            )
        except Exception as e:
            print(f"发送模板邮件失败: {str(e)}")
            return False


# 创建全局邮件发送器实例
email_sender = EmailSender()


def send_welcome_email(to_email: str, username: str) -> bool:
    """
    发送欢迎邮件
    
    Args:
        to_email: 收件人邮箱
        username: 用户名
        
    Returns:
        是否发送成功
    """
    subject = "欢迎使用考勤系统"
    body = f"""
    亲爱的 {username}，
    
    欢迎您注册并使用我们的考勤系统！
    
    您可以使用以下功能：
    - 人脸识别签到
    - 请假申请
    - 考勤记录查询
    - 个人信息管理
    
    如果您有任何问题，请联系管理员。
    
    祝好！
    考勤系统团队
    """
    
    return email_sender.send_email(
        to_emails=[to_email],
        subject=subject,
        body=body
    )


def send_password_reset_email(to_email: str, reset_token: str) -> bool:
    """
    发送密码重置邮件
    
    Args:
        to_email: 收件人邮箱
        reset_token: 重置令牌
        
    Returns:
        是否发送成功
    """
    subject = "密码重置请求"
    reset_url = f"{settings.FRONTEND_URL}/reset-password?token={reset_token}"
    body = f"""
    您好，
    
    我们收到了您的密码重置请求。
    
    请点击以下链接重置您的密码：
    {reset_url}
    
    如果您没有请求密码重置，请忽略此邮件。
    
    此链接将在 {settings.EMAIL_RESET_TOKEN_EXPIRE_HOURS} 小时后失效。
    
    祝好！
    考勤系统团队
    """
    
    return email_sender.send_email(
        to_emails=[to_email],
        subject=subject,
        body=body
    )


def send_leave_notification_email(
    to_emails: List[str],
    employee_name: str,
    leave_type: str,
    start_date: str,
    end_date: str,
    reason: str,
    is_approved: bool = None
) -> bool:
    """
    发送请假通知邮件
    
    Args:
        to_emails: 收件人邮箱列表
        employee_name: 员工姓名
        leave_type: 请假类型
        start_date: 开始日期
        end_date: 结束日期
        reason: 请假原因
        is_approved: 是否批准（None表示申请中）
        
    Returns:
        是否发送成功
    """
    if is_approved is None:
        subject = f"请假申请通知 - {employee_name}"
        status = "待审批"
    elif is_approved:
        subject = f"请假批准通知 - {employee_name}"
        status = "已批准"
    else:
        subject = f"请假拒绝通知 - {employee_name}"
        status = "已拒绝"
    
    body = f"""
    尊敬的管理员，
    
    以下是请假申请详情：
    
    申请人：{employee_name}
    请假类型：{leave_type}
    请假时间：{start_date} 至 {end_date}
    申请状态：{status}
    请假原因：{reason}
    
    请登录系统查看详情并进行相应操作。
    
    祝好！
    考勤系统团队
    """
    
    return email_sender.send_email(
        to_emails=to_emails,
        subject=subject,
        body=body
    )


def send_attendance_report_email(
    to_emails: List[str],
    report_file_path: str,
    report_month: str
) -> bool:
    """
    发送考勤报告邮件
    
    Args:
        to_emails: 收件人邮箱列表
        report_file_path: 报告文件路径
        report_month: 报告月份
        
    Returns:
        是否发送成功
    """
    subject = f"考勤报告 - {report_month}"
    body = f"""
    尊敬的管理员，
    
    附件是 {report_month} 的考勤报告，请查收。
    
    如有任何问题，请联系系统管理员。
    
    祝好！
    考勤系统团队
    """
    
    return email_sender.send_email(
        to_emails=to_emails,
        subject=subject,
        body=body,
        attachments=[report_file_path]
    )


def send_system_notification_email(
    to_emails: List[str],
    title: str,
    message: str
) -> bool:
    """
    发送系统通知邮件
    
    Args:
        to_emails: 收件人邮箱列表
        title: 通知标题
        message: 通知内容
        
    Returns:
        是否发送成功
    """
    subject = f"系统通知 - {title}"
    body = f"""
    尊敬的用户，
    
    {message}
    
    请登录系统查看详情。
    
    祝好！
    考勤系统团队
    """
    
    return email_sender.send_email(
        to_emails=to_emails,
        subject=subject,
        body=body
    )