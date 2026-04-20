import time
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Optional, List, Any, Dict
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, joinedload, selectinload
from sqlalchemy import func
from pydantic import BaseModel
from app.core.database import get_db, SessionLocal
from app.models import (
    Article, Category, Tag, Comment, ArticleLike, ArticleBookmark,
    SiteConfig, Announcement, UserProfile, AvatarType, User
)
from app.schemas import (
    CategoryResponse, TagResponse, ArticleListItem, PaginatedResponse,
    SiteConfigResponse, AnnouncementResponse, UserProfileResponse
)
from app.utils.auth import get_current_user_optional
from app.utils.cache import cache_manager

router = APIRouter(prefix="/init", tags=["Init"])
logger = logging.getLogger(__name__)

executor = ThreadPoolExecutor(max_workers=8)


class InitResponse(BaseModel):
    site_config: List[SiteConfigResponse]
    categories: List[CategoryResponse]
    tags: List[TagResponse]
    announcements: List[AnnouncementResponse]
    articles: PaginatedResponse
    featured_articles: PaginatedResponse
    github_stats: Optional[Dict[str, Any]] = None
    user_profile: Optional[UserProfileResponse] = None
    liked_article_ids: Optional[List[int]] = None
    bookmarked_article_ids: Optional[List[int]] = None


def _get_site_configs_cached() -> List[SiteConfigResponse]:
    db = SessionLocal()
    try:
        cache_key = "all_configs"
        cached = cache_manager.get("site_config", cache_key)
        if cached:
            return [SiteConfigResponse(**c) for c in cached]
        
        configs = db.query(SiteConfig).all()
        result = [SiteConfigResponse.model_validate(c) for c in configs]
        cache_manager.set("site_config", cache_key, [r.model_dump() for r in result])
        return result
    finally:
        db.close()


def _get_categories_cached() -> List[CategoryResponse]:
    db = SessionLocal()
    try:
        cache_key = "all_categories"
        cached = cache_manager.get("categories", cache_key)
        if cached:
            return [CategoryResponse(**c) for c in cached]
        
        categories = db.query(Category).order_by(Category.order).all()
        if not categories:
            return []
        
        category_ids = [c.id for c in categories]
        article_counts = dict(
            db.query(
                Article.category_id,
                func.count(Article.id)
            ).filter(
                Article.category_id.in_(category_ids),
                Article.is_published == True
            ).group_by(Article.category_id).all()
        )
        
        result = []
        for cat in categories:
            cat_response = CategoryResponse.model_validate(cat)
            cat_response.article_count = article_counts.get(cat.id, 0)
            result.append(cat_response)
        
        cache_manager.set("categories", cache_key, [r.model_dump() for r in result])
        return result
    finally:
        db.close()


def _get_tags_cached() -> List[TagResponse]:
    db = SessionLocal()
    try:
        cache_key = "all_tags"
        cached = cache_manager.get("tags", cache_key)
        if cached:
            return [TagResponse(**t) for t in cached]
        
        from app.models import article_tags
        tags = db.query(Tag).all()
        if not tags:
            return []
        
        tag_ids = [t.id for t in tags]
        article_counts = dict(
            db.query(
                article_tags.c.tag_id,
                func.count(article_tags.c.article_id)
            ).filter(
                article_tags.c.tag_id.in_(tag_ids)
            ).group_by(article_tags.c.tag_id).all()
        )
        
        result = []
        for tag in tags:
            tag_response = TagResponse.model_validate(tag)
            tag_response.article_count = article_counts.get(tag.id, 0)
            result.append(tag_response)
        
        cache_manager.set("tags", cache_key, [r.model_dump() for r in result])
        return result
    finally:
        db.close()


def _get_announcements_cached(active_only: bool = True) -> List[AnnouncementResponse]:
    db = SessionLocal()
    try:
        cache_key = f"announcements_{active_only}"
        cached = cache_manager.get("announcements", cache_key)
        if cached:
            return [AnnouncementResponse(**a) for a in cached]
        
        query = db.query(Announcement)
        if active_only:
            query = query.filter(Announcement.is_active == True)
        announcements = query.order_by(Announcement.order, Announcement.created_at.desc()).all()
        result = [AnnouncementResponse.model_validate(a) for a in announcements]
        
        if result:
            cache_manager.set("announcements", cache_key, [r.model_dump() for r in result])
        return result
    finally:
        db.close()


def _get_articles_list(page: int, page_size: int, is_featured: Optional[bool] = None) -> PaginatedResponse:
    db = SessionLocal()
    try:
        query = db.query(Article).options(
            joinedload(Article.category),
            selectinload(Article.tags)
        ).filter(Article.is_published == True)
        
        if is_featured is not None:
            query = query.filter(Article.is_featured == is_featured)
        
        total = query.count()
        total_pages = (total + page_size - 1) // page_size
        articles = query.order_by(
            Article.is_pinned.desc(),
            Article.created_at.desc()
        ).offset((page - 1) * page_size).limit(page_size).all()
        
        comment_counts = {}
        if articles:
            article_ids = [a.id for a in articles]
            comment_query = db.query(
                Comment.article_id,
                func.count(Comment.id).label('count')
            ).filter(
                Comment.article_id.in_(article_ids),
                Comment.status == 'approved',
                Comment.is_deleted == False
            ).group_by(Comment.article_id).all()
            
            comment_counts = {c.article_id: c.count for c in comment_query}
        
        items = []
        for article in articles:
            items.append(ArticleListItem(
                id=article.id,
                title=article.title,
                slug=article.slug,
                summary=article.summary,
                cover_image=article.cover_image,
                is_published=article.is_published,
                is_featured=article.is_featured,
                is_pinned=article.is_pinned or False,
                view_count=article.view_count,
                like_count=article.like_count or 0,
                comment_count=comment_counts.get(article.id, 0),
                reading_time=article.reading_time,
                created_at=article.created_at,
                published_at=article.published_at,
                category=CategoryResponse.model_validate(article.category) if article.category else None,
                tags=[TagResponse.model_validate(tag) for tag in article.tags]
            ))
        
        return PaginatedResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
    finally:
        db.close()


def _get_github_stats_cached() -> Dict[str, Any]:
    import os
    import httpx
    
    db = SessionLocal()
    try:
        GITHUB_CACHE_TTL = 3600
        cache_key = "github_stats"
        cached = cache_manager.get("site_config", cache_key)
        if cached and time.time() - cached.get("timestamp", 0) < GITHUB_CACHE_TTL:
            return cached.get("data", {"enabled": False, "stars": 0, "forks": 0, "watchers": 0, "open_issues": 0})
        
        github_repo_config = db.query(SiteConfig).filter(SiteConfig.key == "github_repo_url").first()
        repo_url = github_repo_config.value if github_repo_config else ""
        
        if not repo_url:
            return {"enabled": False, "stars": 0, "forks": 0, "watchers": 0, "open_issues": 0}
        
        repo_url = repo_url.strip()
        if repo_url.endswith('.git'):
            repo_url = repo_url[:-4]
        if repo_url.endswith('/'):
            repo_url = repo_url[:-1]
        parts = repo_url.split('/')
        if len(parts) < 2:
            return {"enabled": False, "stars": 0, "forks": 0, "watchers": 0, "open_issues": 0}
        
        owner, repo = parts[-2], parts[-1]
        
        try:
            github_token = os.getenv("GITHUB_TOKEN")
            headers = {"Accept": "application/vnd.github.v3+json"}
            if github_token:
                headers["Authorization"] = f"token {github_token}"
            
            with httpx.Client(timeout=10) as client:
                response = client.get(f"https://api.github.com/repos/{owner}/{repo}", headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    result = {
                        "enabled": True,
                        "stars": data.get("stargazers_count", 0),
                        "forks": data.get("forks_count", 0),
                        "watchers": data.get("watchers_count", 0),
                        "open_issues": data.get("open_issues_count", 0)
                    }
                    cache_manager.set("site_config", cache_key, {"data": result, "timestamp": time.time()})
                    return result
        except Exception as e:
            logger.warning(f"Failed to fetch GitHub stats: {e}")
        
        return {"enabled": False, "stars": 0, "forks": 0, "watchers": 0, "open_issues": 0}
    finally:
        db.close()


def _get_user_profile_data(user_id: int, username: str) -> Dict[str, Any]:
    db = SessionLocal()
    try:
        profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
        
        if not profile:
            import random
            gradient = random.sample([
                "#e74c3c", "#3498db", "#2ecc71", "#9b59b6", "#f39c12",
                "#1abc9c", "#e67e22", "#34495e", "#16a085", "#c0392b"
            ], 2)
            profile = UserProfile(
                user_id=user_id,
                default_avatar_gradient=gradient
            )
            db.add(profile)
            db.commit()
            db.refresh(profile)
        
        avatar_url = None
        avatar_type = "default"
        
        if profile.avatar_type == AvatarType.custom and profile.avatar_url:
            avatar_url = profile.avatar_url
            avatar_type = "custom"
        elif profile.oauth_avatar_url:
            avatar_url = profile.oauth_avatar_url
            avatar_type = "oauth"
        
        return {
            "id": profile.id,
            "user_id": profile.user_id,
            "username": username,
            "avatar_type": avatar_type,
            "avatar_url": avatar_url,
            "oauth_avatar_url": profile.oauth_avatar_url,
            "default_avatar_gradient": profile.default_avatar_gradient if not profile.oauth_avatar_url else None,
            "created_at": profile.created_at,
            "updated_at": profile.updated_at
        }
    finally:
        db.close()


def _get_user_interaction_data(user_id: int) -> tuple:
    db = SessionLocal()
    try:
        liked = db.query(ArticleLike.article_id).filter(
            ArticleLike.user_id == user_id
        ).all()
        liked_article_ids = [l[0] for l in liked]
        
        bookmarked = db.query(ArticleBookmark.article_id).filter(
            ArticleBookmark.user_id == user_id
        ).all()
        bookmarked_article_ids = [b[0] for b in bookmarked]
        
        return liked_article_ids, bookmarked_article_ids
    finally:
        db.close()


@router.get("", response_model=InitResponse)
async def get_init_data(
    page: int = Query(1, ge=1),
    page_size: int = Query(6, ge=1, le=100),
    featured_page_size: int = Query(5, ge=1, le=20),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    loop = asyncio.get_event_loop()
    
    public_tasks = [
        loop.run_in_executor(executor, _get_site_configs_cached),
        loop.run_in_executor(executor, _get_categories_cached),
        loop.run_in_executor(executor, _get_tags_cached),
        loop.run_in_executor(executor, _get_announcements_cached, True),
        loop.run_in_executor(executor, _get_articles_list, page, page_size, None),
        loop.run_in_executor(executor, _get_articles_list, 1, featured_page_size, True),
        loop.run_in_executor(executor, _get_github_stats_cached),
    ]
    
    public_results = await asyncio.gather(*public_tasks)
    
    site_config = public_results[0]
    categories = public_results[1]
    tags = public_results[2]
    announcements = public_results[3]
    articles = public_results[4]
    featured_articles = public_results[5]
    github_stats = public_results[6]
    
    user_profile = None
    liked_article_ids = None
    bookmarked_article_ids = None
    
    if current_user:
        user_tasks = [
            loop.run_in_executor(executor, _get_user_profile_data, current_user.id, current_user.username),
            loop.run_in_executor(executor, _get_user_interaction_data, current_user.id),
        ]
        
        user_results = await asyncio.gather(*user_tasks)
        
        user_profile = user_results[0]
        liked_article_ids, bookmarked_article_ids = user_results[1]
    
    return InitResponse(
        site_config=site_config,
        categories=categories,
        tags=tags,
        announcements=announcements,
        articles=articles,
        featured_articles=featured_articles,
        github_stats=github_stats,
        user_profile=user_profile,
        liked_article_ids=liked_article_ids,
        bookmarked_article_ids=bookmarked_article_ids
    )
