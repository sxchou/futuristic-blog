import asyncio
from concurrent.futures import ThreadPoolExecutor
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, case, text
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from app.core.database import get_db, SessionLocal
from app.utils.permissions import require_permission
from app.utils.timezone import get_now, get_today_start, to_local
from app.utils.cache import cache_manager
from app.models.models import (
    Article, User, Comment, ArticleLike, Category, Tag,
    LoginLog, OperationLog, AccessLog, article_tags, RefreshToken
)
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

CACHE_NAME = "dashboard"

CACHE_TTL_OVERVIEW = 300
CACHE_TTL_TRENDS = 600
CACHE_TTL_STATS = 900
CACHE_TTL_ACCESS = 300

executor = ThreadPoolExecutor(max_workers=4)


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


class AllTrendsResponse(BaseModel):
    views_trend: List[TrendData]
    articles_trend: List[TrendData]
    comment_trend: List[TrendData]
    access_trend: List[AccessTrend]


class DashboardInitData(BaseModel):
    overview: OverviewStats
    category_stats: List[CategoryStats]
    tag_stats: List[TagStats]
    article_rank: List[ArticleViewsRank]
    trends: AllTrendsResponse


def _get_overview_stats_sync(db: Session) -> Dict[str, Any]:
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
    
    return {
        "total_articles": article_stats.total or 0,
        "published_articles": article_stats.published or 0,
        "total_views": article_stats.views or 0,
        "total_likes": total_likes,
        "total_comments": total_comments,
        "total_users": user_stats.total or 0,
        "new_users_today": user_stats.today or 0,
        "new_articles_today": article_stats.today or 0
    }


def _get_views_trend_sync(db: Session, days: int) -> List[Dict[str, Any]]:
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
        result.append({"date": date_str, "value": result_dict.get(date_str, 0)})
        current_date += timedelta(days=1)
    
    return result


def _get_articles_trend_sync(db: Session, days: int) -> List[Dict[str, Any]]:
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
        result.append({"date": date_str, "value": result_dict.get(date_str, 0)})
        current_date += timedelta(days=1)
    
    return result


def _get_comment_trend_sync(db: Session, days: int) -> List[Dict[str, Any]]:
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
        result.append({"date": date_str, "value": result_dict.get(date_str, 0)})
        current_date += timedelta(days=1)
    
    return result


def _get_access_trend_sync(db: Session, days: int) -> List[Dict[str, Any]]:
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
        result.append({
            "date": date_str,
            "page_views": stat.page_views if stat else 0,
            "unique_visitors": stat.unique_visitors if stat else 0,
            "avg_response_time": round(stat.avg_response_time, 2) if stat and stat.avg_response_time else 0
        })
        current_date += timedelta(days=1)
    
    return result


def _get_category_stats_sync(db: Session) -> List[Dict[str, Any]]:
    categories = db.query(
        Category.name,
        Category.color,
        func.count(Article.id).label('count')
    ).outerjoin(
        Article, Article.category_id == Category.id
    ).group_by(Category.id).all()
    
    return [
        {"name": cat.name, "value": cat.count, "color": cat.color or '#00d4ff'}
        for cat in categories
    ]


def _get_tag_stats_sync(db: Session, limit: int) -> List[Dict[str, Any]]:
    tags = db.query(
        Tag.name,
        Tag.color,
        func.count(article_tags.c.article_id).label('count')
    ).outerjoin(
        article_tags, article_tags.c.tag_id == Tag.id
    ).group_by(Tag.id).order_by(desc('count')).limit(limit).all()
    
    return [
        {"name": tag.name, "value": tag.count, "color": tag.color or '#7c3aed'}
        for tag in tags
    ]


def _get_article_rank_sync(db: Session, limit: int, sort_by: str) -> List[Dict[str, Any]]:
    query = db.query(
        Article.id,
        Article.title,
        Article.view_count,
        Article.like_count,
        Article.comment_count
    ).filter(Article.is_published == True)
    
    if sort_by == 'views':
        query = query.order_by(desc(Article.view_count))
    elif sort_by == 'likes':
        query = query.order_by(desc(Article.like_count))
    else:
        query = query.order_by(desc(Article.comment_count))
    
    articles = query.limit(limit).all()
    
    return [
        {
            "id": a.id,
            "title": a.title,
            "views": a.view_count,
            "likes": a.like_count,
            "comments": a.comment_count
        }
        for a in articles
    ]


async def warmup_dashboard_cache():
    """Pre-warm dashboard cache on application startup"""
    logger.info("Starting dashboard cache warmup...")
    db = SessionLocal()
    try:
        _get_overview_stats_sync(db)
        _get_category_stats_sync(db)
        _get_tag_stats_sync(db, 10)
        _get_article_rank_sync(db, 10, 'views')
        logger.info("Dashboard cache warmed up successfully")
    except Exception as e:
        logger.warning(f"Dashboard cache warmup failed: {e}")
    finally:
        db.close()


@router.get("/public-stats", response_model=PublicStats)
async def get_public_stats(
    db: Session = Depends(get_db)
):
    cache_key = "public_stats"
    cached = cache_manager.get(CACHE_NAME, cache_key)
    if cached:
        if isinstance(cached, dict):
            return PublicStats(**cached)
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
    
    cache_manager.set(CACHE_NAME, cache_key, result.model_dump(), ttl=CACHE_TTL_OVERVIEW)
    return result


@router.get("/overview", response_model=OverviewStats)
async def get_overview_stats(
    db: Session = Depends(get_db),
    current_user = Depends(require_permission("dashboard.view"))
):
    cache_key = "overview"
    cached = cache_manager.get(CACHE_NAME, cache_key)
    if cached:
        return cached
    
    loop = asyncio.get_running_loop()
    result_dict = await loop.run_in_executor(executor, _get_overview_stats_sync, db)
    
    result = OverviewStats(**result_dict)
    cache_manager.set(CACHE_NAME, cache_key, result.model_dump(), ttl=CACHE_TTL_OVERVIEW)
    return result


@router.get("/views-trend", response_model=List[TrendData])
async def get_views_trend(
    days: int = Query(default=30, ge=7, le=90),
    db: Session = Depends(get_db),
    current_user = Depends(require_permission("dashboard.view"))
):
    cache_key = f"views_trend_{days}"
    cached = cache_manager.get(CACHE_NAME, cache_key)
    if cached:
        return [TrendData(**item) for item in cached]
    
    loop = asyncio.get_running_loop()
    result_list = await loop.run_in_executor(executor, _get_views_trend_sync, db, days)
    
    result = [TrendData(**item) for item in result_list]
    cache_manager.set(CACHE_NAME, cache_key, result_list, ttl=CACHE_TTL_TRENDS)
    return result


@router.get("/articles-trend", response_model=List[TrendData])
async def get_articles_trend(
    days: int = Query(default=30, ge=7, le=90),
    db: Session = Depends(get_db),
    current_user = Depends(require_permission("dashboard.view"))
):
    cache_key = f"articles_trend_{days}"
    cached = cache_manager.get(CACHE_NAME, cache_key)
    if cached:
        return [TrendData(**item) for item in cached]
    
    loop = asyncio.get_running_loop()
    result_list = await loop.run_in_executor(executor, _get_articles_trend_sync, db, days)
    
    result = [TrendData(**item) for item in result_list]
    cache_manager.set(CACHE_NAME, cache_key, result_list, ttl=CACHE_TTL_TRENDS)
    return result


@router.get("/category-stats", response_model=List[CategoryStats])
async def get_category_stats(
    db: Session = Depends(get_db),
    current_user = Depends(require_permission("dashboard.view"))
):
    cache_key = "category_stats"
    cached = cache_manager.get(CACHE_NAME, cache_key)
    if cached:
        return [CategoryStats(**item) for item in cached]
    
    loop = asyncio.get_running_loop()
    result_list = await loop.run_in_executor(executor, _get_category_stats_sync, db)
    
    result = [CategoryStats(**item) for item in result_list]
    cache_manager.set(CACHE_NAME, cache_key, result_list, ttl=CACHE_TTL_STATS)
    return result


@router.get("/tag-stats", response_model=List[TagStats])
async def get_tag_stats(
    limit: int = Query(default=10, ge=5, le=20),
    db: Session = Depends(get_db),
    current_user = Depends(require_permission("dashboard.view"))
):
    cache_key = f"tag_stats_{limit}"
    cached = cache_manager.get(CACHE_NAME, cache_key)
    if cached:
        return [TagStats(**item) for item in cached]
    
    loop = asyncio.get_running_loop()
    result_list = await loop.run_in_executor(executor, _get_tag_stats_sync, db, limit)
    
    result = [TagStats(**item) for item in result_list]
    cache_manager.set(CACHE_NAME, cache_key, result_list, ttl=CACHE_TTL_STATS)
    return result


@router.get("/article-rank", response_model=List[ArticleViewsRank])
async def get_article_rank(
    limit: int = Query(default=10, ge=5, le=20),
    sort_by: str = Query(default='views', pattern='^(views|likes|comments)$'),
    db: Session = Depends(get_db),
    current_user = Depends(require_permission("dashboard.view"))
):
    cache_key = f"article_rank_{limit}_{sort_by}"
    cached = cache_manager.get(CACHE_NAME, cache_key)
    if cached:
        return [ArticleViewsRank(**item) for item in cached]
    
    loop = asyncio.get_running_loop()
    result_list = await loop.run_in_executor(executor, _get_article_rank_sync, db, limit, sort_by)
    
    result = [ArticleViewsRank(**item) for item in result_list]
    cache_manager.set(CACHE_NAME, cache_key, result_list, ttl=CACHE_TTL_STATS)
    return result


@router.get("/user-activity", response_model=List[UserActivity])
async def get_user_activity(
    days: int = Query(default=30, ge=7, le=90),
    db: Session = Depends(get_db),
    current_user = Depends(require_permission("dashboard.view"))
):
    cache_key = f"user_activity_{days}"
    cached = cache_manager.get(CACHE_NAME, cache_key)
    if cached:
        return cached
    
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
    
    cache_manager.set(CACHE_NAME, cache_key, [r.model_dump() for r in result], ttl=CACHE_TTL_TRENDS)
    return result


@router.get("/access-trend", response_model=List[AccessTrend])
async def get_access_trend(
    days: int = Query(default=7, ge=1, le=30),
    db: Session = Depends(get_db),
    current_user = Depends(require_permission("dashboard.view"))
):
    cache_key = f"access_trend_{days}"
    cached = cache_manager.get(CACHE_NAME, cache_key)
    if cached:
        return [AccessTrend(**item) for item in cached]
    
    loop = asyncio.get_running_loop()
    result_list = await loop.run_in_executor(executor, _get_access_trend_sync, db, days)
    
    result = [AccessTrend(**item) for item in result_list]
    cache_manager.set(CACHE_NAME, cache_key, result_list, ttl=CACHE_TTL_ACCESS)
    return result


@router.get("/comment-trend", response_model=List[TrendData])
async def get_comment_trend(
    days: int = Query(default=30, ge=7, le=90),
    db: Session = Depends(get_db),
    current_user = Depends(require_permission("dashboard.view"))
):
    cache_key = f"comment_trend_{days}"
    cached = cache_manager.get(CACHE_NAME, cache_key)
    if cached:
        return [TrendData(**item) for item in cached]
    
    loop = asyncio.get_running_loop()
    result_list = await loop.run_in_executor(executor, _get_comment_trend_sync, db, days)
    
    result = [TrendData(**item) for item in result_list]
    cache_manager.set(CACHE_NAME, cache_key, result_list, ttl=CACHE_TTL_TRENDS)
    return result


@router.get("/trends", response_model=AllTrendsResponse)
async def get_all_trends(
    trend_days: int = Query(default=30, ge=7, le=90, description="Days for views/articles/comments trends"),
    access_days: int = Query(default=7, ge=1, le=30, description="Days for access trend"),
    db: Session = Depends(get_db),
    current_user = Depends(require_permission("dashboard.view"))
):
    cache_key = f"all_trends_{trend_days}_{access_days}"
    cached = cache_manager.get(CACHE_NAME, cache_key)
    if cached:
        return AllTrendsResponse(
            views_trend=[TrendData(**item) for item in cached['views_trend']],
            articles_trend=[TrendData(**item) for item in cached['articles_trend']],
            comment_trend=[TrendData(**item) for item in cached['comment_trend']],
            access_trend=[AccessTrend(**item) for item in cached['access_trend']]
        )
    
    loop = asyncio.get_running_loop()
    
    views_task = loop.run_in_executor(executor, _get_views_trend_sync, db, trend_days)
    articles_task = loop.run_in_executor(executor, _get_articles_trend_sync, db, trend_days)
    comment_task = loop.run_in_executor(executor, _get_comment_trend_sync, db, trend_days)
    access_task = loop.run_in_executor(executor, _get_access_trend_sync, db, access_days)
    
    views_result, articles_result, comment_result, access_result = await asyncio.gather(
        views_task, articles_task, comment_task, access_task
    )
    
    result_dict = {
        'views_trend': views_result,
        'articles_trend': articles_result,
        'comment_trend': comment_result,
        'access_trend': access_result
    }
    
    cache_manager.set(CACHE_NAME, cache_key, result_dict, ttl=CACHE_TTL_TRENDS)
    
    return AllTrendsResponse(
        views_trend=[TrendData(**item) for item in views_result],
        articles_trend=[TrendData(**item) for item in articles_result],
        comment_trend=[TrendData(**item) for item in comment_result],
        access_trend=[AccessTrend(**item) for item in access_result]
    )


@router.get("/init", response_model=DashboardInitData)
async def get_dashboard_init(
    trend_days: int = Query(default=30, ge=7, le=90),
    access_days: int = Query(default=7, ge=1, le=30),
    tag_limit: int = Query(default=10, ge=5, le=20),
    rank_limit: int = Query(default=10, ge=5, le=20),
    rank_sort_by: str = Query(default='views', pattern='^(views|likes|comments)$'),
    db: Session = Depends(get_db),
    current_user = Depends(require_permission("dashboard.view"))
):
    cache_key = f"dashboard_init_{trend_days}_{access_days}_{tag_limit}_{rank_limit}_{rank_sort_by}"
    cached = cache_manager.get(CACHE_NAME, cache_key)
    if cached:
        return DashboardInitData(
            overview=OverviewStats(**cached['overview']),
            category_stats=[CategoryStats(**item) for item in cached['category_stats']],
            tag_stats=[TagStats(**item) for item in cached['tag_stats']],
            article_rank=[ArticleViewsRank(**item) for item in cached['article_rank']],
            trends=AllTrendsResponse(
                views_trend=[TrendData(**item) for item in cached['trends']['views_trend']],
                articles_trend=[TrendData(**item) for item in cached['trends']['articles_trend']],
                comment_trend=[TrendData(**item) for item in cached['trends']['comment_trend']],
                access_trend=[AccessTrend(**item) for item in cached['trends']['access_trend']]
            )
        )
    
    loop = asyncio.get_running_loop()
    
    overview_task = loop.run_in_executor(executor, _get_overview_stats_sync, db)
    category_task = loop.run_in_executor(executor, _get_category_stats_sync, db)
    tag_task = loop.run_in_executor(executor, _get_tag_stats_sync, db, tag_limit)
    rank_task = loop.run_in_executor(executor, _get_article_rank_sync, db, rank_limit, rank_sort_by)
    views_task = loop.run_in_executor(executor, _get_views_trend_sync, db, trend_days)
    articles_task = loop.run_in_executor(executor, _get_articles_trend_sync, db, trend_days)
    comment_task = loop.run_in_executor(executor, _get_comment_trend_sync, db, trend_days)
    access_task = loop.run_in_executor(executor, _get_access_trend_sync, db, access_days)
    
    results = await asyncio.gather(
        overview_task, category_task, tag_task, rank_task,
        views_task, articles_task, comment_task, access_task
    )
    
    overview_result = results[0]
    category_result = results[1]
    tag_result = results[2]
    rank_result = results[3]
    views_result = results[4]
    articles_result = results[5]
    comment_result = results[6]
    access_result = results[7]
    
    result_dict = {
        'overview': overview_result,
        'category_stats': category_result,
        'tag_stats': tag_result,
        'article_rank': rank_result,
        'trends': {
            'views_trend': views_result,
            'articles_trend': articles_result,
            'comment_trend': comment_result,
            'access_trend': access_result
        }
    }
    
    cache_manager.set(CACHE_NAME, cache_key, result_dict, ttl=CACHE_TTL_OVERVIEW)
    
    return DashboardInitData(
        overview=OverviewStats(**overview_result),
        category_stats=[CategoryStats(**item) for item in category_result],
        tag_stats=[TagStats(**item) for item in tag_result],
        article_rank=[ArticleViewsRank(**item) for item in rank_result],
        trends=AllTrendsResponse(
            views_trend=[TrendData(**item) for item in views_result],
            articles_trend=[TrendData(**item) for item in articles_result],
            comment_trend=[TrendData(**item) for item in comment_result],
            access_trend=[AccessTrend(**item) for item in access_result]
        )
    )


@router.post("/clear-cache")
async def clear_dashboard_cache(
    current_user = Depends(require_permission("settings.edit"))
):
    cache_manager.clear_cache(CACHE_NAME)
    return {"success": True, "message": "Dashboard cache cleared"}


@router.post("/fix-sequence")
async def fix_sequence(
    db: Session = Depends(get_db),
    current_user = Depends(require_permission("settings.edit"))
):
    from app.utils.db_utils import DatabaseUtils
    
    max_id = db.query(func.max(RefreshToken.id)).scalar() or 0
    next_val = max_id + 1
    
    try:
        DatabaseUtils.set_sequence_safe(db, "refresh_tokens_id_seq", next_val)
        return {
            "success": True,
            "message": f"序列已修复，当前最大ID: {max_id}，下一个ID: {next_val}"
        }
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to fix sequence: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }
