from typing import List
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.database import get_db
from app.models import Category, Article
from app.schemas import CategoryCreate, CategoryUpdate, CategoryResponse
from app.utils import get_current_user
from app.utils.permissions import require_permission
from app.utils.helpers import generate_slug, generate_unique_slug
from app.services.log_service import LogService
from app.utils.cache import cache_manager

router = APIRouter(prefix="/categories", tags=["Categories"])

CACHE_NAME = "categories"


def invalidate_categories_cache():
    cache_manager.clear_cache(CACHE_NAME)


@router.get("", response_model=List[CategoryResponse])
async def get_categories(db: Session = Depends(get_db)):
    cache_key = "all_categories"
    cached = cache_manager.get(CACHE_NAME, cache_key)
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
    
    cache_manager.set(CACHE_NAME, cache_key, result)
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
    current_user = Depends(require_permission("category.create"))
):
    existing_name = db.query(Category).filter(Category.name == category_data.name).first()
    if existing_name:
        raise HTTPException(status_code=400, detail="分类名称已存在")
    
    slug = category_data.slug
    if not slug or not slug.strip():
        slug = await generate_slug(category_data.name)
        existing_slugs = [r[0] for r in db.query(Category.slug).all()]
        slug = generate_unique_slug(slug, existing_slugs)
    else:
        existing_slug = db.query(Category).filter(Category.slug == slug).first()
        if existing_slug:
            raise HTTPException(status_code=400, detail="Slug已存在")
    
    new_category = Category(
        name=category_data.name,
        slug=slug,
        description=category_data.description,
        icon=category_data.icon,
        color=category_data.color,
        order=category_data.order
    )
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
    current_user = Depends(require_permission("category.edit"))
):
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
    current_user = Depends(require_permission("category.delete"))
):
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    article_count = db.query(func.count(Article.id)).filter(
        Article.category_id == category.id
    ).scalar()
    
    if article_count > 0:
        raise HTTPException(
            status_code=400, 
            detail=f"此分类无法删除，因为它当前被 {article_count} 篇文章使用。请先将这些文章重新分配到其他分类，或移除分类关联后再删除。"
        )
    
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
