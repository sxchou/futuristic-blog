from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models import NotificationSettings, User
from app.schemas import NotificationSettingsUpdate, NotificationSettingsResponse
from app.utils import get_current_admin_user
from app.services.log_service import LogService

router = APIRouter(prefix="/notifications", tags=["Notifications"])


def get_or_create_settings(db: Session) -> NotificationSettings:
    settings = db.query(NotificationSettings).first()
    if not settings:
        settings = NotificationSettings(
            notify_on_register=True,
            notify_on_comment=True,
            notify_on_like=True,
            notify_on_reply=True,
            require_comment_audit=False
        )
        db.add(settings)
        db.commit()
        db.refresh(settings)
    return settings


@router.get("/settings", response_model=NotificationSettingsResponse)
async def get_notification_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    return get_or_create_settings(db)


@router.put("/settings", response_model=NotificationSettingsResponse)
async def update_notification_settings(
    settings_data: NotificationSettingsUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    settings = get_or_create_settings(db)
    
    if settings_data.notify_on_register is not None:
        settings.notify_on_register = settings_data.notify_on_register
    if settings_data.notify_on_comment is not None:
        settings.notify_on_comment = settings_data.notify_on_comment
    if settings_data.notify_on_like is not None:
        settings.notify_on_like = settings_data.notify_on_like
    if settings_data.notify_on_reply is not None:
        settings.notify_on_reply = settings_data.notify_on_reply
    if settings_data.require_comment_audit is not None:
        settings.require_comment_audit = settings_data.require_comment_audit
    
    db.commit()
    db.refresh(settings)
    
    LogService.log_operation(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        action="更新",
        module="通知管理",
        description="更新通知设置",
        target_type="通知设置",
        target_id=settings.id,
        request=request,
        status="success"
    )
    
    return settings
