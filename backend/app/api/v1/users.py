from typing import List
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models import User, UserProfile, AvatarType, OAuthConnection, Article, Comment, ArticleFile, EmailLog, OperationLog, LoginLog, AccessLog
from app.schemas import UserListItem, UserAdminUpdate, PaginatedResponse
from app.utils import get_current_user, get_password_hash
from app.services.log_service import LogService
from app.services.avatar_service import AvatarFileService

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("", response_model=PaginatedResponse)
async def get_users(
    page: int = 1,
    page_size: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="无权限查看用户列表")
    
    total = db.query(User).count()
    total_pages = (total + page_size - 1) // page_size
    users = db.query(User).order_by(User.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    
    items = []
    for user in users:
        profile = db.query(UserProfile).filter(UserProfile.user_id == user.id).first()
        item = UserListItem(
            id=user.id,
            username=user.username,
            email=user.email,
            avatar=user.avatar,
            avatar_type=profile.avatar_type.value if profile and profile.avatar_type else None,
            avatar_url=profile.avatar_url if profile else None,
            avatar_gradient=profile.default_avatar_gradient if profile else None,
            bio=user.bio,
            is_admin=user.is_admin,
            is_verified=user.is_verified,
            created_at=user.created_at
        )
        items.append(item)
    
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/{user_id}", response_model=UserListItem)
async def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="无权限查看用户信息")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return UserListItem.model_validate(user)


@router.put("/{user_id}", response_model=UserListItem)
async def update_user(
    user_id: int,
    user_data: UserAdminUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="无权限修改此用户")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user_data.username:
        existing = db.query(User).filter(User.username == user_data.username, User.id != user_id).first()
        if existing:
            raise HTTPException(status_code=400, detail="Username already exists")
        user.username = user_data.username
    
    if user_data.email:
        existing = db.query(User).filter(User.email == user_data.email, User.id != user_id).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email already exists")
        user.email = user_data.email
    
    if user_data.avatar is not None:
        user.avatar = user_data.avatar
    if user_data.bio is not None:
        user.bio = user_data.bio
    if user_data.is_admin is not None:
        user.is_admin = user_data.is_admin
    
    db.commit()
    db.refresh(user)
    
    LogService.log_operation(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        action="更新",
        module="用户管理",
        description=f"更新用户信息: {user.username}",
        target_type="用户",
        target_id=user.id,
        request=request,
        status="success"
    )
    
    return UserListItem.model_validate(user)


@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="无权限删除此用户")
    
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="不能删除自己")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    username = user.username
    
    user_profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
    avatar_url_to_delete = None
    if user_profile and user_profile.avatar_type == AvatarType.custom and user_profile.avatar_url:
        avatar_url_to_delete = user_profile.avatar_url
    
    db.query(OAuthConnection).filter(OAuthConnection.user_id == user_id).delete()
    
    db.query(Comment).filter(Comment.user_id == user_id).update({Comment.user_id: None, Comment.author_name: username})
    
    db.query(Article).filter(Article.author_id == user_id).update({Article.author_id: None})
    
    db.query(ArticleFile).filter(ArticleFile.uploaded_by == user_id).update({ArticleFile.uploaded_by: None})
    
    db.query(EmailLog).filter(EmailLog.user_id == user_id).update({EmailLog.user_id: None})
    
    db.query(OperationLog).filter(OperationLog.user_id == user_id).update({OperationLog.user_id: None})
    
    db.query(LoginLog).filter(LoginLog.user_id == user_id).update({LoginLog.user_id: None})
    
    db.query(AccessLog).filter(AccessLog.user_id == user_id).update({AccessLog.user_id: None})
    
    if user_profile:
        db.delete(user_profile)
    
    db.delete(user)
    db.commit()
    
    if avatar_url_to_delete:
        AvatarFileService.delete_avatar_file(
            avatar_url=avatar_url_to_delete,
            db=db,
            user=current_user,
            request=request,
            reason="user_deletion"
        )
    
    LogService.log_operation(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        action="删除",
        module="用户管理",
        description=f"删除用户: {username}",
        target_type="用户",
        target_id=user_id,
        request=request,
        status="success"
    )
    
    return {"message": "User deleted successfully"}


@router.post("/{user_id}/reset-password")
async def reset_user_password(
    user_id: int,
    new_password: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="无权限重置密码")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.hashed_password = get_password_hash(new_password)
    db.commit()
    
    LogService.log_operation(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        action="重置密码",
        module="用户管理",
        description=f"重置用户密码: {user.username}",
        target_type="用户",
        target_id=user.id,
        request=request,
        status="success"
    )
    
    return {"message": "Password reset successfully"}
