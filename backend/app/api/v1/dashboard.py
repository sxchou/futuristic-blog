from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, case, text
from datetime import datetime, timedelta
from typing import List, Optional
from pydantic import BaseModel
from app.core.database import get_db
from app.utils.auth import get_current_admin_user
from app.utils.timezone import get_now, get_today_start, to_local
from app.utils.cache import cache_manager
from app.models.models import (
    Article, User, Comment, ArticleLike, Category, Tag,
    LoginLog, OperationLog, AccessLog, article_tags, RefreshToken
)

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

CACHE_NAME = "dashboard"


class PublicStats(BaseModel):
    total_articles: int
    total_views: int
    total_likes: int
    total_comments: int


class OverviewStats(BaseModel):
    total_articles: int
    published_articles: int
    total_views: int
    total_likes: int
    total_comments: int
    total_users: int
    new_users_today: int
    new_articles_today: int


class TrendData(BaseModel):
    date: str
    value: int


class CategoryStats(BaseModel):
    name: str
    value: int
    color: str


class TagStats(BaseModel):
    name: str
    value: int
    color: str


class ArticleViewsRank(BaseModel):
    id: int
    title: str
    views: int
    likes: int
    comments: int


class UserActivity(BaseModel):
    date: str
    logins: int
    registrations: int
    comments: int


class AccessTrend(BaseModel):
    date: str
    page_views: int
    unique_visitors: int
    avg_response_time: float


@router.get("/public-stats", response_model=PublicStats)
async def get_public_stats(
    db: Session = Depends(get_db)
):
    cache_key = "public_stats"
    cached = cache_manager.get(CACHE_NAME, cache_key)
    if cached:
        return cached
    
    total_articles = db.query(func.count(Article.id)).filter(
        Article.is_published == True
    ).scalar() or 0
    
    total_views = db.query(func.sum(Article.view_count)).filter(
        Article.is_published == True
    ).scalar() or 0
    
    total_likes = db.query(func.count(ArticleLike.id)).scalar() or 0
    
    total_comments = db.query(func.count(Comment.id)).filter(
        Comment.is_deleted == False, 
        Comment.status == 'approved'
    ).scalar() or 0
    
    result = PublicStats(
        total_articles=total_articles,
        total_views=total_views,
        total_likes=total_likes,
        total_comments=total_comments
    )
    
    cache_manager.set(CACHE_NAME, cache_key, result)
    return result


@router.get("/overview", response_model=OverviewStats)
async def get_overview_stats(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    today = get_today_start()
    
    article_stats = db.query(
        func.count(Article.id).label('total'),
        func.sum(case((Article.is_published == True, 1), else_=0)).label('published'),
        func.sum(Article.view_count).label('views'),
        func.sum(case((Article.created_at >= today, 1), else_=0)).label('today')
    ).first()
    
    total_likes = db.query(func.count(ArticleLike.id)).scalar() or 0
    total_comments = db.query(func.count(Comment.id)).filter(
        Comment.is_deleted == False, 
        Comment.status == 'approved'
    ).scalar() or 0
    
    user_stats = db.query(
        func.count(User.id).label('total'),
        func.sum(case((User.created_at >= today, 1), else_=0)).label('today')
    ).first()
    
    return OverviewStats(
        total_articles=article_stats.total or 0,
        published_articles=article_stats.published or 0,
        total_views=article_stats.views or 0,
        total_likes=total_likes,
        total_comments=total_comments,
        total_users=user_stats.total or 0,
        new_users_today=user_stats.today or 0,
        new_articles_today=article_stats.today or 0
    )


@router.get("/views-trend", response_model=List[TrendData])
async def get_views_trend(
    days: int = Query(default=30, ge=7, le=90),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    end_date = get_now().date()
    start_date = end_date - timedelta(days=days - 1)
    
    daily_views = db.query(
        func.date(Article.created_at).label('date'),
        func.sum(Article.view_count).label('views')
    ).filter(
        Article.created_at >= start_date
    ).group_by(
        func.date(Article.created_at)
    ).all()
    
    result_dict = {str(d.date): d.views for d in daily_views if d.date}
    
    result = []
    current_date = start_date
    while current_date <= end_date:
        date_str = current_date.isoformat()
        result.append(TrendData(
            date=date_str,
            value=result_dict.get(date_str, 0)
        ))
        current_date += timedelta(days=1)
    
    return result


@router.get("/articles-trend", response_model=List[TrendData])
async def get_articles_trend(
    days: int = Query(default=30, ge=7, le=90),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    end_date = get_now().date()
    start_date = end_date - timedelta(days=days - 1)
    
    daily_articles = db.query(
        func.date(Article.created_at).label('date'),
        func.count(Article.id).label('count')
    ).filter(
        Article.created_at >= start_date
    ).group_by(
        func.date(Article.created_at)
    ).all()
    
    result_dict = {str(d.date): d.count for d in daily_articles if d.date}
    
    result = []
    current_date = start_date
    while current_date <= end_date:
        date_str = current_date.isoformat()
        result.append(TrendData(
            date=date_str,
            value=result_dict.get(date_str, 0)
        ))
        current_date += timedelta(days=1)
    
    return result


@router.get("/category-stats", response_model=List[CategoryStats])
async def get_category_stats(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    categories = db.query(
        Category.name,
        Category.color,
        func.count(Article.id).label('count')
    ).outerjoin(
        Article, Article.category_id == Category.id
    ).group_by(Category.id).all()
    
    return [
        CategoryStats(name=cat.name, value=cat.count, color=cat.color or '#00d4ff')
        for cat in categories
    ]


@router.get("/tag-stats", response_model=List[TagStats])
async def get_tag_stats(
    limit: int = Query(default=10, ge=5, le=20),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    tags = db.query(
        Tag.name,
        Tag.color,
        func.count(article_tags.c.article_id).label('count')
    ).outerjoin(
        article_tags, article_tags.c.tag_id == Tag.id
    ).group_by(Tag.id).order_by(desc('count')).limit(limit).all()
    
    return [
        TagStats(name=tag.name, value=tag.count, color=tag.color or '#7c3aed')
        for tag in tags
    ]


@router.get("/article-rank", response_model=List[ArticleViewsRank])
async def get_article_rank(
    limit: int = Query(default=10, ge=5, le=20),
    sort_by: str = Query(default='views', pattern='^(views|likes|comments)$'),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    comment_subquery = db.query(
        Comment.article_id,
        func.count(Comment.id).label('comment_count')
    ).filter(
        Comment.is_deleted == False,
        Comment.status == 'approved'
    ).group_by(Comment.article_id).subquery()
    
    query = db.query(
        Article.id,
        Article.title,
        Article.view_count,
        Article.like_count,
        func.coalesce(comment_subquery.c.comment_count, 0).label('comment_count')
    ).outerjoin(
        comment_subquery, Article.id == comment_subquery.c.article_id
    ).filter(Article.is_published == True)
    
    if sort_by == 'views':
        query = query.order_by(desc(Article.view_count))
    elif sort_by == 'likes':
        query = query.order_by(desc(Article.like_count))
    else:
        query = query.order_by(desc('comment_count'))
    
    articles = query.limit(limit).all()
    
    return [
        ArticleViewsRank(
            id=a.id,
            title=a.title,
            views=a.view_count,
            likes=a.like_count,
            comments=a.comment_count
        )
        for a in articles
    ]


@router.get("/user-activity", response_model=List[UserActivity])
async def get_user_activity(
    days: int = Query(default=30, ge=7, le=90),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    end_date = get_now().date()
    start_date = end_date - timedelta(days=days - 1)
    
    login_counts = dict(
        db.query(
            func.date(LoginLog.created_at).label('date'),
            func.count(LoginLog.id).label('count')
        ).filter(
            LoginLog.created_at >= start_date,
            LoginLog.status == 'success'
        ).group_by(func.date(LoginLog.created_at)).all()
    )
    
    registration_counts = dict(
        db.query(
            func.date(User.created_at).label('date'),
            func.count(User.id).label('count')
        ).filter(
            User.created_at >= start_date
        ).group_by(func.date(User.created_at)).all()
    )
    
    comment_counts = dict(
        db.query(
            func.date(Comment.created_at).label('date'),
            func.count(Comment.id).label('count')
        ).filter(
            Comment.created_at >= start_date,
            Comment.is_deleted == False
        ).group_by(func.date(Comment.created_at)).all()
    )
    
    result = []
    current_date = start_date
    while current_date <= end_date:
        date_str = current_date.isoformat()
        result.append(UserActivity(
            date=date_str,
            logins=login_counts.get(date_str, 0),
            registrations=registration_counts.get(date_str, 0),
            comments=comment_counts.get(date_str, 0)
        ))
        current_date += timedelta(days=1)
    
    return result


@router.get("/access-trend", response_model=List[AccessTrend])
async def get_access_trend(
    days: int = Query(default=7, ge=1, le=30),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    end_date = get_now().date()
    start_date = end_date - timedelta(days=days - 1)
    
    access_stats = db.query(
        func.date(AccessLog.created_at).label('date'),
        func.count(AccessLog.id).label('page_views'),
        func.count(func.distinct(AccessLog.ip_address)).label('unique_visitors'),
        func.avg(AccessLog.response_time).label('avg_response_time')
    ).filter(
        AccessLog.created_at >= start_date
    ).group_by(
        func.date(AccessLog.created_at)
    ).all()
    
    stats_dict = {str(s.date): s for s in access_stats if s.date}
    
    result = []
    current_date = start_date
    while current_date <= end_date:
        date_str = current_date.isoformat()
        stat = stats_dict.get(date_str)
        result.append(AccessTrend(
            date=date_str,
            page_views=stat.page_views if stat else 0,
            unique_visitors=stat.unique_visitors if stat else 0,
            avg_response_time=round(stat.avg_response_time, 2) if stat and stat.avg_response_time else 0
        ))
        current_date += timedelta(days=1)
    
    return result


@router.get("/comment-trend", response_model=List[TrendData])
async def get_comment_trend(
    days: int = Query(default=30, ge=7, le=90),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    end_date = get_now().date()
    start_date = end_date - timedelta(days=days - 1)
    
    daily_comments = db.query(
        func.date(Comment.created_at).label('date'),
        func.count(Comment.id).label('count')
    ).filter(
        Comment.created_at >= start_date,
        Comment.is_deleted == False
    ).group_by(
        func.date(Comment.created_at)
    ).all()
    
    result_dict = {str(d.date): d.count for d in daily_comments if d.date}
    
    result = []
    current_date = start_date
    while current_date <= end_date:
        date_str = current_date.isoformat()
        result.append(TrendData(
            date=date_str,
            value=result_dict.get(date_str, 0)
        ))
        current_date += timedelta(days=1)
    
    return result


@router.post("/fix-sequence")
async def fix_sequence(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    max_id = db.query(func.max(RefreshToken.id)).scalar() or 0
    next_val = max_id + 1
    
    try:
        db.execute(text(f"SELECT setval('refresh_tokens_id_seq', {next_val})"))
        db.commit()
        return {
            "success": True,
            "message": f"序列已修复，当前最大ID: {max_id}，下一个ID: {next_val}"
        }
    except Exception as e:
        db.rollback()
        return {
            "success": False,
            "error": str(e)
        }
