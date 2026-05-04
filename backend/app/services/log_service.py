import json
from typing import Optional
from datetime import datetime
from fastapi import Request
from sqlalchemy.orm import Session
from app.models import OperationLog, LoginLog, AccessLog
from app.core.database import SessionLocal
from app.utils.timezone import get_now


def get_client_ip(request: Request) -> Optional[str]:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else None


def get_user_agent(request: Request) -> Optional[str]:
    return request.headers.get("User-Agent")


def parse_user_agent(user_agent: str) -> dict:
    result = {
        "browser": "Unknown",
        "os": "Unknown",
        "device": "Desktop"
    }
    
    if not user_agent:
        return result
    
    ua_lower = user_agent.lower()
    
    if "edg/" in ua_lower:
        result["browser"] = "Edge"
    elif "chrome/" in ua_lower:
        result["browser"] = "Chrome"
    elif "firefox/" in ua_lower:
        result["browser"] = "Firefox"
    elif "safari/" in ua_lower and "chrome/" not in ua_lower:
        result["browser"] = "Safari"
    elif "opera/" in ua_lower or "opr/" in ua_lower:
        result["browser"] = "Opera"
    
    if "windows" in ua_lower:
        result["os"] = "Windows"
    elif "mac" in ua_lower:
        result["os"] = "macOS"
    elif "linux" in ua_lower:
        result["os"] = "Linux"
    elif "android" in ua_lower:
        result["os"] = "Android"
        result["device"] = "Mobile"
    elif "iphone" in ua_lower or "ipad" in ua_lower:
        result["os"] = "iOS"
        result["device"] = "Mobile"
    
    return result


class LogService:
    @staticmethod
    def log_operation(
        db: Session,
        user_id: Optional[int] = None,
        username: Optional[str] = None,
        action: str = "",
        module: str = "",
        description: Optional[str] = None,
        target_type: Optional[str] = None,
        target_id: Optional[int] = None,
        request: Optional[Request] = None,
        status: str = "success",
        error_message: Optional[str] = None
    ) -> OperationLog:
        log = OperationLog(
            user_id=user_id,
            username=username,
            action=action,
            module=module,
            description=description,
            target_type=target_type,
            target_id=target_id,
            status=status,
            error_message=error_message
        )
        
        if request:
            log.request_method = request.method
            log.request_url = str(request.url.path)
            log.ip_address = get_client_ip(request)
            log.user_agent = get_user_agent(request)
        
        db.add(log)
        db.commit()
        return log
    
    @staticmethod
    def log_login(
        db: Session,
        user_id: Optional[int] = None,
        username: Optional[str] = None,
        login_type: str = "login",
        request: Optional[Request] = None,
        status: str = "success",
        fail_reason: Optional[str] = None
    ) -> LoginLog:
        log = LoginLog(
            user_id=user_id,
            username=username,
            login_type=login_type,
            status=status,
            fail_reason=fail_reason
        )
        
        if request:
            log.ip_address = get_client_ip(request)
            user_agent = get_user_agent(request)
            log.user_agent = user_agent
            
            if user_agent:
                parsed = parse_user_agent(user_agent)
                log.browser = parsed["browser"]
                log.os = parsed["os"]
                log.device = parsed["device"]
        
        db.add(log)
        db.commit()
        return log
    
    @staticmethod
    def log_access(
        db: Session,
        request: Request,
        response_status: int,
        response_time: float,
        user_id: Optional[int] = None,
        username: Optional[str] = None
    ) -> AccessLog:
        log = AccessLog(
            user_id=user_id,
            username=username,
            request_method=request.method,
            request_path=str(request.url.path),
            request_query=str(request.url.query) if request.url.query else None,
            response_status=response_status,
            response_time=response_time,
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request),
            referer=request.headers.get("Referer")
        )
        db.add(log)
        db.commit()
        return log


def log_operation_sync(
    user_id: Optional[int] = None,
    username: Optional[str] = None,
    action: str = "",
    module: str = "",
    description: Optional[str] = None,
    target_type: Optional[str] = None,
    target_id: Optional[int] = None,
    request: Optional[Request] = None,
    status: str = "success",
    error_message: Optional[str] = None
):
    db = SessionLocal()
    try:
        LogService.log_operation(
            db=db,
            user_id=user_id,
            username=username,
            action=action,
            module=module,
            description=description,
            target_type=target_type,
            target_id=target_id,
            request=request,
            status=status,
            error_message=error_message
        )
    finally:
        db.close()


def log_login_sync(
    user_id: Optional[int] = None,
    username: Optional[str] = None,
    login_type: str = "login",
    request: Optional[Request] = None,
    status: str = "success",
    fail_reason: Optional[str] = None
):
    db = SessionLocal()
    try:
        LogService.log_login(
            db=db,
            user_id=user_id,
            username=username,
            login_type=login_type,
            request=request,
            status=status,
            fail_reason=fail_reason
        )
    finally:
        db.close()
