from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.core.database import get_db
from app.models import Article, ArticleLike, User, NotificationSettings
from app.schemas import LikeResponse
from app.utils.auth import get_current_user_optional
from app.services.email_service import EmailService
from typing import Optional

router = APIRouter(prefix="/likes", tags=["likes"])


def get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def check_user_liked(db: Session, article_id: int, user_id: Optional[int], ip_address: Optional[str]) -> bool:
    if user_id:
        like = db.query(ArticleLike).filter(
            and_(ArticleLike.article_id == article_id, ArticleLike.user_id == user_id)
        ).first()
    elif ip_address:
        like = db.query(ArticleLike).filter(
            and_(ArticleLike.article_id == article_id, ArticleLike.ip_address == ip_address)
        ).first()
    else:
        return False
    return like is not None


def send_like_notification_bg(article_title: str, article_slug: str, liker_name: str):
    from app.core.database import SessionLocal
    db = SessionLocal()
    try:
        settings = db.query(NotificationSettings).first()
        if settings and settings.notify_on_like:
            EmailService.send_new_like_notification_db(
                db=db,
                liker_name=liker_name,
                article_title=article_title,
                article_slug=article_slug
            )
    except Exception as e:
        print(f"Failed to send like notification: {e}")
    finally:
        db.close()


@router.post("/{article_id}", response_model=LikeResponse)
async def toggle_like(
    article_id: int,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    user_id = current_user.id if current_user else None
    ip_address = get_client_ip(request) if not user_id else None
    
    existing_like = None
    if user_id:
        existing_like = db.query(ArticleLike).filter(
            and_(ArticleLike.article_id == article_id, ArticleLike.user_id == user_id)
        ).first()
    elif ip_address:
        existing_like = db.query(ArticleLike).filter(
            and_(ArticleLike.article_id == article_id, ArticleLike.ip_address == ip_address)
        ).first()
    
    if existing_like:
        db.delete(existing_like)
        article.like_count = max(0, article.like_count - 1)
        is_liked = False
    else:
        new_like = ArticleLike(
            article_id=article_id,
            user_id=user_id,
            ip_address=ip_address
        )
        db.add(new_like)
        article.like_count += 1
        is_liked = True
        
        liker_name = current_user.username if current_user else "匿名用户"
        article_title = article.title
        article_slug = article.slug
        background_tasks.add_task(send_like_notification_bg, article_title, article_slug, liker_name)
    
    db.commit()
    db.refresh(article)
    
    return LikeResponse(
        article_id=article_id,
        like_count=article.like_count,
        is_liked=is_liked
    )


@router.get("/{article_id}", response_model=LikeResponse)
async def get_like_status(
    article_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    user_id = current_user.id if current_user else None
    ip_address = get_client_ip(request) if not user_id else None
    
    is_liked = check_user_liked(db, article_id, user_id, ip_address)
    
    return LikeResponse(
        article_id=article_id,
        like_count=article.like_count,
        is_liked=is_liked
    )
