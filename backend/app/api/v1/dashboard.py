from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import datetime, timedelta
from typing import List, Optional
from pydantic import BaseModel
from app.core.database import get_db
from app.utils.auth import get_current_admin_user
from app.utils.timezone import get_now, get_today_start
from app.models.models import (
    Article, User, Comment, ArticleLike, Category, Tag,
    LoginLog, OperationLog, AccessLog
)

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


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


@router.get("/overview", response_model=OverviewStats)
async def get_overview_stats(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    total_articles = db.query(Article).count()
    published_articles = db.query(Article).filter(Article.is_published == True).count()
    total_views = db.query(func.sum(Article.view_count)).scalar() or 0
    total_likes = db.query(ArticleLike).count()
    total_comments = db.query(Comment).filter(Comment.is_deleted == False, Comment.status == 'approved').count()
    total_users = db.query(User).count()
    
    today = get_today_start()
    new_users_today = db.query(User).filter(User.created_at >= today).count()
    new_articles_today = db.query(Article).filter(Article.created_at >= today).count()
    
    return OverviewStats(
        total_articles=total_articles,
        published_articles=published_articles,
        total_views=total_views,
        total_likes=total_likes,
        total_comments=total_comments,
        total_users=total_users,
        new_users_today=new_users_today,
        new_articles_today=new_articles_today
    )


@router.get("/views-trend", response_model=List[TrendData])
async def get_views_trend(
    days: int = Query(default=30, ge=7, le=90),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    end_date = get_now().date()
    start_date = end_date - timedelta(days=days - 1)
    
    articles = db.query(Article).all()
    
    daily_views = {}
    current_date = start_date
    while current_date <= end_date:
        daily_views[current_date.isoformat()] = 0
        current_date += timedelta(days=1)
    
    for article in articles:
        article_date = article.created_at.date()
        if article_date >= start_date:
            date_str = article_date.isoformat()
            if date_str in daily_views:
                daily_views[date_str] += article.view_count
    
    return [TrendData(date=k, value=v) for k, v in sorted(daily_views.items())]


@router.get("/articles-trend", response_model=List[TrendData])
async def get_articles_trend(
    days: int = Query(default=30, ge=7, le=90),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    end_date = get_now().date()
    start_date = end_date - timedelta(days=days - 1)
    
    daily_articles = {}
    current_date = start_date
    while current_date <= end_date:
        daily_articles[current_date.isoformat()] = 0
        current_date += timedelta(days=1)
    
    articles = db.query(Article).filter(
        Article.created_at >= start_date
    ).all()
    
    for article in articles:
        date_str = article.created_at.date().isoformat()
        if date_str in daily_articles:
            daily_articles[date_str] += 1
    
    return [TrendData(date=k, value=v) for k, v in sorted(daily_articles.items())]


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
    from app.models.models import article_tags
    
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
    articles = db.query(Article).filter(Article.is_published == True)
    
    if sort_by == 'views':
        articles = articles.order_by(desc(Article.view_count))
    elif sort_by == 'likes':
        articles = articles.order_by(desc(Article.like_count))
    else:
        articles = articles.order_by(desc(Article.id))
    
    articles = articles.limit(limit).all()
    
    result = []
    for article in articles:
        comment_count = db.query(Comment).filter(
            Comment.article_id == article.id,
            Comment.is_deleted == False,
            Comment.status == 'approved'
        ).count()
        
        result.append(ArticleViewsRank(
            id=article.id,
            title=article.title,
            views=article.view_count,
            likes=article.like_count,
            comments=comment_count
        ))
    
    return result


@router.get("/user-activity", response_model=List[UserActivity])
async def get_user_activity(
    days: int = Query(default=30, ge=7, le=90),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    end_date = get_now().date()
    start_date = end_date - timedelta(days=days - 1)
    
    daily_data = {}
    current_date = start_date
    while current_date <= end_date:
        daily_data[current_date.isoformat()] = {
            'logins': 0,
            'registrations': 0,
            'comments': 0
        }
        current_date += timedelta(days=1)
    
    logins = db.query(LoginLog).filter(
        LoginLog.created_at >= start_date,
        LoginLog.status == 'success'
    ).all()
    
    for login in logins:
        date_str = login.created_at.date().isoformat()
        if date_str in daily_data:
            daily_data[date_str]['logins'] += 1
    
    registrations = db.query(User).filter(
        User.created_at >= start_date
    ).all()
    
    for user in registrations:
        date_str = user.created_at.date().isoformat()
        if date_str in daily_data:
            daily_data[date_str]['registrations'] += 1
    
    comments = db.query(Comment).filter(
        Comment.created_at >= start_date,
        Comment.is_deleted == False
    ).all()
    
    for comment in comments:
        date_str = comment.created_at.date().isoformat()
        if date_str in daily_data:
            daily_data[date_str]['comments'] += 1
    
    return [
        UserActivity(
            date=k,
            logins=v['logins'],
            registrations=v['registrations'],
            comments=v['comments']
        )
        for k, v in sorted(daily_data.items())
    ]


@router.get("/access-trend", response_model=List[AccessTrend])
async def get_access_trend(
    days: int = Query(default=7, ge=1, le=30),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    end_date = get_now().date()
    start_date = end_date - timedelta(days=days - 1)
    
    daily_data = {}
    current_date = start_date
    while current_date <= end_date:
        daily_data[current_date.isoformat()] = {
            'page_views': 0,
            'unique_ips': set(),
            'response_times': []
        }
        current_date += timedelta(days=1)
    
    access_logs = db.query(AccessLog).filter(
        AccessLog.created_at >= start_date
    ).all()
    
    for log in access_logs:
        date_str = log.created_at.date().isoformat()
        if date_str in daily_data:
            daily_data[date_str]['page_views'] += 1
            if log.ip_address:
                daily_data[date_str]['unique_ips'].add(log.ip_address)
            if log.response_time:
                daily_data[date_str]['response_times'].append(log.response_time)
    
    result = []
    for date_str, data in sorted(daily_data.items()):
        avg_time = 0
        if data['response_times']:
            avg_time = sum(data['response_times']) / len(data['response_times'])
        
        result.append(AccessTrend(
            date=date_str,
            page_views=data['page_views'],
            unique_visitors=len(data['unique_ips']),
            avg_response_time=round(avg_time, 2)
        ))
    
    return result


@router.get("/comment-trend", response_model=List[TrendData])
async def get_comment_trend(
    days: int = Query(default=30, ge=7, le=90),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    end_date = get_now().date()
    start_date = end_date - timedelta(days=days - 1)
    
    daily_comments = {}
    current_date = start_date
    while current_date <= end_date:
        daily_comments[current_date.isoformat()] = 0
        current_date += timedelta(days=1)
    
    comments = db.query(Comment).filter(
        Comment.created_at >= start_date,
        Comment.is_deleted == False
    ).all()
    
    for comment in comments:
        date_str = comment.created_at.date().isoformat()
        if date_str in daily_comments:
            daily_comments[date_str] += 1
    
    return [TrendData(date=k, value=v) for k, v in sorted(daily_comments.items())]
