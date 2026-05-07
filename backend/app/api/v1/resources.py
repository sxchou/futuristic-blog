from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.core.database import get_db
from app.models import Resource, ResourceCategory
from app.schemas import ResourceCreate, ResourceUpdate, ResourceResponse
from app.utils import get_current_user
from app.utils.permissions import require_permission
from app.services.log_service import LogService
from app.utils.cache import cache_manager

router = APIRouter(prefix="/resources", tags=["Resources"])

CACHE_NAME = "resources"


def invalidate_resources_cache():
    cache_manager.clear_cache(CACHE_NAME)


@router.get("/categories")
async def get_resource_categories(db: Session = Depends(get_db)):
    cache_key = "categories"
    cached = cache_manager.get(CACHE_NAME, cache_key)
    if cached:
        return cached
    
    categories = db.query(ResourceCategory).filter(ResourceCategory.is_active == True).order_by(ResourceCategory.order).all()
    result = [{"id": c.id, "name": c.name, "slug": c.slug, "icon": c.icon} for c in categories]
    
    cache_manager.set(CACHE_NAME, cache_key, result)
    return result


@router.get("/check-unique")
async def check_unique(
    field: str = Query(..., description="Field to check: 'title' or 'url'"),
    value: str = Query(..., description="Value to check"),
    exclude_id: Optional[int] = Query(None, description="Resource ID to exclude (for updates)"),
    db: Session = Depends(get_db)
):
    if field not in ["title", "url"]:
        raise HTTPException(status_code=400, detail="Invalid field. Must be 'title' or 'url'")
    
    query = db.query(Resource)
    if field == "title":
        query = query.filter(Resource.title == value)
    else:
        query = query.filter(Resource.url == value)
    
    if exclude_id:
        query = query.filter(Resource.id != exclude_id)
    
    exists = query.first() is not None
    return {"exists": exists, "field": field, "value": value}


@router.get("", response_model=List[ResourceResponse])
async def get_resources(db: Session = Depends(get_db)):
    cache_key = "active_resources"
    cached = cache_manager.get(CACHE_NAME, cache_key)
    if cached:
        return cached
    
    resources = db.query(Resource).filter(Resource.is_active == True).order_by(Resource.order, Resource.id).all()
    result = [ResourceResponse.model_validate(r) for r in resources]
    
    cache_manager.set(CACHE_NAME, cache_key, [r.model_dump() for r in result])
    return result


@router.get("/admin", response_model=List[ResourceResponse])
async def get_admin_resources(
    db: Session = Depends(get_db),
    current_user = Depends(require_permission("resource.view"))
):
    resources = db.query(Resource).order_by(Resource.order, Resource.id).all()
    return [ResourceResponse.model_validate(r) for r in resources]


@router.post("", response_model=ResourceResponse)
async def create_resource(
    resource_data: ResourceCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user = Depends(require_permission("resource.create"))
):
    resource_dict = resource_data.model_dump()
    
    existing_title = db.query(Resource).filter(Resource.title == resource_dict.get('title')).first()
    if existing_title:
        raise HTTPException(status_code=400, detail="资源标题已存在，请使用其他标题")
    
    existing_url = db.query(Resource).filter(Resource.url == resource_dict.get('url')).first()
    if existing_url:
        raise HTTPException(status_code=400, detail="资源链接已存在，请使用其他链接")
    
    max_order = db.query(Resource).order_by(Resource.order.desc()).first()
    next_order = (max_order.order + 1) if max_order else 1
    
    if resource_dict.get('order', 0) == 0:
        resource_dict['order'] = next_order
    
    if resource_dict.get('category_id'):
        cat = db.query(ResourceCategory).filter(ResourceCategory.id == resource_dict['category_id']).first()
        if cat:
            resource_dict['category'] = cat.name
    elif resource_dict.get('category') is None:
        resource_dict['category'] = ''
    
    try:
        new_resource = Resource(**resource_dict)
        db.add(new_resource)
        db.commit()
        db.refresh(new_resource)
    except IntegrityError as e:
        db.rollback()
        error_msg = str(e.orig) if hasattr(e, 'orig') else str(e)
        if 'title' in error_msg.lower() or 'uq_resource' in error_msg.lower():
            raise HTTPException(status_code=400, detail="资源标题已存在，请使用其他标题")
        elif 'url' in error_msg.lower():
            raise HTTPException(status_code=400, detail="资源链接已存在，请使用其他链接")
        else:
            raise HTTPException(status_code=400, detail="数据保存失败，请检查输入内容")
    
    invalidate_resources_cache()
    
    LogService.log_operation(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        action="创建",
        module="资源管理",
        description=f"创建资源: {new_resource.title}",
        target_type="资源",
        target_id=new_resource.id,
        request=request,
        status="success"
    )
    
    return ResourceResponse.model_validate(new_resource)


@router.put("/{resource_id}", response_model=ResourceResponse)
async def update_resource(
    resource_id: int,
    resource_data: ResourceUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user = Depends(require_permission("resource.edit"))
):
    resource = db.query(Resource).filter(Resource.id == resource_id).first()
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")
    
    old_is_active = resource.is_active
    update_data = resource_data.model_dump(exclude_unset=True)
    
    if 'title' in update_data:
        existing_title = db.query(Resource).filter(
            Resource.title == update_data['title'],
            Resource.id != resource_id
        ).first()
        if existing_title:
            raise HTTPException(status_code=400, detail="资源标题已存在，请使用其他标题")
    
    if 'url' in update_data:
        existing_url = db.query(Resource).filter(
            Resource.url == update_data['url'],
            Resource.id != resource_id
        ).first()
        if existing_url:
            raise HTTPException(status_code=400, detail="资源链接已存在，请使用其他链接")
    
    if 'category_id' in update_data:
        if update_data['category_id']:
            cat = db.query(ResourceCategory).filter(ResourceCategory.id == update_data['category_id']).first()
            if cat:
                update_data['category'] = cat.name
        else:
            update_data['category'] = ''
    
    for field, value in update_data.items():
        setattr(resource, field, value)
    
    try:
        db.commit()
        db.refresh(resource)
    except IntegrityError as e:
        db.rollback()
        error_msg = str(e.orig) if hasattr(e, 'orig') else str(e)
        if 'title' in error_msg.lower() or 'uq_resource' in error_msg.lower():
            raise HTTPException(status_code=400, detail="资源标题已存在，请使用其他标题")
        elif 'url' in error_msg.lower():
            raise HTTPException(status_code=400, detail="资源链接已存在，请使用其他链接")
        else:
            raise HTTPException(status_code=400, detail="数据保存失败，请检查输入内容")
    
    invalidate_resources_cache()
    
    description = f"更新资源: {resource.title}"
    action = "更新"
    
    if 'is_active' in update_data and len(update_data) == 1:
        if old_is_active != resource.is_active:
            if resource.is_active:
                description = f"启用资源: {resource.title}"
                action = "启用"
            else:
                description = f"禁用资源: {resource.title}"
                action = "禁用"
    
    LogService.log_operation(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        action=action,
        module="资源管理",
        description=description,
        target_type="资源",
        target_id=resource.id,
        request=request,
        status="success"
    )
    
    return ResourceResponse.model_validate(resource)


@router.delete("/{resource_id}")
async def delete_resource(
    resource_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user = Depends(require_permission("resource.delete"))
):
    resource = db.query(Resource).filter(Resource.id == resource_id).first()
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")
    
    resource_title = resource.title
    db.delete(resource)
    db.commit()
    
    invalidate_resources_cache()
    
    LogService.log_operation(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        action="删除",
        module="资源管理",
        description=f"删除资源: {resource_title}",
        target_type="资源",
        target_id=resource_id,
        request=request,
        status="success"
    )
    
    return {"message": "Resource deleted successfully"}
