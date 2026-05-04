from typing import Optional
from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.utils import get_current_user
from app.models import User, Permission
from app.services.permission_service import PermissionService


def require_permission(permission_code: str):
    async def permission_checker(
        request: Request,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
    ):
        if PermissionService.check_super_admin(current_user, db):
            return current_user
        
        if not PermissionService.has_permission_strict(db, current_user.id, permission_code):
            permission = db.query(Permission).filter(Permission.code == permission_code).first()
            permission_name = permission.name if permission else permission_code
            raise HTTPException(
                status_code=403,
                detail=f"权限不足，需要「{permission_name}」权限"
            )
        return current_user
    return permission_checker


def require_any_permission(*permission_codes: str):
    async def permission_checker(
        request: Request,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
    ):
        if PermissionService.check_super_admin(current_user, db):
            return current_user
        
        permissions = PermissionService.get_user_permissions(db, current_user.id, strict_mode=True)
        if not any(code in permissions for code in permission_codes):
            perm_names = []
            for code in permission_codes:
                perm = db.query(Permission).filter(Permission.code == code).first()
                perm_names.append(perm.name if perm else code)
            raise HTTPException(
                status_code=403,
                detail=f"权限不足，需要以下任一权限: {', '.join(perm_names)}"
            )
        return current_user
    return permission_checker


def require_all_permissions(*permission_codes: str):
    async def permission_checker(
        request: Request,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
    ):
        if PermissionService.check_super_admin(current_user, db):
            return current_user
        
        permissions = PermissionService.get_user_permissions(db, current_user.id, strict_mode=True)
        if not all(code in permissions for code in permission_codes):
            perm_names = []
            for code in permission_codes:
                perm = db.query(Permission).filter(Permission.code == code).first()
                perm_names.append(perm.name if perm else code)
            raise HTTPException(
                status_code=403,
                detail=f"权限不足，需要所有权限: {', '.join(perm_names)}"
            )
        return current_user
    return permission_checker


def optional_permission(permission_code: str):
    async def permission_checker(
        request: Request,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
    ):
        has_perm = PermissionService.has_permission_strict(db, current_user.id, permission_code)
        request.state.has_permission = has_perm
        return current_user
    return permission_checker


class PermissionChecker:
    def __init__(self, db: Session, user_id: int):
        self.db = db
        self.user_id = user_id
    
    def check(self, permission_code: str) -> bool:
        return PermissionService.has_permission_strict(self.db, self.user_id, permission_code)
    
    def check_any(self, *permission_codes: str) -> bool:
        permissions = PermissionService.get_user_permissions(self.db, self.user_id, strict_mode=True)
        return any(code in permissions for code in permission_codes)
    
    def check_all(self, *permission_codes: str) -> bool:
        permissions = PermissionService.get_user_permissions(self.db, self.user_id, strict_mode=True)
        return all(code in permissions for code in permission_codes)
    
    def get_permissions(self) -> set:
        return PermissionService.get_user_permissions(self.db, self.user_id, strict_mode=True)


async def require_super_admin(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> User:
    if not PermissionService.check_super_admin(current_user, db):
        raise HTTPException(
            status_code=403,
            detail="此操作需要超级管理员权限"
        )
    return current_user


async def get_permission_checker(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> PermissionChecker:
    return PermissionChecker(db, current_user.id)
