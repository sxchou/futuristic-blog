import os
import uuid
import aiofiles
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models import ArticleFile
from app.schemas import ArticleFileResponse, FileOrderUpdate
from app.utils import get_current_active_user
from app.utils.timezone import get_now
from app.core.config import settings


router = APIRouter(prefix="/files", tags=["Files"])

UPLOAD_DIR = settings.AVATAR_STORAGE_PATH or os.getenv("RAILWAY_VOLUME_MOUNT_PATH") or os.getenv("AVATAR_STORAGE_PATH") or "uploads"
ALLOWED_IMAGE_TYPES = [
    "image/jpeg", "image/png", "image/gif", "image/webp", "image/svg+xml", "image/bmp", "image/x-icon"
]
ALLOWED_FILE_TYPES = [
    "application/pdf",
    "application/zip",
    "application/x-rar-compressed",
    "application/x-rar",
    "application/x-7z-compressed",
    "application/x-tar",
    "application/gzip",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.ms-powerpoint",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "text/plain",
    "text/markdown",
    "text/csv",
    "application/json",
    "text/xml",
    "text/html",
    "text/css",
    "text/javascript",
    "application/javascript",
]
ALLOWED_AUDIO_TYPES = [
    "audio/mpeg",
    "audio/wav",
    "audio/ogg",
    "audio/flac",
    "audio/aac",
    "audio/mp4",
    "audio/x-ms-wma",
]
ALLOWED_VIDEO_TYPES = [
    "video/mp4",
    "video/webm",
    "video/x-msvideo",
    "video/quicktime",
    "video/x-ms-wmv",
    "video/x-flv",
    "video/x-matroska",
]
MAX_FILE_SIZE = 50 * 1024 * 1024


def ensure_upload_dir():
    if not os.path.exists(UPLOAD_DIR):
        os.makedirs(UPLOAD_DIR)
    
    articles_dir = os.path.join(UPLOAD_DIR, "articles")
    if not os.path.exists(articles_dir):
        os.makedirs(articles_dir)
    
    images_dir = os.path.join(UPLOAD_DIR, "images")
    if not os.path.exists(images_dir):
        os.makedirs(images_dir)
    
    audio_dir = os.path.join(UPLOAD_DIR, "audio")
    if not os.path.exists(audio_dir):
        os.makedirs(audio_dir)
    
    videos_dir = os.path.join(UPLOAD_DIR, "videos")
    if not os.path.exists(videos_dir):
        os.makedirs(videos_dir)


def get_file_type(mime_type: str) -> str:
    if mime_type in ALLOWED_IMAGE_TYPES:
        return "image"
    elif mime_type in ALLOWED_AUDIO_TYPES:
        return "audio"
    elif mime_type in ALLOWED_VIDEO_TYPES:
        return "video"
    elif mime_type in ALLOWED_FILE_TYPES:
        return "document"
    else:
        return "other"


def format_file_size(size: int) -> str:
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024:
            return f"{size:.2f} {unit}"
        size /= 1024
    return f"{size:.2f} TB"


@router.post("/upload", response_model=ArticleFileResponse)
async def upload_file(
    file: UploadFile = File(...),
    article_id: Optional[int] = Form(None),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    ensure_upload_dir()
    
    content = await file.read()
    file_size = len(content)
    
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail=f"文件大小超过限制 (最大 {format_file_size(MAX_FILE_SIZE)})")
    
    mime_type = file.content_type or "application/octet-stream"
    is_image = mime_type in ALLOWED_IMAGE_TYPES
    is_audio = mime_type in ALLOWED_AUDIO_TYPES
    is_video = mime_type in ALLOWED_VIDEO_TYPES
    is_allowed = (
        is_image or 
        is_audio or 
        is_video or 
        mime_type in ALLOWED_FILE_TYPES or
        mime_type.startswith('text/')
    )
    
    if not is_allowed:
        allowed_types = (
            ALLOWED_IMAGE_TYPES + 
            ALLOWED_FILE_TYPES + 
            ALLOWED_AUDIO_TYPES + 
            ALLOWED_VIDEO_TYPES
        )
        raise HTTPException(
            status_code=400, 
            detail=f"不支持的文件类型: {mime_type}。支持的类型: {', '.join(allowed_types[:10])}..."
        )
    
    file_ext = os.path.splitext(file.filename)[1] if file.filename else ""
    unique_filename = f"{get_now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}{file_ext}"
    
    if is_image:
        file_path = os.path.join(UPLOAD_DIR, "images", unique_filename)
    elif is_audio:
        file_path = os.path.join(UPLOAD_DIR, "audio", unique_filename)
    elif is_video:
        file_path = os.path.join(UPLOAD_DIR, "videos", unique_filename)
    else:
        file_path = os.path.join(UPLOAD_DIR, "articles", unique_filename)
    
    dir_path = os.path.dirname(file_path)
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
    
    async with aiofiles.open(file_path, 'wb') as f:
        await f.write(content)
    
    db_file = ArticleFile(
        filename=unique_filename,
        original_filename=file.filename or "unknown",
        file_path=file_path,
        file_size=file_size,
        file_type=get_file_type(mime_type),
        mime_type=mime_type,
        is_image=is_image,
        article_id=article_id,
        uploaded_by=current_user.id
    )
    
    db.add(db_file)
    db.commit()
    db.refresh(db_file)
    
    return db_file


@router.post("/upload-image", response_model=ArticleFileResponse)
async def upload_image(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    ensure_upload_dir()
    
    mime_type = file.content_type or ""
    if mime_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(status_code=400, detail="只支持图片文件 (JPEG, PNG, GIF, WebP)")
    
    content = await file.read()
    file_size = len(content)
    
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail=f"文件大小超过限制 (最大 {format_file_size(MAX_FILE_SIZE)})")
    
    file_ext = os.path.splitext(file.filename)[1] if file.filename else ".jpg"
    unique_filename = f"{get_now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}{file_ext}"
    
    file_path = os.path.join(UPLOAD_DIR, "images", unique_filename)
    
    async with aiofiles.open(file_path, 'wb') as f:
        await f.write(content)
    
    db_file = ArticleFile(
        filename=unique_filename,
        original_filename=file.filename or "image",
        file_path=file_path,
        file_size=file_size,
        file_type="image",
        mime_type=mime_type,
        is_image=True,
        uploaded_by=current_user.id
    )
    
    db.add(db_file)
    db.commit()
    db.refresh(db_file)
    
    return db_file


@router.get("", response_model=List[ArticleFileResponse])
async def get_files(
    article_id: Optional[int] = None,
    file_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(ArticleFile)
    
    if article_id:
        query = query.filter(ArticleFile.article_id == article_id)
    if file_type:
        query = query.filter(ArticleFile.file_type == file_type)
    
    return query.order_by(ArticleFile.order.asc(), ArticleFile.created_at.desc()).all()


@router.get("/{file_id}", response_model=ArticleFileResponse)
async def get_file_info(
    file_id: int,
    db: Session = Depends(get_db)
):
    db_file = db.query(ArticleFile).filter(ArticleFile.id == file_id).first()
    if not db_file:
        raise HTTPException(status_code=404, detail="文件不存在")
    return db_file


@router.get("/{file_id}/download")
async def download_file(
    file_id: int,
    db: Session = Depends(get_db)
):
    db_file = db.query(ArticleFile).filter(ArticleFile.id == file_id).first()
    if not db_file:
        raise HTTPException(status_code=404, detail="文件不存在")
    
    if not os.path.exists(db_file.file_path):
        raise HTTPException(status_code=404, detail="文件已被删除")
    
    db_file.download_count += 1
    db.commit()
    
    return FileResponse(
        path=db_file.file_path,
        filename=db_file.original_filename,
        media_type=db_file.mime_type
    )


@router.delete("/{file_id}")
async def delete_file(
    file_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    db_file = db.query(ArticleFile).filter(ArticleFile.id == file_id).first()
    if not db_file:
        raise HTTPException(status_code=404, detail="文件不存在")
    
    file_path = db_file.file_path
    filename = db_file.original_filename
    
    try:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
    except Exception as e:
        pass
    
    db.delete(db_file)
    db.commit()
    
    return {"message": "文件已删除"}


@router.put("/order")
async def update_file_order(
    data: FileOrderUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    for item in data.orders:
        db_file = db.query(ArticleFile).filter(ArticleFile.id == item.id).first()
        if db_file:
            db_file.order = item.order
    
    db.commit()
    return {"message": "排序已更新"}


@router.get("/admin/storage-info")
async def get_storage_info(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="需要管理员权限")
    
    result = {
        "upload_dir": UPLOAD_DIR,
        "total_size": 0,
        "total_files": 0,
        "directories": {},
        "orphan_files": [],
        "db_files_count": 0
    }
    
    db_files = db.query(ArticleFile).all()
    result["db_files_count"] = len(db_files)
    db_file_paths = {f.file_path for f in db_files}
    db_file_map = {f.file_path: f for f in db_files}
    
    PROTECTED_DIRS = {'avatars'}
    
    if os.path.exists(UPLOAD_DIR):
        for root, dirs, files in os.walk(UPLOAD_DIR):
            rel_path = os.path.relpath(root, UPLOAD_DIR)
            dir_name = rel_path if rel_path != "." else "root"
            
            is_protected = dir_name in PROTECTED_DIRS or dir_name.startswith('avatars/')
            
            dir_size = 0
            dir_files = []
            
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    file_size = os.path.getsize(file_path)
                    file_stat = os.stat(file_path)
                    dir_size += file_size
                    result["total_size"] += file_size
                    result["total_files"] += 1
                    
                    db_file = db_file_map.get(file_path)
                    display_name = db_file.original_filename if db_file else file
                    
                    file_info = {
                        "name": file,
                        "display_name": display_name,
                        "path": file_path,
                        "size": file_size,
                        "size_formatted": format_file_size(file_size),
                        "modified": datetime.fromtimestamp(file_stat.st_mtime).isoformat(),
                        "is_avatar": dir_name == 'avatars' or dir_name.startswith('avatars/')
                    }
                    dir_files.append(file_info)
                    
                    if file_path not in db_file_paths and not is_protected:
                        result["orphan_files"].append(file_info)
                        
                except Exception as e:
                    pass
            
            result["directories"][dir_name] = {
                "size": dir_size,
                "size_formatted": format_file_size(dir_size),
                "file_count": len(dir_files),
                "files": dir_files[:20],
                "is_protected": is_protected
            }
    
    result["total_size_formatted"] = format_file_size(result["total_size"])
    result["orphan_count"] = len(result["orphan_files"])
    
    return result


@router.delete("/admin/orphan-files")
async def delete_orphan_files(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="需要管理员权限")
    
    db_files = db.query(ArticleFile).all()
    db_file_paths = {f.file_path for f in db_files}
    
    EXCLUDED_DIRS = {'avatars'}
    
    deleted_files = []
    deleted_size = 0
    errors = []
    
    if os.path.exists(UPLOAD_DIR):
        for root, dirs, files in os.walk(UPLOAD_DIR):
            dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]
            
            for file in files:
                file_path = os.path.join(root, file)
                if file_path not in db_file_paths:
                    try:
                        file_size = os.path.getsize(file_path)
                        os.remove(file_path)
                        deleted_files.append({
                            "path": file_path,
                            "name": file,
                            "size": file_size
                        })
                        deleted_size += file_size
                    except Exception as e:
                        errors.append({
                            "path": file_path,
                            "error": str(e)
                        })
    
    return {
        "deleted_count": len(deleted_files),
        "deleted_size": deleted_size,
        "deleted_size_formatted": format_file_size(deleted_size),
        "deleted_files": deleted_files,
        "errors": errors
    }
