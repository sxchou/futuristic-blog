from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import datetime, timedelta
from app.core.database import get_db
from app.models import OperationLog, LoginLog, AccessLog, UserProfile
from app.utils.auth import get_current_admin_user
from app.utils.timezone import get_now, get_today_start
from pydantic import BaseModel

router = APIRouter(prefix="/logs", tags=["Logs"])


class OperationLogItem(BaseModel):
    id: int
    username: Optional[str]
    user_id: Optional[int]
    avatar_type: Optional[str] = None
    avatar_url: Optional[str] = None
    avatar_gradient: Optional[list] = None
    oauth_avatar_url: Optional[str] = None
    action: str
    module: str
    description: Optional[str]
    target_type: Optional[str]
    target_id: Optional[int]
    request_method: Optional[str]
    request_url: Optional[str]
    ip_address: Optional[str]
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class LoginLogItem(BaseModel):
    id: int
    username: Optional[str]
    user_id: Optional[int]
    avatar_type: Optional[str] = None
    avatar_url: Optional[str] = None
    avatar_gradient: Optional[list] = None
    oauth_avatar_url: Optional[str] = None
    login_type: str
    ip_address: Optional[str]
    location: Optional[str]
    browser: Optional[str]
    os: Optional[str]
    device: Optional[str]
    status: str
    fail_reason: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class AccessLogItem(BaseModel):
    id: int
    username: Optional[str]
    request_method: Optional[str]
    request_path: Optional[str]
    response_status: Optional[int]
    response_time: Optional[float]
    ip_address: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class LogStats(BaseModel):
    total_operations: int
    total_logins: int
    total_access: int
    today_operations: int
    today_logins: int
    failed_logins: int


@router.get("/stats", response_model=LogStats)
async def get_log_stats(
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_admin_user)
):
    today_start = get_today_start()
    
    return {
        "total_operations": db.query(OperationLog).count(),
        "total_logins": db.query(LoginLog).count(),
        "total_access": db.query(AccessLog).count(),
        "today_operations": db.query(OperationLog).filter(OperationLog.created_at >= today_start).count(),
        "today_logins": db.query(LoginLog).filter(LoginLog.created_at >= today_start).count(),
        "failed_logins": db.query(LoginLog).filter(LoginLog.status == 'failed').count(),
    }


@router.get("/operations", response_model=dict)
async def get_operation_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    module: Optional[str] = None,
    action: Optional[str] = None,
    status: Optional[str] = None,
    username: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_admin_user)
):
    query = db.query(OperationLog)
    
    if module:
        query = query.filter(OperationLog.module == module)
    if action:
        query = query.filter(OperationLog.action == action)
    if status:
        query = query.filter(OperationLog.status == status)
    if username:
        query = query.filter(OperationLog.username.contains(username))
    if start_date:
        query = query.filter(OperationLog.created_at >= datetime.fromisoformat(start_date))
    if end_date:
        query = query.filter(OperationLog.created_at <= datetime.fromisoformat(end_date))
    
    total = query.count()
    logs = query.order_by(desc(OperationLog.created_at)).offset((page - 1) * page_size).limit(page_size).all()
    
    user_avatar_cache = {}
    items = []
    for log in logs:
        avatar_type = None
        avatar_url = None
        avatar_gradient = None
        oauth_avatar_url = None
        
        if log.user_id:
            if log.user_id not in user_avatar_cache:
                profile = db.query(UserProfile).filter(UserProfile.user_id == log.user_id).first()
                user_avatar_cache[log.user_id] = profile
            profile = user_avatar_cache.get(log.user_id)
            if profile:
                avatar_type = profile.avatar_type.value if profile.avatar_type else None
                avatar_url = profile.avatar_url
                avatar_gradient = profile.default_avatar_gradient
                oauth_avatar_url = profile.oauth_avatar_url
        
        items.append(OperationLogItem(
            id=log.id,
            username=log.username,
            user_id=log.user_id,
            avatar_type=avatar_type,
            avatar_url=avatar_url,
            avatar_gradient=avatar_gradient,
            oauth_avatar_url=oauth_avatar_url,
            action=log.action,
            module=log.module,
            description=log.description,
            target_type=log.target_type,
            target_id=log.target_id,
            request_method=log.request_method,
            request_url=log.request_url,
            ip_address=log.ip_address,
            status=log.status,
            created_at=log.created_at
        ))
    
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.get("/logins", response_model=dict)
async def get_login_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    login_type: Optional[str] = None,
    status: Optional[str] = None,
    username: Optional[str] = None,
    ip_address: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_admin_user)
):
    query = db.query(LoginLog)
    
    if login_type:
        query = query.filter(LoginLog.login_type == login_type)
    if status:
        query = query.filter(LoginLog.status == status)
    if username:
        query = query.filter(LoginLog.username.contains(username))
    if ip_address:
        query = query.filter(LoginLog.ip_address.contains(ip_address))
    if start_date:
        query = query.filter(LoginLog.created_at >= datetime.fromisoformat(start_date))
    if end_date:
        query = query.filter(LoginLog.created_at <= datetime.fromisoformat(end_date))
    
    total = query.count()
    logs = query.order_by(desc(LoginLog.created_at)).offset((page - 1) * page_size).limit(page_size).all()
    
    user_avatar_cache = {}
    items = []
    for log in logs:
        avatar_type = None
        avatar_url = None
        avatar_gradient = None
        oauth_avatar_url = None
        
        if log.user_id:
            if log.user_id not in user_avatar_cache:
                profile = db.query(UserProfile).filter(UserProfile.user_id == log.user_id).first()
                user_avatar_cache[log.user_id] = profile
            profile = user_avatar_cache.get(log.user_id)
            if profile:
                avatar_type = profile.avatar_type.value if profile.avatar_type else None
                avatar_url = profile.avatar_url
                avatar_gradient = profile.default_avatar_gradient
                oauth_avatar_url = profile.oauth_avatar_url
        
        items.append(LoginLogItem(
            id=log.id,
            username=log.username,
            user_id=log.user_id,
            avatar_type=avatar_type,
            avatar_url=avatar_url,
            avatar_gradient=avatar_gradient,
            oauth_avatar_url=oauth_avatar_url,
            login_type=log.login_type,
            ip_address=log.ip_address,
            location=log.location,
            browser=log.browser,
            os=log.os,
            device=log.device,
            status=log.status,
            fail_reason=log.fail_reason,
            created_at=log.created_at
        ))
    
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.get("/access", response_model=dict)
async def get_access_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    request_method: Optional[str] = None,
    username: Optional[str] = None,
    ip_address: Optional[str] = None,
    path: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_admin_user)
):
    query = db.query(AccessLog)
    
    if request_method:
        query = query.filter(AccessLog.request_method == request_method)
    if username:
        query = query.filter(AccessLog.username.contains(username))
    if ip_address:
        query = query.filter(AccessLog.ip_address.contains(ip_address))
    if path:
        query = query.filter(AccessLog.request_path.contains(path))
    if start_date:
        query = query.filter(AccessLog.created_at >= datetime.fromisoformat(start_date))
    if end_date:
        query = query.filter(AccessLog.created_at <= datetime.fromisoformat(end_date))
    
    total = query.count()
    logs = query.order_by(desc(AccessLog.created_at)).offset((page - 1) * page_size).limit(page_size).all()
    
    return {
        "items": [AccessLogItem.model_validate(log) for log in logs],
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.delete("/operations/clear")
async def clear_operation_logs(
    days: int = Query(30, ge=1),
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_admin_user)
):
    cutoff_date = get_now() - timedelta(days=days)
    deleted = db.query(OperationLog).filter(OperationLog.created_at < cutoff_date).delete()
    db.commit()
    return {"message": f"已删除 {deleted} 条操作日志"}


@router.delete("/logins/clear")
async def clear_login_logs(
    days: int = Query(30, ge=1),
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_admin_user)
):
    cutoff_date = get_now() - timedelta(days=days)
    deleted = db.query(LoginLog).filter(LoginLog.created_at < cutoff_date).delete()
    db.commit()
    return {"message": f"已删除 {deleted} 条登录日志"}


@router.delete("/access/clear")
async def clear_access_logs(
    days: int = Query(30, ge=1),
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_admin_user)
):
    cutoff_date = get_now() - timedelta(days=days)
    deleted = db.query(AccessLog).filter(AccessLog.created_at < cutoff_date).delete()
    db.commit()
    return {"message": f"已删除 {deleted} 条访问日志"}
