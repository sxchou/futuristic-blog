from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.utils import get_current_user
from app.utils.permissions import require_permission, require_super_admin as require_super_admin_dep
from app.models import User, Role, Permission, user_roles, role_permissions
from app.schemas.schemas import (
    RoleCreate, RoleUpdate, RoleResponse,
    UserRoleAssign, UserRoleRemove, UserWithRolesResponse,
    RolePermissionUpdate, RoleTemplateCreate
)
from app.services.permission_service import PermissionService
from app.services.log_service import LogService
import json

router = APIRouter(prefix="/roles", tags=["roles"])


def get_client_ip(request: Request) -> Optional[str]:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else None


@router.get("", response_model=List[RoleResponse])
async def get_roles(
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("role.view"))
):
    
    query = db.query(Role)
    
    if is_active is not None:
        query = query.filter(Role.is_active == is_active)
    
    roles = query.order_by(Role.priority.desc()).all()
    
    result = []
    for role in roles:
        role_perms = db.execute(
            role_permissions.select().where(
                role_permissions.c.role_id == role.id
            )
        ).fetchall()
        
        perm_ids = [rp.permission_id for rp in role_perms]
        perms = db.query(Permission).filter(
            Permission.id.in_(perm_ids),
            Permission.module != 'permission'
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
        result.append(role_dict)
    
    return result


@router.get("/{role_id}", response_model=RoleResponse)
async def get_role(
    role_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("role.view"))
):
    
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="角色不存在")
    
    role_perms = db.execute(
        role_permissions.select().where(
            role_permissions.c.role_id == role.id
        )
    ).fetchall()
    
    perm_ids = [rp.permission_id for rp in role_perms]
    perms = db.query(Permission).filter(
        Permission.id.in_(perm_ids),
        Permission.module != 'permission'
    ).all()
    
    return {
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


@router.post("", response_model=RoleResponse)
async def create_role(
    role_data: RoleCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin_dep)
):
    
    existing = db.query(Role).filter(Role.code == role_data.code).first()
    if existing:
        raise HTTPException(status_code=400, detail="角色代码已存在")
    
    existing_name = db.query(Role).filter(Role.name == role_data.name).first()
    if existing_name:
        raise HTTPException(status_code=400, detail="角色名称已存在")
    
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
            perm = db.query(Permission).filter(Permission.id == perm_id).first()
            if perm:
                db.execute(
                    role_permissions.insert().values(
                        role_id=role.id,
                        permission_id=perm.id
                    )
                )
    
    db.commit()
    db.refresh(role)
    
    PermissionService.log_permission_change(
        db=db,
        operator_id=current_user.id,
        operator_name=current_user.username,
        target_type="role",
        target_id=role.id,
        target_name=role.name,
        action="create",
        old_value=None,
        new_value=json.dumps(role_data.model_dump(), ensure_ascii=False),
        description=f"创建角色: {role.name}",
        ip_address=get_client_ip(request)
    )
    
    LogService.log_operation(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        action="create",
        module="role",
        description=f"创建角色: {role.name}",
        target_type="role",
        target_id=role.id,
        request=request
    )
    
    role_perms = db.execute(
        role_permissions.select().where(
            role_permissions.c.role_id == role.id
        )
    ).fetchall()
    
    perm_ids = [rp.permission_id for rp in role_perms]
    perms = db.query(Permission).filter(
        Permission.id.in_(perm_ids),
        Permission.module != 'permission'
    ).all()
    
    return {
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


@router.post("/from-template", response_model=RoleResponse)
async def create_role_from_template(
    template_data: RoleTemplateCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin_dep)
):
    
    existing = db.query(Role).filter(Role.code == template_data.code).first()
    if existing:
        raise HTTPException(status_code=400, detail="角色代码已存在")
    
    template_role = db.query(Role).filter(
        Role.id == template_data.copy_from_role_id
    ).first()
    if not template_role:
        raise HTTPException(status_code=404, detail="模板角色不存在")
    
    role = Role(
        name=template_data.name,
        code=template_data.code,
        description=template_data.description or template_role.description,
        priority=template_role.priority
    )
    db.add(role)
    db.flush()
    
    template_perms = db.execute(
        role_permissions.select().where(
            role_permissions.c.role_id == template_role.id
        )
    ).fetchall()
    
    for tp in template_perms:
        db.execute(
            role_permissions.insert().values(
                role_id=role.id,
                permission_id=tp.permission_id
            )
        )
    
    db.commit()
    db.refresh(role)
    
    PermissionService.log_permission_change(
        db=db,
        operator_id=current_user.id,
        operator_name=current_user.username,
        target_type="role",
        target_id=role.id,
        target_name=role.name,
        action="create_from_template",
        old_value=json.dumps({'template_id': template_role.id}, ensure_ascii=False),
        new_value=json.dumps({
            'name': template_data.name,
            'code': template_data.code
        }, ensure_ascii=False),
        description=f"从模板创建角色: {role.name} (模板: {template_role.name})",
        ip_address=get_client_ip(request)
    )
    
    LogService.log_operation(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        action="create_from_template",
        module="role",
        description=f"从模板创建角色: {role.name} (模板: {template_role.name})",
        target_type="role",
        target_id=role.id,
        request=request
    )
    
    role_perms = db.execute(
        role_permissions.select().where(
            role_permissions.c.role_id == role.id
        )
    ).fetchall()
    
    perm_ids = [rp.permission_id for rp in role_perms]
    perms = db.query(Permission).filter(
        Permission.id.in_(perm_ids),
        Permission.module != 'permission'
    ).all()
    
    return {
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


@router.put("/{role_id}", response_model=RoleResponse)
async def update_role(
    role_id: int,
    role_data: RoleUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin_dep)
):
    
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="角色不存在")
    
    if role.code == 'super_admin':
        raise HTTPException(status_code=400, detail="超级管理员拥有所有权限，不允许修改")
    
    old_perms = db.execute(
        role_permissions.select().where(
            role_permissions.c.role_id == role.id
        )
    ).fetchall()
    old_perm_ids = [rp.permission_id for rp in old_perms]
    
    old_is_active = role.is_active
    
    old_value = json.dumps({
        'name': role.name,
        'description': role.description,
        'is_active': role.is_active,
        'priority': role.priority,
        'permission_ids': old_perm_ids
    }, ensure_ascii=False)
    
    update_data = role_data.model_dump(exclude_unset=True)
    
    is_only_is_active_change = False
    if role.is_system and 'is_active' in update_data:
        del update_data['is_active']
    elif 'is_active' in update_data and len(update_data) == 1 and 'permission_ids' not in role_data.model_dump(exclude_unset=True):
        is_only_is_active_change = True
    
    permission_ids = update_data.pop('permission_ids', None)
    
    for key, value in update_data.items():
        setattr(role, key, value)
    
    if permission_ids is not None:
        db.execute(
            role_permissions.delete().where(
                role_permissions.c.role_id == role.id
            )
        )
        
        for perm_id in permission_ids:
            perm = db.query(Permission).filter(Permission.id == perm_id).first()
            if perm:
                db.execute(
                    role_permissions.insert().values(
                        role_id=role.id,
                        permission_id=perm.id
                    )
                )
    
    db.commit()
    db.refresh(role)
    
    new_perms = db.execute(
        role_permissions.select().where(
            role_permissions.c.role_id == role.id
        )
    ).fetchall()
    new_perm_ids = [rp.permission_id for rp in new_perms]
    
    new_value = json.dumps({
        'name': role.name,
        'description': role.description,
        'is_active': role.is_active,
        'priority': role.priority,
        'permission_ids': new_perm_ids
    }, ensure_ascii=False)
    
    description = f"更新角色: {role.name}"
    action = "update"
    
    if is_only_is_active_change and old_is_active != role.is_active:
        if role.is_active:
            description = f"启用角色: {role.name}"
            action = "启用"
        else:
            description = f"禁用角色: {role.name}"
            action = "禁用"
    
    PermissionService.log_permission_change(
        db=db,
        operator_id=current_user.id,
        operator_name=current_user.username,
        target_type="role",
        target_id=role.id,
        target_name=role.name,
        action=action,
        old_value=old_value,
        new_value=new_value,
        description=description,
        ip_address=get_client_ip(request)
    )
    
    LogService.log_operation(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        action=action,
        module="role",
        description=description,
        target_type="role",
        target_id=role.id,
        request=request
    )
    
    perms = db.query(Permission).filter(
        Permission.id.in_(new_perm_ids)
    ).all()
    
    return {
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


@router.put("/{role_id}/permissions")
async def update_role_permissions(
    role_id: int,
    perm_data: RolePermissionUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin_dep)
):
    
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="角色不存在")
    
    if role.code == 'super_admin':
        raise HTTPException(status_code=400, detail="超级管理员拥有所有权限，不允许修改")
    
    old_perms = db.execute(
        role_permissions.select().where(
            role_permissions.c.role_id == role.id
        )
    ).fetchall()
    old_perm_ids = [rp.permission_id for rp in old_perms]
    
    PermissionService.assign_permissions_to_role(
        db=db,
        role_id=role_id,
        permission_ids=perm_data.permission_ids
    )
    
    PermissionService.log_permission_change(
        db=db,
        operator_id=current_user.id,
        operator_name=current_user.username,
        target_type="role",
        target_id=role.id,
        target_name=role.name,
        action="update_permissions",
        old_value=json.dumps(old_perm_ids),
        new_value=json.dumps(perm_data.permission_ids),
        description=f"更新角色权限: {role.name}",
        ip_address=get_client_ip(request)
    )
    
    LogService.log_operation(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        action="update_permissions",
        module="role",
        description=f"更新角色权限: {role.name}",
        target_type="role",
        target_id=role.id,
        request=request
    )
    
    return {"message": "权限已更新"}


@router.delete("/{role_id}")
async def delete_role(
    role_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin_dep)
):
    
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="角色不存在")
    
    if role.is_system:
        raise HTTPException(status_code=400, detail="系统角色不能删除")
    
    db.execute(
        role_permissions.delete().where(
            role_permissions.c.role_id == role_id
        )
    )
    
    db.execute(
        user_roles.delete().where(
            user_roles.c.role_id == role_id
        )
    )
    
    old_value = json.dumps({
        'name': role.name,
        'code': role.code
    }, ensure_ascii=False)
    
    db.delete(role)
    db.commit()
    
    PermissionService.log_permission_change(
        db=db,
        operator_id=current_user.id,
        operator_name=current_user.username,
        target_type="role",
        target_id=role_id,
        target_name=role.name,
        action="delete",
        old_value=old_value,
        new_value=None,
        description=f"删除角色: {role.name}",
        ip_address=get_client_ip(request)
    )
    
    LogService.log_operation(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        action="delete",
        module="role",
        description=f"删除角色: {role.name}",
        target_type="role",
        target_id=role_id,
        request=request
    )
    
    return {"message": "角色已删除"}


@router.post("/assign", response_model=dict)
async def assign_roles(
    assign_data: UserRoleAssign,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("role.assign"))
):
    if not assign_data.role_ids or len(assign_data.role_ids) == 0:
        raise HTTPException(
            status_code=400,
            detail="请至少选择一个角色"
        )
    
    for user_id in assign_data.user_ids:
        if user_id == 1:
            raise HTTPException(
                status_code=403,
                detail="初始超级管理员的角色不能被修改"
            )
        
        if user_id == current_user.id:
            raise HTTPException(
                status_code=403,
                detail="不能修改自己的角色"
            )
    
    if not PermissionService.check_super_admin(current_user, db):
        for role_id in assign_data.role_ids:
            role = db.query(Role).filter(Role.id == role_id).first()
            if role and role.code == 'super_admin':
                raise HTTPException(
                    status_code=403, 
                    detail="只有超级管理员可以分配超级管理员角色"
                )
        
        for user_id in assign_data.user_ids:
            user = db.query(User).filter(User.id == user_id).first()
            if user and PermissionService.is_admin_user(db, user.id):
                raise HTTPException(
                    status_code=403,
                    detail="普通管理员不能为其他管理员分配角色"
                )
    
    users = db.query(User).filter(User.id.in_(assign_data.user_ids)).all()
    roles = db.query(Role).filter(Role.id.in_(assign_data.role_ids)).all()
    user_names = [u.username for u in users]
    role_names = [r.name for r in roles]
    
    for user_id in assign_data.user_ids:
        PermissionService.assign_roles_to_user(
            db=db,
            user_id=user_id,
            role_ids=assign_data.role_ids,
            assigned_by=current_user.id
        )
    
    description = f"为用户 [{', '.join(user_names)}] 分配角色 [{', '.join(role_names)}]"
    
    PermissionService.log_permission_change(
        db=db,
        operator_id=current_user.id,
        operator_name=current_user.username,
        target_type="user_roles",
        target_id=None,
        target_name=f"{len(assign_data.user_ids)}个用户",
        action="assign_roles",
        old_value=None,
        new_value=json.dumps({
            'user_ids': assign_data.user_ids,
            'role_ids': assign_data.role_ids,
            'user_names': user_names,
            'role_names': role_names
        }, ensure_ascii=False),
        description=description,
        ip_address=get_client_ip(request)
    )
    
    LogService.log_operation(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        action="assign_roles",
        module="role",
        description=description,
        request=request
    )
    
    return {"message": "角色分配成功"}


@router.post("/remove", response_model=dict)
async def remove_roles(
    remove_data: UserRoleRemove,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("role.assign"))
):
    for user_id in remove_data.user_ids:
        if user_id == 1:
            raise HTTPException(
                status_code=403,
                detail="初始超级管理员的角色不能被修改"
            )
        
        if user_id == current_user.id:
            raise HTTPException(
                status_code=403,
                detail="不能修改自己的角色"
            )
    
    for user_id in remove_data.user_ids:
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            current_roles = PermissionService.get_user_roles(db, user_id)
            remaining_roles = [r for r in current_roles if r.id not in remove_data.role_ids]
            if len(remaining_roles) == 0:
                raise HTTPException(
                    status_code=400,
                    detail=f"用户 {user.username} 必须至少保留一个角色"
                )
    
    if not PermissionService.check_super_admin(current_user, db):
        for role_id in remove_data.role_ids:
            role = db.query(Role).filter(Role.id == role_id).first()
            if role and role.code == 'super_admin':
                raise HTTPException(
                    status_code=403, 
                    detail="只有超级管理员可以移除超级管理员角色"
                )
        
        for user_id in remove_data.user_ids:
            user = db.query(User).filter(User.id == user_id).first()
            if user and PermissionService.is_admin_user(db, user.id):
                raise HTTPException(
                    status_code=403,
                    detail="普通管理员不能移除其他管理员的角色"
                )
    
    users = db.query(User).filter(User.id.in_(remove_data.user_ids)).all()
    roles = db.query(Role).filter(Role.id.in_(remove_data.role_ids)).all()
    user_names = [u.username for u in users]
    role_names = [r.name for r in roles]
    
    for user_id in remove_data.user_ids:
        PermissionService.remove_roles_from_user(
            db=db,
            user_id=user_id,
            role_ids=remove_data.role_ids
        )
    
    description = f"移除用户 [{', '.join(user_names)}] 的角色 [{', '.join(role_names)}]"
    
    PermissionService.log_permission_change(
        db=db,
        operator_id=current_user.id,
        operator_name=current_user.username,
        target_type="user_roles",
        target_id=None,
        target_name=f"{len(remove_data.user_ids)}个用户",
        action="remove_roles",
        old_value=json.dumps({
            'user_ids': remove_data.user_ids,
            'role_ids': remove_data.role_ids,
            'user_names': user_names,
            'role_names': role_names
        }, ensure_ascii=False),
        new_value=None,
        description=description,
        ip_address=get_client_ip(request)
    )
    
    LogService.log_operation(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        action="remove_roles",
        module="role",
        description=description,
        request=request
    )
    
    return {"message": "角色移除成功"}


@router.get("/users/{user_id}", response_model=UserWithRolesResponse)
async def get_user_with_roles(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("role.view"))
):
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    roles = PermissionService.get_user_roles(db, user_id)
    
    role_responses = []
    for role in roles:
        role_perms = db.execute(
            role_permissions.select().where(
                role_permissions.c.role_id == role.id
            )
        ).fetchall()
        
        perm_ids = [rp.permission_id for rp in role_perms]
        perms = db.query(Permission).filter(
            Permission.id.in_(perm_ids),
            Permission.module != 'permission'
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
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'is_admin': PermissionService.is_admin_user(db, user.id),
        'roles': role_responses,
        'created_at': user.created_at
    }


@router.get("/{role_id}/users")
async def get_users_by_role(
    role_id: int,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("role.view"))
):
    
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="角色不存在")
    
    result = db.execute(
        """
        SELECT u.id, u.username, u.email, u.created_at
        FROM users u
        JOIN user_roles ur ON u.id = ur.user_id
        WHERE ur.role_id = :role_id
        ORDER BY u.created_at DESC
        """,
        {"role_id": role_id}
    )
    
    users = []
    for row in result:
        user_dict = dict(row._mapping)
        user_dict['is_admin'] = PermissionService.is_admin_user(db, user_dict['id'])
        users.append(user_dict)
    total = len(users)
    
    start = (page - 1) * page_size
    end = start + page_size
    users = users[start:end]
    
    return {
        "items": users,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size
    }


DEFAULT_ROLE_PERMISSIONS = {
    "super_admin": "all",
    "admin": [
        "article.view", "article.create", "article.edit", "article.delete", "article.publish",
        "article.upload_image", "article.upload_file",
        "category.view", "category.create", "category.edit", "category.delete",
        "tag.view", "tag.create", "tag.edit", "tag.delete",
        "comment.view", "comment.audit", "comment.delete",
        "user.view", "user.edit", "user.reset_password",
        "resource.view", "resource.create", "resource.edit", "resource.delete",
        "announcement.view", "announcement.create", "announcement.edit", "announcement.delete",
        "storage.view", "storage.delete",
        "settings.view", "settings.edit",
        "profile.view", "profile.edit",
        "log.view", "log.clear",
        "dashboard.view", "dashboard.export",
        "email.view", "email.create", "email.edit", "email.delete", "email.activate", "email.switch_provider", "email.test", "email.view_logs",
        "notification.view", "notification.edit",
        "oauth.view",
        "role.view",
    ],
    "editor": [
        "article.view", "article.create", "article.edit", "article.publish",
        "article.upload_image", "article.upload_file",
        "category.view", "category.create", "category.edit",
        "tag.view", "tag.create", "tag.edit",
        "comment.view", "comment.audit",
        "resource.view", "resource.create", "resource.edit",
        "storage.view",
        "settings.view",
        "profile.view",
        "oauth.view",
        "role.view",
    ],
    "author": [
        "article.view", "article.create", "article.edit", "article.publish",
        "article.upload_image", "article.upload_file",
        "category.view",
        "tag.view",
        "comment.view",
        "resource.view",
        "storage.view",
        "settings.view",
        "profile.view",
        "oauth.view",
        "role.view",
    ],
    "guest": [
        "category.view",
        "tag.view",
        "role.view",
        "settings.view",
        "oauth.view",
        "profile.view",
    ],
}


@router.post("/{role_id}/reset-permissions")
async def reset_role_permissions(
    role_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin_dep)
):
    
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="角色不存在")
    
    if role.code not in DEFAULT_ROLE_PERMISSIONS:
        raise HTTPException(status_code=400, detail="该角色没有默认权限配置")
    
    old_perms = db.execute(
        role_permissions.select().where(
            role_permissions.c.role_id == role.id
        )
    ).fetchall()
    old_perm_ids = [rp.permission_id for rp in old_perms]
    
    db.execute(
        role_permissions.delete().where(
            role_permissions.c.role_id == role.id
        )
    )
    
    default_perm_codes = DEFAULT_ROLE_PERMISSIONS[role.code]
    
    if default_perm_codes == "all":
        all_perms = db.query(Permission).filter(Permission.is_active == True).all()
        new_perm_ids = [p.id for p in all_perms]
    else:
        all_perms = db.query(Permission).filter(
            Permission.code.in_(default_perm_codes),
            Permission.is_active == True
        ).all()
        new_perm_ids = [p.id for p in all_perms]
    
    for perm_id in new_perm_ids:
        db.execute(
            role_permissions.insert().values(
                role_id=role.id,
                permission_id=perm_id
            )
        )
    
    db.commit()
    
    PermissionService.log_permission_change(
        db=db,
        operator_id=current_user.id,
        operator_name=current_user.username,
        target_type="role",
        target_id=role.id,
        target_name=role.name,
        action="reset_permissions",
        old_value=json.dumps(old_perm_ids),
        new_value=json.dumps(new_perm_ids),
        description=f"重置角色权限为默认状态: {role.name}",
        ip_address=get_client_ip(request)
    )
    
    return {
        "message": "权限已重置为默认状态",
        "permission_count": len(new_perm_ids)
    }
