from typing import List
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.database import get_db
from app.models import Tag, Article, article_tags
from app.schemas import TagCreate, TagUpdate, TagResponse
from app.utils import get_current_user
from app.utils.helpers import generate_slug, generate_unique_slug
from app.services.log_service import LogService
from app.utils.cache import cache_manager

router = APIRouter(prefix="/tags", tags=["Tags"])

CACHE_NAME = "tags"


def invalidate_tags_cache():
    cache_manager.clear_cache(CACHE_NAME)


@router.get("", response_model=List[TagResponse])
async def get_tags(db: Session = Depends(get_db)):
    cache_key = "all_tags"
    cached = cache_manager.get(CACHE_NAME, cache_key)
    if cached:
        return cached
    
    tags = db.query(Tag).all()
    
    if not tags:
        return []
    
    tag_ids = [t.id for t in tags]
    article_counts = dict(
        db.query(
            article_tags.c.tag_id,
            func.count(article_tags.c.article_id)
        ).filter(
            article_tags.c.tag_id.in_(tag_ids)
        ).group_by(article_tags.c.tag_id).all()
    )
    
    result = []
    for tag in tags:
        tag_response = TagResponse.model_validate(tag)
        tag_response.article_count = article_counts.get(tag.id, 0)
        result.append(tag_response)
    
    cache_manager.set(CACHE_NAME, cache_key, result)
    return result


@router.get("/{tag_id}", response_model=TagResponse)
async def get_tag(tag_id: int, db: Session = Depends(get_db)):
    tag = db.query(Tag).filter(Tag.id == tag_id).first()
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    
    article_count = db.query(func.count(article_tags.c.article_id)).filter(
        article_tags.c.tag_id == tag.id
    ).scalar()
    
    tag_response = TagResponse.model_validate(tag)
    tag_response.article_count = article_count
    return tag_response


@router.post("", response_model=TagResponse)
async def create_tag(
    tag_data: TagCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="无权限创建标签")
    
    existing_name = db.query(Tag).filter(Tag.name == tag_data.name).first()
    if existing_name:
        raise HTTPException(status_code=400, detail="标签名称已存在")
    
    slug = tag_data.slug
    if not slug or not slug.strip():
        slug = generate_slug(tag_data.name)
        existing_slugs = [r[0] for r in db.query(Tag.slug).all()]
        slug = generate_unique_slug(slug, existing_slugs)
    else:
        existing_slug = db.query(Tag).filter(Tag.slug == slug).first()
        if existing_slug:
            raise HTTPException(status_code=400, detail="Slug已存在")
    
    new_tag = Tag(
        name=tag_data.name,
        slug=slug,
        color=tag_data.color
    )
    db.add(new_tag)
    db.commit()
    db.refresh(new_tag)
    
    invalidate_tags_cache()
    
    LogService.log_operation(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        action="创建",
        module="标签管理",
        description=f"创建标签: {new_tag.name}",
        target_type="标签",
        target_id=new_tag.id,
        request=request,
        status="success"
    )
    
    return TagResponse.model_validate(new_tag)


@router.put("/{tag_id}", response_model=TagResponse)
async def update_tag(
    tag_id: int,
    tag_data: TagUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="无权限修改此标签")
    
    tag = db.query(Tag).filter(Tag.id == tag_id).first()
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    
    update_data = tag_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(tag, field, value)
    
    db.commit()
    db.refresh(tag)
    
    invalidate_tags_cache()
    
    LogService.log_operation(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        action="更新",
        module="标签管理",
        description=f"更新标签: {tag.name}",
        target_type="标签",
        target_id=tag.id,
        request=request,
        status="success"
    )
    
    return TagResponse.model_validate(tag)


@router.delete("/{tag_id}")
async def delete_tag(
    tag_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="无权限删除此标签")
    
    tag = db.query(Tag).filter(Tag.id == tag_id).first()
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    
    article_count = db.query(func.count(article_tags.c.article_id)).filter(
        article_tags.c.tag_id == tag.id
    ).scalar()
    
    if article_count > 0:
        raise HTTPException(
            status_code=400, 
            detail=f"此标签无法删除，因为它当前被 {article_count} 篇文章使用。请先将这些文章的标签关联移除后再删除。"
        )
    
    tag_name = tag.name
    db.delete(tag)
    db.commit()
    
    invalidate_tags_cache()
    
    LogService.log_operation(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        action="删除",
        module="标签管理",
        description=f"删除标签: {tag_name}",
        target_type="标签",
        target_id=tag_id,
        request=request,
        status="success"
    )
    
    return {"message": "Tag deleted successfully"}
