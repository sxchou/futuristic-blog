import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
import secrets
from typing import Optional
from sqlalchemy.orm import Session
from app.core.config import settings
from app.models import EmailConfig, EmailLog, SiteConfig
from app.utils.timezone import get_now


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
        'port': 465,
        'use_ssl': True
    },
    'outlook': {
        'host': 'smtp-mail.outlook.com',
        'port': 587
    }
}


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
        return settings.is_email_configured
    
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
        
        if not config:
            if settings.is_email_configured:
                return EmailService._send_with_env_settings(
                    db=db,
                    to_email=to_email,
                    subject=subject,
                    html_content=html_content,
                    text_content=text_content,
                    email_type=email_type,
                    recipient_name=recipient_name,
                    user_id=user_id,
                    verification_token=verification_token
                )
            else:
                print(f"[DEV MODE] No email config, skipping email to: {to_email}")
                print(f"[DEV MODE] Subject: {subject}")
                if verification_token:
                    print(f"[DEV MODE] Verification URL: {settings.FRONTEND_URL}/verify-email?token={verification_token}")
                return True
        
        return EmailService._send_with_db_config(
            db=db,
            config=config,
            to_email=to_email,
            subject=subject,
            html_content=html_content,
            text_content=text_content,
            email_type=email_type,
            recipient_name=recipient_name,
            user_id=user_id,
            verification_token=verification_token
        )
    
    @staticmethod
    def _send_with_env_settings(
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
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL}>"
            msg['To'] = to_email
            
            if text_content:
                part1 = MIMEText(text_content, 'plain', 'utf-8')
                msg.attach(part1)
            
            part2 = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(part2)
            
            port = settings.SMTP_PORT
            if port == 465:
                server = smtplib.SMTP_SSL(settings.SMTP_HOST, port, timeout=10)
            else:
                server = smtplib.SMTP(settings.SMTP_HOST, port, timeout=10)
                server.starttls()
            
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.sendmail(settings.SMTP_FROM_EMAIL, to_email, msg.as_string())
            server.quit()
            
            log.status = 'sent'
            log.sent_at = get_now()
            return True
            
        except Exception as e:
            log.status = 'failed'
            log.error_message = str(e)
            print(f"Failed to send email: {e}")
            return False
        finally:
            db.add(log)
            db.commit()
    
    @staticmethod
    def _send_with_db_config(
        db: Session,
        config: EmailConfig,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: str = None,
        email_type: str = "verification",
        recipient_name: str = None,
        user_id: int = None,
        verification_token: str = None
    ) -> bool:
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
            provider_config = EMAIL_PROVIDERS.get(config.provider, {})
            
            host = provider_config.get('host', config.smtp_host or settings.SMTP_HOST)
            default_port = provider_config.get('port', 587)
            use_ssl = provider_config.get('use_ssl', False)
            
            port = config.smtp_port or default_port
            
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{config.from_name} <{config.from_email}>"
            msg['To'] = to_email
            
            if text_content:
                part1 = MIMEText(text_content, 'plain', 'utf-8')
                msg.attach(part1)
            
            part2 = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(part2)
            
            if use_ssl or port == 465:
                server = smtplib.SMTP_SSL(host, port, timeout=10)
            else:
                server = smtplib.SMTP(host, port, timeout=10)
                server.starttls()
            
            server.login(config.smtp_user, config.smtp_password)
            server.sendmail(config.from_email, to_email, msg.as_string())
            server.quit()
            
            log.status = 'sent'
            log.sent_at = get_now()
            return True
            
        except Exception as e:
            log.status = 'failed'
            log.error_message = str(e)
            print(f"Failed to send email: {e}")
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
