import smtplib
import httpx
import json
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
import secrets
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from app.core.config import settings
from app.models import EmailConfig, EmailLog, SiteConfig
from app.utils.timezone import get_now


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
        return datetime.now().year
    
    @staticmethod
    def generate_verification_token() -> str:
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def get_token_expiry() -> datetime:
        return get_now() + timedelta(hours=24)
    
    @staticmethod
    def get_active_config(db: Session) -> Optional[EmailConfig]:
        return db.query(EmailConfig).filter(EmailConfig.is_active == True).first()
    
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
        
        with httpx.Client(timeout=30.0) as client:
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
        smtp_user = config.smtp_user if config else settings.SMTP_USER
        smtp_password = config.smtp_password if config else settings.SMTP_PASSWORD
        from_email = config.from_email if config else settings.SMTP_FROM_EMAIL
        from_name = config.from_name if config else settings.SMTP_FROM_NAME
        
        if not all([smtp_host, smtp_user, smtp_password]):
            raise ValueError("SMTP configuration is incomplete")
        
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f"{from_name} <{from_email}>"
        msg['To'] = to_email
        
        if text_content:
            part1 = MIMEText(text_content, 'plain', 'utf-8')
            msg.attach(part1)
        
        part2 = MIMEText(html_content, 'html', 'utf-8')
        msg.attach(part2)
        
        logger.info(f"Sending email via SMTP to {to_email}")
        
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.sendmail(from_email, to_email, msg.as_string())
        
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
                log.sent_at = get_now()
                log.error_message = f"Provider: {provider_used}"
                logger.info(f"Email sent successfully via {provider_used} to {to_email}")
                return True
            else:
                raise Exception("Failed to send email")
                
        except Exception as e:
            log.status = 'failed'
            log.error_message = str(e)
            logger.error(f"Failed to send email to {to_email}: {e}")
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
        from app.models import User
        admin_users = db.query(User).filter(User.is_admin == True).all()
        
        if not admin_users:
            logger.warning("No admin users found to notify")
            return False
        
        success = True
        for admin in admin_users:
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
        comment_content: str
    ) -> bool:
        site_name = EmailService.get_site_name(db)
        current_year = EmailService.get_current_year()
        
        article_url = f"{settings.FRONTEND_URL}/article/{article_slug}#comments"
        
        truncated_content = comment_content[:200] + "..." if len(comment_content) > 200 else comment_content
        
        text_content = f"""
新评论通知

文章: {article_title}
评论者: {commenter_name}

评论内容:
{truncated_content}

查看完整上下文: {article_url}

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
        <p>您的文章收到了一条新评论：</p>
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
        <a href="{article_url}" class="button">查看完整上下文</a>
        <p>或复制以下链接到浏览器：</p>
        <p class="link">{article_url}</p>
        <p>请登录管理后台查看详情并进行审核。</p>
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
            subject=f"新评论 - {article_title}",
            html_content=html_content,
            text_content=text_content,
            notification_type="new_comment"
        )
    
    @staticmethod
    def send_new_like_notification_db(
        db: Session,
        liker_name: str,
        article_title: str,
        article_slug: str
    ) -> bool:
        site_name = EmailService.get_site_name(db)
        current_year = EmailService.get_current_year()
        
        article_url = f"{settings.FRONTEND_URL}/article/{article_slug}"
        
        text_content = f"""
新点赞通知

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
        <p>您的文章收到了一个新的点赞：</p>
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
        
        return EmailService.send_admin_notification_db(
            db=db,
            subject=f"新点赞 - {article_title}",
            html_content=html_content,
            text_content=text_content,
            notification_type="new_like"
        )
    
    @staticmethod
    def test_email_provider(
        db: Session,
        provider: str = None,
        test_email: str = None
    ) -> Dict[str, Any]:
        provider = provider or EmailService.get_email_provider(db)
        test_email = test_email or settings.ADMIN_EMAIL
        
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
