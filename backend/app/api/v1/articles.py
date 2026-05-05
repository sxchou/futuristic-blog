from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session, joinedload, selectinload
from sqlalchemy import func, or_
from sqlalchemy.exc import IntegrityError
from app.core.database import get_db
from app.models import Article, Category, Tag, Comment, ArticleLike, ArticleBookmark, ArticleFile, User, article_tags
from app.schemas import (
    ArticleCreate, ArticleUpdate, ArticleResponse, ArticleListItem,
    CategoryResponse, TagResponse, PaginatedResponse, UserResponse
)
from app.utils import get_current_user, generate_slug, calculate_reading_time
from app.utils.helpers import generate_unique_slug, translate_to_english, generate_slug_from_text
from app.utils.auth import get_current_user_optional
from app.utils.permissions import require_permission
from app.services.log_service import LogService
from app.services.baidu_push_service import baidu_push_service
from app.services.permission_service import PermissionService
from app.utils.cache import cache_manager
import asyncio
import os
import re


def check_user_liked(db: Session, article_id: int, user_id: Optional[int]) -> bool:
    from sqlalchemy import and_
    if user_id:
        like = db.query(ArticleLike).filter(
            and_(ArticleLike.article_id == article_id, ArticleLike.user_id == user_id)
        ).first()
        return like is not None
    return False
from functools import lru_cache

router = APIRouter(prefix="/articles", tags=["Articles"])

CACHE_NAME = "articles"


def invalidate_articles_cache():
    cache_manager.clear_cache(CACHE_NAME)


def link_files_to_article(db: Session, article_id: int, content: str, cover_image: Optional[str] = None):
    """关联文章内容中的图片和封面图到文章"""
    image_urls = set()
    
    if content:
        markdown_pattern = r'!\[.*?\]\((/uploads/images/[^)]+)\)'
        matches = re.findall(markdown_pattern, content)
        image_urls.update(matches)
    
    if cover_image and cover_image.startswith('/uploads/'):
        image_urls.add(cover_image)
    
    if image_urls:
        for url in image_urls:
            db.query(ArticleFile).filter(
                ArticleFile.file_path == url,
                ArticleFile.article_id == None
            ).update({"article_id": article_id})
        db.commit()


@lru_cache(maxsize=1000)
def get_english_variants(text: str) -> tuple:
    if not text:
        return ()
    
    variants = []
    
    slug_form = generate_slug_from_text(text)
    if slug_form:
        variants.append(slug_form.lower())
    
    words = re.findall(r'[a-zA-Z]+', text)
    if words:
        initials = ''.join([w[0].lower() for w in words if w])
        if initials and initials != slug_form:
            variants.append(initials.lower())
    
    return tuple(variants)


def contains_chinese(text: str) -> bool:
    return bool(re.search(r'[\u4e00-\u9fff]', text))


def wildcard_to_regex(pattern: str) -> str:
    regex = re.escape(pattern)
    regex = regex.replace(r'\*', '.*')
    regex = regex.replace(r'\?', '.')
    return regex


def highlight_text(text: str, search_term: str, max_length: int = 200) -> str:
    if not text or not search_term:
        return text[:max_length] if text else ""
    
    if '*' in search_term or '?' in search_term:
        try:
            pattern = wildcard_to_regex(search_term)
            regex = re.compile(pattern, re.IGNORECASE)
        except:
            regex = re.compile(re.escape(search_term), re.IGNORECASE)
    else:
        regex = re.compile(re.escape(search_term), re.IGNORECASE)
    
    match = regex.search(text)
    if match:
        start = max(0, match.start() - 50)
        end = min(len(text), match.end() + 150)
        snippet = text[start:end]
        
        if start > 0:
            snippet = "..." + snippet
        if end < len(text):
            snippet = snippet + "..."
        
        highlighted = regex.sub(r'<mark class="search-highlight">\g<0></mark>', snippet)
        return highlighted
    else:
        return text[:max_length] + "..." if len(text) > max_length else text


def search_articles(db: Session, search: str, page: int = 1, page_size: int = 10) -> tuple:
    articles = db.query(Article).options(
        joinedload(Article.category),
        selectinload(Article.tags),
        joinedload(Article.author)
    ).filter(Article.is_published == True).all()
    
    matched_articles = []
    search_lower = search.lower()
    has_wildcard = '*' in search or '?' in search
    
    if has_wildcard:
        try:
            pattern = wildcard_to_regex(search)
            search_regex = re.compile(pattern, re.IGNORECASE)
        except:
            search_regex = None
    else:
        search_regex = None
    
    for article in articles:
        title_lower = article.title.lower() if article.title else ""
        summary_lower = article.summary.lower() if article.summary else ""
        content_lower = article.content.lower() if article.content else ""
        
        matched = False
        match_type = None
        
        if has_wildcard and search_regex:
            if search_regex.search(article.title or ""):
                matched = True
                match_type = "title_wildcard"
            elif search_regex.search(article.summary or ""):
                matched = True
                match_type = "summary_wildcard"
            elif search_regex.search(article.content or ""):
                matched = True
                match_type = "content_wildcard"
        
        if not matched:
            if search_lower in title_lower:
                matched = True
                match_type = "title"
            elif search_lower in summary_lower:
                matched = True
                match_type = "summary"
            elif search_lower in content_lower:
                matched = True
                match_type = "content"
        
        if matched:
            highlighted_title = highlight_text(article.title, search, max_length=100)
            highlighted_summary = highlight_text(article.summary, search, max_length=200)
            
            article_dict = {
                'article': article,
                'highlighted_title': highlighted_title,
                'highlighted_summary': highlighted_summary,
                'match_type': match_type
            }
            matched_articles.append(article_dict)
    
    matched_articles.sort(key=lambda x: x['article'].created_at, reverse=True)
    
    total = len(matched_articles)
    total_pages = (total + page_size - 1) // page_size if total > 0 else 0
    
    start = (page - 1) * page_size
    end = start + page_size
    paginated = matched_articles[start:end]
    
    return paginated, total, total_pages


@router.get("", response_model=PaginatedResponse)
async def get_articles(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    category_id: Optional[int] = None,
    tag_id: Optional[int] = None,
    is_featured: Optional[bool] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    if search:
        matched_articles, total, total_pages = search_articles(db, search, page, page_size)
        
        comment_counts = {}
        if matched_articles:
            article_ids = [item['article'].id for item in matched_articles]
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
        for item in matched_articles:
            article = item['article']
            items.append(ArticleListItem(
                id=article.id,
                title=article.title,
                slug=article.slug,
                summary=article.summary,
                cover_image=article.cover_image,
                is_published=article.is_published,
                is_featured=article.is_featured,
                is_pinned=article.is_pinned or False,
                pinned_order=article.pinned_order or 0,
                view_count=article.view_count,
                like_count=article.like_count or 0,
                bookmark_count=article.bookmark_count or 0,
                comment_count=comment_counts.get(article.id, 0),
                reading_time=article.reading_time,
                created_at=article.created_at,
                published_at=article.published_at,
                category=CategoryResponse.model_validate(article.category) if article.category else None,
                tags=[TagResponse.model_validate(tag) for tag in article.tags],
                author=UserResponse.model_validate(article.author) if article.author else None,
                author_name=article.author_name,
                highlighted_title=item.get('highlighted_title'),
                highlighted_summary=item.get('highlighted_summary'),
                match_type=item.get('match_type')
            ))
        
        return PaginatedResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
    
    query = db.query(Article).options(
        joinedload(Article.category),
        selectinload(Article.tags),
        joinedload(Article.author)
    ).filter(Article.is_published == True)
    
    if category_id:
        query = query.filter(Article.category_id == category_id)
    if tag_id:
        query = query.join(Article.tags).filter(Tag.id == tag_id)
    if is_featured is not None:
        query = query.filter(Article.is_featured == is_featured)
    
    total = query.count()
    total_pages = (total + page_size - 1) // page_size
    articles = query.order_by(
        Article.is_pinned.desc(),
        Article.pinned_order.asc(),
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
            pinned_order=article.pinned_order or 0,
            view_count=article.view_count,
            like_count=article.like_count or 0,
            bookmark_count=article.bookmark_count or 0,
            comment_count=comment_counts.get(article.id, 0),
            reading_time=article.reading_time,
            created_at=article.created_at,
            published_at=article.published_at,
            category=CategoryResponse.model_validate(article.category) if article.category else None,
            tags=[TagResponse.model_validate(tag) for tag in article.tags],
            author=UserResponse.model_validate(article.author) if article.author else None,
            author_name=article.author_name
        ))
    
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/user/my-articles", response_model=PaginatedResponse)
async def get_user_articles(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Article).options(
        joinedload(Article.category),
        selectinload(Article.tags),
        joinedload(Article.author)
    ).filter(Article.author_id == current_user.id)
    
    total = query.count()
    total_pages = (total + page_size - 1) // page_size
    articles = query.order_by(Article.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    
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
            pinned_order=article.pinned_order or 0,
            view_count=article.view_count,
            like_count=article.like_count or 0,
            bookmark_count=article.bookmark_count or 0,
            comment_count=comment_counts.get(article.id, 0),
            reading_time=article.reading_time,
            created_at=article.created_at,
            published_at=article.published_at,
            category=CategoryResponse.model_validate(article.category) if article.category else None,
            tags=[TagResponse.model_validate(tag) for tag in article.tags],
            author=UserResponse.model_validate(article.author) if article.author else None,
            author_name=article.author_name
        ))
    
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/admin", response_model=PaginatedResponse)
async def get_admin_articles(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user = Depends(require_permission("article.view"))
):
    query = db.query(Article).options(
        joinedload(Article.category),
        selectinload(Article.tags),
        joinedload(Article.author)
    )
    
    total = query.count()
    total_pages = (total + page_size - 1) // page_size
    articles = query.order_by(Article.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    
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
            pinned_order=article.pinned_order or 0,
            view_count=article.view_count,
            like_count=article.like_count or 0,
            bookmark_count=article.bookmark_count or 0,
            comment_count=comment_counts.get(article.id, 0),
            reading_time=article.reading_time,
            created_at=article.created_at,
            published_at=article.published_at,
            category=CategoryResponse.model_validate(article.category) if article.category else None,
            tags=[TagResponse.model_validate(tag) for tag in article.tags],
            author=UserResponse.model_validate(article.author) if article.author else None,
            author_name=article.author_name
        ))
    
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/archive/list")
async def get_article_archive(db: Session = Depends(get_db)):
    cache_key = "article_archive"
    cached = cache_manager.get(CACHE_NAME, cache_key)
    if cached:
        return cached
    
    from app.utils.timezone import to_local
    
    articles = db.query(Article).filter(
        Article.is_published == True
    ).order_by(Article.created_at.desc()).all()
    
    archive: Dict[str, Dict[str, List[Dict[str, Any]]]] = {}
    
    for article in articles:
        local_created_at = to_local(article.created_at)
        year = local_created_at.year
        month = local_created_at.month
        
        year_str = str(year)
        month_str = f"{month:02d}"
        
        if year_str not in archive:
            archive[year_str] = {}
        
        if month_str not in archive[year_str]:
            archive[year_str][month_str] = []
        
        archive[year_str][month_str].append({
            "id": article.id,
            "title": article.title,
            "slug": article.slug,
            "created_at": local_created_at.isoformat(),
            "category": {
                "id": article.category.id,
                "name": article.category.name,
                "slug": article.category.slug,
                "color": article.category.color
            } if article.category else None
        })
    
    result = []
    for year in sorted(archive.keys(), reverse=True):
        year_data = {
            "year": int(year),
            "months": []
        }
        for month in sorted(archive[year].keys(), reverse=True):
            year_data["months"].append({
                "month": int(month),
                "count": len(archive[year][month]),
                "articles": archive[year][month]
            })
        result.append(year_data)
    
    cache_manager.set(CACHE_NAME, cache_key, result)
    return result


@router.get("/admin/{slug}", response_model=ArticleResponse)
async def get_admin_article(
    slug: str, 
    db: Session = Depends(get_db),
    current_user = Depends(require_permission("article.view"))
):
    article = db.query(Article).filter(Article.slug == slug).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    return ArticleResponse.model_validate(article)


@router.get("/{slug}", response_model=ArticleResponse)
async def get_article(
    slug: str, 
    request: Request,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user_optional)
):
    article = db.query(Article).options(
        joinedload(Article.category),
        selectinload(Article.tags),
        joinedload(Article.author),
        selectinload(Article.files)
    ).filter(Article.slug == slug, Article.is_published == True).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    article.view_count += 1
    db.commit()
    
    user_id = current_user.id if current_user else None
    is_liked = check_user_liked(db, article.id, user_id)
    
    response = ArticleResponse.model_validate(article)
    response.is_liked = is_liked
    
    return response


@router.post("", response_model=ArticleResponse)
async def create_article(
    article_data: ArticleCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user = Depends(require_permission("article.create"))
):
    slug = article_data.slug
    if not slug or not slug.strip():
        slug = await generate_slug(article_data.title)
        existing_slugs = [r[0] for r in db.query(Article.slug).all()]
        slug = generate_unique_slug(slug, existing_slugs)
    else:
        existing = db.query(Article).filter(Article.slug == slug).first()
        if existing:
            raise HTTPException(status_code=400, detail="Article with this slug already exists")
    
    reading_time = calculate_reading_time(article_data.content)
    
    can_publish = PermissionService.has_permission(db, current_user.id, "article.publish")
    
    was_publish_requested = article_data.is_published
    actual_is_published = article_data.is_published if can_publish else False
    
    new_article = Article(
        title=article_data.title,
        slug=slug,
        summary=article_data.summary,
        content=article_data.content,
        cover_image=article_data.cover_image,
        is_published=actual_is_published,
        is_featured=article_data.is_featured,
        is_pinned=article_data.is_pinned or False,
        pinned_order=article_data.pinned_order or 0,
        category_id=article_data.category_id,
        author_id=current_user.id,
        author_name=current_user.username,
        reading_time=reading_time
    )
    
    if article_data.tag_ids:
        tags = db.query(Tag).filter(Tag.id.in_(article_data.tag_ids)).all()
        new_article.tags = tags
    
    db.add(new_article)
    db.commit()
    db.refresh(new_article)
    
    invalidate_articles_cache()
    
    link_files_to_article(db, new_article.id, article_data.content, article_data.cover_image)
    
    LogService.log_operation(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        action="创建",
        module="文章管理",
        description=f"创建文章: {new_article.title}",
        target_type="文章",
        target_id=new_article.id,
        request=request,
        status="success"
    )
    
    if new_article.is_published:
        asyncio.create_task(baidu_push_service.push_article(new_article.slug))
    
    response = ArticleResponse.model_validate(new_article)
    response_dict = response.model_dump()
    
    if was_publish_requested and not can_publish:
        response_dict["warning"] = "您没有发布权限，文章已保存为草稿"
    
    return response_dict


@router.put("/{article_id}", response_model=ArticleResponse)
async def update_article(
    article_id: int,
    article_data: ArticleUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user = Depends(require_permission("article.edit"))
):
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    update_data = article_data.model_dump(exclude_unset=True, exclude={"tag_ids"})
    
    if "content" in update_data and not update_data["content"]:
        del update_data["content"]
    
    if "content" in update_data:
        update_data["reading_time"] = calculate_reading_time(update_data["content"])
    
    if article_data.cover_image is None and "cover_image" not in update_data:
        update_data["cover_image"] = None
    
    can_publish = PermissionService.has_permission(db, current_user.id, "article.publish")
    was_publish_change_requested = "is_published" in update_data
    original_is_published = article.is_published
    
    if "is_published" in update_data and not can_publish:
        del update_data["is_published"]
    
    for field, value in update_data.items():
        setattr(article, field, value)
    
    if article_data.tag_ids is not None:
        tags = db.query(Tag).filter(Tag.id.in_(article_data.tag_ids)).all()
        article.tags = tags
    
    try:
        db.commit()
        db.refresh(article)
    except IntegrityError as e:
        db.rollback()
        error_msg = str(e)
        if "ix_articles_slug" in error_msg or "slug" in error_msg.lower():
            raise HTTPException(
                status_code=400,
                detail={"message": "该slug已存在，请使用其他slug", "field": "slug"}
            )
        else:
            raise HTTPException(status_code=400, detail="保存失败，数据冲突")
    
    invalidate_articles_cache()
    
    link_files_to_article(db, article.id, article.content, article.cover_image)
    
    description = f"更新文章: {article.title}"
    action = "更新"
    
    if 'is_published' in update_data and len(update_data) == 1 and 'tag_ids' not in article_data.model_dump(exclude_unset=True):
        if original_is_published != article.is_published:
            if article.is_published:
                description = f"发布文章: {article.title}"
                action = "发布"
            else:
                description = f"取消发布文章: {article.title}"
                action = "取消发布"
    
    LogService.log_operation(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        action=action,
        module="文章管理",
        description=description,
        target_type="文章",
        target_id=article.id,
        request=request,
        status="success"
    )
    
    if article.is_published and article_data.is_published:
        asyncio.create_task(baidu_push_service.push_article(article.slug))
    
    response = ArticleResponse.model_validate(article)
    response_dict = response.model_dump()
    
    if was_publish_change_requested and not can_publish:
        response_dict["warning"] = f"您没有发布权限，文章发布状态未更改（当前：{'已发布' if original_is_published else '草稿'}）"
    
    return response_dict


@router.delete("/{article_id}")
async def delete_article(
    article_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user = Depends(require_permission("article.delete"))
):
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    article_title = article.title
    
    try:
        files = db.query(ArticleFile).filter(ArticleFile.article_id == article_id).all()
        for file in files:
            if file.file_path and os.path.exists(file.file_path):
                try:
                    os.remove(file.file_path)
                except Exception as e:
                    pass
        
        db.query(Comment).filter(Comment.article_id == article_id).delete()
        db.query(ArticleLike).filter(ArticleLike.article_id == article_id).delete()
        db.query(ArticleBookmark).filter(ArticleBookmark.article_id == article_id).delete()
        db.query(ArticleFile).filter(ArticleFile.article_id == article_id).delete()
        db.execute(article_tags.delete().where(article_tags.c.article_id == article_id))
        
        db.delete(article)
        db.commit()
        
        invalidate_articles_cache()
        
        LogService.log_operation(
            db=db,
            user_id=current_user.id,
            username=current_user.username,
            action="删除",
            module="文章管理",
            description=f"删除文章: {article_title}",
            target_type="文章",
            target_id=article_id,
            request=request,
            status="success"
        )
        
        return {"message": "Article deleted successfully"}
    except Exception as e:
        db.rollback()
        
        LogService.log_operation(
            db=db,
            user_id=current_user.id,
            username=current_user.username,
            action="删除",
            module="文章管理",
            description=f"删除文章失败: {article_title}",
            target_type="文章",
            target_id=article_id,
            request=request,
            status="failed",
            error_message=str(e)
        )
        
        raise HTTPException(status_code=500, detail=f"删除文章失败: {str(e)}")


@router.post("/{article_id}/push-baidu")
async def push_article_to_baidu(
    article_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(require_permission("article.publish"))
):
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    if not article.is_published:
        raise HTTPException(status_code=400, detail="只能推送已发布的文章")
    
    result = await baidu_push_service.push_article(article.slug)
    
    return {
        "article_id": article_id,
        "article_title": article.title,
        "push_result": result
    }


@router.post("/push-all-baidu")
async def push_all_articles_to_baidu(
    db: Session = Depends(get_db),
    current_user = Depends(require_permission("article.publish"))
):
    articles = db.query(Article).filter(Article.is_published == True).all()
    
    if not articles:
        return {"message": "没有已发布的文章", "push_result": {"success": 0}}
    
    slugs = [article.slug for article in articles]
    result = await baidu_push_service.push_articles(slugs)
    
    return {
        "total_articles": len(articles),
        "push_result": result
    }
