from datetime import timedelta, datetime
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.config import settings
from app.models import User, EmailLog, NotificationSettings
from app.schemas import UserCreate, UserResponse, Token
from app.utils import verify_password, get_password_hash, create_access_token, get_current_user
from app.services.email_service import EmailService
from app.services.log_service import log_login_sync
from app.utils.timezone import get_now

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
    return {"access_token": access_token, "token_type": "bearer"}


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
    
    from datetime import datetime
    now = datetime.now()
    if user.verification_token_expires and user.verification_token_expires < now:
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
        email_log.verified_at = datetime.now()
    
    db.commit()
    
    return {"message": "邮箱验证成功，您现在可以登录了"}


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
