from typing import List
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.models import Announcement
from app.schemas.schemas import AnnouncementCreate, AnnouncementUpdate, AnnouncementResponse
from app.utils.auth import get_current_user
from app.services.log_service import LogService
from app.utils.cache import cache_manager

router = APIRouter(prefix="/announcements", tags=["Announcements"])

CACHE_NAME = "announcements"


def invalidate_announcements_cache():
    cache_manager.clear_cache(CACHE_NAME)


@router.get("", response_model=List[AnnouncementResponse])
def get_announcements(
    active_only: bool = False,
    db: Session = Depends(get_db)
):
    cache_key = f"announcements_{active_only}"
    cached = cache_manager.get(CACHE_NAME, cache_key)
    if cached:
        return cached
    
    query = db.query(Announcement)
    if active_only:
        query = query.filter(Announcement.is_active == True)
    announcements = query.order_by(Announcement.order, Announcement.created_at.desc()).all()
    result = [AnnouncementResponse.model_validate(a) for a in announcements]
    
    if result:
        cache_manager.set(CACHE_NAME, cache_key, [r.model_dump() for r in result])
    return result


@router.get("/{announcement_id}", response_model=AnnouncementResponse)
def get_announcement(
    announcement_id: int,
    db: Session = Depends(get_db)
):
    announcement = db.query(Announcement).filter(Announcement.id == announcement_id).first()
    if not announcement:
        raise HTTPException(status_code=404, detail="公告不存在")
    return announcement


@router.post("", response_model=AnnouncementResponse)
def create_announcement(
    announcement_data: AnnouncementCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="无权限创建公告")
    
    max_order = db.query(Announcement).order_by(Announcement.order.desc()).first()
    next_order = (max_order.order + 1) if max_order else 1
    
    order_value = announcement_data.order if announcement_data.order and announcement_data.order > 0 else next_order
    
    announcement = Announcement(
        title=announcement_data.title,
        content=announcement_data.content,
        type=announcement_data.type,
        is_active=announcement_data.is_active,
        order=order_value
    )
    db.add(announcement)
    db.commit()
    db.refresh(announcement)
    
    invalidate_announcements_cache()
    
    LogService.log_operation(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        action="创建",
        module="公告管理",
        description=f"创建公告: {announcement.title}",
        target_type="公告",
        target_id=announcement.id,
        request=request,
        status="success"
    )
    
    return announcement


@router.put("/{announcement_id}", response_model=AnnouncementResponse)
def update_announcement(
    announcement_id: int,
    announcement_data: AnnouncementUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="无权限修改公告")
    
    announcement = db.query(Announcement).filter(Announcement.id == announcement_id).first()
    if not announcement:
        raise HTTPException(status_code=404, detail="公告不存在")
    
    update_data = announcement_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(announcement, key, value)
    
    db.commit()
    db.refresh(announcement)
    
    invalidate_announcements_cache()
    
    LogService.log_operation(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        action="更新",
        module="公告管理",
        description=f"更新公告: {announcement.title}",
        target_type="公告",
        target_id=announcement.id,
        request=request,
        status="success"
    )
    
    return announcement


@router.delete("/{announcement_id}")
def delete_announcement(
    announcement_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="无权限删除公告")
    
    announcement = db.query(Announcement).filter(Announcement.id == announcement_id).first()
    if not announcement:
        raise HTTPException(status_code=404, detail="公告不存在")
    
    title = announcement.title
    db.delete(announcement)
    db.commit()
    
    invalidate_announcements_cache()
    
    LogService.log_operation(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        action="删除",
        module="公告管理",
        description=f"删除公告: {title}",
        target_type="公告",
        target_id=announcement_id,
        request=request,
        status="success"
    )
    
    return {"message": "公告删除成功"}
