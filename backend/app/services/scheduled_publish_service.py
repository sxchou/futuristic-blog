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
        self._checker_running = False
        self._checker_task = None
        self._nearest_scheduled_time: datetime | None = None  # 内存中记录最近的定时时间
    
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
    
    def _get_nearest_scheduled_time(self, db: Session) -> datetime | None:
        """获取最近的定时文章发布时间"""
        now = get_db_now()
        nearest = db.query(Article).filter(
            Article.is_published == False,
            Article.published_at != None,
            Article.published_at > now
        ).order_by(Article.published_at.asc()).first()
        
        return nearest.published_at if nearest else None
    
    def _should_start_publish_service(self, db: Session) -> bool:
        """判断是否需要启动发布服务（最近时间距离当前时间 <= 5分钟）"""
        nearest_time = self._get_nearest_scheduled_time(db)
        if not nearest_time:
            return False
        
        now = get_db_now()
        time_diff = (nearest_time - now).total_seconds()
        
        # 如果最近时间距离当前时间 <= 5分钟，启动发布服务
        return time_diff <= 300  # 5分钟 = 300秒
    
    def update_nearest_time(self, db: Session):
        """更新内存中的最近定时时间"""
        nearest_time = self._get_nearest_scheduled_time(db)
        self._nearest_scheduled_time = nearest_time
        if nearest_time:
            logger.info(f"Updated nearest scheduled time to {nearest_time}")
        else:
            logger.info("No scheduled articles found, cleared nearest scheduled time")
    
    async def start_if_needed(self):
        """智能启动：根据最近时间判断是否启动服务"""
        if self._running:
            return
        
        # 如果检查服务在运行，先停止它
        if self._checker_running:
            await self._stop_checker()
        
        db: Session = SessionLocal()
        try:
            has_scheduled = self._has_scheduled_articles(db)
            if not has_scheduled:
                self._nearest_scheduled_time = None
                return
            
            # 更新内存中的最近定时时间
            self.update_nearest_time(db)
            
            if self._should_start_publish_service(db):
                await self.start()
                logger.info("Started publish service due to upcoming scheduled article within 5 minutes")
            else:
                # 启动轻量级检查服务
                await self._start_checker()
                logger.info("Started checker service to monitor scheduled articles")
        finally:
            db.close()
    
    async def _start_checker(self):
        """启动轻量级检查服务"""
        if self._checker_running:
            return
        
        self._checker_running = True
        self._checker_task = asyncio.create_task(self._run_checker())
        logger.info("Checker service started")
    
    async def _stop_checker(self):
        """停止轻量级检查服务"""
        if not self._checker_running:
            return
        
        self._checker_running = False
        if self._checker_task:
            self._checker_task.cancel()
            try:
                await self._checker_task
            except asyncio.CancelledError:
                pass
        logger.info("Checker service stopped")
    
    async def _run_checker(self):
        """轻量级检查服务，使用内存中的时间计算等待时间，不查询数据库"""
        while self._checker_running:
            try:
                # 如果没有最近的定时时间，停止检查服务
                if not self._nearest_scheduled_time:
                    logger.info("No nearest scheduled time in memory, stopping checker service")
                    self._checker_running = False
                    break
                
                now = get_db_now()
                time_diff = (self._nearest_scheduled_time - now).total_seconds()
                
                # 如果最近时间距离当前时间 <= 5分钟，启动发布服务
                if time_diff <= 300:
                    logger.info("Nearest scheduled article within 5 minutes, starting publish service")
                    self._checker_running = False
                    await self.start()
                    break
                
                # 计算需要等待的时间
                # 策略：等待到距离发布时间5分钟时启动发布服务
                # time_diff > 300，所以 wait_time = time_diff - 300
                wait_time = time_diff - 300
                
                # 最多等待5分钟（避免等待时间过长）
                wait_time = min(wait_time, 300)
                
                if wait_time > 0:
                    logger.info(f"Waiting {wait_time:.0f} seconds before starting publish service (time_diff: {time_diff:.0f}s)")
                    await asyncio.sleep(wait_time)
                else:
                    # 如果计算的时间已经过了，立即启动发布服务
                    await asyncio.sleep(1)
                    
            except Exception as e:
                logger.error(f"Error in checker service: {e}", exc_info=True)
                await asyncio.sleep(300)
    
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
                        self._nearest_scheduled_time = None
                        self._running = False
                        break
                    
                    # 更新内存中的最近定时时间
                    self.update_nearest_time(db)
                    
                    # 检查是否还有即将到期的文章（5分钟内）
                    if not self._should_start_publish_service(db):
                        logger.info("No upcoming articles within 5 minutes, switching to checker mode")
                        self._running = False
                        await self._start_checker()
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
