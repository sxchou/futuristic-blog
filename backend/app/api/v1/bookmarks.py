from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.core.database import get_db
from app.models import Article, ArticleBookmark, User
from app.schemas import BookmarkResponse, ArticleListItem, PaginatedResponse
from app.utils.auth import get_current_user
from typing import List

router = APIRouter(prefix="/bookmarks", tags=["bookmarks"])


@router.get("/ids", response_model=List[int])
async def get_bookmarked_article_ids(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    bookmarks = db.query(ArticleBookmark.article_id).filter(
        ArticleBookmark.user_id == current_user.id
    ).all()
    
    return [b[0] for b in bookmarks]


@router.get("/", response_model=PaginatedResponse)
async def get_user_bookmarks(
    page: int = 1,
    page_size: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(ArticleBookmark).filter(
        ArticleBookmark.user_id == current_user.id
    ).order_by(ArticleBookmark.created_at.desc())
    
    total = query.count()
    bookmarks = query.offset((page - 1) * page_size).limit(page_size).all()
    
    articles = []
    for bookmark in bookmarks:
        article = bookmark.article
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
                author=article.author,
                is_bookmarked=True,
                bookmarked_at=bookmark.created_at
            ))
    
    return PaginatedResponse(
        items=articles,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size
    )


@router.post("/{article_id}", response_model=BookmarkResponse)
async def toggle_bookmark(
    article_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    existing_bookmark = db.query(ArticleBookmark).filter(
        and_(
            ArticleBookmark.article_id == article_id,
            ArticleBookmark.user_id == current_user.id
        )
    ).first()
    
    if existing_bookmark:
        db.delete(existing_bookmark)
        is_bookmarked = False
    else:
        new_bookmark = ArticleBookmark(
            article_id=article_id,
            user_id=current_user.id
        )
        db.add(new_bookmark)
        is_bookmarked = True
    
    db.commit()
    
    bookmark_count = db.query(ArticleBookmark).filter(
        ArticleBookmark.article_id == article_id
    ).count()
    
    return BookmarkResponse(
        article_id=article_id,
        is_bookmarked=is_bookmarked,
        bookmark_count=bookmark_count
    )


@router.get("/{article_id}", response_model=BookmarkResponse)
async def get_bookmark_status(
    article_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    existing_bookmark = db.query(ArticleBookmark).filter(
        and_(
            ArticleBookmark.article_id == article_id,
            ArticleBookmark.user_id == current_user.id
        )
    ).first()
    
    bookmark_count = db.query(ArticleBookmark).filter(
        ArticleBookmark.article_id == article_id
    ).count()
    
    return BookmarkResponse(
        article_id=article_id,
        is_bookmarked=existing_bookmark is not None,
        bookmark_count=bookmark_count
    )
