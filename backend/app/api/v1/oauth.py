from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List, Optional
from pydantic import BaseModel
from app.core.database import get_db
from app.utils.auth import create_access_token, create_refresh_token
from app.utils.permissions import require_permission
from app.models import OAuthProvider, OAuthConnection, User
from app.core.config import settings
from app.services.permission_service import PermissionService
from app.services.log_service import LogService
import httpx
import secrets
from datetime import datetime, timedelta, timezone

router = APIRouter(prefix="/oauth", tags=["oauth"])


def send_oauth_email_verification_bg(email: str, username: str, temp_token: str, provider_name: str):
    from app.core.database import SessionLocal
    from app.services.email_service import EmailService
    db = SessionLocal()
    try:
        EmailService.send_oauth_email_verification(
            db=db,
            email=email,
            username=username,
            temp_token=temp_token,
            provider_name=provider_name
        )
    except Exception as e:
        print(f"Failed to send OAuth email verification: {e}")
    finally:
        db.close()


class OAuthProviderBase(BaseModel):
    name: str
    display_name: str
    icon: Optional[str] = None
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    redirect_uri: Optional[str] = None
    authorize_url: Optional[str] = None
    token_url: Optional[str] = None
    userinfo_url: Optional[str] = None
    scope: Optional[str] = None
    is_enabled: bool = False
    show_on_login: bool = True
    order: int = 0


class OAuthProviderCreate(OAuthProviderBase):
    pass


class OAuthProviderUpdate(BaseModel):
    display_name: Optional[str] = None
    icon: Optional[str] = None
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    redirect_uri: Optional[str] = None
    authorize_url: Optional[str] = None
    token_url: Optional[str] = None
    userinfo_url: Optional[str] = None
    scope: Optional[str] = None
    is_enabled: Optional[bool] = None
    show_on_login: Optional[bool] = None
    order: Optional[int] = None


class OAuthProviderResponse(BaseModel):
    id: int
    name: str
    display_name: str
    icon: Optional[str]
    is_enabled: bool
    show_on_login: bool
    is_configured: bool
    order: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class OAuthProviderDetail(OAuthProviderResponse):
    client_id: Optional[str]
    redirect_uri: Optional[str]
    authorize_url: Optional[str]
    token_url: Optional[str]
    userinfo_url: Optional[str]
    scope: Optional[str]


class OAuthLoginResponse(BaseModel):
    authorize_url: str
    state: str


class OAuthCallbackResponse(BaseModel):
    access_token: str
    token_type: str
    refresh_token: Optional[str] = None
    expires_in: Optional[int] = None
    user: dict
    needs_email: bool = False
    temp_token: Optional[str] = None


class OAuthEmailVerifyRequest(BaseModel):
    email: str


class OAuthEmailVerifyResponse(BaseModel):
    message: str
    temp_token: str


def check_provider_configured(provider: OAuthProvider) -> bool:
    return bool(
        provider.client_id and
        provider.client_secret and
        provider.redirect_uri and
        provider.authorize_url and
        provider.token_url and
        provider.userinfo_url
    )


@router.get("/providers", response_model=List[OAuthProviderResponse])
def get_oauth_providers(db: Session = Depends(get_db)):
    providers = db.query(OAuthProvider).order_by(OAuthProvider.order).all()
    return [
        OAuthProviderResponse(
            id=p.id,
            name=p.name,
            display_name=p.display_name,
            icon=p.icon,
            is_enabled=p.is_enabled,
            show_on_login=p.show_on_login,
            is_configured=check_provider_configured(p),
            order=p.order,
            created_at=p.created_at,
            updated_at=p.updated_at
        )
        for p in providers
    ]


@router.get("/providers/login", response_model=List[OAuthProviderResponse])
def get_login_providers(db: Session = Depends(get_db)):
    providers = db.query(OAuthProvider).filter(
        OAuthProvider.show_on_login == True
    ).order_by(OAuthProvider.order).all()
    return [
        OAuthProviderResponse(
            id=p.id,
            name=p.name,
            display_name=p.display_name,
            icon=p.icon,
            is_enabled=p.is_enabled,
            show_on_login=p.show_on_login,
            is_configured=check_provider_configured(p),
            order=p.order,
            created_at=p.created_at,
            updated_at=p.updated_at
        )
        for p in providers
    ]


@router.get("/providers/{provider_id}", response_model=OAuthProviderDetail)
def get_oauth_provider(provider_id: int, db: Session = Depends(get_db)):
    provider = db.query(OAuthProvider).filter(OAuthProvider.id == provider_id).first()
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    
    return OAuthProviderDetail(
        id=provider.id,
        name=provider.name,
        display_name=provider.display_name,
        icon=provider.icon,
        client_id=provider.client_id,
        redirect_uri=provider.redirect_uri,
        authorize_url=provider.authorize_url,
        token_url=provider.token_url,
        userinfo_url=provider.userinfo_url,
        scope=provider.scope,
        is_enabled=provider.is_enabled,
        show_on_login=provider.show_on_login,
        is_configured=check_provider_configured(provider),
        order=provider.order,
        created_at=provider.created_at,
        updated_at=provider.updated_at
    )


@router.post("/providers", response_model=OAuthProviderResponse)
def create_oauth_provider(
    data: OAuthProviderCreate, 
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("oauth.edit"))
):
    existing = db.query(OAuthProvider).filter(OAuthProvider.name == data.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Provider already exists")
    
    provider = OAuthProvider(**data.model_dump())
    db.add(provider)
    
    try:
        db.commit()
        db.refresh(provider)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="数据保存失败，请检查输入内容")
    
    LogService.log_operation(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        action="create",
        module="oauth",
        description=f"创建OAuth提供商: {provider.display_name}",
        target_type="oauth_provider",
        target_id=provider.id,
        request=request
    )
    
    return OAuthProviderResponse(
        id=provider.id,
        name=provider.name,
        display_name=provider.display_name,
        icon=provider.icon,
        is_enabled=provider.is_enabled,
        show_on_login=provider.show_on_login,
        is_configured=check_provider_configured(provider),
        order=provider.order,
        created_at=provider.created_at,
        updated_at=provider.updated_at
    )


@router.put("/providers/{provider_id}", response_model=OAuthProviderResponse)
def update_oauth_provider(
    provider_id: int, 
    data: OAuthProviderUpdate, 
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("oauth.edit"))
):
    provider = db.query(OAuthProvider).filter(OAuthProvider.id == provider_id).first()
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    
    old_is_enabled = provider.is_enabled
    old_show_on_login = provider.show_on_login
    
    update_data = data.model_dump(exclude_unset=True)
    
    if data.display_name is not None:
        if not data.display_name.strip():
            raise HTTPException(status_code=400, detail="显示名称不能为空")
    
    if data.client_id is not None:
        if not data.client_id.strip():
            raise HTTPException(status_code=400, detail="Client ID不能为空")
    
    if data.redirect_uri is not None:
        if not data.redirect_uri.strip():
            raise HTTPException(status_code=400, detail="回调地址不能为空")
        if not data.redirect_uri.startswith('http'):
            raise HTTPException(status_code=400, detail="回调地址必须以 http 或 https 开头")
    
    if data.authorize_url is not None:
        if not data.authorize_url.strip():
            raise HTTPException(status_code=400, detail="授权地址不能为空")
        if not data.authorize_url.startswith('http'):
            raise HTTPException(status_code=400, detail="授权地址必须以 http 或 https 开头")
    
    if data.token_url is not None:
        if not data.token_url.strip():
            raise HTTPException(status_code=400, detail="令牌地址不能为空")
        if not data.token_url.startswith('http'):
            raise HTTPException(status_code=400, detail="令牌地址必须以 http 或 https 开头")
    
    if data.userinfo_url is not None:
        if not data.userinfo_url.strip():
            raise HTTPException(status_code=400, detail="用户信息地址不能为空")
        if not data.userinfo_url.startswith('http'):
            raise HTTPException(status_code=400, detail="用户信息地址必须以 http 或 https 开头")
    
    if data.scope is not None:
        if not data.scope.strip():
            raise HTTPException(status_code=400, detail="授权范围不能为空")
    
    for key, value in update_data.items():
        setattr(provider, key, value)
    
    try:
        db.commit()
        db.refresh(provider)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="数据保存失败，请检查输入内容")
    
    description = f"更新OAuth提供商: {provider.display_name}"
    action = "update"
    
    if 'is_enabled' in update_data and len(update_data) == 1:
        if old_is_enabled != provider.is_enabled:
            if provider.is_enabled:
                description = f"启用OAuth提供商: {provider.display_name}"
                action = "启用"
            else:
                description = f"禁用OAuth提供商: {provider.display_name}"
                action = "禁用"
    elif 'show_on_login' in update_data and len(update_data) == 1:
        if old_show_on_login != provider.show_on_login:
            if provider.show_on_login:
                description = f"在登录页显示OAuth提供商: {provider.display_name}"
                action = "显示"
            else:
                description = f"在登录页隐藏OAuth提供商: {provider.display_name}"
                action = "隐藏"
    
    LogService.log_operation(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        action=action,
        module="oauth",
        description=description,
        target_type="oauth_provider",
        target_id=provider.id,
        request=request
    )
    
    return OAuthProviderResponse(
        id=provider.id,
        name=provider.name,
        display_name=provider.display_name,
        icon=provider.icon,
        is_enabled=provider.is_enabled,
        show_on_login=provider.show_on_login,
        is_configured=check_provider_configured(provider),
        order=provider.order,
        created_at=provider.created_at,
        updated_at=provider.updated_at
    )


@router.delete("/providers/{provider_id}")
def delete_oauth_provider(
    provider_id: int, 
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("oauth.edit"))
):
    provider = db.query(OAuthProvider).filter(OAuthProvider.id == provider_id).first()
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    
    provider_name = provider.display_name
    db.query(OAuthConnection).filter(OAuthConnection.provider_id == provider_id).delete()
    db.delete(provider)
    db.commit()
    
    LogService.log_operation(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        action="delete",
        module="oauth",
        description=f"删除OAuth提供商: {provider_name}",
        target_type="oauth_provider",
        target_id=provider_id,
        request=request
    )
    
    return {"message": "Provider deleted successfully"}


@router.get("/login/{provider_name}", response_model=OAuthLoginResponse)
def oauth_login(provider_name: str, db: Session = Depends(get_db)):
    provider = db.query(OAuthProvider).filter(
        OAuthProvider.name == provider_name,
        OAuthProvider.is_enabled == True
    ).first()
    
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found or not enabled")
    
    if not check_provider_configured(provider):
        raise HTTPException(status_code=400, detail="Provider not properly configured")
    
    state = secrets.token_urlsafe(32)
    
    params = {
        "client_id": provider.client_id,
        "redirect_uri": provider.redirect_uri,
        "scope": provider.scope or "openid profile email",
        "response_type": "code",
        "state": state
    }
    
    if provider_name == "google":
        params["access_type"] = "offline"
        params["prompt"] = "consent"
    
    query_string = "&".join(f"{k}={v}" for k, v in params.items())
    authorize_url = f"{provider.authorize_url}?{query_string}"
    
    return OAuthLoginResponse(authorize_url=authorize_url, state=state)


@router.get("/callback/{provider_name}")
async def oauth_callback(
    provider_name: str,
    code: str,
    state: str,
    db: Session = Depends(get_db)
):
    provider = db.query(OAuthProvider).filter(
        OAuthProvider.name == provider_name
    ).first()
    
    if not provider:
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url=f"{settings.FRONTEND_URL}/login?error=Provider not found")
    
    if not check_provider_configured(provider):
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url=f"{settings.FRONTEND_URL}/login?error=Provider not properly configured")
    
    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            provider.token_url,
            data={
                "client_id": provider.client_id,
                "client_secret": provider.client_secret,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": provider.redirect_uri
            },
            headers={"Accept": "application/json"}
        )
        
        if token_response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to get access token")
        
        token_data = token_response.json()
        access_token = token_data.get("access_token")
        
        if not access_token:
            raise HTTPException(status_code=400, detail="Failed to get access token from provider")
        
        userinfo_response = await client.get(
            provider.userinfo_url,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json"
            }
        )
        
        if userinfo_response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to get user info")
        
        user_info = userinfo_response.json()
        
        oauth_email = None
        if provider_name == "google":
            oauth_email = user_info.get("email")
        elif provider_name == "github":
            oauth_email = user_info.get("email")
            if not oauth_email:
                try:
                    emails_response = await client.get(
                        "https://api.github.com/user/emails",
                        headers={
                            "Authorization": f"Bearer {access_token}",
                            "Accept": "application/json"
                        }
                    )
                    if emails_response.status_code == 200:
                        emails = emails_response.json()
                        for email_entry in emails:
                            if email_entry.get("primary") and email_entry.get("verified"):
                                oauth_email = email_entry.get("email")
                                break
                except Exception:
                    pass
    
    provider_user_id = None
    name = None
    avatar = None
    
    if provider_name == "google":
        provider_user_id = user_info.get("id")
        name = user_info.get("name")
        avatar = user_info.get("picture")
    elif provider_name == "github":
        provider_user_id = str(user_info.get("id"))
        name = user_info.get("login")
        avatar = user_info.get("avatar_url")
    elif provider_name == "twitter" or provider_name == "x":
        provider_user_id = user_info.get("data", {}).get("id")
        name = user_info.get("data", {}).get("username")
        avatar = user_info.get("data", {}).get("profile_image_url")
    elif provider_name == "wechat":
        provider_user_id = user_info.get("openid")
        name = user_info.get("nickname")
        avatar = user_info.get("headimgurl")
    elif provider_name == "qq":
        provider_user_id = user_info.get("openid")
        name = user_info.get("nickname")
        avatar = user_info.get("figureurl_qq_2") or user_info.get("figureurl_qq_1")
    
    if not provider_user_id:
        raise HTTPException(status_code=400, detail="Failed to get provider user ID")
    
    connection = db.query(OAuthConnection).filter(
        OAuthConnection.provider_id == provider.id,
        OAuthConnection.provider_user_id == provider_user_id
    ).first()
    
    from fastapi.responses import RedirectResponse
    from urllib.parse import urlencode
    
    if connection:
        user = connection.user
        
        if not user:
            db.delete(connection)
            db.commit()
            connection = None
    
    if connection:
        if avatar and user.avatar != avatar:
            user.avatar = avatar
        
        from app.models import UserProfile, AvatarType
        profile = db.query(UserProfile).filter(UserProfile.user_id == user.id).first()
        if not profile:
            gradient = [f"#{hash(user.username) % 16777215:06x}", f"#{(hash(user.username) + 1000) % 16777215:06x}"]
            profile = UserProfile(
                user_id=user.id,
                avatar_type=AvatarType.default,
                default_avatar_gradient=gradient,
                oauth_avatar_url=avatar
            )
            db.add(profile)
        elif avatar and not profile.oauth_avatar_url:
            profile.oauth_avatar_url = avatar
        
        db.commit()
        
        if user.is_verified:
            jwt_token = create_access_token(data={"sub": user.username})
            refresh_token_obj = create_refresh_token(db=db, user_id=user.id, request=None)
            
            params = {
                "access_token": jwt_token,
                "token_type": "bearer",
                "refresh_token": refresh_token_obj.token,
                "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                "user_id": user.id,
                "username": user.username,
                "email": user.email or "",
                "avatar": user.avatar or "",
                "is_admin": str(PermissionService.is_admin_user(db, user.id)).lower(),
                "needs_email": "false"
            }
            return RedirectResponse(url=f"{settings.FRONTEND_URL}/oauth/callback/{provider_name}?{urlencode(params)}")
        
        if oauth_email and (not user.email or user.email.endswith('@oauth.local')):
            existing_email_user = db.query(User).filter(User.email == oauth_email, User.id != user.id).first()
            if not existing_email_user:
                user.email = oauth_email
                user.is_verified = True
                db.commit()
                
                jwt_token = create_access_token(data={"sub": user.username})
                refresh_token_obj = create_refresh_token(db=db, user_id=user.id, request=None)
                
                params = {
                    "access_token": jwt_token,
                    "token_type": "bearer",
                    "refresh_token": refresh_token_obj.token,
                    "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                    "user_id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "avatar": user.avatar or "",
                    "is_admin": str(PermissionService.is_admin_user(db, user.id)).lower(),
                    "needs_email": "false"
                }
                return RedirectResponse(url=f"{settings.FRONTEND_URL}/oauth/callback/{provider_name}?{urlencode(params)}")
        
        import uuid
        temp_token = str(uuid.uuid4())
        
        from app.services.email_service import EmailService
        actual_token = EmailService.store_oauth_temp_token(
            db=db,
            temp_token=temp_token,
            user_id=user.id,
            provider_name=provider_name,
            provider_user_id=provider_user_id
        )
        
        params = {
            "access_token": "",
            "token_type": "bearer",
            "user_id": user.id,
            "username": user.username,
            "email": user.email if user.email and not user.email.endswith('@oauth.local') else "",
            "avatar": user.avatar or "",
            "is_admin": str(PermissionService.is_admin_user(db, user.id)).lower(),
            "needs_email": "true",
            "temp_token": actual_token
        }
        return RedirectResponse(url=f"{settings.FRONTEND_URL}/oauth/callback/{provider_name}?{urlencode(params)}")
    
    username = name or f"{provider_name}_{provider_user_id}"
    base_username = username
    counter = 1
    while db.query(User).filter(User.username == username).first():
        username = f"{base_username}_{counter}"
        counter += 1
    
    if oauth_email:
        existing_email_user = db.query(User).filter(User.email == oauth_email).first()
        if existing_email_user:
            oauth_email = None
    
    user_email = oauth_email or f"{provider_name}_{provider_user_id}@oauth.local"
    user_verified = bool(oauth_email)
    
    user = User(
        username=username,
        email=user_email,
        hashed_password="",
        is_verified=user_verified,
        avatar=avatar
    )
    db.add(user)
    try:
        db.commit()
    except Exception:
        db.rollback()
        user.email = f"{provider_name}_{provider_user_id}@oauth.local"
        user.is_verified = False
        oauth_email = None
        db.commit()
    db.refresh(user)
    
    from app.models import UserProfile, AvatarType, Role
    from app.models.models import user_roles
    guest_role = db.query(Role).filter(Role.code == 'guest').first()
    if guest_role:
        db.execute(
            user_roles.insert().values(
                user_id=user.id,
                role_id=guest_role.id,
                assigned_by=1
            )
        )
        db.commit()
    gradient = [f"#{hash(user.username) % 16777215:06x}", f"#{(hash(user.username) + 1000) % 16777215:06x}"]
    profile = UserProfile(
        user_id=user.id,
        avatar_type=AvatarType.default,
        default_avatar_gradient=gradient,
        oauth_avatar_url=avatar
    )
    db.add(profile)
    
    connection = OAuthConnection(
        user_id=user.id,
        provider_id=provider.id,
        provider_user_id=provider_user_id,
        access_token=access_token,
        refresh_token=token_data.get("refresh_token")
    )
    db.add(connection)
    db.commit()
    
    from app.api.v1.auth import send_register_notification_bg
    send_register_notification_bg(
        new_username=user.username,
        new_email=user.email
    )
    
    if user.is_verified and oauth_email:
        jwt_token = create_access_token(data={"sub": user.username})
        refresh_token_obj = create_refresh_token(db=db, user_id=user.id, request=None)
        
        params = {
            "access_token": jwt_token,
            "token_type": "bearer",
            "refresh_token": refresh_token_obj.token,
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "user_id": user.id,
            "username": user.username,
            "email": user.email,
            "avatar": user.avatar or "",
            "is_admin": str(PermissionService.is_admin_user(db, user.id)).lower(),
            "needs_email": "false"
        }
        return RedirectResponse(url=f"{settings.FRONTEND_URL}/oauth/callback/{provider_name}?{urlencode(params)}")
    
    import uuid
    temp_token = str(uuid.uuid4())
    
    from app.services.email_service import EmailService
    actual_token = EmailService.store_oauth_temp_token(
        db=db,
        temp_token=temp_token,
        user_id=user.id,
        provider_name=provider_name,
        provider_user_id=provider_user_id
    )
    
    params = {
        "access_token": "",
        "token_type": "bearer",
        "user_id": user.id,
        "username": user.username,
        "email": "",
        "avatar": user.avatar or "",
        "is_admin": str(PermissionService.is_admin_user(db, user.id)).lower(),
        "needs_email": "true",
        "temp_token": actual_token
    }
    return RedirectResponse(url=f"{settings.FRONTEND_URL}/oauth/callback/{provider_name}?{urlencode(params)}")


@router.post("/submit-email", response_model=OAuthEmailVerifyResponse)
async def oauth_submit_email(
    data: OAuthEmailVerifyRequest,
    db: Session = Depends(get_db)
):
    from app.services.email_service import EmailService
    from app.models import User
    
    existing_user = db.query(User).filter(User.email == data.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="该邮箱已被使用")
    
    temp_token_record = db.query(OAuthTempToken).filter(
        OAuthTempToken.temp_token == data.temp_token if hasattr(data, 'temp_token') else None
    ).first() if hasattr(data, 'temp_token') else None
    
    return OAuthEmailVerifyResponse(
        message="请检查您的邮箱获取验证链接",
        temp_token=data.temp_token if hasattr(data, 'temp_token') else ""
    )


class OAuthSubmitEmailRequest(BaseModel):
    email: str
    temp_token: str


@router.post("/submit-email-with-token", response_model=OAuthEmailVerifyResponse)
async def oauth_submit_email_with_token(
    data: OAuthSubmitEmailRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    from app.models import User, OAuthTempToken
    
    existing_user = db.query(User).filter(User.email == data.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="该邮箱已被使用")
    
    temp_token_record = db.query(OAuthTempToken).filter(
        OAuthTempToken.temp_token == data.temp_token
    ).first()
    if not temp_token_record:
        raise HTTPException(status_code=400, detail="无效或过期的临时令牌")
    
    user = db.query(User).filter(User.id == temp_token_record.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    user.email = data.email
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=400, detail="该邮箱已被使用，请使用其他邮箱")
    
    background_tasks.add_task(
        send_oauth_email_verification_bg,
        data.email,
        user.username,
        data.temp_token,
        temp_token_record.provider_name
    )
    
    return OAuthEmailVerifyResponse(
        message="验证邮件已发送，请检查您的邮箱",
        temp_token=data.temp_token
    )


@router.get("/verify-email", response_model=OAuthCallbackResponse)
async def oauth_verify_email(
    token: str,
    email: str,
    db: Session = Depends(get_db)
):
    from app.services.email_service import EmailService
    from app.models import User, OAuthTempToken
    from app.utils.timezone import get_db_now
    
    temp_token_record = db.query(OAuthTempToken).filter(
        OAuthTempToken.temp_token == token
    ).first()
    
    if not temp_token_record:
        user = db.query(User).filter(User.email == email, User.is_verified == True).first()
        if user:
            jwt_token = create_access_token(data={"sub": user.username})
            refresh_token_obj = create_refresh_token(db=db, user_id=user.id, request=None)
            
            roles = PermissionService.get_user_roles(db, user.id)
            roles_data = [{"id": r.id, "name": r.name, "code": r.code} for r in roles] if roles else []
            
            return OAuthCallbackResponse(
                access_token=jwt_token,
                token_type="bearer",
                refresh_token=refresh_token_obj.token,
                expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                user={
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "avatar": user.avatar,
                    "bio": user.bio,
                    "is_admin": PermissionService.is_admin_user(db, user.id),
                    "is_verified": user.is_verified,
                    "created_at": user.created_at,
                    "roles": roles_data
                },
                needs_email=False
            )
        raise HTTPException(status_code=400, detail="无效或过期的验证链接")
    
    if temp_token_record.expires_at:
        now = get_db_now()
        if temp_token_record.expires_at < now:
            raise HTTPException(status_code=400, detail="验证链接已过期，请重新获取")
    
    user = db.query(User).filter(User.id == temp_token_record.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    existing_user = db.query(User).filter(User.email == email, User.id != user.id).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="该邮箱已被其他用户使用")
    
    user.email = email
    user.is_verified = True
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=400, detail="该邮箱已被其他用户使用，请更换邮箱重新验证")
    
    jwt_token = create_access_token(data={"sub": user.username})
    refresh_token_obj = create_refresh_token(db=db, user_id=user.id, request=None)
    
    roles = PermissionService.get_user_roles(db, user.id)
    roles_data = [{"id": r.id, "name": r.name, "code": r.code} for r in roles] if roles else []
    
    return OAuthCallbackResponse(
        access_token=jwt_token,
        token_type="bearer",
        refresh_token=refresh_token_obj.token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user={
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "avatar": user.avatar,
            "bio": user.bio,
            "is_admin": PermissionService.is_admin_user(db, user.id),
            "is_verified": user.is_verified,
            "created_at": user.created_at,
            "roles": roles_data
        },
        needs_email=False
    )


class ResendVerificationRequest(BaseModel):
    temp_token: str


class ChangeEmailRequest(BaseModel):
    temp_token: str
    new_email: str


@router.post("/resend-verification")
async def resend_oauth_verification(
    data: ResendVerificationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    from app.models import OAuthTempToken
    from app.utils.timezone import get_db_now
    
    temp_token_record = db.query(OAuthTempToken).filter(
        OAuthTempToken.temp_token == data.temp_token
    ).first()
    if not temp_token_record:
        raise HTTPException(status_code=400, detail="无效或过期的临时令牌")
    
    user = db.query(User).filter(User.id == temp_token_record.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    if user.is_verified:
        raise HTTPException(status_code=400, detail="邮箱已验证")
    
    current_email = user.email
    if not current_email or current_email.endswith('@oauth.local'):
        raise HTTPException(status_code=400, detail="请先设置邮箱地址")
    
    temp_token_record.expires_at = get_db_now() + timedelta(hours=24)
    db.commit()
    
    background_tasks.add_task(
        send_oauth_email_verification_bg,
        current_email,
        user.username,
        data.temp_token,
        temp_token_record.provider_name
    )
    
    return {
        "message": "验证邮件已重新发送",
        "email": current_email,
        "delivery_time": "10秒内",
        "expires_at": temp_token_record.expires_at.isoformat() + "Z"
    }


@router.post("/change-email")
async def change_oauth_email(
    data: ChangeEmailRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    from app.models import OAuthTempToken
    from app.utils.timezone import get_db_now
    
    temp_token_record = db.query(OAuthTempToken).filter(
        OAuthTempToken.temp_token == data.temp_token
    ).first()
    if not temp_token_record:
        raise HTTPException(status_code=400, detail="无效或过期的临时令牌")
    
    user = db.query(User).filter(User.id == temp_token_record.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    existing_user = db.query(User).filter(User.email == data.new_email, User.id != user.id).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="该邮箱已被其他用户使用")
    
    user.email = data.new_email
    temp_token_record.expires_at = get_db_now() + timedelta(hours=24)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=400, detail="该邮箱已被其他用户使用，请使用其他邮箱")
    
    background_tasks.add_task(
        send_oauth_email_verification_bg,
        data.new_email,
        user.username,
        data.temp_token,
        temp_token_record.provider_name
    )
    
    return {
        "message": "验证邮件已发送到新邮箱",
        "email": data.new_email,
        "delivery_time": "10秒内",
        "expires_at": temp_token_record.expires_at.isoformat() + "Z"
    }


@router.get("/pending-verification/{temp_token}")
async def get_pending_verification_info(
    temp_token: str,
    db: Session = Depends(get_db)
):
    from app.models import OAuthTempToken
    from app.utils.timezone import get_db_now
    
    temp_token_record = db.query(OAuthTempToken).filter(
        OAuthTempToken.temp_token == temp_token
    ).first()
    
    if not temp_token_record:
        raise HTTPException(status_code=400, detail="无效或过期的临时令牌")
    
    user = db.query(User).filter(User.id == temp_token_record.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    current_email = user.email
    has_email = current_email and not current_email.endswith('@oauth.local')
    
    is_expired = False
    if temp_token_record.expires_at:
        now = get_db_now()
        if temp_token_record.expires_at < now:
            is_expired = True
    
    return {
        "username": user.username,
        "has_email": has_email,
        "email": current_email if has_email else None,
        "is_verified": user.is_verified,
        "provider_name": temp_token_record.provider_name,
        "expires_at": temp_token_record.expires_at.isoformat() + "Z" if temp_token_record.expires_at else None,
        "is_expired": is_expired
    }
