from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models import Article, Category, Tag
from app.utils import generate_slug
from app.utils.helpers import generate_unique_slug

router = APIRouter(prefix="/utils", tags=["Utils"])


@router.post("/generate-slug")
async def api_generate_slug(
    text: str = Query(..., description="Text to generate slug from"),
    entity_type: Optional[str] = Query(None, description="Entity type: article, category, or tag"),
    exclude_id: Optional[int] = Query(None, description="ID to exclude from uniqueness check"),
    db: Session = Depends(get_db)
):
    base_slug = generate_slug(text)
    
    if not base_slug:
        return {"slug": "untitled", "is_unique": True}
    
    if not entity_type:
        return {"slug": base_slug, "is_unique": True}
    
    existing_slugs = []
    
    if entity_type == "article":
        query = db.query(Article.slug)
        if exclude_id:
            query = query.filter(Article.id != exclude_id)
        existing_slugs = [r[0] for r in query.all()]
    elif entity_type == "category":
        query = db.query(Category.slug)
        if exclude_id:
            query = query.filter(Category.id != exclude_id)
        existing_slugs = [r[0] for r in query.all()]
    elif entity_type == "tag":
        query = db.query(Tag.slug)
        if exclude_id:
            query = query.filter(Tag.id != exclude_id)
        existing_slugs = [r[0] for r in query.all()]
    
    is_unique = base_slug not in existing_slugs
    final_slug = generate_unique_slug(base_slug, existing_slugs) if not is_unique else base_slug
    
    return {
        "slug": final_slug,
        "is_unique": is_unique,
        "base_slug": base_slug
    }


@router.get("/check-slug")
async def check_slug_uniqueness(
    slug: str = Query(..., description="Slug to check"),
    entity_type: str = Query(..., description="Entity type: article, category, or tag"),
    exclude_id: Optional[int] = Query(None, description="ID to exclude from check"),
    db: Session = Depends(get_db)
):
    exists = False
    
    if entity_type == "article":
        query = db.query(Article).filter(Article.slug == slug)
        if exclude_id:
            query = query.filter(Article.id != exclude_id)
        exists = query.first() is not None
    elif entity_type == "category":
        query = db.query(Category).filter(Category.slug == slug)
        if exclude_id:
            query = query.filter(Category.id != exclude_id)
        exists = query.first() is not None
    elif entity_type == "tag":
        query = db.query(Tag).filter(Tag.slug == slug)
        if exclude_id:
            query = query.filter(Tag.id != exclude_id)
        exists = query.first() is not None
    
    return {
        "slug": slug,
        "is_unique": not exists,
        "exists": exists
    }
