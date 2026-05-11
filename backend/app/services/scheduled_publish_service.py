import asyncio
import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models import Article, User
from app.services.baidu_push_service import baidu_push_service
from app.services.email_service import EmailService
from app.utils.timezone import get_db_now, get_now

logger = logging.getLogger(__name__)


class ScheduledPublishService:
    def __init__(self):
        self._running = False
        self._task = None
    
    async def start(self):
        if self._running:
            logger.warning("Scheduled publish service is already running")
            return
        
        self._running = True
        self._task = asyncio.create_task(self._run_scheduler())
        logger.info("Scheduled publish service started")
    
    async def stop(self):
        if not self._running:
            return
        
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Scheduled publish service stopped")
    
    def _has_scheduled_articles(self, db: Session) -> bool:
        """检查是否有待发布的定时文章"""
        now = get_db_now()
        count = db.query(Article).filter(
            Article.is_published == False,
            Article.published_at != None,
            Article.published_at > now
        ).count()
        return count > 0
    
    async def start_if_needed(self):
        """智能启动：只有在有待发布文章时才启动服务"""
        if self._running:
            return
        
        db: Session = SessionLocal()
        try:
            has_scheduled = self._has_scheduled_articles(db)
            if has_scheduled:
                await self.start()
                logger.info("Started scheduled publish service due to pending articles")
        finally:
            db.close()
    
    def _has_upcoming_articles(self, db: Session) -> bool:
        now = get_db_now()
        one_minute_later = now + timedelta(minutes=1)
        
        count = db.query(Article).filter(
            Article.is_published == False,
            Article.published_at != None,
            Article.published_at > now,
            Article.published_at <= one_minute_later
        ).count()
        
        return count > 0
    
    async def _run_scheduler(self):
        while self._running:
            try:
                await self._check_and_publish_scheduled_articles()
                
                db: Session = SessionLocal()
                try:
                    has_scheduled = self._has_scheduled_articles(db)
                    
                    if not has_scheduled:
                        logger.info("No more scheduled articles, stopping service to save resources")
                        self._running = False
                        break
                    
                    has_upcoming = self._has_upcoming_articles(db)
                finally:
                    db.close()
                
                if has_upcoming:
                    await asyncio.sleep(1)
                else:
                    await asyncio.sleep(60)
                    
            except Exception as e:
                logger.error(f"Error in scheduled publish service: {e}", exc_info=True)
                await asyncio.sleep(60)
    
    def _send_publish_notification(self, db: Session, article: Article, author: User):
        try:
            if not author.email:
                logger.warning(f"Author {author.username} has no email, skipping notification")
                return
            
            site_name = EmailService.get_site_name(db)
            current_year = EmailService.get_current_year()
            publish_time = get_now().strftime("%Y-%m-%d %H:%M:%S")
            
            subject = f"文章发布成功 - {article.title}"
            
            text_content = f"""
文章发布成功通知

您的文章已成功发布！

文章标题: {article.title}
发布时间: {publish_time}

您可以点击以下链接查看文章:
{EmailService.get_site_name(db)}/article/{article.slug}

感谢您的创作！

{site_name}
"""
            
            html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
        .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
        .article-info {{ background: white; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #667eea; }}
        .button {{ display: inline-block; padding: 12px 24px; background: #667eea; color: white; text-decoration: none; border-radius: 5px; margin-top: 20px; }}
        .footer {{ text-align: center; margin-top: 30px; color: #666; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎉 文章发布成功</h1>
        </div>
        <div class="content">
            <p>尊敬的 <strong>{author.username}</strong>，</p>
            <p>您的定时文章已成功发布！</p>
            
            <div class="article-info">
                <h3 style="margin-top: 0;">📝 文章信息</h3>
                <p><strong>标题：</strong>{article.title}</p>
                <p><strong>发布时间：</strong>{publish_time}</p>
            </div>
            
            <a href="{site_name}/article/{article.slug}" class="button">查看文章</a>
        </div>
        <div class="footer">
            <p>此邮件为系统自动发送，请勿回复。</p>
            <p>© {current_year} {site_name}. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
"""
            
            EmailService.send_email(
                db=db,
                to_email=author.email,
                subject=subject,
                html_content=html_content,
                text_content=text_content,
                email_type="article_published",
                recipient_name=author.username,
                user_id=author.id
            )
            
            logger.info(f"Publish notification sent to {author.email} for article {article.title}")
            
        except Exception as e:
            logger.error(f"Failed to send publish notification: {e}", exc_info=True)
    
    async def _check_and_publish_scheduled_articles(self):
        db: Session = SessionLocal()
        try:
            now = get_db_now()
            
            scheduled_articles = db.query(Article).filter(
                Article.is_published == False,
                Article.published_at != None,
                Article.published_at <= now
            ).all()
            
            if not scheduled_articles:
                return
            
            logger.info(f"Found {len(scheduled_articles)} scheduled articles to publish")
            
            for article in scheduled_articles:
                try:
                    article.is_published = True
                    db.commit()
                    
                    logger.info(f"Published scheduled article: {article.title} (ID: {article.id})")
                    
                    if baidu_push_service.enabled:
                        asyncio.create_task(baidu_push_service.push_article(article.slug))
                    
                    if article.author_id:
                        author = db.query(User).filter(User.id == article.author_id).first()
                        if author:
                            self._send_publish_notification(db, article, author)
                    
                except Exception as e:
                    logger.error(f"Failed to publish scheduled article {article.id}: {e}", exc_info=True)
                    db.rollback()
                    
        except Exception as e:
            logger.error(f"Error checking scheduled articles: {e}", exc_info=True)
        finally:
            db.close()


scheduled_publish_service = ScheduledPublishService()
