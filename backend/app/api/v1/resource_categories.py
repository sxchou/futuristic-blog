from typing import List
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models import ResourceCategory, Resource
from app.schemas import ResourceCategoryCreate, ResourceCategoryUpdate, ResourceCategoryResponse
from app.utils import get_current_user
from app.services.log_service import LogService
from app.utils.cache import cache_manager

router = APIRouter(prefix="/resource-categories", tags=["Resource Categories"])

CACHE_NAME = "resource_categories"


def invalidate_resource_categories_cache():
    cache_manager.clear_cache(CACHE_NAME)


@router.get("", response_model=List[ResourceCategoryResponse])
async def get_categories(db: Session = Depends(get_db)):
    cache_key = "all_categories"
    cached = cache_manager.get(CACHE_NAME, cache_key)
    if cached:
        return cached
    
    categories = db.query(ResourceCategory).order_by(ResourceCategory.order).all()
    result = [ResourceCategoryResponse.model_validate(c).model_dump() for c in categories]
    
    cache_manager.set(CACHE_NAME, cache_key, result)
    return result


@router.post("", response_model=ResourceCategoryResponse)
async def create_category(
    category_data: ResourceCategoryCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="无权限创建资源分类")
    
    existing = db.query(ResourceCategory).filter(ResourceCategory.slug == category_data.slug).first()
    if existing:
        raise HTTPException(status_code=400, detail="分类标识已存在")
    
    new_category = ResourceCategory(**category_data.model_dump())
    db.add(new_category)
    db.commit()
    db.refresh(new_category)
    
    invalidate_resource_categories_cache()
    
    LogService.log_operation(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        action="创建",
        module="资源分类管理",
        description=f"创建资源分类: {new_category.name}",
        target_type="资源分类",
        target_id=new_category.id,
        request=request,
        status="success"
    )
    
    return ResourceCategoryResponse.model_validate(new_category)


@router.put("/{category_id}", response_model=ResourceCategoryResponse)
async def update_category(
    category_id: int,
    category_data: ResourceCategoryUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="无权限修改此资源分类")
    
    category = db.query(ResourceCategory).filter(ResourceCategory.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="资源分类不存在")
    
    if category_data.slug:
        existing = db.query(ResourceCategory).filter(
            ResourceCategory.slug == category_data.slug,
            ResourceCategory.id != category_id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="分类标识已存在")
    
    update_data = category_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(category, field, value)
    
    db.commit()
    db.refresh(category)
    
    invalidate_resource_categories_cache()
    
    LogService.log_operation(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        action="更新",
        module="资源分类管理",
        description=f"更新资源分类: {category.name}",
        target_type="资源分类",
        target_id=category.id,
        request=request,
        status="success"
    )
    
    return ResourceCategoryResponse.model_validate(category)


@router.delete("/{category_id}")
async def delete_category(
    category_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="无权限删除此资源分类")
    
    category = db.query(ResourceCategory).filter(ResourceCategory.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="资源分类不存在")
    
    resource_count = db.query(Resource).filter(Resource.category_id == category_id).count()
    if resource_count > 0:
        raise HTTPException(status_code=400, detail=f"该分类下有 {resource_count} 个资源，无法删除")
    
    category_name = category.name
    db.delete(category)
    db.commit()
    
    invalidate_resource_categories_cache()
    
    LogService.log_operation(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        action="删除",
        module="资源分类管理",
        description=f"删除资源分类: {category_name}",
        target_type="资源分类",
        target_id=category_id,
        request=request,
        status="success"
    )
    
    return {"message": "资源分类已删除"}


@router.post("/reorder")
async def reorder_categories(
    order_data: List[dict],
    request: Request,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="无权限排序资源分类")
    
    for item in order_data:
        category = db.query(ResourceCategory).filter(ResourceCategory.id == item['id']).first()
        if category:
            category.order = item['order']
    
    db.commit()
    
    LogService.log_operation(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        action="排序",
        module="资源分类管理",
        description="重新排序资源分类",
        target_type="资源分类",
        target_id=0,
        request=request,
        status="success"
    )
    
    return {"message": "排序已更新"}
