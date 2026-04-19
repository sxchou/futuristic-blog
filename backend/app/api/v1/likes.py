from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.core.database import get_db
from app.models import Article, ArticleLike, User, NotificationSettings
from app.schemas import LikeResponse, ArticleListItem, PaginatedResponse
from app.utils.auth import get_current_user_optional, get_current_user
from app.services.email_service import EmailService
from typing import Optional

router = APIRouter(prefix="/likes", tags=["likes"])


def check_user_liked(db: Session, article_id: int, user_id: Optional[int]) -> bool:
    if user_id:
        like = db.query(ArticleLike).filter(
            and_(ArticleLike.article_id == article_id, ArticleLike.user_id == user_id)
        ).first()
        return like is not None
    return False


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


@router.get("/user/liked", response_model=PaginatedResponse)
async def get_user_liked_articles(
    page: int = 1,
    page_size: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(ArticleLike).filter(
        ArticleLike.user_id == current_user.id
    ).order_by(ArticleLike.created_at.desc())
    
    total = query.count()
    likes = query.offset((page - 1) * page_size).limit(page_size).all()
    
    articles = []
    for like in likes:
        article = db.query(Article).filter(Article.id == like.article_id).first()
        if article:
            articles.append(ArticleListItem(
                id=article.id,
                title=article.title,
                slug=article.slug,
                summary=article.summary,
                cover_image=article.cover_image,
                view_count=article.view_count,
                like_count=article.like_count,
                comment_count=article.comment_count,
                is_published=article.is_published,
                is_featured=article.is_featured,
                is_pinned=article.is_pinned,
                reading_time=article.reading_time,
                created_at=article.created_at,
                published_at=article.published_at,
                category=article.category,
                tags=article.tags,
                is_liked=True,
                liked_at=like.created_at
            ))
    
    return PaginatedResponse(
        items=articles,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size
    )


@router.post("/{article_id}", response_model=LikeResponse)
async def toggle_like(
    article_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    user_id = current_user.id
    
    existing_like = db.query(ArticleLike).filter(
        and_(ArticleLike.article_id == article_id, ArticleLike.user_id == user_id)
    ).first()
    
    if existing_like:
        db.delete(existing_like)
        article.like_count = max(0, article.like_count - 1)
        is_liked = False
    else:
        new_like = ArticleLike(
            article_id=article_id,
            user_id=user_id,
            ip_address=None
        )
        db.add(new_like)
        article.like_count += 1
        is_liked = True
        
        liker_name = current_user.username
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
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    user_id = current_user.id if current_user else None
    
    is_liked = check_user_liked(db, article_id, user_id)
    
    return LikeResponse(
        article_id=article_id,
        like_count=article.like_count,
        is_liked=is_liked
    )
