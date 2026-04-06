import os
import uuid
import aiofiles
import zipfile
import tarfile
import gzip
import httpx
from datetime import datetime
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse, RedirectResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.core.database import get_db
from app.models import ArticleFile
from app.schemas import ArticleFileResponse, FileOrderUpdate
from app.utils import get_current_active_user
from app.utils.timezone import get_now
from app.core.config import settings
from app.services.supabase_storage import supabase_storage
from io import BytesIO

try:
    import rarfile
    HAS_RARFILE = True
except ImportError:
    HAS_RARFILE = False

try:
    import py7zr
    HAS_PY7ZR = True
except ImportError:
    HAS_PY7ZR = False


def decode_filename(filename_bytes: bytes) -> str:
    """
    尝试多种编码解码文件名，确保中文和4字节字符正确显示
    """
    if isinstance(filename_bytes, str):
        return filename_bytes
    
    encodings = ['utf-8', 'gb18030', 'gbk', 'gb2312', 'cp437', 'latin-1']
    
    for encoding in encodings:
        try:
            decoded = filename_bytes.decode(encoding)
            if all(ord(c) < 0xD800 or ord(c) > 0xDFFF for c in decoded):
                return decoded
        except (UnicodeDecodeError, UnicodeEncodeError):
            continue
    
    return filename_bytes.decode('utf-8', errors='replace')


def safe_filename(filename: str) -> str:
    """
    确保文件名是有效的 UTF-8 字符串
    """
    if not filename:
        return ""
    
    try:
        if isinstance(filename, bytes):
            return decode_filename(filename)
        
        filename.encode('utf-8')
        return filename
    except UnicodeEncodeError:
        return filename.encode('utf-8', errors='replace').decode('utf-8')


router = APIRouter(prefix="/files", tags=["Files"])

UPLOAD_DIR = settings.AVATAR_STORAGE_PATH or os.getenv("RAILWAY_VOLUME_MOUNT_PATH") or os.getenv("AVATAR_STORAGE_PATH") or "uploads"

ALLOWED_IMAGE_TYPES = [
    "image/jpeg", "image/png", "image/gif", "image/webp", "image/svg+xml", "image/bmp", "image/x-icon"
]
ALLOWED_FILE_TYPES = [
    "application/pdf",
    "application/zip",
    "application/x-zip-compressed",
    "application/x-zip",
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

ALLOWED_EXTENSIONS = {
    'image': ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg', '.bmp', '.ico'],
    'audio': ['.mp3', '.wav', '.ogg', '.flac', '.aac', '.m4a', '.wma'],
    'video': ['.mp4', '.webm', '.avi', '.mov', '.wmv', '.flv', '.mkv'],
    'document': [
        '.pdf', 
        '.zip', '.rar', '.7z', '.tar', '.gz',
        '.doc', '.docx', 
        '.xls', '.xlsx', 
        '.ppt', '.pptx',
        '.txt', '.md', '.csv', '.json', '.xml', '.html', '.css', '.js'
    ]
}

MAX_FILE_SIZE = 100 * 1024 * 1024


def get_file_category_by_extension(filename: str) -> Optional[str]:
    if not filename:
        return None
    ext = os.path.splitext(filename)[1].lower()
    for category, extensions in ALLOWED_EXTENSIONS.items():
        if ext in extensions:
            return category
    return None


def is_allowed_file(filename: str, mime_type: str) -> tuple[bool, str]:
    ext_category = get_file_category_by_extension(filename)
    
    if ext_category:
        return True, ext_category
    
    if mime_type in ALLOWED_IMAGE_TYPES:
        return True, 'image'
    if mime_type in ALLOWED_AUDIO_TYPES:
        return True, 'audio'
    if mime_type in ALLOWED_VIDEO_TYPES:
        return True, 'video'
    if mime_type in ALLOWED_FILE_TYPES:
        return True, 'document'
    if mime_type.startswith('text/'):
        return True, 'document'
    
    return False, ''


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
    
    is_allowed, file_category = is_allowed_file(file.filename or "", mime_type)
    
    if not is_allowed:
        all_extensions = []
        for exts in ALLOWED_EXTENSIONS.values():
            all_extensions.extend(exts)
        raise HTTPException(
            status_code=400, 
            detail=f"不支持的文件类型。支持的扩展名: {', '.join(all_extensions[:20])}..."
        )
    
    is_image = file_category == 'image'
    is_audio = file_category == 'audio'
    is_video = file_category == 'video'
    
    file_ext = os.path.splitext(file.filename)[1] if file.filename else ""
    unique_filename = f"{get_now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}{file_ext}"
    
    if is_image:
        folder = "images"
    elif is_audio:
        folder = "audio"
    elif is_video:
        folder = "videos"
    else:
        folder = "articles"
    
    storage_key = f"{folder}/{unique_filename}"
    
    if supabase_storage.is_enabled():
        file_io = BytesIO(content)
        public_url = await supabase_storage.upload_file(file_io, storage_key, mime_type)
        if public_url:
            file_path = public_url
        else:
            raise HTTPException(status_code=500, detail="文件上传到 Supabase 失败")
    else:
        file_path = os.path.join(UPLOAD_DIR, folder, unique_filename)
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
    ext_category = get_file_category_by_extension(file.filename or "")
    
    if ext_category != 'image' and mime_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(status_code=400, detail="只支持图片文件 (JPEG, PNG, GIF, WebP, SVG, BMP, ICO)")
    
    content = await file.read()
    file_size = len(content)
    
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail=f"文件大小超过限制 (最大 {format_file_size(MAX_FILE_SIZE)})")
    
    file_ext = os.path.splitext(file.filename)[1] if file.filename else ".jpg"
    unique_filename = f"{get_now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}{file_ext}"
    
    storage_key = f"images/{unique_filename}"
    
    if supabase_storage.is_enabled():
        file_io = BytesIO(content)
        public_url = await supabase_storage.upload_file(file_io, storage_key, mime_type)
        if public_url:
            file_path = public_url
        else:
            raise HTTPException(status_code=500, detail="文件上传到 Supabase 失败")
    else:
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
    
    db_file.download_count += 1
    db.commit()
    
    if db_file.file_path.startswith("http"):
        return RedirectResponse(url=db_file.file_path, status_code=302)
    
    if not os.path.exists(db_file.file_path):
        raise HTTPException(status_code=404, detail="文件已被删除")
    
    return FileResponse(
        path=db_file.file_path,
        filename=db_file.original_filename,
        media_type=db_file.mime_type
    )


@router.get("/{file_id}/content")
async def get_file_content(
    file_id: int,
    db: Session = Depends(get_db)
):
    db_file = db.query(ArticleFile).filter(ArticleFile.id == file_id).first()
    if not db_file:
        raise HTTPException(status_code=404, detail="文件不存在")
    
    if db_file.file_path.startswith("http"):
        from fastapi.responses import StreamingResponse
        
        async def stream_from_supabase():
            async with httpx.AsyncClient(timeout=120.0) as client:
                async with client.stream("GET", db_file.file_path) as response:
                    if response.status_code != 200:
                        raise HTTPException(status_code=500, detail="无法获取文件内容")
                    async for chunk in response.aiter_bytes(chunk_size=65536):
                        yield chunk
        
        return StreamingResponse(
            stream_from_supabase(),
            media_type=db_file.mime_type,
            headers={
                "Content-Disposition": f'inline; filename="{db_file.original_filename}"',
                "Cache-Control": "public, max-age=86400",
                "Access-Control-Allow-Origin": "*"
            }
        )
    
    if not os.path.exists(db_file.file_path):
        raise HTTPException(status_code=404, detail="文件已被删除")
    
    return FileResponse(
        path=db_file.file_path,
        filename=db_file.original_filename,
        media_type=db_file.mime_type
    )


@router.post("/{file_id}/preview")
async def preview_file(
    file_id: int,
    db: Session = Depends(get_db)
):
    db_file = db.query(ArticleFile).filter(ArticleFile.id == file_id).first()
    if not db_file:
        raise HTTPException(status_code=404, detail="文件不存在")
    
    try:
        db_file.preview_count += 1
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Failed to update preview count: {e}")
    
    return {
        "preview_count": db_file.preview_count,
        "file_id": file_id
    }


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
        if file_path:
            if file_path.startswith("http") and supabase_storage.is_enabled():
                storage_key = f"{db_file.filename}"
                if "images/" in file_path:
                    storage_key = f"images/{storage_key}"
                elif "articles/" in file_path:
                    storage_key = f"articles/{storage_key}"
                elif "avatars/" in file_path:
                    storage_key = f"avatars/{storage_key}"
                await supabase_storage.delete_file(storage_key)
            elif os.path.exists(file_path):
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
        "db_files_count": 0,
        "storage_type": "supabase" if supabase_storage.is_enabled() else "local"
    }
    
    db_files = db.query(ArticleFile).all()
    result["db_files_count"] = len(db_files)
    
    if supabase_storage.is_enabled():
        result["upload_dir"] = f"{settings.SUPABASE_URL}/storage/v1/object/public/{settings.SUPABASE_BUCKET}"
        
        dir_stats = {}
        for f in db_files:
            folder = "articles"
            if "images/" in f.file_path:
                folder = "images"
            elif "avatars/" in f.file_path:
                folder = "avatars"
            elif "videos/" in f.file_path:
                folder = "videos"
            elif "audio/" in f.file_path:
                folder = "audio"
            
            if folder not in dir_stats:
                dir_stats[folder] = {"size": 0, "files": []}
            
            dir_stats[folder]["size"] += f.file_size or 0
            dir_stats[folder]["files"].append({
                "name": f.filename,
                "display_name": f.original_filename,
                "path": f.file_path,
                "size": f.file_size or 0,
                "size_formatted": format_file_size(f.file_size or 0),
                "modified": f.created_at.isoformat() if f.created_at else "",
                "is_avatar": folder == "avatars"
            })
            result["total_size"] += f.file_size or 0
            result["total_files"] += 1
        
        for folder, stats in dir_stats.items():
            result["directories"][folder] = {
                "size": stats["size"],
                "size_formatted": format_file_size(stats["size"]),
                "file_count": len(stats["files"]),
                "files": stats["files"][:20],
                "is_protected": folder == "avatars"
            }
    else:
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


class ArchiveEntry(BaseModel):
    name: str
    path: str
    is_dir: bool
    size: int
    compressed_size: int
    modified: Optional[str] = None

class ArchiveContent(BaseModel):
    format: str
    total_files: int
    total_dirs: int
    total_size: int
    compressed_size: int
    entries: List[ArchiveEntry]
    tree: Dict[str, Any]


def build_tree(entries: List[Dict[str, Any]]) -> Dict[str, Any]:
    root = {"name": "", "children": {}, "is_dir": True, "size": 0}
    
    for entry in entries:
        parts = entry["path"].split("/")
        current = root
        
        for i, part in enumerate(parts):
            if not part:
                continue
                
            if part not in current["children"]:
                is_dir = i < len(parts) - 1 or entry["is_dir"]
                current["children"][part] = {
                    "name": part,
                    "children": {} if is_dir else None,
                    "is_dir": is_dir,
                    "size": entry["size"] if not is_dir else 0,
                    "path": "/".join(parts[:i+1])
                }
            
            current = current["children"][part]
    
    def sort_children(node):
        if node["children"]:
            sorted_children = dict(
                sorted(
                    node["children"].items(),
                    key=lambda x: (not x[1]["is_dir"], x[0].lower())
                )
            )
            for child in sorted_children.values():
                sort_children(child)
            node["children"] = sorted_children
    
    sort_children(root)
    return root


def parse_zip(file_path: str) -> Dict[str, Any]:
    entries = []
    total_size = 0
    compressed_size = 0
    
    with zipfile.ZipFile(file_path, 'r') as zf:
        for info in zf.infolist():
            is_dir = info.is_dir()
            
            filename = info.filename
            if info.flag_bits & 0x800:
                try:
                    if isinstance(filename, bytes):
                        filename = filename.decode('utf-8')
                except:
                    pass
            else:
                try:
                    if isinstance(filename, bytes):
                        filename = decode_filename(filename)
                    else:
                        try:
                            filename.encode('cp437')
                            try:
                                filename = filename.encode('cp437').decode('gb18030')
                            except:
                                try:
                                    filename = filename.encode('cp437').decode('utf-8')
                                except:
                                    pass
                        except:
                            pass
                except:
                    pass
            
            filename = safe_filename(filename)
            
            entries.append({
                "name": os.path.basename(filename.rstrip('/')) or filename,
                "path": filename.rstrip('/'),
                "is_dir": is_dir,
                "size": info.file_size,
                "compressed_size": info.compress_size,
                "modified": datetime(*info.date_time).isoformat() if info.date_time else None
            })
            if not is_dir:
                total_size += info.file_size
                compressed_size += info.compress_size
    
    return {
        "format": "ZIP",
        "total_files": sum(1 for e in entries if not e["is_dir"]),
        "total_dirs": sum(1 for e in entries if e["is_dir"]),
        "total_size": total_size,
        "compressed_size": compressed_size,
        "entries": entries,
        "tree": build_tree(entries)
    }


def parse_tar(file_path: str, mode: str = 'r') -> Dict[str, Any]:
    entries = []
    total_size = 0
    compressed_size = 0
    
    with tarfile.open(file_path, mode, encoding='utf-8', errors='replace') as tf:
        for member in tf.getmembers():
            name = safe_filename(member.name)
            entries.append({
                "name": os.path.basename(name.rstrip('/')) or name,
                "path": name.rstrip('/'),
                "is_dir": member.isdir(),
                "size": member.size,
                "compressed_size": member.size,
                "modified": datetime.fromtimestamp(member.mtime).isoformat() if member.mtime else None
            })
            if member.isfile():
                total_size += member.size
                compressed_size += member.size
    
    return {
        "format": "TAR" if mode == 'r' else "TAR.GZ",
        "total_files": sum(1 for e in entries if not e["is_dir"]),
        "total_dirs": sum(1 for e in entries if e["is_dir"]),
        "total_size": total_size,
        "compressed_size": compressed_size,
        "entries": entries,
        "tree": build_tree(entries)
    }


def parse_rar(file_path: str) -> Dict[str, Any]:
    if not HAS_RARFILE:
        return {"error": "RAR 支持未安装", "format": "RAR", "entries": [], "tree": {}}
    
    entries = []
    total_size = 0
    compressed_size = 0
    
    with rarfile.RarFile(file_path, 'r') as rf:
        for info in rf.infolist():
            is_dir = info.isdir()
            filename = safe_filename(info.filename)
            
            modified = None
            if info.mtime:
                if isinstance(info.mtime, datetime):
                    modified = info.mtime.isoformat()
                else:
                    try:
                        modified = datetime.fromtimestamp(info.mtime).isoformat()
                    except (TypeError, OSError):
                        modified = None
            
            entries.append({
                "name": os.path.basename(filename.rstrip('/')) or filename,
                "path": filename.rstrip('/'),
                "is_dir": is_dir,
                "size": info.file_size,
                "compressed_size": info.compress_size,
                "modified": modified
            })
            if not is_dir:
                total_size += info.file_size
                compressed_size += info.compress_size
    
    return {
        "format": "RAR",
        "total_files": sum(1 for e in entries if not e["is_dir"]),
        "total_dirs": sum(1 for e in entries if e["is_dir"]),
        "total_size": total_size,
        "compressed_size": compressed_size,
        "entries": entries,
        "tree": build_tree(entries)
    }


def parse_7z(file_path: str) -> Dict[str, Any]:
    if not HAS_PY7ZR:
        return {"error": "7z 支持未安装", "format": "7Z", "entries": [], "tree": {}}
    
    entries = []
    total_size = 0
    compressed_size = 0
    
    with py7zr.SevenZipFile(file_path, 'r') as szf:
        file_list = szf.list()
        
        for info in file_list:
            is_dir = info.is_directory
            safe_name = safe_filename(info.filename)
            
            file_size = info.uncompressed if info.uncompressed is not None else 0
            compressed = info.compressed if info.compressed is not None else 0
            
            entries.append({
                "name": os.path.basename(safe_name.rstrip('/')) or safe_name,
                "path": safe_name.rstrip('/'),
                "is_dir": is_dir,
                "size": file_size,
                "compressed_size": compressed,
                "modified": info.creationtime.isoformat() if info.creationtime else None
            })
            
            if not is_dir:
                total_size += file_size
                compressed_size += compressed
    
    return {
        "format": "7Z",
        "total_files": sum(1 for e in entries if not e["is_dir"]),
        "total_dirs": sum(1 for e in entries if e["is_dir"]),
        "total_size": total_size,
        "compressed_size": compressed_size,
        "entries": entries,
        "tree": build_tree(entries)
    }


def parse_gz(file_path: str) -> Dict[str, Any]:
    entries = []
    total_size = 0
    compressed_size = os.path.getsize(file_path)
    
    with gzip.open(file_path, 'rb') as gf:
        try:
            content = gf.read()
            total_size = len(content)
            original_name = os.path.basename(file_path)
            if original_name.endswith('.gz'):
                original_name = original_name[:-3]
            
            original_name = safe_filename(original_name)
            
            entries.append({
                "name": original_name,
                "path": original_name,
                "is_dir": False,
                "size": total_size,
                "compressed_size": compressed_size,
                "modified": None
            })
        except Exception:
            pass
    
    return {
        "format": "GZIP",
        "total_files": 1,
        "total_dirs": 0,
        "total_size": total_size,
        "compressed_size": compressed_size,
        "entries": entries,
        "tree": build_tree(entries)
    }


@router.get("/{file_id}/archive-content", response_model=ArchiveContent)
async def get_archive_content(
    file_id: int,
    db: Session = Depends(get_db)
):
    db_file = db.query(ArticleFile).filter(ArticleFile.id == file_id).first()
    if not db_file:
        raise HTTPException(status_code=404, detail="文件不存在")
    
    ext = os.path.splitext(db_file.original_filename)[1].lower()
    
    temp_file_path = None
    
    try:
        if db_file.file_path.startswith("http"):
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.get(db_file.file_path, follow_redirects=True)
                if response.status_code != 200:
                    raise HTTPException(status_code=404, detail="文件下载失败")
                
                import tempfile
                with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as temp_file:
                    temp_file.write(response.content)
                    temp_file_path = temp_file.name
                file_path = temp_file_path
        else:
            if not os.path.exists(db_file.file_path):
                raise HTTPException(status_code=404, detail="文件不存在")
            file_path = db_file.file_path
        
        if ext == '.zip':
            result = parse_zip(file_path)
        elif ext == '.tar':
            result = parse_tar(file_path, 'r')
        elif ext in ['.tar.gz', '.tgz']:
            result = parse_tar(file_path, 'r:gz')
        elif ext in ['.tar.bz2', '.tbz2']:
            result = parse_tar(file_path, 'r:bz2')
        elif ext == '.rar':
            result = parse_rar(file_path)
        elif ext == '.7z':
            result = parse_7z(file_path)
        elif ext == '.gz':
            result = parse_gz(file_path)
        else:
            raise HTTPException(status_code=400, detail="不支持的压缩格式")
        
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"解析压缩文件失败: {str(e)}")
    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
            except:
                pass
