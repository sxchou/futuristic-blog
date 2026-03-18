from typing import List
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.database import get_db
from app.models import Category, Article
from app.schemas import CategoryCreate, CategoryUpdate, CategoryResponse
from app.utils import get_current_user
from app.services.log_service import LogService
from app.utils.cache import cache

router = APIRouter(prefix="/categories", tags=["Categories"])

CATEGORIES_CACHE_KEY = "categories:all"
CATEGORIES_CACHE_TTL = 120


def invalidate_categories_cache():
    cache.delete(CATEGORIES_CACHE_KEY)


@router.get("", response_model=List[CategoryResponse])
async def get_categories(db: Session = Depends(get_db)):
    cached = cache.get(CATEGORIES_CACHE_KEY)
    if cached:
        return cached
    
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
    
    cache.set(CATEGORIES_CACHE_KEY, result, CATEGORIES_CACHE_TTL)
    return result


@router.get("/{category_id}", response_model=CategoryResponse)
async def get_category(category_id: int, db: Session = Depends(get_db)):
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    article_count = db.query(func.count(Article.id)).filter(
        Article.category_id == category.id,
        Article.is_published == True
    ).scalar()
    
    cat_response = CategoryResponse.model_validate(category)
    cat_response.article_count = article_count
    return cat_response


@router.post("", response_model=CategoryResponse)
async def create_category(
    category_data: CategoryCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="无权限创建分类")
    
    existing = db.query(Category).filter(
        (Category.name == category_data.name) | (Category.slug == category_data.slug)
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Category name or slug already exists")
    
    new_category = Category(**category_data.model_dump())
    db.add(new_category)
    db.commit()
    db.refresh(new_category)
    
    invalidate_categories_cache()
    
    LogService.log_operation(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        action="创建",
        module="分类管理",
        description=f"创建分类: {new_category.name}",
        target_type="分类",
        target_id=new_category.id,
        request=request,
        status="success"
    )
    
    return CategoryResponse.model_validate(new_category)


@router.put("/{category_id}", response_model=CategoryResponse)
async def update_category(
    category_id: int,
    category_data: CategoryUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="无权限修改此分类")
    
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    update_data = category_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(category, field, value)
    
    db.commit()
    db.refresh(category)
    
    invalidate_categories_cache()
    
    LogService.log_operation(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        action="更新",
        module="分类管理",
        description=f"更新分类: {category.name}",
        target_type="分类",
        target_id=category.id,
        request=request,
        status="success"
    )
    
    return CategoryResponse.model_validate(category)


@router.delete("/{category_id}")
async def delete_category(
    category_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="无权限删除此分类")
    
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    category_name = category.name
    db.delete(category)
    db.commit()
    
    invalidate_categories_cache()
    
    LogService.log_operation(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        action="删除",
        module="分类管理",
        description=f"删除分类: {category_name}",
        target_type="分类",
        target_id=category_id,
        request=request,
        status="success"
    )
    
    return {"message": "Category deleted successfully"}
