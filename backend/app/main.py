from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse, Response
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.config import settings
from app.core.database import engine, Base, SessionLocal
from app.api import router as api_router
from app.services.init_data import init_database
from app.services.log_service import LogService
from app.utils import cleanup_expired_tokens
from app.utils.cache import cache_manager
from app.utils.performance import performance_metrics, performance_monitor
from app.models.models import Article, Category, Tag
import os
import time
import asyncio
from concurrent.futures import ThreadPoolExecutor
import logging
from contextlib import contextmanager
from datetime import datetime

IS_VERCEL = os.environ.get("VERCEL") == "1"
IS_RENDER = os.environ.get("RENDER") == "true"
IS_CLOUD_PLATFORM = IS_VERCEL or IS_RENDER

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

logger.info("Initializing FastAPI application...")

app = FastAPI(
    title="Futuristic Blog API",
    description="A futuristic personal blog system API",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

logger.info("FastAPI application created")

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
    allow_origins=settings.get_cors_origins,
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

async def cache_cleanup_task():
    while True:
        try:
            await asyncio.sleep(3600)
            cleaned = cache_manager.cleanup_all_expired()
            total_cleaned = sum(cleaned.values())
            if total_cleaned > 0:
                logger.info(f"Cleaned up {total_cleaned} expired cache entries")
        except Exception as e:
            logger.error(f"Error cleaning up cache: {e}")

async def performance_report_task():
    while True:
        try:
            await asyncio.sleep(3600)
            performance_monitor.log_report()
        except Exception as e:
            logger.error(f"Error generating performance report: {e}")

class PerformanceMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        response_time = (time.time() - start_time) * 1000
        
        performance_metrics.record_request(
            path=request.url.path,
            method=request.method,
            response_time=response_time,
            status_code=response.status_code
        )
        
        response.headers["X-Response-Time"] = f"{response_time:.2f}ms"
        
        return response

app.add_middleware(PerformanceMiddleware)

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


if not IS_VERCEL:
    def ensure_uploads_dir():
        uploads_dir = (
            settings.AVATAR_STORAGE_PATH or 
            os.getenv("AVATAR_STORAGE_PATH") or 
            os.getenv("RAILWAY_VOLUME_MOUNT_PATH") or
            os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
        )
        if not os.path.exists(uploads_dir):
            os.makedirs(uploads_dir, exist_ok=True)
        
        subdirs = ["avatars", "images", "articles", "logos"]
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
    logger.info("=== Application startup event triggered ===")
    logger.info(f"Database URL: {str(engine.url)[:50]}...")
    logger.info(f"IS_VERCEL: {IS_VERCEL}, IS_RENDER: {IS_RENDER}, IS_CLOUD_PLATFORM: {IS_CLOUD_PLATFORM}")
    
    if IS_CLOUD_PLATFORM:
        logger.info("Running in cloud platform environment, executing synchronous initialization...")
        try:
            logger.info("Creating database tables...")
            Base.metadata.create_all(bind=engine)
            logger.info("Database tables created successfully")
            
            logger.info("Initializing database data...")
            init_database()
            logger.info("Database data initialized successfully")
            
            logger.info("Syncing article comment counts...")
            sync_article_comment_counts()
            logger.info("Article comment counts synced successfully")
            
            logger.info("=== Application initialized successfully for cloud platform ===")
        except Exception as e:
            logger.error(f"Database initialization error: {e}", exc_info=True)
            raise
    else:
        logger.info("Running in local environment, executing asynchronous initialization...")
        asyncio.create_task(background_init())


async def background_init():
    logger.info("Starting background initialization...")
    try:
        logger.info("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created")
        
        logger.info("Initializing database data...")
        init_database()
        logger.info("Database data initialized")
        
        logger.info("Syncing article comment counts...")
        sync_article_comment_counts()
        logger.info("Article comment counts synced")
        
        asyncio.create_task(cleanup_expired_tokens_task())
        asyncio.create_task(cache_cleanup_task())
        asyncio.create_task(performance_report_task())
        logger.info("=== Application initialized successfully ===")
    except Exception as e:
        logger.error(f"Background init error: {e}", exc_info=True)


def sync_article_comment_counts():
    from sqlalchemy import func
    from app.models.models import Comment
    
    db = SessionLocal()
    try:
        articles = db.query(Article).all()
        updated_count = 0
        
        for article in articles:
            actual_count = db.query(func.count(Comment.id)).filter(
                Comment.article_id == article.id,
                Comment.status == 'approved',
                Comment.is_deleted == False
            ).scalar()
            
            if article.comment_count != actual_count:
                article.comment_count = actual_count
                updated_count += 1
        
        db.commit()
        logger.info(f"Synced comment counts for {updated_count} articles")
    except Exception as e:
        logger.error(f"Error syncing comment counts: {e}")
    finally:
        db.close()


@app.get("/")
async def root():
    return {
        "message": "Welcome to Futuristic Blog API",
        "docs": "/api/docs",
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check(request: Request):
    logger.info(f"Health check requested from: {request.headers.get('host', 'unknown')}")
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


@app.get("/api/performance")
async def get_performance_stats():
    return performance_monitor.get_full_report()


@app.get("/api/cache-stats")
async def get_cache_stats():
    return cache_manager.get_all_stats()


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
