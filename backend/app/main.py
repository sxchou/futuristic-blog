from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.staticfiles import StaticFiles
from starlette.responses import FileResponse as StarletteFileResponse
from app.core.config import settings
from app.core.database import engine, Base, SessionLocal
from app.api import router as api_router
from app.services.init_data import init_database
from app.services.log_service import LogService
from app.utils import cleanup_expired_tokens
from app.models.models import Article, Category, Tag
import os
import time
import asyncio
from concurrent.futures import ThreadPoolExecutor
import logging
from contextlib import contextmanager
from datetime import datetime

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Futuristic Blog API",
    description="A futuristic personal blog system API",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

app.add_middleware(GZipMiddleware, minimum_size=1000)

class PrefetchMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        sec_purpose = request.headers.get('Sec-Purpose', '')
        purpose = request.headers.get('Purpose', '')
        
        if 'prefetch' in sec_purpose.lower() or 'prefetch' in purpose.lower():
            response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate'
            response.headers['Vary'] = 'Sec-Purpose, Purpose'
        
        return response

app.add_middleware(PrefetchMiddleware)

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        if request.url.path.startswith('/uploads/'):
            response.headers["Content-Security-Policy"] = "frame-ancestors 'self' https://view.officeapps.live.com https://*.officeapps.live.com"
        elif '/files/' in request.url.path and ('/preview' in request.url.path or '/office-preview' in request.url.path):
            response.headers["Content-Security-Policy"] = "frame-ancestors 'self' https://view.officeapps.live.com https://*.officeapps.live.com"
        else:
            response.headers["X-Frame-Options"] = "DENY"
        
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        if request.url.path.startswith("/api"):
            if '/files/' not in request.url.path:
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

class CORSStaticFiles(StaticFiles):
    async def get_response(self, path: str, scope):
        response = await super().get_response(path, scope)
        if isinstance(response, StarletteFileResponse):
            response.headers["Access-Control-Allow-Origin"] = "*"
            response.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
            response.headers["Access-Control-Allow-Headers"] = "*"
            
            ext = path.lower().split('.')[-1] if '.' in path else ''
            office_extensions = ['xlsx', 'xls', 'docx', 'doc', 'pptx', 'ppt']
            if ext in office_extensions:
                response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            else:
                response.headers["Cache-Control"] = "public, max-age=3600"
        return response

try:
    app.mount("/uploads", CORSStaticFiles(directory=uploads_dir), name="uploads")
except Exception as e:
    logger.warning(f"Failed to mount uploads directory: {e}")


def run_migrations():
    """Run database migrations for schema updates."""
    from sqlalchemy import text
    from app.core.database import is_sqlite
    db = SessionLocal()
    try:
        if is_sqlite:
            result = db.execute(text("""
                SELECT name FROM pragma_table_info('article_files')
            """))
            existing_columns = [row[0] for row in result.fetchall()]
        else:
            result = db.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'article_files'
            """))
            existing_columns = [row[0] for row in result.fetchall()]
        
        if 'view_count' not in existing_columns:
            logger.info("Adding view_count column to article_files...")
            db.execute(text('ALTER TABLE article_files ADD COLUMN view_count INTEGER DEFAULT 0'))
        
        if 'order' not in existing_columns:
            logger.info("Adding order column to article_files...")
            db.execute(text('ALTER TABLE article_files ADD COLUMN "order" INTEGER DEFAULT 0'))
        
        db.commit()
        logger.info("Database migrations completed")
    except Exception as e:
        db.rollback()
        logger.warning(f"Migration check: {e}")
    finally:
        db.close()

@app.on_event("startup")
async def startup_event():
    try:
        Base.metadata.create_all(bind=engine)
        run_migrations()
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


@app.get("/sitemap.xml")
async def get_sitemap():
    base_url = getattr(settings, 'SITE_URL', 'https://zhouzhouya.top')
    
    db = SessionLocal()
    try:
        urls = []
        
        urls.append({
            'loc': base_url,
            'lastmod': datetime.utcnow().strftime('%Y-%m-%d'),
            'changefreq': 'daily',
            'priority': '1.0'
        })
        
        static_pages = [
            ('/about', '0.8'),
            ('/categories', '0.8'),
            ('/tags', '0.8'),
            ('/resources', '0.7'),
            ('/archive', '0.7'),
        ]
        
        for path, priority in static_pages:
            urls.append({
                'loc': f'{base_url}{path}',
                'lastmod': datetime.utcnow().strftime('%Y-%m-%d'),
                'changefreq': 'weekly',
                'priority': priority
            })
        
        articles = db.query(Article).filter(
            Article.is_published == True
        ).order_by(Article.updated_at.desc()).all()
        
        for article in articles:
            lastmod = article.updated_at if article.updated_at else article.created_at
            urls.append({
                'loc': f'{base_url}/article/{article.slug}',
                'lastmod': lastmod.strftime('%Y-%m-%d') if lastmod else datetime.utcnow().strftime('%Y-%m-%d'),
                'changefreq': 'weekly',
                'priority': '0.9' if article.is_featured else '0.7'
            })
        
        categories = db.query(Category).all()
        for category in categories:
            urls.append({
                'loc': f'{base_url}/categories/{category.slug}',
                'lastmod': datetime.utcnow().strftime('%Y-%m-%d'),
                'changefreq': 'weekly',
                'priority': '0.6'
            })
        
        tags = db.query(Tag).all()
        for tag in tags:
            urls.append({
                'loc': f'{base_url}/tags/{tag.slug}',
                'lastmod': datetime.utcnow().strftime('%Y-%m-%d'),
                'changefreq': 'weekly',
                'priority': '0.5'
            })
        
        xml_content = '<?xml version="1.0" encoding="UTF-8"?>\n'
        xml_content += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        
        for url in urls:
            xml_content += '  <url>\n'
            xml_content += f'    <loc>{url["loc"]}</loc>\n'
            xml_content += f'    <lastmod>{url["lastmod"]}</lastmod>\n'
            xml_content += f'    <changefreq>{url["changefreq"]}</changefreq>\n'
            xml_content += f'    <priority>{url["priority"]}</priority>\n'
            xml_content += '  </url>\n'
        
        xml_content += '</urlset>'
        
        return Response(
            content=xml_content,
            media_type="application/xml",
            headers={"Cache-Control": "public, max-age=3600"}
        )
    finally:
        db.close()


@app.get("/robots.txt")
async def get_robots():
    base_url = getattr(settings, 'SITE_URL', 'https://zhouzhouya.top')
    
    robots_content = f"""User-agent: *
Allow: /
Allow: /article/
Allow: /categories/
Allow: /tags/
Allow: /about
Allow: /resources
Allow: /archive

Disallow: /admin
Disallow: /api/
Disallow: /login
Disallow: /register
Disallow: /forgot-password
Disallow: /verify-email

User-agent: Googlebot
Allow: /

User-agent: Bingbot
Allow: /

User-agent: Baiduspider
Allow: /

Sitemap: {base_url}/sitemap.xml
"""
    
    return Response(
        content=robots_content,
        media_type="text/plain",
        headers={"Cache-Control": "public, max-age=86400"}
    )
