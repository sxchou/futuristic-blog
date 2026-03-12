from typing import List
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models import User
from app.schemas import UserListItem, UserAdminUpdate, PaginatedResponse
from app.utils import get_current_user, get_password_hash
from app.services.log_service import LogService

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
    
    items = [UserListItem.model_validate(user) for user in users]
    
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
    db.delete(user)
    db.commit()
    
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
