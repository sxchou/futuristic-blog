from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.config import settings
from app.models import EmailConfig, EmailLog, User
from app.schemas import (
    EmailConfigCreate, 
    EmailConfigUpdate, 
    EmailConfigResponse, 
    EmailLogResponse,
    EmailTestRequest,
    PaginatedResponse
)
from app.utils import get_current_admin_user
from app.services.log_service import LogService
from app.utils.timezone import get_now
import smtplib
import socket
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

router = APIRouter(prefix="/email", tags=["Email Management"])

EMAIL_PROVIDERS = {
    'qq': {
        'host': 'smtp.qq.com',
        'port': 587,
        'ssl_port': 465,
        'name': 'QQ邮箱',
        'description': '使用QQ邮箱SMTP服务，需要开启SMTP服务并获取授权码',
        'use_ssl': False
    },
    'gmail': {
        'host': 'smtp.gmail.com',
        'port': 587,
        'ssl_port': 465,
        'name': 'Gmail',
        'description': '使用Gmail SMTP服务，需要开启两步验证并生成应用专用密码',
        'use_ssl': True
    }
}


def get_active_email_config(db: Session) -> Optional[EmailConfig]:
    return db.query(EmailConfig).filter(EmailConfig.is_active == True).first()


def send_email_with_config(
    config: EmailConfig,
    to_email: str,
    subject: str,
    html_content: str,
    db: Session,
    email_type: str = "test",
    recipient_name: str = None,
    user_id: int = None,
    verification_token: str = None
) -> dict:
    log = EmailLog(
        email_type=email_type,
        recipient_email=to_email,
        recipient_name=recipient_name,
        subject=subject,
        status='pending',
        verification_token=verification_token,
        user_id=user_id
    )
    
    try:
        provider_config = EMAIL_PROVIDERS.get(config.provider)
        if not provider_config:
            raise ValueError(f"Unknown email provider: {config.provider}")
        
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f"{config.from_name} <{config.from_email}>"
        msg['To'] = to_email
        
        html_part = MIMEText(html_content, 'html', 'utf-8')
        msg.attach(html_part)
        
        host = provider_config['host']
        use_ssl = provider_config.get('use_ssl', False)
        last_error = None
        
        if use_ssl:
            ports_to_try = [465, 587]
        else:
            ports_to_try = [587, 465]
        
        for port in ports_to_try:
            try:
                if port == 465:
                    server = smtplib.SMTP_SSL(host, port, timeout=10)
                else:
                    server = smtplib.SMTP(host, port, timeout=10)
                    server.starttls()
                
                server.login(config.smtp_user, config.smtp_password)
                server.sendmail(config.from_email, to_email, msg.as_string())
                server.quit()
                
                log.status = 'sent'
                log.sent_at = get_now()
                
                return {'success': True, 'message': 'Email sent successfully'}
                
            except (smtplib.SMTPException, socket.error, socket.timeout) as e:
                last_error = str(e)
                continue
        
        raise Exception(f"All connection attempts failed. Last error: {last_error}")
        
    except Exception as e:
        log.status = 'failed'
        log.error_message = str(e)
        return {'success': False, 'error': str(e)}
        
    finally:
        db.add(log)
        db.commit()


@router.get("/providers")
async def get_email_providers():
    return {
        "providers": [
            {
                "id": key,
                "name": info['name'],
                "host": info['host'],
                "port": info['port'],
                "ssl_port": info['ssl_port'],
                "description": info['description'],
                "use_ssl": info.get('use_ssl', False)
            }
            for key, info in EMAIL_PROVIDERS.items()
        ]
    }


@router.get("/configs", response_model=List[EmailConfigResponse])
async def get_all_email_configs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    configs = db.query(EmailConfig).order_by(EmailConfig.created_at.desc()).all()
    return configs


@router.get("/config", response_model=Optional[EmailConfigResponse])
async def get_active_config(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    config = get_active_email_config(db)
    return config


@router.post("/config", response_model=EmailConfigResponse)
async def create_email_config(
    config_data: EmailConfigCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    provider_config = EMAIL_PROVIDERS.get(config_data.provider)
    if not provider_config:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不支持的邮箱提供商"
        )
    
    new_config = EmailConfig(
        provider=config_data.provider,
        smtp_host=provider_config['host'],
        smtp_port=provider_config['port'],
        smtp_user=config_data.smtp_user,
        smtp_password=config_data.smtp_password,
        from_email=config_data.from_email,
        from_name=config_data.from_name,
        is_active=False
    )
    
    db.add(new_config)
    db.commit()
    db.refresh(new_config)
    
    LogService.log_operation(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        action="创建",
        module="邮件管理",
        description=f"创建邮箱配置: {provider_config['name']} - {config_data.smtp_user}",
        target_type="邮箱配置",
        target_id=new_config.id,
        request=request,
        status="success"
    )
    
    return new_config


@router.put("/config/{config_id}", response_model=EmailConfigResponse)
async def update_email_config(
    config_id: int,
    config_data: EmailConfigUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    config = db.query(EmailConfig).filter(EmailConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")
    
    update_data = config_data.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(config, field, value)
    
    db.commit()
    db.refresh(config)
    
    LogService.log_operation(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        action="更新",
        module="邮件管理",
        description=f"更新邮箱配置: {config.smtp_user}",
        target_type="邮箱配置",
        target_id=config.id,
        request=request,
        status="success"
    )
    
    return config


@router.post("/config/{config_id}/activate")
async def activate_email_config(
    config_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    config = db.query(EmailConfig).filter(EmailConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")
    
    db.query(EmailConfig).update({EmailConfig.is_active: False})
    config.is_active = True
    db.commit()
    
    provider_name = EMAIL_PROVIDERS.get(config.provider, {}).get('name', config.provider)
    
    LogService.log_operation(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        action="激活",
        module="邮件管理",
        description=f"激活邮箱配置: {provider_name} - {config.smtp_user}",
        target_type="邮箱配置",
        target_id=config.id,
        request=request,
        status="success"
    )
    
    return {"message": f"已激活配置: {config.smtp_user}", "config": EmailConfigResponse.model_validate(config)}


@router.delete("/config/{config_id}")
async def delete_email_config(
    config_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    config = db.query(EmailConfig).filter(EmailConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")
    
    provider_name = EMAIL_PROVIDERS.get(config.provider, {}).get('name', config.provider)
    smtp_user = config.smtp_user
    was_active = config.is_active
    
    db.delete(config)
    db.commit()
    
    LogService.log_operation(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        action="删除",
        module="邮件管理",
        description=f"删除邮箱配置: {provider_name} - {smtp_user}",
        target_type="邮箱配置",
        target_id=config_id,
        request=request,
        status="success"
    )
    
    return {"message": "配置已删除", "was_active": was_active}


@router.post("/test")
async def test_email_config(
    test_data: EmailTestRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    config = get_active_email_config(db)
    if not config:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="没有激活的邮箱配置，请先选择并激活一个配置"
        )
    
    subject = f"[测试邮件] 来自 {config.from_name} 的测试"
    html_content = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; background: linear-gradient(135deg, #0f0f23 0%, #1a1a3e 100%); border-radius: 10px;">
        <div style="text-align: center; margin-bottom: 30px;">
            <h1 style="color: #00d4ff; margin: 0;">🎉 邮件配置测试成功</h1>
        </div>
        <div style="background: rgba(255,255,255,0.1); padding: 20px; border-radius: 8px; margin-bottom: 20px;">
            <p style="color: #ffffff; margin: 0 0 10px 0;">这是一封测试邮件，如果您收到此邮件，说明您的邮箱配置正确！</p>
            <p style="color: #a0a0a0; margin: 0;">发送时间: {get_now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
        <div style="text-align: center; color: #666; font-size: 12px;">
            <p>此邮件由 {config.from_name} 系统自动发送</p>
        </div>
    </div>
    """
    
    result = send_email_with_config(
        config=config,
        to_email=test_data.recipient_email,
        subject=subject,
        html_content=html_content,
        db=db,
        email_type='test',
        recipient_name=current_user.username,
        user_id=current_user.id
    )
    
    LogService.log_operation(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        action="测试",
        module="邮件管理",
        description=f"测试邮件发送: {test_data.recipient_email}",
        target_type="邮箱配置",
        target_id=config.id,
        request=request,
        status="success" if result['success'] else "failed"
    )
    
    if result['success']:
        return {"message": "测试邮件发送成功，请查收"}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"邮件发送失败: {result['error']}"
        )


@router.get("/logs", response_model=PaginatedResponse)
async def get_email_logs(
    page: int = 1,
    page_size: int = 20,
    email_type: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    query = db.query(EmailLog)
    
    if email_type:
        query = query.filter(EmailLog.email_type == email_type)
    if status:
        query = query.filter(EmailLog.status == status)
    
    total = query.count()
    total_pages = (total + page_size - 1) // page_size
    
    logs = query.order_by(EmailLog.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    
    return PaginatedResponse(
        items=[EmailLogResponse.model_validate(log) for log in logs],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/stats")
async def get_email_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    total_sent = db.query(EmailLog).filter(EmailLog.status == 'sent').count()
    total_failed = db.query(EmailLog).filter(EmailLog.status == 'failed').count()
    total_verified = db.query(EmailLog).filter(EmailLog.is_verified == True).count()
    total_pending = db.query(EmailLog).filter(EmailLog.status == 'pending').count()
    
    verification_rate = 0
    if total_sent > 0:
        verification_rate = round(total_verified / total_sent * 100, 1)
    
    return {
        "total_sent": total_sent,
        "total_failed": total_failed,
        "total_verified": total_verified,
        "total_pending": total_pending,
        "verification_rate": verification_rate
    }


@router.post("/logs/{log_id}/verify")
async def mark_email_verified(
    log_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    log = db.query(EmailLog).filter(EmailLog.id == log_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="记录不存在")
    
    log.is_verified = True
    log.verified_at = get_now()
    db.commit()
    
    LogService.log_operation(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        action="标记验证",
        module="邮件管理",
        description=f"标记邮件为已验证: {log.recipient_email}",
        target_type="邮件日志",
        target_id=log.id,
        request=request,
        status="success"
    )
    
    return {"message": "已标记为已验证"}


@router.get("/diagnose")
async def diagnose_network():
    import subprocess
    import platform
    
    results = {
        "timestamp": get_now().isoformat(),
        "platform": platform.platform(),
        "python_version": platform.python_version(),
        "tests": {}
    }
    
    smtp_hosts = [
        {"name": "QQ邮箱", "host": "smtp.qq.com", "ports": [587, 465]},
        {"name": "Gmail", "host": "smtp.gmail.com", "ports": [587, 465]},
        {"name": "163邮箱", "host": "smtp.163.com", "ports": [465, 25]},
    ]
    
    for smtp in smtp_hosts:
        host = smtp["host"]
        host_result = {
            "dns_resolution": None,
            "port_tests": {}
        }
        
        try:
            ip = socket.gethostbyname(host)
            host_result["dns_resolution"] = {
                "success": True,
                "ip": ip
            }
        except socket.gaierror as e:
            host_result["dns_resolution"] = {
                "success": False,
                "error": str(e)
            }
            results["tests"][smtp["name"]] = host_result
            continue
        except Exception as e:
            host_result["dns_resolution"] = {
                "success": False,
                "error": f"Unexpected error: {str(e)}"
            }
            results["tests"][smtp["name"]] = host_result
            continue
        
        for port in smtp["ports"]:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5)
                result = sock.connect_ex((host, port))
                sock.close()
                
                if result == 0:
                    host_result["port_tests"][port] = {
                        "success": True,
                        "message": "Port is open"
                    }
                else:
                    host_result["port_tests"][port] = {
                        "success": False,
                        "message": f"Connection refused (error code: {result})"
                    }
            except socket.timeout:
                host_result["port_tests"][port] = {
                    "success": False,
                    "message": "Connection timeout"
                }
            except OSError as e:
                host_result["port_tests"][port] = {
                    "success": False,
                    "message": f"OS Error: {str(e)} (errno: {e.errno if hasattr(e, 'errno') else 'unknown'})"
                }
            except Exception as e:
                host_result["port_tests"][port] = {
                    "success": False,
                    "message": f"Error: {str(e)}"
                }
        
        results["tests"][smtp["name"]] = host_result
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex(("8.8.8.8", 53))
        sock.close()
        results["internet_connection"] = {
            "success": result == 0,
            "message": "Google DNS (8.8.8.8:53)" + (" reachable" if result == 0 else " not reachable")
        }
    except Exception as e:
        results["internet_connection"] = {
            "success": False,
            "message": f"Error: {str(e)}"
        }
    
    env_config = {
        "SMTP_HOST": settings.SMTP_HOST if settings.SMTP_HOST else "Not configured",
        "SMTP_PORT": settings.SMTP_PORT if settings.SMTP_PORT else "Not configured",
        "SMTP_USER": "***" if settings.SMTP_USER else "Not configured",
        "SMTP_PASSWORD": "***" if settings.SMTP_PASSWORD else "Not configured",
        "SMTP_FROM_EMAIL": settings.SMTP_FROM_EMAIL if settings.SMTP_FROM_EMAIL else "Not configured",
        "is_email_configured": settings.is_email_configured
    }
    results["env_config"] = env_config
    
    return results
