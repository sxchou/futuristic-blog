import os
import logging
import time
from typing import List
from pathlib import Path
from io import BytesIO
from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.models import SiteConfig
from app.schemas.schemas import SiteConfigBase, SiteConfigResponse
from app.utils.auth import get_current_user
from app.services.log_service import LogService
from app.services.supabase_storage import supabase_storage
from app.core.config import settings

router = APIRouter(prefix="/site-config", tags=["Site Configuration"])
logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".ico", ".svg"}
MAX_FILE_SIZE = 2 * 1024 * 1024


def get_logo_base_path() -> Path:
    if settings.AVATAR_STORAGE_PATH:
        return Path(settings.AVATAR_STORAGE_PATH) / "logos"
    
    env_path = os.getenv("AVATAR_STORAGE_PATH") or os.getenv("RAILWAY_VOLUME_MOUNT_PATH")
    if env_path:
        return Path(env_path) / "logos"
    
    backend_dir = Path(__file__).parent.parent.parent.parent
    return backend_dir / "uploads" / "logos"


def ensure_logo_directory() -> Path:
    logo_path = get_logo_base_path()
    logo_path.mkdir(parents=True, exist_ok=True)
    return logo_path


def validate_logo_file(file: UploadFile) -> None:
    if not file.filename:
        raise HTTPException(status_code=400, detail="文件名不能为空")
    
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400, 
            detail=f"不支持的文件格式，仅支持: {', '.join(ALLOWED_EXTENSIONS)}"
        )


async def save_logo_file(file: UploadFile) -> str:
    ensure_logo_directory()
    
    ext = os.path.splitext(file.filename)[1].lower()
    timestamp = int(time.time() * 1000)
    filename = f"logo_{timestamp}{ext}"
    
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="文件大小不能超过2MB")
    
    if supabase_storage.is_enabled():
        storage_key = f"logos/{filename}"
        file_io = BytesIO(content)
        public_url = await supabase_storage.upload_file(file_io, storage_key, file.content_type)
        if public_url:
            return public_url
        else:
            raise HTTPException(status_code=500, detail="Logo上传到 Supabase 失败")
    else:
        logo_path = get_logo_base_path()
        file_path = logo_path / filename
        
        with open(file_path, "wb") as f:
            f.write(content)
        
        return f"/uploads/logos/{filename}"


def delete_logo_file(logo_url: str) -> bool:
    if not logo_url or logo_url.startswith("http"):
        return True
    
    try:
        if logo_url.startswith("/uploads/logos/"):
            filename = logo_url[len("/uploads/logos/"):]
        else:
            return True
        
        logo_path = get_logo_base_path() / filename
        if logo_path.exists():
            logo_path.unlink()
            return True
        return True
    except Exception as e:
        logger.error(f"Failed to delete logo file: {e}")
        return False


@router.get("", response_model=List[SiteConfigResponse])
def get_site_configs(db: Session = Depends(get_db)):
    configs = db.query(SiteConfig).all()
    return configs


@router.get("/{key}", response_model=SiteConfigResponse)
def get_site_config(key: str, db: Session = Depends(get_db)):
    config = db.query(SiteConfig).filter(SiteConfig.key == key).first()
    if not config:
        return {"key": key, "value": "", "description": "", "id": 0, "updated_at": None}
    return config


@router.put("/{key}", response_model=SiteConfigResponse)
def update_site_config(
    key: str,
    config_data: SiteConfigBase,
    request: Request,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="无权限修改网站设置")
    
    config = db.query(SiteConfig).filter(SiteConfig.key == key).first()
    
    if config:
        config.value = config_data.value
        if config_data.description:
            config.description = config_data.description
    else:
        config = SiteConfig(
            key=key,
            value=config_data.value,
            description=config_data.description
        )
        db.add(config)
    
    db.commit()
    db.refresh(config)
    
    LogService.log_operation(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        action="更新",
        module="网站设置",
        description=f"更新网站配置: {key}",
        target_type="网站配置",
        target_id=config.id,
        request=request,
        status="success"
    )
    
    return config


@router.post("", response_model=SiteConfigResponse)
def create_site_config(
    config_data: SiteConfigBase,
    request: Request,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="无权限创建网站配置")
    
    existing = db.query(SiteConfig).filter(SiteConfig.key == config_data.key).first()
    if existing:
        raise HTTPException(status_code=400, detail="Config key already exists")
    
    config = SiteConfig(
        key=config_data.key,
        value=config_data.value,
        description=config_data.description
    )
    db.add(config)
    db.commit()
    db.refresh(config)
    
    LogService.log_operation(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        action="创建",
        module="网站设置",
        description=f"创建网站配置: {config_data.key}",
        target_type="网站配置",
        target_id=config.id,
        request=request,
        status="success"
    )
    
    return config


@router.post("/upload-logo", response_model=SiteConfigResponse)
async def upload_logo(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    request: Request = None
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="无权限上传网站Logo")
    
    validate_logo_file(file)
    
    config = db.query(SiteConfig).filter(SiteConfig.key == "site_logo").first()
    old_logo_url = config.value if config else None
    
    try:
        logo_url = await save_logo_file(file)
        
        if config:
            config.value = logo_url
        else:
            config = SiteConfig(
                key="site_logo",
                value=logo_url,
                description="网站Logo"
            )
            db.add(config)
        
        db.commit()
        db.refresh(config)
        
        if old_logo_url:
            delete_logo_file(old_logo_url)
        
        LogService.log_operation(
            db=db,
            user_id=current_user.id,
            username=current_user.username,
            action="上传",
            module="网站设置",
            description="上传网站Logo",
            target_type="网站配置",
            target_id=config.id,
            request=request,
            status="success"
        )
        
        return config
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to upload logo: {e}")
        raise HTTPException(status_code=500, detail=f"Logo上传失败: {str(e)}")


@router.post("/reset-logo", response_model=SiteConfigResponse)
async def reset_logo(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    request: Request = None
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="无权限重置网站Logo")
    
    config = db.query(SiteConfig).filter(SiteConfig.key == "site_logo").first()
    
    if config and config.value:
        delete_logo_file(config.value)
        config.value = ""
        db.commit()
        db.refresh(config)
    
    LogService.log_operation(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        action="重置",
        module="网站设置",
        description="重置网站Logo为默认",
        target_type="网站配置",
        target_id=config.id if config else 0,
        request=request,
        status="success"
    )
    
    if config:
        return config
    return {"key": "site_logo", "value": "", "description": "网站Logo", "id": 0, "updated_at": None}


@router.delete("/{key}")
def delete_site_config(
    key: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="无权限删除网站配置")
    
    config = db.query(SiteConfig).filter(SiteConfig.key == key).first()
    if not config:
        raise HTTPException(status_code=404, detail="Config not found")
    
    if key == "site_logo" and config.value:
        delete_logo_file(config.value)
    
    db.delete(config)
    db.commit()
    
    LogService.log_operation(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        action="删除",
        module="网站设置",
        description=f"删除网站配置: {key}",
        target_type="网站配置",
        target_id=config.id,
        request=request,
        status="success"
    )
    
    return {"message": "Config deleted successfully"}
