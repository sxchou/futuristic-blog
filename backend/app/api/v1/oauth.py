from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from app.core.database import get_db
from app.utils.auth import create_access_token
from app.models import OAuthProvider, OAuthConnection, User
from app.core.config import settings
import httpx
import secrets
from datetime import datetime

router = APIRouter(prefix="/oauth", tags=["oauth"])


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
    user: dict


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
def create_oauth_provider(data: OAuthProviderCreate, db: Session = Depends(get_db)):
    existing = db.query(OAuthProvider).filter(OAuthProvider.name == data.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Provider already exists")
    
    provider = OAuthProvider(**data.model_dump())
    db.add(provider)
    db.commit()
    db.refresh(provider)
    
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
def update_oauth_provider(provider_id: int, data: OAuthProviderUpdate, db: Session = Depends(get_db)):
    provider = db.query(OAuthProvider).filter(OAuthProvider.id == provider_id).first()
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(provider, key, value)
    
    db.commit()
    db.refresh(provider)
    
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
def delete_oauth_provider(provider_id: int, db: Session = Depends(get_db)):
    provider = db.query(OAuthProvider).filter(OAuthProvider.id == provider_id).first()
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    
    db.delete(provider)
    db.commit()
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


@router.get("/callback/{provider_name}", response_model=OAuthCallbackResponse)
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
        raise HTTPException(status_code=404, detail="Provider not found")
    
    if not check_provider_configured(provider):
        raise HTTPException(status_code=400, detail="Provider not properly configured")
    
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
    
    provider_user_id = None
    email = None
    name = None
    avatar = None
    
    if provider_name == "google":
        provider_user_id = user_info.get("id")
        email = user_info.get("email")
        name = user_info.get("name")
        avatar = user_info.get("picture")
    elif provider_name == "github":
        provider_user_id = str(user_info.get("id"))
        email = user_info.get("email")
        name = user_info.get("login")
        avatar = user_info.get("avatar_url")
    elif provider_name == "twitter" or provider_name == "x":
        provider_user_id = user_info.get("data", {}).get("id")
        email = user_info.get("data", {}).get("email")
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
    
    if connection:
        user = connection.user
    else:
        if not email:
            email = f"{provider_name}_{provider_user_id}@oauth.local"
        
        user = db.query(User).filter(User.email == email).first()
        
        if not user:
            username = name or f"{provider_name}_{provider_user_id}"
            base_username = username
            counter = 1
            while db.query(User).filter(User.username == username).first():
                username = f"{base_username}_{counter}"
                counter += 1
            
            user = User(
                username=username,
                email=email,
                hashed_password="",
                is_verified=True,
                avatar=avatar
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        
        connection = OAuthConnection(
            user_id=user.id,
            provider_id=provider.id,
            provider_user_id=provider_user_id,
            access_token=access_token,
            refresh_token=token_data.get("refresh_token")
        )
        db.add(connection)
        db.commit()
    
    jwt_token = create_access_token(data={"sub": user.username})
    
    return OAuthCallbackResponse(
        access_token=jwt_token,
        token_type="bearer",
        user={
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "avatar": user.avatar,
            "is_admin": user.is_admin
        }
    )
