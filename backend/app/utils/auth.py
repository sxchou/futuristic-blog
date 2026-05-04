import bcrypt
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
import secrets
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import get_db
from app.models import User, RefreshToken
from app.utils.timezone import get_now, get_db_now

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    if not hashed_password:
        return False
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except (ValueError, TypeError):
        return False


def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def create_refresh_token_value() -> str:
    return secrets.token_urlsafe(64)


def create_refresh_token(
    db: Session,
    user_id: int,
    request: Optional[Request] = None,
    device_fingerprint: Optional[str] = None
) -> RefreshToken:
    token_value = create_refresh_token_value()
    expires_at = get_db_now() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    ip_address = None
    user_agent = None
    if request:
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            ip_address = forwarded.split(",")[0].strip()
        elif request.client:
            ip_address = request.client.host
        user_agent = request.headers.get("User-Agent", "")[:500]
    
    refresh_token = RefreshToken(
        token=token_value,
        user_id=user_id,
        ip_address=ip_address,
        user_agent=user_agent,
        device_fingerprint=device_fingerprint,
        expires_at=expires_at,
        last_used_at=get_db_now()
    )
    db.add(refresh_token)
    db.commit()
    db.refresh(refresh_token)
    return refresh_token


def verify_refresh_token(
    db: Session,
    token_value: str,
    request: Optional[Request] = None
) -> Tuple[Optional[RefreshToken], Optional[str]]:
    refresh_token = db.query(RefreshToken).filter(
        RefreshToken.token == token_value,
        RefreshToken.is_revoked == False
    ).first()
    
    if not refresh_token:
        return None, "无效的刷新令牌"
    
    now = get_db_now()
    if refresh_token.expires_at < now:
        return None, "刷新令牌已过期"
    
    if request:
        forwarded = request.headers.get("X-Forwarded-For")
        current_ip = None
        if forwarded:
            current_ip = forwarded.split(",")[0].strip()
        elif request.client:
            current_ip = request.client.host
        
        if refresh_token.ip_address and current_ip and refresh_token.ip_address != current_ip:
            refresh_token.is_revoked = True
            refresh_token.revoked_at = get_db_now()
            refresh_token.revoked_reason = "IP地址变更"
            db.commit()
            return None, "检测到IP地址变更，请重新登录"
    
    return refresh_token, None


def update_refresh_token_usage(db: Session, refresh_token: RefreshToken) -> None:
    refresh_token.last_used_at = get_db_now()
    db.commit()


def revoke_refresh_token(db: Session, token_value: str, reason: str = "用户登出") -> bool:
    refresh_token = db.query(RefreshToken).filter(
        RefreshToken.token == token_value
    ).first()
    
    if refresh_token and not refresh_token.is_revoked:
        refresh_token.is_revoked = True
        refresh_token.revoked_at = get_db_now()
        refresh_token.revoked_reason = reason
        db.commit()
        return True
    return False


def revoke_all_user_tokens(db: Session, user_id: int, reason: str = "安全措施") -> int:
    count = db.query(RefreshToken).filter(
        RefreshToken.user_id == user_id,
        RefreshToken.is_revoked == False
    ).update({
        "is_revoked": True,
        "revoked_at": get_db_now(),
        "revoked_reason": reason
    })
    db.commit()
    return count


def cleanup_expired_tokens(db: Session) -> int:
    count = db.query(RefreshToken).filter(
        RefreshToken.expires_at < get_db_now()
    ).delete()
    db.commit()
    return count


def decode_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None


async def get_current_user_optional(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> Optional[User]:
    if token is None:
        return None
    payload = decode_token(token)
    if payload is None:
        return None
    username: str = payload.get("sub")
    if username is None:
        return None
    user = db.query(User).filter(User.username == username).first()
    return user


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if token is None:
        raise credentials_exception
    payload = decode_token(token)
    if payload is None:
        raise credentials_exception
    username: str = payload.get("sub")
    if username is None:
        raise credentials_exception
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    return user


async def get_current_admin_user(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> User:
    from app.services.permission_service import PermissionService
    if not PermissionService.is_admin_user(db, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


get_current_active_user = get_current_admin_user
