import smtplib
import httpx
import json
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr
from email.header import Header
from datetime import datetime, timedelta
import secrets
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from app.core.config import settings
from app.models import EmailConfig, EmailLog, SiteConfig
from app.utils.timezone import get_now, get_db_now


logger = logging.getLogger(__name__)

EMAIL_PROVIDERS = {
    'qq': {
        'host': 'smtp.qq.com',
        'port': 587
    },
    'gmail': {
        'host': 'smtp.gmail.com',
        'port': 587
    },
    '163': {
        'host': 'smtp.163.com',
        'port': 465
    },
    'outlook': {
        'host': 'smtp-mail.outlook.com',
        'port': 587
    }
}

RESEND_API_URL = "https://api.resend.com/emails"


class EmailService:
    @staticmethod
    def get_site_name(db: Session) -> str:
        config = db.query(SiteConfig).filter(SiteConfig.key == "site_name").first()
        if config and config.value:
            return config.value
        return "Futuristic Blog"
    
    @staticmethod
    def get_current_year() -> int:
        return get_now().year
    
    @staticmethod
    def generate_verification_token() -> str:
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def get_token_expiry() -> datetime:
        return get_db_now() + timedelta(hours=24)
    
    @staticmethod
    def get_active_config(db: Session) -> Optional[EmailConfig]:
        return db.query(EmailConfig).filter(EmailConfig.is_active == True).first()
    
    @staticmethod
    def get_admin_real_email(db: Session) -> Optional[str]:
        from app.services.permission_service import PermissionService
        admin_users = PermissionService.get_admin_users(db)
        for admin in admin_users:
            if admin.email and admin.email != 'admin@futuristic-blog.com':
                return admin.email
        admin_email = getattr(settings, 'ADMIN_EMAIL', None)
        if admin_email and admin_email != 'admin@futuristic-blog.com':
            return admin_email
        return None
    
    @staticmethod
    def is_email_configured(db: Session) -> bool:
        config = EmailService.get_active_config(db)
        if config:
            return True
        if settings.RESEND_API_KEY:
            return True
        if settings.is_email_configured:
            return True
        return False
    
    @staticmethod
    def get_email_provider(db: Session) -> str:
        config = EmailService.get_active_config(db)
        if config and config.provider:
            return config.provider
        return settings.EMAIL_PROVIDER
    
    @staticmethod
    def send_via_resend(
        to_email: str,
        subject: str,
        html_content: str,
        text_content: str = None,
        from_email: str = None,
        from_name: str = None
    ) -> Dict[str, Any]:
        if not settings.RESEND_API_KEY:
            raise ValueError("RESEND_API_KEY is not configured")
        
        sender_email = from_email or settings.RESEND_FROM_EMAIL or "onboarding@resend.dev"
        sender_name = from_name or settings.SMTP_FROM_NAME or "Futuristic Blog"
        
        payload = {
            "from": f"{sender_name} <{sender_email}>",
            "to": [to_email],
            "subject": subject,
            "html": html_content
        }
        
        if text_content:
            payload["text"] = text_content
        
        headers = {
            "Authorization": f"Bearer {settings.RESEND_API_KEY}",
            "Content-Type": "application/json"
        }
        
        logger.info(f"Sending email via Resend to {to_email}")
        
        with httpx.Client(timeout=10.0) as client:
            response = client.post(
                RESEND_API_URL,
                headers=headers,
                json=payload
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"Resend email sent successfully: {result.get('id')}")
                return {
                    "success": True,
                    "message_id": result.get("id"),
                    "provider": "resend"
                }
            else:
                error_detail = response.text
                logger.error(f"Resend API error: {response.status_code} - {error_detail}")
                raise Exception(f"Resend API error: {error_detail}")
    
    @staticmethod
    def send_via_smtp(
        to_email: str,
        subject: str,
        html_content: str,
        text_content: str = None,
        config: EmailConfig = None
    ) -> Dict[str, Any]:
        smtp_host = config.smtp_host if config else settings.SMTP_HOST
        smtp_port = config.smtp_port if config else settings.SMTP_PORT
        smtp_user = (config.smtp_user if config else settings.SMTP_USER or '').strip()
        smtp_password = (config.smtp_password if config else settings.SMTP_PASSWORD or '').replace(' ', '').replace('\xa0', '').replace('\u00a0', '').strip()
        from_email = config.from_email if config else settings.SMTP_FROM_EMAIL
        from_name = config.from_name if config else settings.SMTP_FROM_NAME
        
        if not all([smtp_host, smtp_user, smtp_password]):
            raise ValueError("SMTP configuration is incomplete")
        
        msg = MIMEMultipart('alternative')
        msg['Subject'] = Header(subject, 'utf-8')
        msg['From'] = formataddr((str(Header(from_name, 'utf-8')), from_email))
        msg['To'] = to_email
        
        if text_content:
            part1 = MIMEText(text_content, 'plain', 'utf-8')
            msg.attach(part1)
        
        part2 = MIMEText(html_content, 'html', 'utf-8')
        msg.attach(part2)
        
        logger.info(f"Sending email via SMTP to {to_email}")
        
        use_ssl = smtp_port == 465
        
        try:
            if use_ssl:
                server = smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=10)
                server.login(smtp_user, smtp_password)
                server.sendmail(from_email, to_email, msg.as_string())
                server.quit()
            else:
                server = smtplib.SMTP(smtp_host, smtp_port, timeout=10)
                server.ehlo()
                server.starttls()
                server.ehlo()
                server.login(smtp_user, smtp_password)
                server.sendmail(from_email, to_email, msg.as_string())
                server.quit()
        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"SMTP authentication failed: {e}")
            raise Exception(f"SMTP 认证失败，请检查邮箱和授权码是否正确")
        except smtplib.SMTPConnectError as e:
            logger.error(f"SMTP connection failed: {e}")
            raise Exception(f"SMTP 连接失败，请检查网络或 SMTP 服务器地址")
        except TimeoutError as e:
            logger.error(f"SMTP connection timeout: {e}")
            raise Exception(f"SMTP 连接超时，请检查网络连接")
        
        logger.info(f"SMTP email sent successfully to {to_email}")
        return {
            "success": True,
            "provider": "smtp"
        }
    
    @staticmethod
    def send_email(
        db: Session,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: str = None,
        email_type: str = "verification",
        recipient_name: str = None,
        user_id: int = None,
        verification_token: str = None
    ) -> bool:
        config = EmailService.get_active_config(db)
        provider = EmailService.get_email_provider(db)
        
        log = EmailLog(
            email_type=email_type,
            recipient_email=to_email,
            recipient_name=recipient_name,
            subject=subject,
            status='pending',
            verification_token=verification_token,
            user_id=user_id
        )
        
        try:
            result = None
            provider_used = None
            
            if provider == 'resend' and settings.RESEND_API_KEY:
                try:
                    from_email = settings.RESEND_FROM_EMAIL or (config.from_email if config else None)
                    from_name = config.from_name if config else None
                    result = EmailService.send_via_resend(
                        to_email=to_email,
                        subject=subject,
                        html_content=html_content,
                        text_content=text_content,
                        from_email=from_email,
                        from_name=from_name
                    )
                    provider_used = 'resend'
                except Exception as resend_error:
                    logger.warning(f"Resend failed, falling back to SMTP: {resend_error}")
                    if config or settings.is_email_configured:
                        result = EmailService.send_via_smtp(
                            to_email=to_email,
                            subject=subject,
                            html_content=html_content,
                            text_content=text_content,
                            config=config
                        )
                        provider_used = 'smtp'
                    else:
                        raise
            
            elif provider == 'smtp' or provider in EMAIL_PROVIDERS:
                if config or settings.is_email_configured:
                    result = EmailService.send_via_smtp(
                        to_email=to_email,
                        subject=subject,
                        html_content=html_content,
                        text_content=text_content,
                        config=config
                    )
                    provider_used = 'smtp'
                else:
                    raise ValueError("No email configuration available")
            
            else:
                if settings.RESEND_API_KEY:
                    result = EmailService.send_via_resend(
                        to_email=to_email,
                        subject=subject,
                        html_content=html_content,
                        text_content=text_content
                    )
                    provider_used = 'resend'
                elif config or settings.is_email_configured:
                    result = EmailService.send_via_smtp(
                        to_email=to_email,
                        subject=subject,
                        html_content=html_content,
                        text_content=text_content,
                        config=config
                    )
                    provider_used = 'smtp'
                else:
                    logger.warning("No email provider configured, running in dev mode")
                    print(f"[DEV MODE] Email to: {to_email}")
                    print(f"[DEV MODE] Subject: {subject}")
                    if verification_token:
                        print(f"[DEV MODE] Verification URL: {settings.FRONTEND_URL}/verify-email?token={verification_token}")
                    log.status = 'dev_mode'
                    log.error_message = 'No email provider configured'
                    db.add(log)
                    db.commit()
                    return True
            
            if result and result.get('success'):
                log.status = 'sent'
                log.sent_at = get_db_now()
                logger.info(f"Email sent successfully via {provider_used} to {to_email}")
                return True
            else:
                raise Exception("Failed to send email")
                
        except Exception as e:
            log.status = 'failed'
            log.error_message = str(e)
            logger.error(f"Failed to send email to {to_email}: {e}")
            logger.error(
                f"邮件发送失败通知 | 类型: {email_type} | 收件人: {to_email} | "
                f"主题: {subject[:50]}{'...' if len(subject) > 50 else ''} | 错误: {str(e)}"
            )
            return False
        finally:
            db.add(log)
            db.commit()
    
    @staticmethod
    def send_verification_email_db(
        db: Session, 
        email: str, 
        username: str, 
        token: str,
        user_id: int = None
    ) -> bool:
        site_name = EmailService.get_site_name(db)
        current_year = EmailService.get_current_year()
        
        verification_url = f"{settings.FRONTEND_URL}/verify-email?token={token}"
        
        text_content = f"""
您好 {username}，

感谢您注册 {site_name}！

请点击以下链接验证您的邮箱地址：
{verification_url}

此链接将在24小时后过期。

如果您没有注册账户，请忽略此邮件。

祝好，
{site_name} 团队
"""
        
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f5f5f5; color: #333333; padding: 20px; margin: 0; }}
        .container {{ max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 8px; padding: 40px; border: 1px solid #e0e0e0; }}
        .logo {{ font-size: 24px; font-weight: bold; color: #0066cc; margin-bottom: 30px; }}
        .title {{ font-size: 20px; margin-bottom: 20px; color: #333333; }}
        .button {{ display: inline-block; padding: 12px 32px; background-color: #0066cc; color: #ffffff; text-decoration: none; border-radius: 6px; margin: 20px 0; font-weight: 500; }}
        .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #e0e0e0; font-size: 14px; color: #666666; }}
        .link {{ word-break: break-all; color: #0066cc; }}
        p {{ line-height: 1.6; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="logo">🚀 {site_name}</div>
        <h1 class="title">欢迎加入我们，{username}！</h1>
        <p>感谢您注册 {site_name}！请点击下方按钮验证您的邮箱地址：</p>
        <a href="{verification_url}" class="button">验证邮箱</a>
        <p>或复制以下链接到浏览器：</p>
        <p class="link">{verification_url}</p>
        <p>此链接将在 <strong>24小时</strong> 后过期。</p>
        <div class="footer">
            <p>如果您没有注册账户，请忽略此邮件。</p>
            <p>© {current_year} {site_name}. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
"""
        
        return EmailService.send_email(
            db=db,
            to_email=email,
            subject=f"验证您的邮箱 - {site_name}",
            html_content=html_content,
            text_content=text_content,
            email_type='verification',
            recipient_name=username,
            user_id=user_id,
            verification_token=token
        )
    
    @staticmethod
    def send_verification_email(email: str, username: str, token: str) -> bool:
        site_name = settings.SMTP_FROM_NAME if settings.SMTP_FROM_NAME else "Futuristic Blog"
        current_year = EmailService.get_current_year()
        
        verification_url = f"{settings.FRONTEND_URL}/verify-email?token={token}"
        
        text_content = f"""
您好 {username}，

感谢您注册 {site_name}！

请点击以下链接验证您的邮箱地址：
{verification_url}

此链接将在24小时后过期。

如果您没有注册账户，请忽略此邮件。

祝好，
{site_name} 团队
"""
        
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f5f5f5; color: #333333; padding: 20px; margin: 0; }}
        .container {{ max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 8px; padding: 40px; border: 1px solid #e0e0e0; }}
        .logo {{ font-size: 24px; font-weight: bold; color: #0066cc; margin-bottom: 30px; }}
        .title {{ font-size: 20px; margin-bottom: 20px; color: #333333; }}
        .button {{ display: inline-block; padding: 12px 32px; background-color: #0066cc; color: #ffffff; text-decoration: none; border-radius: 6px; margin: 20px 0; font-weight: 500; }}
        .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #e0e0e0; font-size: 14px; color: #666666; }}
        .link {{ word-break: break-all; color: #0066cc; }}
        p {{ line-height: 1.6; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="logo">🚀 {site_name}</div>
        <h1 class="title">欢迎加入我们，{username}！</h1>
        <p>感谢您注册 {site_name}！请点击下方按钮验证您的邮箱地址：</p>
        <a href="{verification_url}" class="button">验证邮箱</a>
        <p>或复制以下链接到浏览器：</p>
        <p class="link">{verification_url}</p>
        <p>此链接将在 <strong>24小时</strong> 后过期。</p>
        <div class="footer">
            <p>如果您没有注册账户，请忽略此邮件。</p>
            <p>© {current_year} {site_name}. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
"""
        
        try:
            if settings.RESEND_API_KEY:
                result = EmailService.send_via_resend(
                    to_email=email,
                    subject=f"验证您的邮箱 - {site_name}",
                    html_content=html_content,
                    text_content=text_content
                )
                return result.get('success', False)
            elif settings.is_email_configured:
                result = EmailService.send_via_smtp(
                    to_email=email,
                    subject=f"验证您的邮箱 - {site_name}",
                    html_content=html_content,
                    text_content=text_content
                )
                return result.get('success', False)
            else:
                print(f"[DEV MODE] Verification token for {email}: {token}")
                print(f"[DEV MODE] Verification URL: {verification_url}")
                return True
        except Exception as e:
            logger.error(f"Failed to send verification email: {e}")
            return False
    
    @staticmethod
    def send_resend_verification(email: str, username: str, token: str) -> bool:
        return EmailService.send_verification_email(email, username, token)
    
    @staticmethod
    def send_admin_notification_db(
        db: Session,
        subject: str,
        html_content: str,
        text_content: str = None,
        notification_type: str = "admin_notification"
    ) -> bool:
        from app.services.permission_service import PermissionService
        admin_users = PermissionService.get_admin_users(db)
        
        if not admin_users:
            logger.warning("No admin users found to notify")
            return False
        
        success = True
        for admin in admin_users:
            if not admin.email or admin.email == 'admin@futuristic-blog.com':
                continue
            result = EmailService.send_email(
                db=db,
                to_email=admin.email,
                subject=subject,
                html_content=html_content,
                text_content=text_content,
                email_type=notification_type,
                recipient_name=admin.username,
                user_id=admin.id
            )
            if not result:
                success = False
        
        return success
    
    @staticmethod
    def send_new_user_notification_db(
        db: Session,
        new_username: str,
        new_email: str
    ) -> bool:
        site_name = EmailService.get_site_name(db)
        current_year = EmailService.get_current_year()
        
        text_content = f"""
新用户注册通知

用户名: {new_username}
邮箱: {new_email}

请登录管理后台查看详情。

{site_name}
"""
        
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f5f5f5; color: #333333; padding: 20px; margin: 0; }}
        .container {{ max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 8px; padding: 40px; border: 1px solid #e0e0e0; }}
        .logo {{ font-size: 24px; font-weight: bold; color: #0066cc; margin-bottom: 30px; }}
        .title {{ font-size: 20px; margin-bottom: 20px; color: #0066cc; }}
        .info-box {{ background-color: #f0f7ff; border-radius: 8px; padding: 20px; margin: 20px 0; }}
        .info-item {{ margin: 10px 0; }}
        .label {{ color: #666666; font-size: 14px; }}
        .value {{ color: #333333; font-size: 16px; font-weight: 500; }}
        .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #e0e0e0; font-size: 14px; color: #666666; }}
        p {{ line-height: 1.6; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="logo">🚀 {site_name}</div>
        <h1 class="title">新用户注册通知</h1>
        <p>有一位新用户刚刚注册了账户：</p>
        <div class="info-box">
            <div class="info-item">
                <span class="label">用户名：</span>
                <span class="value">{new_username}</span>
            </div>
            <div class="info-item">
                <span class="label">邮箱：</span>
                <span class="value">{new_email}</span>
            </div>
        </div>
        <p>请登录管理后台查看详情。</p>
        <div class="footer">
            <p>此邮件为系统自动发送，请勿回复。</p>
            <p>© {current_year} {site_name}. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
"""
        
        return EmailService.send_admin_notification_db(
            db=db,
            subject=f"新用户注册 - {new_username}",
            html_content=html_content,
            text_content=text_content,
            notification_type="new_user"
        )
    
    @staticmethod
    def send_new_comment_notification_db(
        db: Session,
        commenter_name: str,
        article_title: str,
        article_slug: str,
        comment_content: str,
        author_email: str,
        author_name: str,
        comment_id: int = None
    ) -> bool:
        from app.services.permission_service import PermissionService
        
        site_name = EmailService.get_site_name(db)
        current_year = EmailService.get_current_year()
        
        if comment_id:
            article_url = f"{settings.FRONTEND_URL}/article/{article_slug}#comment-{comment_id}"
        else:
            article_url = f"{settings.FRONTEND_URL}/article/{article_slug}#comments"
        
        truncated_content = comment_content[:200] + "..." if len(comment_content) > 200 else comment_content
        
        is_deactivated = author_name and '已注销' in author_name
        
        if is_deactivated:
            greeting = f"{author_name}的文章收到了一条新评论"
        else:
            greeting = "您的文章收到了一条新评论"
        
        text_content = f"""
新评论通知

{greeting}

文章: {article_title}
评论者: {commenter_name}

评论内容:
{truncated_content}

查看评论: {article_url}

{site_name}
"""
        
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f5f5f5; color: #333333; padding: 20px; margin: 0; }}
        .container {{ max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 8px; padding: 40px; border: 1px solid #e0e0e0; }}
        .logo {{ font-size: 24px; font-weight: bold; color: #0066cc; margin-bottom: 30px; }}
        .title {{ font-size: 20px; margin-bottom: 20px; color: #0066cc; }}
        .info-box {{ background-color: #f0f7ff; border-radius: 8px; padding: 20px; margin: 20px 0; }}
        .comment-box {{ background-color: #f5f0ff; border-radius: 8px; padding: 20px; margin: 20px 0; border-left: 4px solid #7c3aed; }}
        .info-item {{ margin: 10px 0; }}
        .label {{ color: #666666; font-size: 14px; }}
        .value {{ color: #333333; font-size: 16px; font-weight: 500; }}
        .button {{ display: inline-block; padding: 12px 32px; background-color: #0066cc; color: #ffffff; text-decoration: none; border-radius: 6px; margin: 20px 0; font-weight: 500; }}
        .link {{ word-break: break-all; color: #0066cc; }}
        .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #e0e0e0; font-size: 14px; color: #666666; }}
        p {{ line-height: 1.6; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="logo">🚀 {site_name}</div>
        <h1 class="title">新评论通知</h1>
        <p>{greeting}：</p>
        <div class="info-box">
            <div class="info-item">
                <span class="label">文章：</span>
                <span class="value">{article_title}</span>
            </div>
            <div class="info-item">
                <span class="label">评论者：</span>
                <span class="value">{commenter_name}</span>
            </div>
        </div>
        <div class="comment-box">
            <p class="label">评论内容：</p>
            <p class="value">{truncated_content}</p>
        </div>
        <a href="{article_url}" class="button">查看评论</a>
        <p>或复制以下链接到浏览器：</p>
        <p class="link">{article_url}</p>
        <div class="footer">
            <p>此邮件为系统自动发送，请勿回复。</p>
            <p>© {current_year} {site_name}. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
"""
        
        admin_users = PermissionService.get_admin_users(db)
        recipients = set()
        
        if author_email:
            recipients.add(author_email)
        
        for admin in admin_users:
            if admin.email and admin.email != 'admin@futuristic-blog.com':
                recipients.add(admin.email)
        
        success = True
        for recipient_email in recipients:
            result = EmailService.send_email(
                db=db,
                to_email=recipient_email,
                subject=f"新评论 - {article_title}",
                html_content=html_content,
                text_content=text_content,
                email_type="new_comment"
            )
            if not result:
                success = False
        
        return success
    
    @staticmethod
    def send_new_like_notification_db(
        db: Session,
        liker_name: str,
        article_title: str,
        article_slug: str,
        author_email: str = None,
        author_name: str = None
    ) -> bool:
        if not author_email:
            author_email = EmailService.get_admin_real_email(db)
        
        if not author_email:
            return False
        
        site_name = EmailService.get_site_name(db)
        current_year = EmailService.get_current_year()
        
        article_url = f"{settings.FRONTEND_URL}/article/{article_slug}"
        
        is_deactivated = author_name and '已注销' in author_name
        
        if is_deactivated:
            greeting = f"{author_name}的文章收到了一个新的点赞"
        else:
            greeting = "您的文章收到了一个新的点赞"
        
        text_content = f"""
新点赞通知

{greeting}

文章: {article_title}
点赞者: {liker_name}

查看文章: {article_url}

{site_name}
"""
        
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f5f5f5; color: #333333; padding: 20px; margin: 0; }}
        .container {{ max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 8px; padding: 40px; border: 1px solid #e0e0e0; }}
        .logo {{ font-size: 24px; font-weight: bold; color: #0066cc; margin-bottom: 30px; }}
        .title {{ font-size: 20px; margin-bottom: 20px; color: #e91e63; }}
        .info-box {{ background-color: #fce4ec; border-radius: 8px; padding: 20px; margin: 20px 0; }}
        .info-item {{ margin: 10px 0; }}
        .label {{ color: #666666; font-size: 14px; }}
        .value {{ color: #333333; font-size: 16px; font-weight: 500; }}
        .heart {{ color: #e91e63; font-size: 24px; }}
        .button {{ display: inline-block; padding: 12px 32px; background-color: #e91e63; color: #ffffff; text-decoration: none; border-radius: 6px; margin: 20px 0; font-weight: 500; }}
        .link {{ word-break: break-all; color: #e91e63; }}
        .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #e0e0e0; font-size: 14px; color: #666666; }}
        p {{ line-height: 1.6; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="logo">🚀 {site_name}</div>
        <h1 class="title">新点赞通知 <span class="heart">❤️</span></h1>
        <p>{greeting}：</p>
        <div class="info-box">
            <div class="info-item">
                <span class="label">文章：</span>
                <span class="value">{article_title}</span>
            </div>
            <div class="info-item">
                <span class="label">点赞者：</span>
                <span class="value">{liker_name}</span>
            </div>
        </div>
        <a href="{article_url}" class="button">查看文章</a>
        <div class="footer">
            <p>此邮件为系统自动发送，请勿回复。</p>
            <p>© {current_year} {site_name}. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
"""
        
        return EmailService.send_email(
            db=db,
            to_email=author_email,
            subject=f"新点赞 - {article_title}",
            html_content=html_content,
            text_content=text_content,
            email_type="new_like",
            recipient_name=author_name
        )
    
    @staticmethod
    def test_email_provider(
        db: Session,
        provider: str = None,
        test_email: str = None
    ) -> Dict[str, Any]:
        provider = provider or EmailService.get_email_provider(db)
        test_email = test_email or EmailService.get_admin_real_email(db)
        
        if not test_email:
            return {
                "success": False,
                "error": "No test email address provided"
            }
        
        site_name = EmailService.get_site_name(db)
        
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f5f5f5; color: #333333; padding: 20px; margin: 0; }}
        .container {{ max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 8px; padding: 40px; border: 1px solid #e0e0e0; }}
        .logo {{ font-size: 24px; font-weight: bold; color: #0066cc; margin-bottom: 30px; }}
        .title {{ font-size: 20px; margin-bottom: 20px; color: #333333; }}
        .success {{ color: #10b981; font-size: 48px; }}
        .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #e0e0e0; font-size: 14px; color: #666666; }}
        p {{ line-height: 1.6; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="logo">🚀 {site_name}</div>
        <h1 class="title">邮件服务测试成功！</h1>
        <p class="success">✅</p>
        <p>恭喜！您的邮件服务配置正确，可以正常发送邮件。</p>
        <p>邮件服务商: <strong>{provider.upper()}</strong></p>
        <div class="footer">
            <p>此邮件为系统自动发送的测试邮件。</p>
            <p>© {EmailService.get_current_year()} {site_name}. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
"""
        
        try:
            return EmailService.send_email(
                db=db,
                to_email=test_email,
                subject=f"邮件服务测试 - {site_name}",
                html_content=html_content,
                text_content="邮件服务测试成功！",
                email_type='test',
                recipient_name='Admin'
            )
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    @staticmethod
    def send_reply_notification_db(
        db: Session,
        recipient_email: str,
        recipient_name: str,
        article_title: str,
        article_slug: str,
        reply_content: str,
        commenter_name: str,
        comment_id: int = None,
        parent_comment_id: int = None
    ) -> bool:
        site_name = EmailService.get_site_name(db)
        current_year = EmailService.get_current_year()
        
        target_id = parent_comment_id or comment_id
        if target_id:
            article_url = f"{settings.FRONTEND_URL}/article/{article_slug}#comment-{target_id}"
        else:
            article_url = f"{settings.FRONTEND_URL}/article/{article_slug}#comments"
        
        text_content = f"""
评论回复通知

您好，{recipient_name}！

您在文章「{article_title}」中的评论收到了新回复：

回复者：{commenter_name}
回复内容：{reply_content}

查看评论：{article_url}

{site_name}
"""
        
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f5f5f5; color: #333333; padding: 20px; margin: 0; }}
        .container {{ max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 8px; padding: 40px; border: 1px solid #e0e0e0; }}
        .logo {{ font-size: 24px; font-weight: bold; color: #0066cc; margin-bottom: 30px; }}
        .title {{ font-size: 20px; margin-bottom: 20px; color: #10b981; }}
        .info-box {{ background-color: #ecfdf5; border-radius: 8px; padding: 20px; margin: 20px 0; }}
        .comment-box {{ background-color: #f0f7ff; border-radius: 8px; padding: 20px; margin: 20px 0; border-left: 4px solid #10b981; }}
        .info-item {{ margin: 10px 0; }}
        .label {{ color: #666666; font-size: 14px; }}
        .value {{ color: #333333; font-size: 16px; font-weight: 500; }}
        .button {{ display: inline-block; padding: 12px 32px; background-color: #10b981; color: #ffffff; text-decoration: none; border-radius: 6px; margin: 20px 0; font-weight: 500; }}
        .link {{ word-break: break-all; color: #10b981; }}
        .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #e0e0e0; font-size: 14px; color: #666666; }}
        p {{ line-height: 1.6; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="logo">🚀 {site_name}</div>
        <h1 class="title">💬 您的评论收到了新回复</h1>
        <p>您好，{recipient_name}！</p>
        <p>您在文章「<strong>{article_title}</strong>」中的评论收到了新回复：</p>
        <div class="info-box">
            <div class="info-item">
                <span class="label">回复者：</span>
                <span class="value">{commenter_name}</span>
            </div>
        </div>
        <div class="comment-box">
            <p style="margin: 0; white-space: pre-wrap;">{reply_content}</p>
        </div>
        <a href="{article_url}" class="button">查看文章</a>
        <div class="footer">
            <p>此邮件为系统自动发送，请勿回复。</p>
            <p>© {current_year} {site_name}. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
"""
        
        try:
            return EmailService.send_email(
                db=db,
                to_email=recipient_email,
                subject=f"您的评论收到了新回复 - {article_title}",
                html_content=html_content,
                text_content=text_content,
                email_type='reply_notification',
                recipient_name=recipient_name
            )
        except Exception as e:
            logger.error(f"Failed to send reply notification: {e}")
            return False

    @staticmethod
    def send_comment_approved_notification_db(
        db: Session,
        recipient_email: str,
        recipient_name: str,
        article_title: str,
        article_slug: str,
        comment_content: str,
        comment_id: int = None
    ) -> bool:
        site_name = EmailService.get_site_name(db)
        current_year = EmailService.get_current_year()
        
        if comment_id:
            article_url = f"{settings.FRONTEND_URL}/article/{article_slug}#comment-{comment_id}"
        else:
            article_url = f"{settings.FRONTEND_URL}/article/{article_slug}#comments"
        
        text_content = f"""
评论审核通过通知

您好，{recipient_name}！

您在文章「{article_title}」中的评论已通过审核：

评论内容：{comment_content}

查看评论：{article_url}

{site_name}
"""
        
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f5f5f5; color: #333333; padding: 20px; margin: 0; }}
        .container {{ max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 8px; padding: 40px; border: 1px solid #e0e0e0; }}
        .logo {{ font-size: 24px; font-weight: bold; color: #0066cc; margin-bottom: 30px; }}
        .title {{ font-size: 20px; margin-bottom: 20px; color: #10b981; }}
        .success-icon {{ color: #10b981; font-size: 48px; text-align: center; }}
        .comment-box {{ background-color: #f0f7ff; border-radius: 8px; padding: 20px; margin: 20px 0; border-left: 4px solid #10b981; }}
        .button {{ display: inline-block; padding: 12px 32px; background-color: #10b981; color: #ffffff; text-decoration: none; border-radius: 6px; margin: 20px 0; font-weight: 500; }}
        .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #e0e0e0; font-size: 14px; color: #666666; }}
        p {{ line-height: 1.6; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="logo">🚀 {site_name}</div>
        <h1 class="title">✅ 评论审核通过</h1>
        <p class="success-icon">✅</p>
        <p>您好，{recipient_name}！</p>
        <p>您在文章「<strong>{article_title}</strong>」中的评论已通过审核：</p>
        <div class="comment-box">
            <p style="margin: 0; white-space: pre-wrap;">{comment_content}</p>
        </div>
        <a href="{article_url}" class="button">查看评论</a>
        <div class="footer">
            <p>此邮件为系统自动发送，请勿回复。</p>
            <p>© {current_year} {site_name}. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
"""
        
        try:
            return EmailService.send_email(
                db=db,
                to_email=recipient_email,
                subject=f"您的评论已通过审核 - {article_title}",
                html_content=html_content,
                text_content=text_content,
                email_type='comment_approved',
                recipient_name=recipient_name
            )
        except Exception as e:
            logger.error(f"Failed to send comment approved notification: {e}")
            return False

    @staticmethod
    def send_comment_rejected_notification_db(
        db: Session,
        recipient_email: str,
        recipient_name: str,
        article_title: str,
        comment_content: str,
        reason: str = None
    ) -> bool:
        site_name = EmailService.get_site_name(db)
        current_year = EmailService.get_current_year()
        
        reason_section = ""
        if reason:
            reason_section = f"""
        <div style="background-color: #fef2f2; border-radius: 8px; padding: 20px; margin: 20px 0; border-left: 4px solid #ef4444;">
            <p style="margin: 0; color: #666666; font-size: 14px;">拒绝原因：</p>
            <p style="margin: 8px 0 0 0; color: #333333; font-size: 16px; font-weight: 500; white-space: pre-wrap;">{reason}</p>
        </div>
"""
        
        reason_text = f"\n拒绝原因：{reason}" if reason else ""
        
        text_content = f"""
评论审核拒绝通知

您好，{recipient_name}！

您在文章「{article_title}」中的评论未通过审核。

评论内容：{comment_content}{reason_text}

如有疑问，请联系管理员。

{site_name}
"""
        
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f5f5f5; color: #333333; padding: 20px; margin: 0; }}
        .container {{ max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 8px; padding: 40px; border: 1px solid #e0e0e0; }}
        .logo {{ font-size: 24px; font-weight: bold; color: #0066cc; margin-bottom: 30px; }}
        .title {{ font-size: 20px; margin-bottom: 20px; color: #ef4444; }}
        .reject-icon {{ color: #ef4444; font-size: 48px; text-align: center; }}
        .comment-box {{ background-color: #f5f5f5; border-radius: 8px; padding: 20px; margin: 20px 0; border-left: 4px solid #ef4444; }}
        .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #e0e0e0; font-size: 14px; color: #666666; }}
        p {{ line-height: 1.6; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="logo">🚀 {site_name}</div>
        <h1 class="title">❌ 评论审核未通过</h1>
        <p class="reject-icon">❌</p>
        <p>您好，{recipient_name}！</p>
        <p>您在文章「<strong>{article_title}</strong>」中的评论未通过审核：</p>
        <div class="comment-box">
            <p style="margin: 0; white-space: pre-wrap;">{comment_content}</p>
        </div>
        {reason_section}
        <div class="footer">
            <p>如有疑问，请联系管理员。</p>
            <p>此邮件为系统自动发送，请勿回复。</p>
            <p>© {current_year} {site_name}. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
"""
        
        try:
            return EmailService.send_email(
                db=db,
                to_email=recipient_email,
                subject=f"您的评论未通过审核 - {article_title}",
                html_content=html_content,
                text_content=text_content,
                email_type='comment_rejected',
                recipient_name=recipient_name
            )
        except Exception as e:
            logger.error(f"Failed to send comment rejected notification: {e}")
            return False

    @staticmethod
    def send_pending_comment_notification_db(
        db: Session,
        commenter_name: str,
        article_title: str,
        article_slug: str,
        comment_content: str,
        comment_id: int = None
    ) -> bool:
        site_name = EmailService.get_site_name(db)
        current_year = EmailService.get_current_year()
        
        if comment_id:
            article_url = f"{settings.FRONTEND_URL}/article/{article_slug}#comment-{comment_id}"
        else:
            article_url = f"{settings.FRONTEND_URL}/article/{article_slug}#comments"
        admin_url = f"{settings.FRONTEND_URL}/admin/comments"
        
        text_content = f"""
待审核评论通知

文章：{article_title}
评论者：{commenter_name}
评论内容：{comment_content}

查看评论：{article_url}
管理后台审核：{admin_url}

{site_name}
"""
        
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f5f5f5; color: #333333; padding: 20px; margin: 0; }}
        .container {{ max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 8px; padding: 40px; border: 1px solid #e0e0e0; }}
        .logo {{ font-size: 24px; font-weight: bold; color: #0066cc; margin-bottom: 30px; }}
        .title {{ font-size: 20px; margin-bottom: 20px; color: #f59e0b; }}
        .warning-icon {{ color: #f59e0b; font-size: 48px; text-align: center; }}
        .info-box {{ background-color: #fffbeb; border-radius: 8px; padding: 20px; margin: 20px 0; }}
        .comment-box {{ background-color: #f5f5f5; border-radius: 8px; padding: 20px; margin: 20px 0; border-left: 4px solid #f59e0b; }}
        .info-item {{ margin: 10px 0; }}
        .label {{ color: #666666; font-size: 14px; }}
        .value {{ color: #333333; font-size: 16px; font-weight: 500; }}
        .button {{ display: inline-block; padding: 12px 32px; background-color: #f59e0b; color: #ffffff; text-decoration: none; border-radius: 6px; margin: 20px 0; font-weight: 500; }}
        .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #e0e0e0; font-size: 14px; color: #666666; }}
        p {{ line-height: 1.6; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="logo">🚀 {site_name}</div>
        <h1 class="title">⏳ 新评论待审核</h1>
        <p class="warning-icon">⏳</p>
        <p>有一新评论等待审核：</p>
        <div class="info-box">
            <div class="info-item">
                <span class="label">文章：</span>
                <span class="value">{article_title}</span>
            </div>
            <div class="info-item">
                <span class="label">评论者：</span>
                <span class="value">{commenter_name}</span>
            </div>
        </div>
        <div class="comment-box">
            <p style="margin: 0; white-space: pre-wrap;">{comment_content}</p>
        </div>
        <div style="margin: 20px 0;">
            <a href="{article_url}" class="button" style="margin-right: 10px;">查看评论</a>
            <a href="{admin_url}" class="button" style="background-color: #10b981;">前往审核</a>
        </div>
        <div class="footer">
            <p>此邮件为系统自动发送，请勿回复。</p>
            <p>© {current_year} {site_name}. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
"""
        
        return EmailService.send_admin_notification_db(
            db=db,
            subject=f"待审核评论 - {article_title}",
            html_content=html_content,
            text_content=text_content,
            notification_type="pending_comment"
        )
    
    @staticmethod
    def send_password_reset_email_db(
        db: Session,
        email: str,
        username: str,
        code: str
    ) -> bool:
        site_name = EmailService.get_site_name(db)
        current_year = EmailService.get_current_year()
        
        text_content = f"""
您好 {username}，

您正在重置 {site_name} 账户的密码。

您的验证码是：{code}

验证码将在15分钟后过期。

如果您没有请求重置密码，请忽略此邮件。

祝好，
{site_name} 团队
"""
        
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f5f5f5; color: #333333; padding: 20px; margin: 0; }}
        .container {{ max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 8px; padding: 40px; border: 1px solid #e0e0e0; }}
        .logo {{ font-size: 24px; font-weight: bold; color: #0066cc; margin-bottom: 30px; }}
        .title {{ font-size: 20px; margin-bottom: 20px; color: #333333; }}
        .code-box {{ background-color: #f0f7ff; border-radius: 8px; padding: 30px; margin: 20px 0; text-align: center; }}
        .code {{ font-size: 32px; font-weight: bold; color: #0066cc; letter-spacing: 8px; }}
        .warning {{ background-color: #fff3cd; border-radius: 8px; padding: 15px; margin: 20px 0; color: #856404; }}
        .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #e0e0e0; font-size: 14px; color: #666666; }}
        p {{ line-height: 1.6; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="logo">🚀 {site_name}</div>
        <h1 class="title">密码重置验证码</h1>
        <p>您好 <strong>{username}</strong>，</p>
        <p>您正在重置 {site_name} 账户的密码。请使用以下验证码完成密码重置：</p>
        <div class="code-box">
            <span class="code">{code}</span>
        </div>
        <div class="warning">
            <p>⚠️ 验证码将在 <strong>15分钟</strong> 后过期，请尽快使用。</p>
        </div>
        <p>如果您没有请求重置密码，请忽略此邮件，您的账户仍然是安全的。</p>
        <div class="footer">
            <p>此邮件为系统自动发送，请勿回复。</p>
            <p>© {current_year} {site_name}. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
"""
        
        return EmailService.send_email(
            db=db,
            to_email=email,
            subject=f"密码重置验证码 - {site_name}",
            html_content=html_content,
            text_content=text_content,
            email_type='password_reset',
            recipient_name=username
        )
    
    @staticmethod
    def send_email_change_verification_email_db(
        db: Session,
        email: str,
        username: str,
        code: str,
        user_id: int = None
    ) -> bool:
        site_name = EmailService.get_site_name(db)
        current_year = EmailService.get_current_year()
        
        text_content = f"""
您好 {username}，

您正在更改 {site_name} 账户的邮箱地址。

您的验证码是：{code}

验证码将在10分钟后过期。

如果您没有请求更改邮箱，请忽略此邮件。

祝好，
{site_name} 团队
"""
        
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f5f5f5; color: #333333; padding: 20px; margin: 0; }}
        .container {{ max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 8px; padding: 40px; border: 1px solid #e0e0e0; }}
        .logo {{ font-size: 24px; font-weight: bold; color: #0066cc; margin-bottom: 30px; }}
        .title {{ font-size: 20px; margin-bottom: 20px; color: #333333; }}
        .code-box {{ background-color: #f0f7ff; border-radius: 8px; padding: 30px; margin: 20px 0; text-align: center; }}
        .code {{ font-size: 32px; font-weight: bold; color: #0066cc; letter-spacing: 8px; }}
        .warning {{ background-color: #fff3cd; border-radius: 8px; padding: 15px; margin: 20px 0; color: #856404; }}
        .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #e0e0e0; font-size: 14px; color: #666666; }}
        p {{ line-height: 1.6; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="logo">🚀 {site_name}</div>
        <h1 class="title">邮箱更改验证码</h1>
        <p>您好 <strong>{username}</strong>，</p>
        <p>您正在更改 {site_name} 账户的邮箱地址。请使用以下验证码完成邮箱更改：</p>
        <div class="code-box">
            <span class="code">{code}</span>
        </div>
        <div class="warning">
            <p>⚠️ 验证码将在 <strong>10分钟</strong> 后过期，请尽快使用。</p>
        </div>
        <p>如果您没有请求更改邮箱，请忽略此邮件，您的账户仍然是安全的。</p>
        <div class="footer">
            <p>此邮件为系统自动发送，请勿回复。</p>
            <p>© {current_year} {site_name}. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
"""
        
        return EmailService.send_email(
            db=db,
            to_email=email,
            subject=f"邮箱更改验证码 - {site_name}",
            html_content=html_content,
            text_content=text_content,
            email_type='email_change',
            recipient_name=username,
            user_id=user_id
        )
    
    @staticmethod
    def store_oauth_temp_token(
        db: Session,
        temp_token: str,
        user_id: int,
        provider_name: str,
        provider_user_id: str
    ) -> str:
        from app.models import OAuthTempToken
        from app.utils.timezone import get_db_now
        
        existing_token = db.query(OAuthTempToken).filter(
            OAuthTempToken.user_id == user_id,
            OAuthTempToken.expires_at > get_db_now()
        ).first()
        
        if existing_token:
            return existing_token.temp_token
        
        temp_token_record = OAuthTempToken(
            temp_token=temp_token,
            user_id=user_id,
            provider_name=provider_name,
            provider_user_id=provider_user_id,
            expires_at=get_db_now() + timedelta(hours=24)
        )
        db.add(temp_token_record)
        db.commit()
        
        return temp_token
    
    @staticmethod
    def get_oauth_temp_token(db: Session, temp_token: str) -> Optional['OAuthTempToken']:
        from app.models import OAuthTempToken
        from app.utils.timezone import get_db_now
        
        record = db.query(OAuthTempToken).filter(
            OAuthTempToken.temp_token == temp_token,
            OAuthTempToken.expires_at > get_db_now()
        ).first()
        return record
    
    @staticmethod
    def delete_oauth_temp_token(db: Session, temp_token: str) -> None:
        from app.models import OAuthTempToken
        db.query(OAuthTempToken).filter(OAuthTempToken.temp_token == temp_token).delete()
        db.commit()
    
    @staticmethod
    def send_oauth_email_verification(
        db: Session,
        email: str,
        username: str,
        temp_token: str,
        provider_name: str
    ) -> bool:
        from app.utils.timezone import get_now
        
        site_name = EmailService.get_site_name(db)
        current_year = EmailService.get_current_year()
        
        verification_url = f"{settings.FRONTEND_URL}/oauth/verify-email?token={temp_token}&email={email}"
        
        provider_display = {
            'github': 'GitHub',
            'google': 'Google',
            'twitter': 'Twitter',
            'x': 'X',
            'wechat': '微信',
            'qq': 'QQ'
        }.get(provider_name, provider_name)
        
        text_content = f"""
您好 {username}，

您正在使用 {provider_display} 登录 {site_name}。

请点击以下链接验证您的邮箱地址：
{verification_url}

此链接将在24小时后过期。

如果您没有进行此操作，请忽略此邮件。

祝好，
{site_name} 团队
"""
        
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f5f5f5; color: #333333; padding: 20px; margin: 0; }}
        .container {{ max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 8px; padding: 40px; border: 1px solid #e0e0e0; }}
        .logo {{ font-size: 24px; font-weight: bold; color: #0066cc; margin-bottom: 30px; }}
        .title {{ font-size: 20px; margin-bottom: 20px; color: #333333; }}
        .button {{ display: inline-block; padding: 12px 32px; background-color: #0066cc; color: #ffffff; text-decoration: none; border-radius: 6px; margin: 20px 0; font-weight: 500; }}
        .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #e0e0e0; font-size: 14px; color: #666666; }}
        .link {{ word-break: break-all; color: #0066cc; }}
        p {{ line-height: 1.6; }}
        .provider {{ color: #0066cc; font-weight: 500; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="logo">🚀 {site_name}</div>
        <h1 class="title">验证您的邮箱地址</h1>
        <p>您好 <strong>{username}</strong>，</p>
        <p>您正在使用 <span class="provider">{provider_display}</span> 登录 {site_name}。</p>
        <p>请点击下方按钮验证您的邮箱地址：</p>
        <a href="{verification_url}" class="button">验证邮箱</a>
        <p>或复制以下链接到浏览器：</p>
        <p class="link">{verification_url}</p>
        <p>此链接将在 <strong>24小时</strong> 后过期。</p>
        <div class="footer">
            <p>如果您没有进行此操作，请忽略此邮件。</p>
            <p>© {current_year} {site_name}. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
"""
        
        return EmailService.send_email(
            db=db,
            to_email=email,
            subject=f"验证您的邮箱 - {site_name}",
            html_content=html_content,
            text_content=text_content,
            email_type='oauth_verification',
            recipient_name=username
        )

    @staticmethod
    def send_error_log_notification_db(
        db: Session,
        error_logs: list
    ) -> bool:
        """
        发送错误日志通知邮件给管理员
        
        Args:
            db: 数据库会话
            error_logs: 错误日志列表，每个元素包含:
                - level: 日志级别 (WARNING/ERROR/CRITICAL)
                - logger: 日志记录器名称
                - message: 错误消息
                - file: 文件路径
                - line: 行号
                - function: 函数名
                - time: 时间戳
        
        Returns:
            bool: 是否发送成功
        """
        from app.models import User
        from app.services.permission_service import PermissionService
        
        site_name = EmailService.get_site_name(db)
        current_year = EmailService.get_current_year()
        
        admin_users = PermissionService.get_admin_users(db)
        
        if not admin_users:
            logger.warning("No admin users found to notify about errors")
            return False
        
        error_count = len(error_logs)
        warning_count = sum(1 for log in error_logs if log.get('level') == 'WARNING')
        critical_count = sum(1 for log in error_logs if log.get('level') == 'CRITICAL')
        actual_error_count = error_count - warning_count
        
        level_emoji = {
            'WARNING': '⚠️',
            'ERROR': '❌',
            'CRITICAL': '🚨'
        }
        
        logs_html = ""
        for i, log in enumerate(error_logs[:10], 1):
            emoji = level_emoji.get(log.get('level', 'ERROR'), '❌')
            level_color = 'orange' if log.get('level') == 'WARNING' else 'red'
            
            logs_html += f"""
            <div class="error-item">
                <div class="error-header">
                    <span class="error-level" style="background-color: {level_color};">{emoji} {log.get('level')}</span>
                    <span class="error-time">{datetime.fromtimestamp(log.get('time', 0)).strftime('%Y-%m-%d %H:%M:%S')}</span>
                </div>
                <div class="error-logger">Logger: {log.get('logger', 'unknown')}</div>
                <div class="error-message">{log.get('message', '')}</div>
                <div class="error-location">
                    <span>📁 {log.get('file', 'unknown')}:{log.get('line', 0)}</span>
                    <span>🔧 {log.get('function', 'unknown')}()</span>
                </div>
            </div>
            """
        
        if error_count > 10:
            logs_html += f"""
            <div class="more-errors">
                <p>... 还有 {error_count - 10} 条错误未显示</p>
            </div>
            """
        
        text_content = f"""
错误日志通知

网站: {site_name}
错误总数: {error_count}
- 警告: {warning_count}
- 错误: {actual_error_count}
- 严重错误: {critical_count}

请登录管理后台查看详情。

{site_name}
"""
        
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f5f5f5; color: #333333; padding: 20px; margin: 0; }}
        .container {{ max-width: 700px; margin: 0 auto; background-color: #ffffff; border-radius: 8px; padding: 40px; border: 1px solid #e0e0e0; }}
        .logo {{ font-size: 24px; font-weight: bold; color: #dc2626; margin-bottom: 30px; }}
        .title {{ font-size: 20px; margin-bottom: 20px; color: #dc2626; }}
        .stats {{ display: flex; gap: 20px; margin: 20px 0; flex-wrap: wrap; }}
        .stat-box {{ flex: 1; min-width: 120px; background-color: #fef2f2; border-radius: 8px; padding: 15px; text-align: center; border: 1px solid #fecaca; }}
        .stat-number {{ font-size: 28px; font-weight: bold; color: #dc2626; }}
        .stat-label {{ font-size: 14px; color: #666666; margin-top: 5px; }}
        .error-item {{ background-color: #fafafa; border-radius: 8px; padding: 15px; margin: 15px 0; border-left: 4px solid #dc2626; }}
        .error-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; flex-wrap: wrap; gap: 10px; }}
        .error-level {{ color: white; padding: 4px 12px; border-radius: 4px; font-size: 12px; font-weight: bold; }}
        .error-time {{ color: #666666; font-size: 12px; }}
        .error-logger {{ color: #6b7280; font-size: 13px; margin-bottom: 8px; font-family: monospace; }}
        .error-message {{ background-color: #1f2937; color: #f9fafb; padding: 12px; border-radius: 6px; font-family: monospace; font-size: 13px; white-space: pre-wrap; word-break: break-all; overflow-x: auto; }}
        .error-location {{ margin-top: 10px; font-size: 12px; color: #6b7280; display: flex; gap: 15px; flex-wrap: wrap; }}
        .more-errors {{ text-align: center; padding: 15px; color: #6b7280; font-style: italic; }}
        .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #e0e0e0; font-size: 14px; color: #666666; }}
        p {{ line-height: 1.6; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="logo">🚨 {site_name} - 错误日志通知</div>
        <h1 class="title">检测到 {error_count} 条错误日志</h1>
        
        <div class="stats">
            <div class="stat-box">
                <div class="stat-number">{error_count}</div>
                <div class="stat-label">总计</div>
            </div>
            <div class="stat-box">
                <div class="stat-number" style="color: #f59e0b;">{warning_count}</div>
                <div class="stat-label">警告</div>
            </div>
            <div class="stat-box">
                <div class="stat-number" style="color: #dc2626;">{actual_error_count}</div>
                <div class="stat-label">错误</div>
            </div>
            <div class="stat-box">
                <div class="stat-number" style="color: #7f1d1d;">{critical_count}</div>
                <div class="stat-label">严重</div>
            </div>
        </div>
        
        <h2 style="color: #333; margin-top: 30px;">错误详情</h2>
        {logs_html}
        
        <div class="footer">
            <p>此邮件为系统自动发送，请勿回复。</p>
            <p>建议及时检查并修复相关错误。</p>
            <p>© {current_year} {site_name}. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
"""
        
        success = True
        for admin in admin_users:
            result = EmailService.send_email(
                db=db,
                to_email=admin.email,
                subject=f"🚨 [{site_name}] 错误日志通知 ({error_count}条)",
                html_content=html_content,
                text_content=text_content,
                email_type='error_log',
                recipient_name=admin.username,
                user_id=admin.id
            )
            if not result:
                success = False
        
        return success
