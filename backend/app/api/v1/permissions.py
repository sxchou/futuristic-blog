from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.utils import get_current_user
from app.utils.permissions import require_permission, require_super_admin as require_super_admin_dep
from app.models import User, Role, Permission, user_roles, role_permissions, PermissionChangeLog
from app.schemas.schemas import (
    PermissionCreate, PermissionUpdate, PermissionResponse,
    RoleCreate, RoleUpdate, RoleResponse,
    UserRoleAssign, UserRoleRemove, UserWithRolesResponse,
    PermissionTreeResponse, RolePermissionUpdate,
    PermissionChangeLogResponse, RoleTemplateCreate,
    PermissionExport, PermissionImport
)
from app.services.permission_service import PermissionService
from app.services.log_service import LogService
import json

router = APIRouter(prefix="/permissions", tags=["permissions"])


def get_client_ip(request: Request) -> Optional[str]:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else None


@router.get("", response_model=List[PermissionResponse])
async def get_permissions(
    module: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("permission.view"))
):
    
    query = db.query(Permission)
    
    if module:
        query = query.filter(Permission.module == module)
    if is_active is not None:
        query = query.filter(Permission.is_active == is_active)
    
    permissions = query.order_by(Permission.module, Permission.action).all()
    return permissions


@router.get("/tree", response_model=PermissionTreeResponse)
async def get_permission_tree(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("role.view"))
):
    
    tree = PermissionService.get_permission_tree(db)
    return PermissionTreeResponse(**tree)


@router.post("", response_model=PermissionResponse)
async def create_permission(
    permission_data: PermissionCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin_dep)
):
    
    existing = db.query(Permission).filter(
        Permission.code == permission_data.code
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="权限代码已存在")
    
    permission = Permission(**permission_data.model_dump())
    db.add(permission)
    db.commit()
    db.refresh(permission)
    
    PermissionService.log_permission_change(
        db=db,
        operator_id=current_user.id,
        operator_name=current_user.username,
        target_type="permission",
        target_id=permission.id,
        target_name=permission.name,
        action="create",
        old_value=None,
        new_value=json.dumps(permission_data.model_dump(), ensure_ascii=False),
        description=f"创建权限: {permission.name}",
        ip_address=get_client_ip(request)
    )
    
    LogService.log_operation(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        action="create",
        module="permission",
        description=f"创建权限: {permission.name}",
        target_type="permission",
        target_id=permission.id,
        request=request
    )
    
    return permission


@router.put("/{permission_id}", response_model=PermissionResponse)
async def update_permission(
    permission_id: int,
    permission_data: PermissionUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin_dep)
):
    
    permission = db.query(Permission).filter(
        Permission.id == permission_id
    ).first()
    if not permission:
        raise HTTPException(status_code=404, detail="权限不存在")
    
    old_value = json.dumps({
        'name': permission.name,
        'description': permission.description,
        'is_active': permission.is_active
    }, ensure_ascii=False)
    
    update_data = permission_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(permission, key, value)
    
    db.commit()
    db.refresh(permission)
    
    new_value = json.dumps({
        'name': permission.name,
        'description': permission.description,
        'is_active': permission.is_active
    }, ensure_ascii=False)
    
    PermissionService.log_permission_change(
        db=db,
        operator_id=current_user.id,
        operator_name=current_user.username,
        target_type="permission",
        target_id=permission.id,
        target_name=permission.name,
        action="update",
        old_value=old_value,
        new_value=new_value,
        description=f"更新权限: {permission.name}",
        ip_address=get_client_ip(request)
    )
    
    LogService.log_operation(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        action="update",
        module="permission",
        description=f"更新权限: {permission.name}",
        target_type="permission",
        target_id=permission.id,
        request=request
    )
    
    return permission


@router.delete("/{permission_id}")
async def delete_permission(
    permission_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin_dep)
):
    
    permission = db.query(Permission).filter(
        Permission.id == permission_id
    ).first()
    if not permission:
        raise HTTPException(status_code=404, detail="权限不存在")
    
    db.execute(
        role_permissions.delete().where(
            role_permissions.c.permission_id == permission_id
        )
    )
    
    old_value = json.dumps({
        'code': permission.code,
        'name': permission.name
    }, ensure_ascii=False)
    
    db.delete(permission)
    db.commit()
    
    PermissionService.log_permission_change(
        db=db,
        operator_id=current_user.id,
        operator_name=current_user.username,
        target_type="permission",
        target_id=permission_id,
        target_name=permission.name,
        action="delete",
        old_value=old_value,
        new_value=None,
        description=f"删除权限: {permission.name}",
        ip_address=get_client_ip(request)
    )
    
    LogService.log_operation(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        action="delete",
        module="permission",
        description=f"删除权限: {permission.name}",
        target_type="permission",
        target_id=permission_id,
        request=request
    )
    
    return {"message": "权限已删除"}


@router.get("/export", response_model=PermissionExport)
async def export_permissions(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin_dep)
):
    
    permissions = db.query(Permission).all()
    roles = db.query(Role).all()
    
    role_responses = []
    for role in roles:
        role_perms = db.execute(
            role_permissions.select().where(
                role_permissions.c.role_id == role.id
            )
        ).fetchall()
        
        perm_ids = [rp.permission_id for rp in role_perms]
        perms = db.query(Permission).filter(
            Permission.id.in_(perm_ids)
        ).all()
        
        role_dict = {
            'id': role.id,
            'name': role.name,
            'code': role.code,
            'description': role.description,
            'is_system': role.is_system,
            'is_active': role.is_active,
            'priority': role.priority,
            'permissions': perms,
            'created_at': role.created_at,
            'updated_at': role.updated_at
        }
        role_responses.append(role_dict)
    
    return {
        'permissions': permissions,
        'roles': role_responses
    }


@router.post("/import")
async def import_permissions(
    import_data: PermissionImport,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin_dep)
):
    
    created_permissions = 0
    created_roles = 0
    
    for perm_data in (import_data.permissions or []):
        existing = db.query(Permission).filter(
            Permission.code == perm_data.code
        ).first()
        if not existing:
            permission = Permission(**perm_data.model_dump())
            db.add(permission)
            created_permissions += 1
    
    db.commit()
    
    for role_data in (import_data.roles or []):
        existing = db.query(Role).filter(
            Role.code == role_data.code
        ).first()
        if not existing:
            role = Role(
                name=role_data.name,
                code=role_data.code,
                description=role_data.description,
                priority=role_data.priority
            )
            db.add(role)
            db.flush()
            
            if role_data.permission_ids:
                for perm_id in role_data.permission_ids:
                    perm = db.query(Permission).filter(
                        Permission.id == perm_id
                    ).first()
                    if perm:
                        db.execute(
                            role_permissions.insert().values(
                                role_id=role.id,
                                permission_id=perm.id
                            )
                        )
            
            created_roles += 1
    
    db.commit()
    
    PermissionService.log_permission_change(
        db=db,
        operator_id=current_user.id,
        operator_name=current_user.username,
        target_type="system",
        target_id=None,
        target_name="权限系统",
        action="import",
        old_value=None,
        new_value=json.dumps({
            'permissions': created_permissions,
            'roles': created_roles
        }, ensure_ascii=False),
        description=f"导入权限配置: {created_permissions}个权限, {created_roles}个角色",
        ip_address=get_client_ip(request)
    )
    
    LogService.log_operation(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        action="import",
        module="permission",
        description=f"导入权限配置: {created_permissions}个权限, {created_roles}个角色",
        request=request
    )
    
    return {
        "message": "导入成功",
        "created_permissions": created_permissions,
        "created_roles": created_roles
    }


@router.get("/logs", response_model=List[PermissionChangeLogResponse])
async def get_permission_logs(
    page: int = 1,
    page_size: int = 20,
    target_type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin_dep)
):
    
    query = db.query(PermissionChangeLog)
    
    if target_type:
        query = query.filter(PermissionChangeLog.target_type == target_type)
    
    total = query.count()
    logs = query.order_by(
        PermissionChangeLog.created_at.desc()
    ).offset((page - 1) * page_size).limit(page_size).all()
    
    return logs


@router.get("/check/{permission_code}")
async def check_permission(
    permission_code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    has_perm = PermissionService.has_permission(db, current_user.id, permission_code)
    
    return {
        "has_permission": has_perm,
        "permission_code": permission_code
    }


@router.get("/my-permissions")
async def get_my_permissions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    permissions = PermissionService.get_user_permissions(db, current_user.id, strict_mode=True)
    roles = PermissionService.get_user_roles(db, current_user.id)
    
    return {
        "permissions": list(permissions),
        "roles": [{"id": r.id, "name": r.name, "code": r.code} for r in roles]
    }
