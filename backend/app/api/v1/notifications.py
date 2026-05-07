from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.core.database import get_db
from app.models import NotificationSettings, User
from app.schemas import NotificationSettingsUpdate, NotificationSettingsResponse
from app.utils.permissions import require_permission
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
    current_user: User = Depends(require_permission("notification.view"))
):
    return get_or_create_settings(db)


@router.put("/settings", response_model=NotificationSettingsResponse)
async def update_notification_settings(
    settings_data: NotificationSettingsUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("notification.edit"))
):
    settings = get_or_create_settings(db)
    
    changes = []
    field_names = {
        'notify_on_register': '新用户注册通知',
        'notify_on_comment': '新评论通知',
        'notify_on_like': '点赞通知',
        'notify_on_reply': '回复通知',
        'require_comment_audit': '评论审核'
    }
    
    update_count = 0
    last_field = None
    last_new_value = None
    
    if settings_data.notify_on_register is not None:
        if settings.notify_on_register != settings_data.notify_on_register:
            changes.append(f"{field_names['notify_on_register']}")
            update_count += 1
            last_field = field_names['notify_on_register']
            last_new_value = settings_data.notify_on_register
        settings.notify_on_register = settings_data.notify_on_register
    if settings_data.notify_on_comment is not None:
        if settings.notify_on_comment != settings_data.notify_on_comment:
            changes.append(f"{field_names['notify_on_comment']}")
            update_count += 1
            last_field = field_names['notify_on_comment']
            last_new_value = settings_data.notify_on_comment
        settings.notify_on_comment = settings_data.notify_on_comment
    if settings_data.notify_on_like is not None:
        if settings.notify_on_like != settings_data.notify_on_like:
            changes.append(f"{field_names['notify_on_like']}")
            update_count += 1
            last_field = field_names['notify_on_like']
            last_new_value = settings_data.notify_on_like
        settings.notify_on_like = settings_data.notify_on_like
    if settings_data.notify_on_reply is not None:
        if settings.notify_on_reply != settings_data.notify_on_reply:
            changes.append(f"{field_names['notify_on_reply']}")
            update_count += 1
            last_field = field_names['notify_on_reply']
            last_new_value = settings_data.notify_on_reply
        settings.notify_on_reply = settings_data.notify_on_reply
    if settings_data.require_comment_audit is not None:
        if settings.require_comment_audit != settings_data.require_comment_audit:
            changes.append(f"{field_names['require_comment_audit']}")
            update_count += 1
            last_field = field_names['require_comment_audit']
            last_new_value = settings_data.require_comment_audit
        settings.require_comment_audit = settings_data.require_comment_audit
    
    try:
        db.commit()
        db.refresh(settings)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="数据保存失败，请检查输入内容")
    
    if update_count == 0:
        description = "更新通知设置"
        action = "更新"
    elif update_count == 1:
        action = "开启" if last_new_value else "关闭"
        description = f"{action}通知设置: {last_field}"
    else:
        action = "更新"
        description = f"更新通知设置: {', '.join(changes)}"
    
    LogService.log_operation(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        action=action,
        module="通知管理",
        description=description,
        target_type="通知设置",
        target_id=settings.id,
        request=request,
        status="success"
    )
    
    return settings
