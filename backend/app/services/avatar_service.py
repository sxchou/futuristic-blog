import os
import logging
from pathlib import Path
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from app.services.log_service import LogService
from app.models.models import User
from app.core.config import settings

logger = logging.getLogger(__name__)


class AvatarFileService:
    UPLOAD_DIR_NAME = "uploads"
    AVATAR_DIR_NAME = "avatars"
    
    @classmethod
    def get_avatar_base_path(cls) -> Path:
        if settings.AVATAR_STORAGE_PATH:
            return Path(settings.AVATAR_STORAGE_PATH) / cls.AVATAR_DIR_NAME
        
        env_path = os.getenv("AVATAR_STORAGE_PATH") or os.getenv("RAILWAY_VOLUME_MOUNT_PATH")
        if env_path:
            return Path(env_path) / cls.AVATAR_DIR_NAME
        
        backend_dir = Path(__file__).parent.parent.parent
        return backend_dir / cls.UPLOAD_DIR_NAME / cls.AVATAR_DIR_NAME
    
    @classmethod
    def resolve_avatar_file_path(cls, avatar_url: Optional[str]) -> Optional[Path]:
        if not avatar_url:
            return None
        
        try:
            if avatar_url.startswith("/uploads/avatars/"):
                relative_path = avatar_url[len("/uploads/avatars/"):]
            elif avatar_url.startswith("/uploads/"):
                relative_path = avatar_url[len("/uploads/"):]
            elif avatar_url.startswith("uploads/"):
                relative_path = avatar_url[len("uploads/"):]
            else:
                relative_path = avatar_url
            
            full_path = cls.get_avatar_base_path().parent / relative_path
            
            return full_path.resolve() if full_path.exists() else None
        except Exception as e:
            logger.error(f"Failed to resolve avatar path '{avatar_url}': {e}")
            return None
    
    @classmethod
    def delete_avatar_file(
        cls,
        avatar_url: Optional[str],
        db: Session,
        user: User,
        request=None,
        reason: str = "avatar_change"
    ) -> Tuple[bool, str]:
        if not avatar_url:
            return True, "No avatar URL provided, nothing to delete"
        
        file_path = cls.resolve_avatar_file_path(avatar_url)
        
        if not file_path:
            logger.warning(f"Avatar file not found for deletion: {avatar_url}")
            return True, f"File not found at path: {avatar_url}"
        
        try:
            base_path = cls.get_avatar_base_path().resolve()
            resolved_path = file_path.resolve()
            
            try:
                resolved_path.relative_to(base_path.parent)
            except ValueError:
                logger.error(f"Security: Attempted to delete file outside avatar directory: {file_path}")
                LogService.log_operation(
                    db=db,
                    user_id=user.id,
                    username=user.username,
                    action="安全警告",
                    module="用户头像",
                    description=f"尝试删除非头像目录文件: {avatar_url}",
                    target_type="文件系统",
                    target_id=0,
                    request=request,
                    status="failed"
                )
                return False, "Security violation: file path outside allowed directory"
            
            file_size = file_path.stat().st_size if file_path.exists() else 0
            
            file_path.unlink()
            
            logger.info(f"Successfully deleted avatar file: {file_path} (size: {file_size} bytes)")
            
            LogService.log_operation(
                db=db,
                user_id=user.id,
                username=user.username,
                action="删除",
                module="用户头像",
                description=f"删除旧头像文件: {avatar_url} (原因: {reason}, 大小: {file_size} bytes)",
                target_type="头像文件",
                target_id=0,
                request=request,
                status="success"
            )
            
            return True, f"Successfully deleted: {avatar_url}"
            
        except PermissionError as e:
            error_msg = f"Permission denied when deleting avatar file: {file_path}"
            logger.error(error_msg)
            LogService.log_operation(
                db=db,
                user_id=user.id,
                username=user.username,
                action="删除失败",
                module="用户头像",
                description=f"权限不足无法删除文件: {avatar_url} - {str(e)}",
                target_type="头像文件",
                target_id=0,
                request=request,
                status="failed"
            )
            return False, error_msg
            
        except OSError as e:
            error_msg = f"OS error when deleting avatar file: {file_path} - {e}"
            logger.error(error_msg)
            LogService.log_operation(
                db=db,
                user_id=user.id,
                username=user.username,
                action="删除失败",
                module="用户头像",
                description=f"系统错误无法删除文件: {avatar_url} - {str(e)}",
                target_type="头像文件",
                target_id=0,
                request=request,
                status="failed"
            )
            return False, error_msg
            
        except Exception as e:
            error_msg = f"Unexpected error deleting avatar file: {file_path} - {e}"
            logger.error(error_msg)
            LogService.log_operation(
                db=db,
                user_id=user.id,
                username=user.username,
                action="删除失败",
                module="用户头像",
                description=f"未知错误删除文件: {avatar_url} - {str(e)}",
                target_type="头像文件",
                target_id=0,
                request=request,
                status="failed"
            )
            return False, error_msg
    
    @classmethod
    def ensure_avatar_directory(cls) -> Path:
        avatar_path = cls.get_avatar_base_path()
        avatar_path.mkdir(parents=True, exist_ok=True)
        return avatar_path
    
    @classmethod
    def get_storage_stats(cls) -> dict:
        avatar_path = cls.get_avatar_base_path()
        
        if not avatar_path.exists():
            return {
                "total_files": 0,
                "total_size_bytes": 0,
                "total_size_mb": 0.0
            }
        
        total_files = 0
        total_size = 0
        
        for file_path in avatar_path.iterdir():
            if file_path.is_file():
                total_files += 1
                total_size += file_path.stat().st_size
        
        return {
            "total_files": total_files,
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2)
        }
    
    @classmethod
    def list_avatar_files(cls) -> list:
        avatar_path = cls.get_avatar_base_path()
        
        if not avatar_path.exists():
            return []
        
        files = []
        for file_path in avatar_path.iterdir():
            if file_path.is_file() and file_path.name != ".gitkeep":
                stat = file_path.stat()
                files.append({
                    "name": file_path.name,
                    "size_bytes": stat.st_size,
                    "size_kb": round(stat.st_size / 1024, 2),
                    "modified": stat.st_mtime,
                    "url": f"/uploads/avatars/{file_path.name}"
                })
        
        return sorted(files, key=lambda x: x["modified"], reverse=True)
