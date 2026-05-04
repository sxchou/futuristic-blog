from typing import List, Optional, Set
from sqlalchemy.orm import Session
from sqlalchemy import text
from fastapi import HTTPException, Request
from app.models import User, Role, Permission, user_roles, role_permissions, PermissionChangeLog
import json


class PermissionService:
    
    MODULE_NAMES = {
        'article': '文章管理',
        'category': '分类管理',
        'tag': '标签管理',
        'comment': '评论管理',
        'user': '用户管理',
        'role': '角色管理',
        'permission': '权限管理',
        'resource': '资源管理',
        'announcement': '公告中心',
        'storage': '文件存储',
        'settings': '系统设置',
        'log': '系统日志',
        'dashboard': '仪表盘',
        'email': '邮件服务',
        'notification': '通知设置',
        'oauth': 'OAuth授权',
        'profile': '网站资料',
    }
    
    MODULE_ORDER = [
        'dashboard',
        'article',
        'category',
        'tag',
        'resource',
        'comment',
        'role',
        'user',
        'email',
        'notification',
        'log',
        'announcement',
        'storage',
        'profile',
        'settings',
        'oauth',
    ]
    
    @staticmethod
    def get_user_permissions(db: Session, user_id: int, strict_mode: bool = False) -> Set[str]:
        if not user_id:
            return set()
        
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return set()
        
        if strict_mode:
            result = db.execute(
                text("""
                SELECT DISTINCT p.code 
                FROM permissions p
                JOIN role_permissions rp ON p.id = rp.permission_id
                JOIN roles r ON rp.role_id = r.id
                JOIN user_roles ur ON r.id = ur.role_id
                WHERE ur.user_id = :user_id 
                  AND p.is_active = true 
                  AND r.is_active = true
                """),
                {"user_id": user_id}
            )
        else:
            result = db.execute(
                text("""
                SELECT DISTINCT p.code 
                FROM permissions p
                JOIN role_permissions rp ON p.id = rp.permission_id
                JOIN user_roles ur ON rp.role_id = ur.role_id
                WHERE ur.user_id = :user_id AND p.is_active = true
                """),
                {"user_id": user_id}
            )
        return {row[0] for row in result}
    
    @staticmethod
    def has_permission(db: Session, user_id: int, permission_code: str) -> bool:
        permissions = PermissionService.get_user_permissions(db, user_id)
        return permission_code in permissions
    
    @staticmethod
    def has_permission_strict(db: Session, user_id: int, permission_code: str) -> bool:
        permissions = PermissionService.get_user_permissions(db, user_id, strict_mode=True)
        return permission_code in permissions
    
    @staticmethod
    def has_any_permission(db: Session, user_id: int, permission_codes: List[str]) -> bool:
        permissions = PermissionService.get_user_permissions(db, user_id)
        return any(code in permissions for code in permission_codes)
    
    @staticmethod
    def has_all_permissions(db: Session, user_id: int, permission_codes: List[str]) -> bool:
        permissions = PermissionService.get_user_permissions(db, user_id)
        return all(code in permissions for code in permission_codes)
    
    @staticmethod
    def get_user_roles(db: Session, user_id: int) -> List[Role]:
        result = db.execute(
            text("""
            SELECT r.* 
            FROM roles r
            JOIN user_roles ur ON r.id = ur.role_id
            WHERE ur.user_id = :user_id
            ORDER BY r.priority DESC
            """),
            {"user_id": user_id}
        )
        return [Role(**dict(row._mapping)) for row in result]
    
    @staticmethod
    def is_admin_user(db: Session, user_id: int) -> bool:
        if user_id == 1:
            user = db.query(User).filter(User.id == user_id).first()
            if user and not user.is_verified:
                return False
            return True
        
        result = db.execute(
            text("""
            SELECT r.code 
            FROM roles r
            JOIN user_roles ur ON r.id = ur.role_id
            WHERE ur.user_id = :user_id AND r.code IN ('super_admin', 'admin') AND r.is_active = true
            LIMIT 1
            """),
            {"user_id": user_id}
        )
        return result.first() is not None
    
    @staticmethod
    def get_admin_users(db: Session) -> List[User]:
        return db.query(User).join(
            user_roles, User.id == user_roles.c.user_id
        ).join(
            Role, user_roles.c.role_id == Role.id
        ).filter(
            Role.code.in_(['super_admin', 'admin'])
        ).distinct().all()
    
    @staticmethod
    def assign_roles_to_user(
        db: Session, 
        user_id: int, 
        role_ids: List[int], 
        assigned_by: int
    ) -> None:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")
        
        for role_id in role_ids:
            role = db.query(Role).filter(Role.id == role_id).first()
            if not role:
                continue
            
            existing = db.execute(
                user_roles.select().where(
                    user_roles.c.user_id == user_id,
                    user_roles.c.role_id == role_id
                )
            ).first()
            
            if not existing:
                db.execute(
                    user_roles.insert().values(
                        user_id=user_id,
                        role_id=role_id,
                        assigned_by=assigned_by
                    )
                )
        
        db.commit()
    
    @staticmethod
    def remove_roles_from_user(
        db: Session, 
        user_id: int, 
        role_ids: List[int]
    ) -> None:
        for role_id in role_ids:
            db.execute(
                user_roles.delete().where(
                    user_roles.c.user_id == user_id,
                    user_roles.c.role_id == role_id
                )
            )
        
        db.commit()
    
    @staticmethod
    def assign_permissions_to_role(
        db: Session, 
        role_id: int, 
        permission_ids: List[int]
    ) -> None:
        role = db.query(Role).filter(Role.id == role_id).first()
        if not role:
            raise HTTPException(status_code=404, detail="角色不存在")
        
        db.execute(
            role_permissions.delete().where(
                role_permissions.c.role_id == role_id
            )
        )
        
        for permission_id in permission_ids:
            permission = db.query(Permission).filter(Permission.id == permission_id).first()
            if permission:
                db.execute(
                    role_permissions.insert().values(
                        role_id=role_id,
                        permission_id=permission_id
                    )
                )
        
        db.commit()
    
    @staticmethod
    def get_permission_tree(db: Session) -> dict:
        excluded_modules = {'permission'}
        
        permissions = db.query(Permission).filter(
            Permission.is_active == True,
            Permission.module.notin_(excluded_modules)
        ).order_by(Permission.module, Permission.action).all()
        
        modules = {}
        for perm in permissions:
            if perm.module not in modules:
                modules[perm.module] = {
                    'module': perm.module,
                    'module_name': PermissionService.MODULE_NAMES.get(perm.module, perm.module),
                    'permissions': []
                }
            modules[perm.module]['permissions'].append(perm)
        
        ordered_modules = []
        for module_code in PermissionService.MODULE_ORDER:
            if module_code in modules:
                ordered_modules.append(modules[module_code])
        
        for module_code, module_data in modules.items():
            if module_code not in PermissionService.MODULE_ORDER:
                ordered_modules.append(module_data)
        
        return {
            'modules': ordered_modules
        }
    
    @staticmethod
    def log_permission_change(
        db: Session,
        operator_id: int,
        operator_name: str,
        target_type: str,
        target_id: Optional[int],
        target_name: Optional[str],
        action: str,
        old_value: Optional[str],
        new_value: Optional[str],
        description: Optional[str],
        ip_address: Optional[str]
    ) -> None:
        log = PermissionChangeLog(
            operator_id=operator_id,
            operator_name=operator_name,
            target_type=target_type,
            target_id=target_id,
            target_name=target_name,
            action=action,
            old_value=old_value,
            new_value=new_value,
            description=description,
            ip_address=ip_address
        )
        db.add(log)
        db.commit()
    
    @staticmethod
    def check_super_admin(user: User, db: Session = None) -> bool:
        if user.id == 1:
            return True
        if db:
            result = db.execute(
                text("""
                SELECT r.code 
                FROM roles r
                JOIN user_roles ur ON r.id = ur.role_id
                WHERE ur.user_id = :user_id AND r.code = 'super_admin'
                LIMIT 1
                """),
                {"user_id": user.id}
            )
            return result.first() is not None
        return False
    
    @staticmethod
    def require_super_admin(user: User, db: Session = None) -> None:
        if not PermissionService.check_super_admin(user, db):
            raise HTTPException(
                status_code=403, 
                detail="此操作需要超级管理员权限"
            )
    
    @staticmethod
    def can_modify_user(db: Session, operator: User, target_user: User) -> bool:
        if operator.id == 1:
            return True
        
        if target_user.id == 1:
            return False
        
        operator_is_admin = PermissionService.is_admin_user(db, operator.id)
        target_is_admin = PermissionService.is_admin_user(db, target_user.id)
        
        if operator_is_admin and not target_is_admin:
            return True
        
        return False
    
    @staticmethod
    def can_assign_role(db: Session, operator: User, role: Role) -> bool:
        if operator.id == 1:
            return True
        
        if role.code == 'super_admin':
            return False
        
        return PermissionService.is_admin_user(db, operator.id)
