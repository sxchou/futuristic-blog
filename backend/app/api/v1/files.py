import os
import uuid
import aiofiles
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models import ArticleFile
from app.schemas import ArticleFileResponse, ArticleFileUpdate
from app.utils import get_current_active_user
from app.utils.timezone import get_now
from app.core.config import settings


router = APIRouter(prefix="/files", tags=["Files"])

UPLOAD_DIR = settings.AVATAR_STORAGE_PATH or os.getenv("RAILWAY_VOLUME_MOUNT_PATH") or os.getenv("AVATAR_STORAGE_PATH") or "uploads"
ALLOWED_IMAGE_TYPES = [
    "image/jpeg", "image/png", "image/gif", "image/webp", "image/svg+xml"
]
ALLOWED_FILE_TYPES = [
    "application/pdf",
    "application/zip",
    "application/x-rar-compressed",
    "application/x-7z-compressed",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.ms-powerpoint",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "text/plain",
    "text/markdown",
]
MAX_FILE_SIZE = 10 * 1024 * 1024

PREVIEWABLE_TYPES = {
    "application/pdf": "pdf",
    "image/jpeg": "image",
    "image/png": "image",
    "image/gif": "image",
    "image/webp": "image",
    "image/svg+xml": "image",
    "image/bmp": "image",
    "image/tiff": "image",
    "text/plain": "text",
    "text/markdown": "text",
    "text/html": "text",
    "text/css": "text",
    "text/javascript": "text",
    "application/json": "text",
    "application/xml": "text",
    "application/msword": "office",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "office",
    "application/vnd.ms-excel": "office",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": "office",
    "application/vnd.ms-powerpoint": "office",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation": "office",
}


def ensure_upload_dir():
    if not os.path.exists(UPLOAD_DIR):
        os.makedirs(UPLOAD_DIR)
    
    articles_dir = os.path.join(UPLOAD_DIR, "articles")
    if not os.path.exists(articles_dir):
        os.makedirs(articles_dir)
    
    images_dir = os.path.join(UPLOAD_DIR, "images")
    if not os.path.exists(images_dir):
        os.makedirs(images_dir)


def get_file_type(mime_type: str) -> str:
    if mime_type in ALLOWED_IMAGE_TYPES:
        return "image"
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
    
    file_ext = os.path.splitext(file.filename)[1] if file.filename else ""
    unique_filename = f"{get_now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}{file_ext}"
    
    if is_image:
        file_path = os.path.join(UPLOAD_DIR, "images", unique_filename)
    else:
        file_path = os.path.join(UPLOAD_DIR, "articles", unique_filename)
    
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
    
    return query.order_by(ArticleFile.order.asc(), ArticleFile.created_at.asc()).all()


@router.get("/{file_id}", response_model=ArticleFileResponse)
async def get_file_info(
    file_id: int,
    db: Session = Depends(get_db)
):
    db_file = db.query(ArticleFile).filter(ArticleFile.id == file_id).first()
    if not db_file:
        raise HTTPException(status_code=404, detail="文件不存在")
    
    db_file.view_count += 1
    db.commit()
    
    return db_file


@router.get("/{file_id}/preview")
async def preview_file(
    file_id: int,
    db: Session = Depends(get_db)
):
    db_file = db.query(ArticleFile).filter(ArticleFile.id == file_id).first()
    if not db_file:
        raise HTTPException(status_code=404, detail="文件不存在")
    
    if not os.path.exists(db_file.file_path):
        raise HTTPException(status_code=404, detail="文件已被删除")
    
    preview_type = PREVIEWABLE_TYPES.get(db_file.mime_type)
    
    db_file.view_count += 1
    db.commit()
    
    if preview_type == "text":
        async with aiofiles.open(db_file.file_path, 'r', encoding='utf-8') as f:
            content = await f.read()
        return {
            "type": "text",
            "content": content,
            "filename": db_file.original_filename
        }
    elif preview_type == "office":
        return FileResponse(
            path=db_file.file_path,
            media_type=db_file.mime_type,
            filename=db_file.original_filename
        )
    else:
        return FileResponse(
            path=db_file.file_path,
            media_type=db_file.mime_type
        )


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
    
    if os.path.exists(db_file.file_path):
        os.remove(db_file.file_path)
    
    db.delete(db_file)
    db.commit()
    
    return {"message": "文件已删除"}


@router.patch("/{file_id}", response_model=ArticleFileResponse)
async def update_file(
    file_id: int,
    update_data: ArticleFileUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    db_file = db.query(ArticleFile).filter(ArticleFile.id == file_id).first()
    if not db_file:
        raise HTTPException(status_code=404, detail="文件不存在")
    
    if update_data.order is not None:
        db_file.order = update_data.order
    
    db.commit()
    db.refresh(db_file)
    
    return db_file


@router.post("/batch-order")
async def batch_update_order(
    orders: List[dict],
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    for item in orders:
        file_id = item.get("id")
        order = item.get("order")
        if file_id is not None and order is not None:
            db_file = db.query(ArticleFile).filter(ArticleFile.id == file_id).first()
            if db_file:
                db_file.order = order
    
    db.commit()
    return {"message": "排序已更新"}
