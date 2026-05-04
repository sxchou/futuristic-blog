from typing import Optional, List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models import Article, Category, Tag, User
from app.utils import generate_slug, get_current_user
from app.utils.helpers import (
    generate_unique_slug, 
    translate_to_english, 
    generate_slug_from_text,
    generate_slug_with_fallback,
    find_similar_slug,
    calculate_similarity_score
)

router = APIRouter(prefix="/utils", tags=["Utils"])


def get_existing_slugs(db: Session, entity_type: str, exclude_id: Optional[int] = None) -> List[str]:
    if entity_type == "article":
        query = db.query(Article.slug)
        if exclude_id:
            query = query.filter(Article.id != exclude_id)
        return [r[0] for r in query.all() if r[0]]
    elif entity_type == "category":
        query = db.query(Category.slug)
        if exclude_id:
            query = query.filter(Category.id != exclude_id)
        return [r[0] for r in query.all() if r[0]]
    elif entity_type == "tag":
        query = db.query(Tag.slug)
        if exclude_id:
            query = query.filter(Tag.id != exclude_id)
        return [r[0] for r in query.all() if r[0]]
    return []


@router.post("/generate-slug")
async def api_generate_slug(
    text: str = Query(..., description="Text to generate slug from"),
    entity_type: Optional[str] = Query(None, description="Entity type: article, category, or tag"),
    exclude_id: Optional[int] = Query(None, description="ID to exclude from uniqueness check"),
    enable_similarity: bool = Query(False, description="Enable similarity matching for incomplete titles"),
    similarity_threshold: float = Query(0.6, description="Similarity threshold (0.0-1.0)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    import re
    has_chinese = bool(re.search(r'[\u4e00-\u9fff]', text))
    
    if has_chinese:
        translated = await translate_to_english(text)
        base_slug = generate_slug_from_text(translated)
    else:
        base_slug = generate_slug_from_text(text)
    
    if not base_slug:
        base_slug = "untitled"
    
    if not entity_type:
        return {
            "slug": base_slug,
            "is_unique": True,
            "source": "generated",
            "similarity_score": 0.0,
            "matched_slug": None
        }
    
    existing_slugs = get_existing_slugs(db, entity_type, exclude_id)
    
    if enable_similarity:
        result = await generate_slug_with_fallback(
            text=text,
            existing_slugs=existing_slugs,
            similarity_threshold=similarity_threshold
        )
        return {
            "slug": result['slug'],
            "is_unique": result['source'] == 'generated',
            "source": result['source'],
            "similarity_score": result['similarity_score'],
            "matched_slug": result['matched_slug'],
            "base_slug": base_slug
        }
    
    is_unique = base_slug not in existing_slugs
    final_slug = generate_unique_slug(base_slug, existing_slugs) if not is_unique else base_slug
    
    return {
        "slug": final_slug,
        "is_unique": is_unique,
        "base_slug": base_slug,
        "source": "generated",
        "similarity_score": 0.0,
        "matched_slug": None
    }


@router.get("/find-similar-slug")
async def api_find_similar_slug(
    text: str = Query(..., description="Text to find similar slug for"),
    entity_type: str = Query(..., description="Entity type: article, category, or tag"),
    threshold: float = Query(0.6, description="Similarity threshold (0.0-1.0)"),
    exclude_id: Optional[int] = Query(None, description="ID to exclude from search"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    import re
    has_chinese = bool(re.search(r'[\u4e00-\u9fff]', text))
    
    if has_chinese:
        translated = await translate_to_english(text)
        input_slug = generate_slug_from_text(translated)
    else:
        input_slug = generate_slug_from_text(text)
    
    if not input_slug:
        return {
            "input_slug": "untitled",
            "matched_slug": None,
            "similarity_score": 0.0,
            "found": False
        }
    
    existing_slugs = get_existing_slugs(db, entity_type, exclude_id)
    
    if not existing_slugs:
        return {
            "input_slug": input_slug,
            "matched_slug": None,
            "similarity_score": 0.0,
            "found": False,
            "existing_count": 0
        }
    
    matched_slug = find_similar_slug(input_slug, existing_slugs, threshold)
    
    if matched_slug:
        similarity = calculate_similarity_score(input_slug, matched_slug)
        return {
            "input_slug": input_slug,
            "matched_slug": matched_slug,
            "similarity_score": similarity,
            "found": True,
            "existing_count": len(existing_slugs)
        }
    
    return {
        "input_slug": input_slug,
        "matched_slug": None,
        "similarity_score": 0.0,
        "found": False,
        "existing_count": len(existing_slugs)
    }


@router.get("/check-slug")
async def check_slug_uniqueness(
    slug: str = Query(..., description="Slug to check"),
    entity_type: str = Query(..., description="Entity type: article, category, or tag"),
    exclude_id: Optional[int] = Query(None, description="ID to exclude from check"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
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
