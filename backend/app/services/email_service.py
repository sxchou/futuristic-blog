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
        return config is not None
    
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
            if not settings.is_email_configured:
                print(f"[DEV MODE] No email config in database, using env settings")
                print(f"[DEV MODE] Email to: {to_email}")
                print(f"[DEV MODE] Subject: {subject}")
                if verification_token:
                    print(f"[DEV MODE] Verification URL: {settings.FRONTEND_URL}/verify-email?token={verification_token}")
                return True
            return False
        
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
            provider_config = EMAIL_PROVIDERS.get(config.provider)
            if not provider_config:
                raise ValueError(f"Unknown email provider: {config.provider}")
            
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{config.from_name} <{config.from_email}>"
            msg['To'] = to_email
            
            if text_content:
                part1 = MIMEText(text_content, 'plain', 'utf-8')
                msg.attach(part1)
            
            part2 = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(part2)
            
            with smtplib.SMTP(provider_config['host'], provider_config['port']) as server:
                server.starttls()
                server.login(config.smtp_user, config.smtp_password)
                server.sendmail(config.from_email, to_email, msg.as_string())
            
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
        config = EmailService.get_active_config(db)
        site_name = EmailService.get_site_name(db)
        current_year = EmailService.get_current_year()
        
        if not config:
            print(f"[DEV MODE] Verification token for {email}: {token}")
            print(f"[DEV MODE] Verification URL: {settings.FRONTEND_URL}/verify-email?token={token}")
            
            log = EmailLog(
                email_type='verification',
                recipient_email=email,
                recipient_name=username,
                subject=f"验证您的邮箱 - {site_name}",
                status='pending',
                verification_token=token,
                user_id=user_id
            )
            db.add(log)
            db.commit()
            return True
        
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
            subject=f"验证您的邮箱 - {config.from_name}",
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
        
        if not settings.is_email_configured:
            print(f"[DEV MODE] Verification token for {email}: {token}")
            print(f"[DEV MODE] Verification URL: {settings.FRONTEND_URL}/verify-email?token={token}")
            return True
        
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"验证您的邮箱 - {site_name}"
            msg['From'] = f"{site_name} <{settings.SMTP_FROM_EMAIL}>"
            msg['To'] = email
            
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
            
            part1 = MIMEText(text_content, 'plain', 'utf-8')
            part2 = MIMEText(html_content, 'html', 'utf-8')
            
            msg.attach(part1)
            msg.attach(part2)
            
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                server.starttls()
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.sendmail(settings.SMTP_FROM_EMAIL, email, msg.as_string())
            
            return True
        except Exception as e:
            print(f"Failed to send email: {e}")
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
            print("No admin users found to notify")
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
        <a href="{article_url}" class="button">查看完整上下文</a>
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
        
        return EmailService.send_admin_notification_db(
            db=db,
            subject=f"新点赞 - {article_title}",
            html_content=html_content,
            text_content=text_content,
            notification_type="new_like"
        )
    
    @staticmethod
    def send_reply_notification_db(
        db: Session,
        recipient_email: str,
        recipient_name: str,
        article_title: str,
        article_slug: str,
        reply_content: str,
        commenter_name: str
    ) -> bool:
        site_name = EmailService.get_site_name(db)
        current_year = EmailService.get_current_year()
        
        article_url = f"{settings.FRONTEND_URL}/article/{article_slug}#comments"
        
        truncated_content = reply_content[:200] + "..." if len(reply_content) > 200 else reply_content
        
        text_content = f"""
您好 {recipient_name}，

您在文章「{article_title}」下的评论收到了新回复：

回复者: {commenter_name}

回复内容:
{truncated_content}

查看完整上下文: {article_url}

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
        .reply-box {{ background-color: #f5f0ff; border-radius: 8px; padding: 20px; margin: 20px 0; border-left: 4px solid #7c3aed; }}
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
        <h1 class="title">您的评论收到了新回复</h1>
        <p>您好 {recipient_name}，</p>
        <p>您在文章「{article_title}」下的评论收到了新回复：</p>
        <div class="info-box">
            <div class="info-item">
                <span class="label">回复者：</span>
                <span class="value">{commenter_name}</span>
            </div>
        </div>
        <div class="reply-box">
            <p class="label">回复内容：</p>
            <p class="value">{truncated_content}</p>
        </div>
        <a href="{article_url}" class="button">查看完整上下文</a>
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
        
        return EmailService.send_email(
            db=db,
            to_email=recipient_email,
            subject=f"您的评论收到了新回复 - {article_title}",
            html_content=html_content,
            text_content=text_content,
            email_type='reply_notification',
            recipient_name=recipient_name
        )

    @staticmethod
    def send_pending_comment_notification_db(
        db: Session,
        commenter_name: str,
        article_title: str,
        article_slug: str,
        comment_content: str
    ) -> bool:
        site_name = EmailService.get_site_name(db)
        current_year = EmailService.get_current_year()
        
        article_url = f"{settings.FRONTEND_URL}/article/{article_slug}#comments"
        admin_url = f"{settings.FRONTEND_URL}/admin/comments?status=pending"
        
        truncated_content = comment_content[:200] + "..." if len(comment_content) > 200 else comment_content
        
        text_content = f"""
待审核评论通知

有新评论待审核：

文章: {article_title}
评论者: {commenter_name}

评论内容:
{truncated_content}

查看文章: {article_url}
审核管理: {admin_url}

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
        .warning-badge {{ display: inline-block; background-color: #fef3c7; color: #92400e; padding: 4px 12px; border-radius: 4px; font-size: 14px; margin-bottom: 20px; }}
        .info-box {{ background-color: #fffbeb; border-radius: 8px; padding: 20px; margin: 20px 0; border-left: 4px solid #f59e0b; }}
        .comment-box {{ background-color: #f5f5f5; border-radius: 8px; padding: 20px; margin: 20px 0; }}
        .info-item {{ margin: 10px 0; }}
        .label {{ color: #666666; font-size: 14px; }}
        .value {{ color: #333333; font-size: 16px; font-weight: 500; }}
        .button {{ display: inline-block; padding: 12px 32px; background-color: #f59e0b; color: #ffffff; text-decoration: none; border-radius: 6px; margin: 10px 10px 10px 0; font-weight: 500; }}
        .button-secondary {{ background-color: #0066cc; }}
        .link {{ word-break: break-all; color: #0066cc; }}
        .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #e0e0e0; font-size: 14px; color: #666666; }}
        p {{ line-height: 1.6; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="logo">🚀 {site_name}</div>
        <h1 class="title">⏳ 待审核评论通知</h1>
        <span class="warning-badge">需要审核</span>
        <p>有新评论提交并等待审核：</p>
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
        <a href="{admin_url}" class="button">前往审核</a>
        <a href="{article_url}" class="button button-secondary">查看文章</a>
        <p>或复制以下链接到浏览器：</p>
        <p class="link">审核管理: {admin_url}</p>
        <p class="link">文章链接: {article_url}</p>
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
            subject=f"[待审核] 新评论 - {article_title}",
            html_content=html_content,
            text_content=text_content,
            notification_type="pending_comment"
        )

    @staticmethod
    def send_comment_approved_notification_db(
        db: Session,
        recipient_email: str,
        recipient_name: str,
        article_title: str,
        article_slug: str,
        comment_content: str
    ) -> bool:
        site_name = EmailService.get_site_name(db)
        current_year = EmailService.get_current_year()
        
        article_url = f"{settings.FRONTEND_URL}/article/{article_slug}#comments"
        
        truncated_content = comment_content[:200] + "..." if len(comment_content) > 200 else comment_content
        
        text_content = f"""
您好 {recipient_name}，

您的评论已通过审核！

文章: {article_title}

您的评论:
{truncated_content}

查看文章: {article_url}

感谢您的参与！

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
        .success-badge {{ display: inline-block; background-color: #d1fae5; color: #065f46; padding: 4px 12px; border-radius: 4px; font-size: 14px; margin-bottom: 20px; }}
        .info-box {{ background-color: #ecfdf5; border-radius: 8px; padding: 20px; margin: 20px 0; border-left: 4px solid #10b981; }}
        .comment-box {{ background-color: #f5f5f5; border-radius: 8px; padding: 20px; margin: 20px 0; }}
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
        <h1 class="title">✅ 评论审核通过</h1>
        <span class="success-badge">已通过</span>
        <p>您好 {recipient_name}，</p>
        <p>您在文章「{article_title}」下的评论已通过审核并已公开显示：</p>
        <div class="info-box">
            <div class="info-item">
                <span class="label">文章：</span>
                <span class="value">{article_title}</span>
            </div>
        </div>
        <div class="comment-box">
            <p class="label">您的评论：</p>
            <p class="value">{truncated_content}</p>
        </div>
        <a href="{article_url}" class="button">查看评论</a>
        <p>或复制以下链接到浏览器：</p>
        <p class="link">{article_url}</p>
        <p>感谢您的参与！</p>
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
            to_email=recipient_email,
            subject=f"您的评论已通过审核 - {article_title}",
            html_content=html_content,
            text_content=text_content,
            email_type='comment_approved',
            recipient_name=recipient_name
        )
