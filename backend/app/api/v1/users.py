from typing import List
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from datetime import timedelta
import random
import string
from app.core.database import get_db
from app.core.config import settings
from app.models import User, UserProfile, AvatarType, OAuthConnection, OAuthTempToken, Article, Comment, ArticleFile, ArticleLike, EmailLog, OperationLog, LoginLog, AccessLog, CommentAuditLog, RefreshToken, EmailChangeVerification
from app.schemas import UserListItem, UserAdminUpdate, PaginatedResponse
from app.utils import get_current_user, get_password_hash, verify_password
from app.services.log_service import LogService
from app.services.avatar_service import AvatarFileService
from app.services.email_service import EmailService
from app.utils.timezone import get_db_now

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
        
        avatar_url = None
        avatar_type = "default"
        
        if profile:
            if profile.avatar_type == AvatarType.custom and profile.avatar_url:
                avatar_url = profile.avatar_url
                avatar_type = "custom"
            elif profile.oauth_avatar_url:
                avatar_url = profile.oauth_avatar_url
                avatar_type = "oauth"
        
        item = UserListItem(
            id=user.id,
            username=user.username,
            email=user.email,
            avatar=user.avatar,
            avatar_type=avatar_type,
            avatar_url=avatar_url,
            oauth_avatar_url=profile.oauth_avatar_url if profile else None,
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
    
    if current_user.id != 1 and user_id != current_user.id and user.is_admin:
        raise HTTPException(status_code=403, detail="普通管理员不能修改其他管理员的信息")
    
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
        if user_id == current_user.id:
            if user_data.is_admin != user.is_admin:
                raise HTTPException(status_code=403, detail="不能修改自己的管理员权限")
        else:
            if user.id == 1 and not user_data.is_admin:
                raise HTTPException(status_code=403, detail="不能取消超级管理员的管理员权限")
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
    
    if user.id == 1:
        raise HTTPException(status_code=403, detail="不能删除超级管理员账户")
    
    if current_user.id != 1 and user.is_admin:
        raise HTTPException(status_code=403, detail="普通管理员不能删除其他管理员")
    
    username = user.username
    
    user_profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
    avatar_url_to_delete = None
    if user_profile and user_profile.avatar_type == AvatarType.custom and user_profile.avatar_url:
        avatar_url_to_delete = user_profile.avatar_url
    
    db.query(OAuthConnection).filter(OAuthConnection.user_id == user_id).delete()
    
    db.query(OAuthTempToken).filter(OAuthTempToken.user_id == user_id).delete()
    
    db.query(RefreshToken).filter(RefreshToken.user_id == user_id).delete()
    
    db.query(ArticleLike).filter(ArticleLike.user_id == user_id).delete()
    
    db.query(Comment).filter(Comment.user_id == user_id).update({Comment.user_id: None, Comment.author_name: username})
    
    db.query(Comment).filter(Comment.reply_to_user_id == user_id).update({Comment.reply_to_user_id: None})
    
    db.query(Article).filter(Article.author_id == user_id).update({Article.author_id: None})
    
    db.query(ArticleFile).filter(ArticleFile.uploaded_by == user_id).update({ArticleFile.uploaded_by: None})
    
    db.query(EmailLog).filter(EmailLog.user_id == user_id).update({EmailLog.user_id: None})
    
    db.query(OperationLog).filter(OperationLog.user_id == user_id).update({OperationLog.user_id: None})
    
    db.query(LoginLog).filter(LoginLog.user_id == user_id).update({LoginLog.user_id: None})
    
    db.query(AccessLog).filter(AccessLog.user_id == user_id).update({AccessLog.user_id: None})
    
    db.query(CommentAuditLog).filter(CommentAuditLog.operator_id == user_id).update({CommentAuditLog.operator_id: None, CommentAuditLog.operator_name: username})
    
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
    
    if user.id == 1:
        raise HTTPException(status_code=403, detail="不能重置超级管理员的密码")
    
    if current_user.id != 1 and user.is_admin:
        raise HTTPException(status_code=403, detail="普通管理员不能重置其他管理员的密码")
    
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


@router.post("/change-password")
async def change_password(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    from pydantic import ValidationError
    from app.schemas import ChangePassword
    from app.utils.auth import verify_password
    
    try:
        body = await request.json()
        data = ChangePassword(**body)
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=e.errors()[0]['msg'])
    
    if not verify_password(data.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="当前密码错误")
    
    if data.current_password == data.new_password:
        raise HTTPException(status_code=400, detail="新密码不能与当前密码相同")
    
    current_user.hashed_password = get_password_hash(data.new_password)
    db.commit()
    
    LogService.log_operation(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        action="修改密码",
        module="个人设置",
        description="用户修改了自己的密码",
        target_type="用户",
        target_id=current_user.id,
        request=request,
        status="success"
    )
    
    return {"message": "密码修改成功"}


EMAIL_CHANGE_CODE_EXPIRE_MINUTES = 10
MAX_EMAIL_CHANGE_REQUESTS_PER_HOUR = 5


def generate_email_change_code() -> str:
    return ''.join(random.choices(string.digits, k=6))


def get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


@router.post("/email-change/send-to-old")
async def send_code_to_old_email(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    import re
    
    if not current_user.email:
        raise HTTPException(status_code=400, detail="当前账户没有绑定邮箱")
    
    client_ip = get_client_ip(request)
    one_hour_ago = get_db_now() - timedelta(hours=1)
    
    recent_requests = db.query(EmailChangeVerification).filter(
        EmailChangeVerification.user_id == current_user.id,
        EmailChangeVerification.created_at > one_hour_ago
    ).count()
    
    if recent_requests >= MAX_EMAIL_CHANGE_REQUESTS_PER_HOUR:
        raise HTTPException(
            status_code=429,
            detail=f"请求过于频繁，请稍后再试"
        )
    
    code = generate_email_change_code()
    expires_at = get_db_now() + timedelta(minutes=EMAIL_CHANGE_CODE_EXPIRE_MINUTES)
    
    email_change = EmailChangeVerification(
        user_id=current_user.id,
        new_email=current_user.email,
        code=code,
        ip_address=client_ip,
        expires_at=expires_at,
        verification_type="old_email"
    )
    db.add(email_change)
    db.commit()
    
    try:
        EmailService.send_email_change_verification_email_db(
            db=db,
            email=current_user.email,
            username=current_user.username,
            code=code,
            user_id=current_user.id
        )
    except Exception as e:
        print(f"Failed to send verification email to old email: {e}")
        raise HTTPException(
            status_code=500,
            detail="发送验证码失败，请稍后重试"
        )
    
    return {
        "message": "验证码已发送至当前邮箱",
        "expires_in": EMAIL_CHANGE_CODE_EXPIRE_MINUTES * 60
    }


@router.post("/email-change/request")
async def request_email_change(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    from pydantic import ValidationError, EmailStr
    from pydantic import field_validator, BaseModel
    import re
    
    body = await request.json()
    new_email = body.get("new_email")
    password = body.get("password")
    verification_type = body.get("verification_type", "password")
    old_email_code = body.get("old_email_code")
    
    if not new_email:
        raise HTTPException(status_code=400, detail="请输入新邮箱地址")
    
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, new_email):
        raise HTTPException(status_code=400, detail="请输入有效的邮箱地址")
    
    if new_email == current_user.email:
        raise HTTPException(status_code=400, detail="新邮箱不能与当前邮箱相同")
    
    existing_user = db.query(User).filter(User.email == new_email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="该邮箱已被其他用户注册")
    
    if verification_type == "password":
        if not password:
            raise HTTPException(status_code=400, detail="请输入当前密码")
        
        if not verify_password(password, current_user.hashed_password):
            raise HTTPException(status_code=400, detail="当前密码错误")
    elif verification_type == "old_email":
        if not old_email_code:
            raise HTTPException(status_code=400, detail="请输入原邮箱验证码")
        
        now = get_db_now()
        verification = db.query(EmailChangeVerification).filter(
            EmailChangeVerification.user_id == current_user.id,
            EmailChangeVerification.new_email == current_user.email,
            EmailChangeVerification.code == old_email_code,
            EmailChangeVerification.verification_type == "old_email",
            EmailChangeVerification.is_used == False,
            EmailChangeVerification.expires_at > now
        ).first()
        
        if not verification:
            raise HTTPException(status_code=400, detail="原邮箱验证码无效或已过期")
        
        verification.is_used = True
        verification.used_at = now
        db.commit()
    else:
        raise HTTPException(status_code=400, detail="无效的验证方式")
    
    client_ip = get_client_ip(request)
    one_hour_ago = get_db_now() - timedelta(hours=1)
    
    recent_requests = db.query(EmailChangeVerification).filter(
        EmailChangeVerification.user_id == current_user.id,
        EmailChangeVerification.created_at > one_hour_ago
    ).count()
    
    if recent_requests >= MAX_EMAIL_CHANGE_REQUESTS_PER_HOUR:
        raise HTTPException(
            status_code=429,
            detail=f"请求过于频繁，请稍后再试"
        )
    
    code = generate_email_change_code()
    expires_at = get_db_now() + timedelta(minutes=EMAIL_CHANGE_CODE_EXPIRE_MINUTES)
    
    email_change = EmailChangeVerification(
        user_id=current_user.id,
        new_email=new_email,
        code=code,
        ip_address=client_ip,
        expires_at=expires_at,
        verification_type=verification_type
    )
    db.add(email_change)
    db.commit()
    
    try:
        EmailService.send_email_change_verification_email_db(
            db=db,
            email=new_email,
            username=current_user.username,
            code=code,
            user_id=current_user.id
        )
    except Exception as e:
        print(f"Failed to send email change verification email: {e}")
        raise HTTPException(
            status_code=500,
            detail="发送验证码失败，请稍后重试"
        )
    
    return {
        "message": "验证码已发送至新邮箱",
        "expires_in": EMAIL_CHANGE_CODE_EXPIRE_MINUTES * 60
    }


@router.post("/email-change/verify")
async def verify_email_change(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    body = await request.json()
    new_email = body.get("new_email")
    code = body.get("code")
    password = body.get("password")
    
    if not new_email:
        raise HTTPException(status_code=400, detail="请输入新邮箱地址")
    if not code:
        raise HTTPException(status_code=400, detail="请输入验证码")
    if not password:
        raise HTTPException(status_code=400, detail="请输入当前密码")
    
    if not verify_password(password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="当前密码错误")
    
    existing_user = db.query(User).filter(User.email == new_email).first()
    if existing_user and existing_user.id != current_user.id:
        raise HTTPException(status_code=400, detail="该邮箱已被其他用户注册")
    
    now = get_db_now()
    verification = db.query(EmailChangeVerification).filter(
        EmailChangeVerification.user_id == current_user.id,
        EmailChangeVerification.new_email == new_email,
        EmailChangeVerification.code == code,
        EmailChangeVerification.is_used == False,
        EmailChangeVerification.expires_at > now
    ).first()
    
    if not verification:
        raise HTTPException(status_code=400, detail="验证码无效或已过期")
    
    verification.is_used = True
    verification.used_at = now
    
    old_email = current_user.email
    current_user.email = new_email
    current_user.is_verified = True
    
    db.commit()
    
    LogService.log_operation(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        action="更改邮箱",
        module="个人设置",
        description=f"邮箱从 {old_email} 更改为 {new_email}",
        target_type="用户",
        target_id=current_user.id,
        request=request,
        status="success"
    )
    
    return {"message": "邮箱修改成功"}


@router.post("/change-username")
async def change_username(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    body = await request.json()
    new_username = body.get("new_username")
    password = body.get("password")
    
    if not new_username:
        raise HTTPException(status_code=400, detail="请输入新用户名")
    
    if not password:
        raise HTTPException(status_code=400, detail="请输入当前密码")
    
    if len(new_username) < 4:
        raise HTTPException(status_code=400, detail="用户名长度至少4个字符")
    
    if len(new_username) > 20:
        raise HTTPException(status_code=400, detail="用户名长度不能超过20个字符")
    
    import re
    if not re.match(r'^[a-zA-Z0-9_\u4e00-\u9fa5]+$', new_username):
        raise HTTPException(status_code=400, detail="用户名只能包含字母、数字、下划线和中文")
    
    if not verify_password(password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="当前密码错误")
    
    if new_username == current_user.username:
        raise HTTPException(status_code=400, detail="新用户名不能与当前用户名相同")
    
    existing_user = db.query(User).filter(User.username == new_username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="该用户名已被使用")
    
    old_username = current_user.username
    current_user.username = new_username
    
    db.commit()
    
    LogService.log_operation(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        action="更改用户名",
        module="个人设置",
        description=f"用户名从 {old_username} 更改为 {new_username}",
        target_type="用户",
        target_id=current_user.id,
        request=request,
        status="success"
    )
    
    return {"message": "用户名修改成功", "new_username": new_username}
