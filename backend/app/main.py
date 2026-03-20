from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.config import settings
from app.core.database import engine, Base, SessionLocal
from app.api import router as api_router
from app.services.init_data import init_database
from app.services.log_service import LogService
from app.utils import cleanup_expired_tokens
import os
import time
import asyncio
from concurrent.futures import ThreadPoolExecutor
import logging
from contextlib import contextmanager

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Futuristic Blog API",
    description="A futuristic personal blog system API",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

app.add_middleware(GZipMiddleware, minimum_size=1000)

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        if request.url.path.startswith("/api"):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, proxy-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
        
        return response

app.add_middleware(SecurityHeadersMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

executor = ThreadPoolExecutor(max_workers=4)

SKIP_LOG_PATHS = ['/api/docs', '/api/redoc', '/api/openapi.json', '/uploads', '/health', '/favicon']

@contextmanager
def get_db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def cleanup_expired_tokens_task():
    while True:
        try:
            await asyncio.sleep(86400)
            with get_db_session() as db:
                count = cleanup_expired_tokens(db)
                if count > 0:
                    logger.info(f"Cleaned up {count} expired refresh tokens")
        except Exception as e:
            logger.error(f"Error cleaning up expired tokens: {e}")

class AccessLogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if any(request.url.path.startswith(path) for path in SKIP_LOG_PATHS):
            return await call_next(request)
        
        start_time = time.time()
        response = await call_next(request)
        response_time = (time.time() - start_time) * 1000
        
        if request.url.path.startswith('/api') and response_time > 100:
            loop = asyncio.get_event_loop()
            loop.run_in_executor(
                executor,
                self._log_access_sync,
                request,
                response.status_code,
                response_time
            )
        
        return response
    
    def _log_access_sync(self, request: Request, response_status: int, response_time: float):
        db = SessionLocal()
        try:
            LogService.log_access(
                db=db,
                request=request,
                response_status=response_status,
                response_time=response_time
            )
        except Exception as e:
            logger.warning(f"Failed to log access: {e}")
        finally:
            db.close()


app.add_middleware(AccessLogMiddleware)

app.include_router(api_router, prefix="/api")


def ensure_uploads_dir():
    uploads_dir = (
        settings.AVATAR_STORAGE_PATH or 
        os.getenv("AVATAR_STORAGE_PATH") or 
        os.getenv("RAILWAY_VOLUME_MOUNT_PATH") or
        os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
    )
    if not os.path.exists(uploads_dir):
        os.makedirs(uploads_dir, exist_ok=True)
    
    subdirs = ["avatars", "images", "articles"]
    for subdir in subdirs:
        subdir_path = os.path.join(uploads_dir, subdir)
        if not os.path.exists(subdir_path):
            os.makedirs(subdir_path, exist_ok=True)
    
    return uploads_dir


uploads_dir = ensure_uploads_dir()
try:
    app.mount("/uploads", StaticFiles(directory=uploads_dir), name="uploads")
except Exception as e:
    logger.warning(f"Failed to mount uploads directory: {e}")


@app.on_event("startup")
async def startup_event():
    try:
        Base.metadata.create_all(bind=engine)
        init_database()
        asyncio.create_task(cleanup_expired_tokens_task())
        logger.info("Application started successfully")
    except Exception as e:
        logger.error(f"Startup error: {e}")


@app.get("/")
async def root():
    return {
        "message": "Welcome to Futuristic Blog API",
        "docs": "/api/docs",
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
