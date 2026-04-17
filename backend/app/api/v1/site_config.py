import os
import logging
import time
import httpx
from typing import List, Optional
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
from app.utils.cache import cache_manager

router = APIRouter(prefix="/site-config", tags=["Site Configuration"])
logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".ico", ".svg"}
MAX_FILE_SIZE = 2 * 1024 * 1024

GITHUB_CACHE = {"data": None, "timestamp": 0, "repo_url": ""}
GITHUB_CACHE_TTL = 3600
GITHUB_RATE_LIMIT_CACHE = {"reset_time": 0}

CACHE_NAME = "site_config"


def invalidate_site_config_cache():
    cache_manager.clear_cache(CACHE_NAME)


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
    cache_key = "all_configs"
    cached = cache_manager.get(CACHE_NAME, cache_key)
    if cached:
        return cached
    
    configs = db.query(SiteConfig).all()
    result = [SiteConfigResponse.model_validate(c) for c in configs]
    
    cache_manager.set(CACHE_NAME, cache_key, [r.model_dump() for r in result])
    return result


def parse_github_repo_url(repo_url: str) -> Optional[tuple]:
    if not repo_url:
        return None
    repo_url = repo_url.strip()
    if repo_url.endswith('.git'):
        repo_url = repo_url[:-4]
    if repo_url.endswith('/'):
        repo_url = repo_url[:-1]
    parts = repo_url.split('/')
    if len(parts) >= 2:
        owner = parts[-2]
        repo = parts[-1]
        return (owner, repo)
    return None


@router.get("/github-stats")
async def get_github_stats(db: Session = Depends(get_db)):
    global GITHUB_CACHE, GITHUB_RATE_LIMIT_CACHE
    
    current_time = time.time()
    
    if current_time < GITHUB_RATE_LIMIT_CACHE["reset_time"]:
        logger.info(f"GitHub API rate limited, using cached data. Reset in {int(GITHUB_RATE_LIMIT_CACHE['reset_time'] - current_time)}s")
        if GITHUB_CACHE["data"]:
            return {"enabled": True, **GITHUB_CACHE["data"]}
        return {"enabled": False, "stars": 0, "forks": 0, "watchers": 0, "open_issues": 0}
    
    github_repo_config = db.query(SiteConfig).filter(SiteConfig.key == "github_repo_url").first()
    repo_url = github_repo_config.value if github_repo_config else ""
    
    if not repo_url:
        return {"enabled": False, "stars": 0, "forks": 0, "watchers": 0, "open_issues": 0}
    
    parsed = parse_github_repo_url(repo_url)
    if not parsed:
        return {"enabled": False, "stars": 0, "forks": 0, "watchers": 0, "open_issues": 0}
    
    owner, repo = parsed
    
    if (GITHUB_CACHE["data"] and 
        GITHUB_CACHE["repo_url"] == repo_url and 
        current_time - GITHUB_CACHE["timestamp"] < GITHUB_CACHE_TTL):
        return {"enabled": True, **GITHUB_CACHE["data"]}
    
    try:
        github_token = os.getenv("GITHUB_TOKEN")
        
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "Futuristic-Blog/1.0"
        }
        
        if github_token:
            headers["Authorization"] = f"token {github_token}"
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"https://api.github.com/repos/{owner}/{repo}",
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                stats = {
                    "stars": data.get("stargazers_count", 0),
                    "forks": data.get("forks_count", 0),
                    "watchers": data.get("watchers_count", 0),
                    "open_issues": data.get("open_issues_count", 0),
                    "full_name": data.get("full_name", f"{owner}/{repo}"),
                    "html_url": data.get("html_url", repo_url)
                }
                
                GITHUB_CACHE = {
                    "data": stats,
                    "timestamp": current_time,
                    "repo_url": repo_url
                }
                
                return {"enabled": True, **stats}
            elif response.status_code == 403:
                rate_limit_remaining = response.headers.get("X-RateLimit-Remaining", "0")
                rate_limit_reset = response.headers.get("X-RateLimit-Reset", "0")
                
                logger.warning(f"GitHub API rate limit exceeded. Remaining: {rate_limit_remaining}, Reset: {rate_limit_reset}")
                
                if rate_limit_reset:
                    GITHUB_RATE_LIMIT_CACHE["reset_time"] = int(rate_limit_reset)
                
                if GITHUB_CACHE["data"]:
                    return {"enabled": True, **GITHUB_CACHE["data"]}
                
                return {"enabled": False, "stars": 0, "forks": 0, "watchers": 0, "open_issues": 0}
            else:
                logger.warning(f"GitHub API returned status {response.status_code}")
                
                if GITHUB_CACHE["data"]:
                    return {"enabled": True, **GITHUB_CACHE["data"]}
                
                return {"enabled": False, "stars": 0, "forks": 0, "watchers": 0, "open_issues": 0}
                
    except Exception as e:
        logger.error(f"Failed to fetch GitHub stats: {e}")
        
        if GITHUB_CACHE["data"]:
            return {"enabled": True, **GITHUB_CACHE["data"]}
        
        return {"enabled": False, "stars": 0, "forks": 0, "watchers": 0, "open_issues": 0}


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
    global GITHUB_CACHE
    
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
    
    if key == "github_repo_url":
        GITHUB_CACHE = {"data": None, "timestamp": 0, "repo_url": ""}
    
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
