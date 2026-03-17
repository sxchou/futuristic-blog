import random
import hashlib
import os
import logging
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Request
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.models import UserProfile, AvatarType, User
from app.schemas import UserProfileResponse, UserProfileUpdate
from app.utils.auth import get_current_user
from app.services.log_service import LogService
from app.services.avatar_service import AvatarFileService

router = APIRouter(prefix="/user-profile", tags=["UserProfile"])
logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
MAX_FILE_SIZE = 5 * 1024 * 1024

GRADIENT_PRESETS = [
    ["#667eea", "#764ba2"],
    ["#f093fb", "#f5576c"],
    ["#4facfe", "#00f2fe"],
    ["#43e97b", "#38f9d7"],
    ["#fa709a", "#fee140"],
    ["#a8edea", "#fed6e3"],
    ["#ff9a9e", "#fecfef"],
    ["#ffecd2", "#fcb69f"],
    ["#a1c4fd", "#c2e9fb"],
    ["#d299c2", "#fef9d7"],
    ["#89f7fe", "#66a6ff"],
    ["#cd9cf2", "#f6f3ff"],
    ["#fddb92", "#d1fdff"],
    ["#96fbc4", "#f9f586"],
    ["#ff0844", "#ffb199"],
    ["#3f5efb", "#fc466b"],
    ["#11998e", "#38ef7d"],
    ["#ee0979", "#ff6a00"],
    ["#2193b0", "#6dd5ed"],
    ["#cc2b5e", "#753a88"],
    ["#42275a", "#734b6d"],
    ["#bdc3c7", "#2c3e50"],
    ["#1f4037", "#99f2c8"],
    ["#c33764", "#1d2671"],
    ["#00467f", "#a5cc82"],
]


def generate_gradient_from_username(username: str) -> list:
    hash_value = int(hashlib.md5(username.encode()).hexdigest(), 16)
    index = hash_value % len(GRADIENT_PRESETS)
    return GRADIENT_PRESETS[index]


def get_or_create_user_profile(db: Session, user_id: int, username: str) -> UserProfile:
    profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
    if not profile:
        gradient = generate_gradient_from_username(username)
        profile = UserProfile(
            user_id=user_id,
            avatar_type=AvatarType.default,
            default_avatar_gradient=gradient
        )
        db.add(profile)
        db.commit()
        db.refresh(profile)
    return profile


def validate_avatar_file(file: UploadFile) -> None:
    if not file.filename:
        raise HTTPException(status_code=400, detail="文件名不能为空")
    
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400, 
            detail=f"不支持的文件格式，仅支持: {', '.join(ALLOWED_EXTENSIONS)}"
        )


async def save_avatar_file(file: UploadFile, user_id: int) -> str:
    AvatarFileService.ensure_avatar_directory()
    
    ext = os.path.splitext(file.filename)[1].lower()
    import time
    timestamp = int(time.time() * 1000)
    filename = f"avatar_{user_id}_{timestamp}{ext}"
    
    avatar_path = AvatarFileService.get_avatar_base_path()
    file_path = avatar_path / filename
    
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="文件大小不能超过5MB")
    
    with open(file_path, "wb") as f:
        f.write(content)
    
    return f"/uploads/avatars/{filename}"


@router.get("", response_model=UserProfileResponse)
async def get_user_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    profile = get_or_create_user_profile(db, current_user.id, current_user.username)
    
    return {
        "id": profile.id,
        "user_id": profile.user_id,
        "username": current_user.username,
        "avatar_type": profile.avatar_type.value if profile.avatar_type else "default",
        "avatar_url": profile.avatar_url,
        "default_avatar_gradient": profile.default_avatar_gradient,
        "created_at": profile.created_at,
        "updated_at": profile.updated_at
    }


@router.post("/upload-avatar", response_model=UserProfileResponse)
async def upload_avatar(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    request: Request = None
):
    validate_avatar_file(file)
    
    profile = get_or_create_user_profile(db, current_user.id, current_user.username)
    
    old_avatar_url = profile.avatar_url if profile.avatar_type == AvatarType.custom else None
    
    try:
        avatar_url = await save_avatar_file(file, current_user.id)
        
        profile.avatar_type = AvatarType.custom
        profile.avatar_url = avatar_url
        db.commit()
        db.refresh(profile)
        
        if old_avatar_url:
            delete_success, delete_msg = AvatarFileService.delete_avatar_file(
                avatar_url=old_avatar_url,
                db=db,
                user=current_user,
                request=request,
                reason="avatar_update"
            )
            if not delete_success:
                logger.warning(f"Failed to delete old avatar after upload: {delete_msg}")
        
        LogService.log_operation(
            db=db,
            user_id=current_user.id,
            username=current_user.username,
            action="上传",
            module="用户头像",
            description="上传自定义头像",
            target_type="用户资料",
            target_id=profile.id,
            request=request,
            status="success"
        )
        
        return {
            "id": profile.id,
            "user_id": profile.user_id,
            "username": current_user.username,
            "avatar_type": profile.avatar_type.value,
            "avatar_url": profile.avatar_url,
            "default_avatar_gradient": profile.default_avatar_gradient,
            "created_at": profile.created_at,
            "updated_at": profile.updated_at
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to upload avatar for user {current_user.id}: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"头像上传失败: {str(e)}")


@router.post("/reset-avatar", response_model=UserProfileResponse)
async def reset_avatar(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    request: Request = None
):
    profile = get_or_create_user_profile(db, current_user.id, current_user.username)
    
    old_avatar_url = profile.avatar_url if profile.avatar_type == AvatarType.custom else None
    
    try:
        profile.avatar_type = AvatarType.default
        profile.avatar_url = None
        profile.default_avatar_gradient = generate_gradient_from_username(current_user.username)
        db.commit()
        db.refresh(profile)
        
        if old_avatar_url:
            delete_success, delete_msg = AvatarFileService.delete_avatar_file(
                avatar_url=old_avatar_url,
                db=db,
                user=current_user,
                request=request,
                reason="avatar_reset"
            )
            if not delete_success:
                logger.warning(f"Failed to delete old avatar after reset: {delete_msg}")
        
        LogService.log_operation(
            db=db,
            user_id=current_user.id,
            username=current_user.username,
            action="重置",
            module="用户头像",
            description="重置为默认头像",
            target_type="用户资料",
            target_id=profile.id,
            request=request,
            status="success"
        )
        
        return {
            "id": profile.id,
            "user_id": profile.user_id,
            "username": current_user.username,
            "avatar_type": profile.avatar_type.value,
            "avatar_url": profile.avatar_url,
            "default_avatar_gradient": profile.default_avatar_gradient,
            "created_at": profile.created_at,
            "updated_at": profile.updated_at
        }
        
    except Exception as e:
        logger.error(f"Failed to reset avatar for user {current_user.id}: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"头像重置失败: {str(e)}")


@router.get("/{user_id}", response_model=UserProfileResponse)
async def get_user_profile_by_id(
    user_id: int,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    profile = get_or_create_user_profile(db, user.id, user.username)
    
    return {
        "id": profile.id,
        "user_id": profile.user_id,
        "username": user.username,
        "avatar_type": profile.avatar_type.value if profile.avatar_type else "default",
        "avatar_url": profile.avatar_url,
        "default_avatar_gradient": profile.default_avatar_gradient,
        "created_at": profile.created_at,
        "updated_at": profile.updated_at
    }


@router.get("/storage/stats")
async def get_avatar_storage_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="需要管理员权限")
    
    stats = AvatarFileService.get_storage_stats()
    
    LogService.log_operation(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        action="查看",
        module="存储统计",
        description=f"查看头像存储统计: {stats['total_files']} 个文件, {stats['total_size_mb']} MB",
        target_type="系统",
        target_id=0,
        status="success"
    )
    
    return stats
