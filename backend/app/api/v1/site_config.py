from typing import List
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.models import SiteConfig
from app.schemas.schemas import SiteConfigBase, SiteConfigResponse
from app.utils.auth import get_current_user
from app.services.log_service import LogService

router = APIRouter(prefix="/site-config", tags=["Site Configuration"])


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
