﻿from typing import List
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models import Resource
from app.schemas import ResourceCreate, ResourceUpdate, ResourceResponse
from app.utils import get_current_user
from app.services.log_service import LogService

router = APIRouter(prefix="/resources", tags=["Resources"])


@router.get("", response_model=List[ResourceResponse])
async def get_resources(db: Session = Depends(get_db)):
    resources = db.query(Resource).filter(Resource.is_active == True).order_by(Resource.order).all()
    return [ResourceResponse.model_validate(r) for r in resources]


@router.get("/admin", response_model=List[ResourceResponse])
async def get_admin_resources(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="无权限访问")
    resources = db.query(Resource).order_by(Resource.order).all()
    return [ResourceResponse.model_validate(r) for r in resources]


@router.post("", response_model=ResourceResponse)
async def create_resource(
    resource_data: ResourceCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="无权限创建资源")
    
    new_resource = Resource(**resource_data.model_dump())
    db.add(new_resource)
    db.commit()
    db.refresh(new_resource)
    
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
    current_user = Depends(get_current_user)
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="无权限修改此资源")
    
    resource = db.query(Resource).filter(Resource.id == resource_id).first()
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")
    
    update_data = resource_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(resource, field, value)
    
    db.commit()
    db.refresh(resource)
    
    LogService.log_operation(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        action="更新",
        module="资源管理",
        description=f"更新资源: {resource.title}",
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
    current_user = Depends(get_current_user)
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="无权限删除此资源")
    
    resource = db.query(Resource).filter(Resource.id == resource_id).first()
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")
    
    resource_title = resource.title
    db.delete(resource)
    db.commit()
    
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
