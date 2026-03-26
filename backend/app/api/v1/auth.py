from datetime import timedelta, datetime
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.core.config import settings
from app.models import User, EmailLog, NotificationSettings, PasswordReset, RefreshToken
from app.schemas import UserCreate, UserResponse, Token, PasswordResetRequest, PasswordResetVerify, RefreshTokenRequest, SessionInfo
from app.utils import (
    verify_password, get_password_hash, create_access_token, get_current_user,
    create_refresh_token, verify_refresh_token, update_refresh_token_usage,
    revoke_refresh_token, revoke_all_user_tokens
)
from app.services.email_service import EmailService
from app.services.log_service import log_login_sync
from app.utils.timezone import get_now, get_db_now
import random
import string

router = APIRouter(prefix="/auth", tags=["Authentication"])


def send_register_notification_bg(new_username: str, new_email: str):
    from app.core.database import SessionLocal
    db = SessionLocal()
    try:
        notification_settings = db.query(NotificationSettings).first()
        if notification_settings and notification_settings.notify_on_register:
            EmailService.send_new_user_notification_db(
                db=db,
                new_username=new_username,
                new_email=new_email
            )
    except Exception as e:
        print(f"Failed to send register notification: {e}")
    finally:
        db.close()


def send_verification_email_bg(email: str, username: str, token: str, user_id: int):
    from app.core.database import SessionLocal
    db = SessionLocal()
    try:
        EmailService.send_verification_email_db(
            db=db,
            email=email,
            username=username,
            token=token,
            user_id=user_id
        )
    except Exception as e:
        print(f"Failed to send verification email: {e}")
    finally:
        db.close()


@router.post("/login", response_model=Token)
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(
        (User.username == form_data.username) | (User.email == form_data.username)
    ).first()
    
    if not user:
        log_login_sync(
            username=form_data.username,
            login_type="login",
            request=request,
            status="failed",
            fail_reason="用户不存在"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not verify_password(form_data.password, user.hashed_password):
        log_login_sync(
            user_id=user.id,
            username=user.username,
            login_type="login",
            request=request,
            status="failed",
            fail_reason="密码错误"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_verified and not user.is_admin:
        log_login_sync(
            user_id=user.id,
            username=user.username,
            login_type="login",
            request=request,
            status="failed",
            fail_reason="邮箱未验证"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "message": "请先验证您的邮箱后再登录",
                "email": user.email,
                "need_verification": True
            },
        )
    
    log_login_sync(
        user_id=user.id,
        username=user.username,
        login_type="login",
        request=request,
        status="success"
    )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    refresh_token = create_refresh_token(
        db=db,
        user_id=user.id,
        request=request
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "refresh_token": refresh_token.token,
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }


@router.post("/register", response_model=UserResponse)
async def register(
    user_data: UserCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    existing_user = db.query(User).filter(
        (User.username == user_data.username) | (User.email == user_data.email)
    ).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名或邮箱已被注册"
        )
    
    hashed_password = get_password_hash(user_data.password)
    verification_token = EmailService.generate_verification_token()
    token_expiry = EmailService.get_token_expiry()
    
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password,
        is_admin=False,
        is_verified=False,
        verification_token=verification_token,
        verification_token_expires=token_expiry
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    background_tasks.add_task(
        send_verification_email_bg,
        new_user.email,
        new_user.username,
        verification_token,
        new_user.id
    )
    
    background_tasks.add_task(
        send_register_notification_bg,
        new_user.username,
        new_user.email
    )
    
    return new_user


@router.post("/verify-email")
async def verify_email(
    token: str,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.verification_token == token).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的验证链接"
        )
    
    from app.utils.timezone import get_db_now
    now = get_db_now()
    token_expires = user.verification_token_expires
    if token_expires:
        if token_expires.tzinfo is None:
            if token_expires < now:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="验证链接已过期，请重新发送验证邮件"
                )
        elif token_expires < now:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="验证链接已过期，请重新发送验证邮件"
            )
    
    user.is_verified = True
    user.verification_token = None
    user.verification_token_expires = None
    
    email_log = db.query(EmailLog).filter(EmailLog.verification_token == token).first()
    if email_log:
        email_log.is_verified = True
        email_log.verified_at = get_db_now()
    
    db.commit()
    
    access_token = create_access_token(
        data={"sub": user.username, "user_id": user.id}
    )
    refresh_token = create_refresh_token(
        data={"sub": user.username, "user_id": user.id}
    )
    
    refresh_token_obj = RefreshToken(
        token=refresh_token,
        user_id=user.id,
        expires_at=datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    )
    db.add(refresh_token_obj)
    db.commit()
    
    return {
        "message": "邮箱验证成功",
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "is_admin": user.is_admin,
            "is_verified": user.is_verified
        }
    }


@router.post("/resend-verification")
async def resend_verification(
    email: str,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == email).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="该邮箱未注册"
        )
    
    if user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该邮箱已验证"
        )
    
    verification_token = EmailService.generate_verification_token()
    token_expiry = EmailService.get_token_expiry()
    
    user.verification_token = verification_token
    user.verification_token_expires = token_expiry
    db.commit()
    
    EmailService.send_verification_email_db(
        db=db,
        email=user.email,
        username=user.username,
        token=verification_token,
        user_id=user.id
    )
    
    return {"message": "验证邮件已发送，请查收"}


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/refresh", response_model=Token)
async def refresh_token(
    request: Request,
    data: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    refresh_token_obj, error = verify_refresh_token(db, data.refresh_token, request)
    
    if error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error,
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = db.query(User).filter(User.id == refresh_token_obj.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_verified and not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="账户未验证"
        )
    
    update_refresh_token_usage(db, refresh_token_obj)
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "refresh_token": refresh_token_obj.token,
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }


@router.post("/logout")
async def logout(
    request: Request,
    data: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    revoke_refresh_token(db, data.refresh_token, "用户登出")
    return {"message": "登出成功"}


@router.post("/logout-all")
async def logout_all(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    count = revoke_all_user_tokens(db, current_user.id, "用户登出所有设备")
    return {"message": f"已登出 {count} 个设备"}


@router.get("/sessions", response_model=List[SessionInfo])
async def get_sessions(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    current_token = request.headers.get("X-Refresh-Token")
    
    sessions = db.query(RefreshToken).filter(
        RefreshToken.user_id == current_user.id,
        RefreshToken.is_revoked == False,
        RefreshToken.expires_at > get_db_now()
    ).order_by(RefreshToken.last_used_at.desc()).all()
    
    return [
        SessionInfo(
            id=session.id,
            ip_address=session.ip_address,
            user_agent=session.user_agent,
            last_used_at=session.last_used_at,
            created_at=session.created_at,
            is_current=(session.token == current_token)
        )
        for session in sessions
    ]


@router.delete("/sessions/{session_id}")
async def revoke_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    session = db.query(RefreshToken).filter(
        RefreshToken.id == session_id,
        RefreshToken.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="会话不存在"
        )
    
    session.is_revoked = True
    session.revoked_at = get_db_now()
    session.revoked_reason = "用户手动撤销"
    db.commit()
    
    return {"message": "会话已撤销"}


MAX_RESET_REQUESTS_PER_HOUR = 5
RESET_CODE_EXPIRE_MINUTES = 15


def generate_reset_code() -> str:
    return ''.join(random.choices(string.digits, k=6))


def get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


@router.post("/password-reset/request")
async def request_password_reset(
    request: Request,
    data: PasswordResetRequest,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == data.email).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="该邮箱未注册，请检查或注册新账号"
        )
    
    client_ip = get_client_ip(request)
    one_hour_ago = get_db_now() - timedelta(hours=1)
    
    email_requests = db.query(PasswordReset).filter(
        PasswordReset.email == data.email,
        PasswordReset.created_at >= one_hour_ago
    ).count()
    
    if email_requests >= MAX_RESET_REQUESTS_PER_HOUR:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="请求次数过多，请1小时后再试"
        )
    
    ip_requests = db.query(PasswordReset).filter(
        PasswordReset.ip_address == client_ip,
        PasswordReset.created_at >= one_hour_ago
    ).count()
    
    if ip_requests >= MAX_RESET_REQUESTS_PER_HOUR:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="请求次数过多，请1小时后再试"
        )
    
    code = generate_reset_code()
    expires_at = get_db_now() + timedelta(minutes=RESET_CODE_EXPIRE_MINUTES)
    
    password_reset = PasswordReset(
        email=data.email,
        code=code,
        ip_address=client_ip,
        expires_at=expires_at
    )
    db.add(password_reset)
    db.commit()
    
    try:
        EmailService.send_password_reset_email_db(
            db=db,
            email=user.email,
            username=user.username,
            code=code
        )
    except Exception as e:
        print(f"Failed to send password reset email: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="发送验证码失败，请稍后重试"
        )
    
    return {
        "message": "验证码已发送至您的邮箱",
        "expires_in": RESET_CODE_EXPIRE_MINUTES * 60
    }


@router.post("/password-reset/verify")
async def verify_password_reset(
    data: PasswordResetVerify,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == data.email).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="该邮箱未注册"
        )
    
    now = get_db_now()
    reset_record = db.query(PasswordReset).filter(
        PasswordReset.email == data.email,
        PasswordReset.code == data.code,
        PasswordReset.is_used == False,
        PasswordReset.expires_at > now
    ).first()
    
    if not reset_record:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="验证码无效或已过期"
        )
    
    reset_record.is_used = True
    reset_record.used_at = now
    
    user.hashed_password = get_password_hash(data.new_password)
    
    db.commit()
    
    return {"message": "密码已重置，请使用新密码登录"}
