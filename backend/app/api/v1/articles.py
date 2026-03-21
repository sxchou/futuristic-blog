from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session, joinedload, selectinload
from sqlalchemy import func
from app.core.database import get_db
from app.models import Article, Category, Tag, Comment
from app.schemas import (
    ArticleCreate, ArticleUpdate, ArticleResponse, ArticleListItem,
    CategoryResponse, TagResponse, PaginatedResponse
)
from app.utils import get_current_user, get_current_active_user, generate_slug, calculate_reading_time
from app.services.log_service import LogService

router = APIRouter(prefix="/articles", tags=["Articles"])


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
    query = db.query(Article).options(
        joinedload(Article.category),
        selectinload(Article.tags)
    ).filter(Article.is_published == True)
    
    if category_id:
        query = query.filter(Article.category_id == category_id)
    if tag_id:
        query = query.join(Article.tags).filter(Tag.id == tag_id)
    if is_featured is not None:
        query = query.filter(Article.is_featured == is_featured)
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (Article.title.ilike(search_term)) | 
            (Article.summary.ilike(search_term))
        )
    
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


@router.get("/admin", response_model=PaginatedResponse)
async def get_admin_articles(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    query = db.query(Article)
    
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


@router.get("/archive/list")
async def get_article_archive(db: Session = Depends(get_db)):
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
    
    return result


@router.get("/admin/{slug}", response_model=ArticleResponse)
async def get_admin_article(
    slug: str, 
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    article = db.query(Article).filter(Article.slug == slug).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    return ArticleResponse.model_validate(article)


@router.get("/{slug}", response_model=ArticleResponse)
async def get_article(slug: str, db: Session = Depends(get_db)):
    article = db.query(Article).filter(Article.slug == slug, Article.is_published == True).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    article.view_count += 1
    db.commit()
    
    return ArticleResponse.model_validate(article)


@router.post("", response_model=ArticleResponse)
async def create_article(
    article_data: ArticleCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    existing = db.query(Article).filter(Article.slug == article_data.slug).first()
    if existing:
        raise HTTPException(status_code=400, detail="Article with this slug already exists")
    
    reading_time = calculate_reading_time(article_data.content)
    
    new_article = Article(
        title=article_data.title,
        slug=article_data.slug,
        summary=article_data.summary,
        content=article_data.content,
        cover_image=article_data.cover_image,
        is_published=article_data.is_published,
        is_featured=article_data.is_featured,
        category_id=article_data.category_id,
        author_id=current_user.id,
        reading_time=reading_time
    )
    
    if article_data.tag_ids:
        tags = db.query(Tag).filter(Tag.id.in_(article_data.tag_ids)).all()
        new_article.tags = tags
    
    db.add(new_article)
    db.commit()
    db.refresh(new_article)
    
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
    
    return ArticleResponse.model_validate(new_article)


@router.put("/{article_id}", response_model=ArticleResponse)
async def update_article(
    article_id: int,
    article_data: ArticleUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    if not current_user.is_admin and article.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权限修改此文章")
    
    update_data = article_data.model_dump(exclude_unset=True, exclude={"tag_ids"})
    
    if "content" in update_data and not update_data["content"]:
        del update_data["content"]
    
    if "content" in update_data:
        update_data["reading_time"] = calculate_reading_time(update_data["content"])
    
    for field, value in update_data.items():
        setattr(article, field, value)
    
    if article_data.tag_ids is not None:
        tags = db.query(Tag).filter(Tag.id.in_(article_data.tag_ids)).all()
        article.tags = tags
    
    db.commit()
    db.refresh(article)
    
    LogService.log_operation(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        action="更新",
        module="文章管理",
        description=f"更新文章: {article.title}",
        target_type="文章",
        target_id=article.id,
        request=request,
        status="success"
    )
    
    return ArticleResponse.model_validate(article)


@router.delete("/{article_id}")
async def delete_article(
    article_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    if not current_user.is_admin and article.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权限删除此文章")
    
    article_title = article.title
    db.delete(article)
    db.commit()
    
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
