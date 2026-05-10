from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse, Response
from app.core.config import settings
from app.core.database import engine, Base, SessionLocal, is_sqlite
from app.api import router as api_router
from app.services.init_data import init_database
from app.services.log_service import LogService
from app.services.scheduled_publish_service import scheduled_publish_service
from app.utils import cleanup_expired_tokens
from app.utils.cache import cache_manager
from app.utils.performance import performance_metrics, performance_monitor
from app.utils.exception_handlers import register_exception_handlers
from app.utils.rate_limiter import setup_rate_limiting
from app.utils.health_check import readiness_check, liveness_check
from app.models.models import Article, Category, Tag
import os
import time
import asyncio
from concurrent.futures import ThreadPoolExecutor
import logging
from contextlib import contextmanager, asynccontextmanager
from datetime import datetime, timezone

IS_VERCEL = os.environ.get("VERCEL") == "1"
IS_RENDER = os.environ.get("RENDER") == "true"
IS_CLOUD_PLATFORM = IS_VERCEL or IS_RENDER

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

logger.info("Initializing FastAPI application...")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("=== Application startup event triggered ===")
    logger.info(f"Database URL: {str(engine.url)[:50]}...")
    logger.info(f"IS_VERCEL: {IS_VERCEL}, IS_RENDER: {IS_RENDER}, IS_CLOUD_PLATFORM: {IS_CLOUD_PLATFORM}")
    
    from app.utils.error_email_handler import setup_error_email_handler
    setup_error_email_handler(
        min_level=logging.WARNING,
        cooldown_seconds=300,
        batch_seconds=60,
        max_batch_size=10
    )
    logger.info("Error email handler initialized")
    
    if IS_CLOUD_PLATFORM:
        logger.info("Running in cloud platform environment, executing synchronous initialization...")
        try:
            logger.info("Creating database tables...")
            Base.metadata.create_all(bind=engine)
            
            migrate_foreign_key_ondelete()
            migrate_add_bookmark_count()
            migrate_add_author_name_and_reply_to_user_name()
            migrate_resources_category_nullable()
            logger.info("Database tables created successfully")
            
            logger.info("Initializing database data...")
            init_database()
            logger.info("Database data initialized successfully")
            
            logger.info("Syncing article comment counts...")
            sync_article_comment_counts()
            logger.info("Article comment counts synced successfully")
            
            logger.info("Syncing article bookmark counts...")
            sync_article_bookmark_counts()
            logger.info("Article bookmark counts synced successfully")
            
            logger.info("Syncing author_name and reply_to_user_name...")
            sync_author_name_and_reply_to_user_name()
            logger.info("author_name and reply_to_user_name synced successfully")
            
            logger.info("Fixing database sequences...")
            fix_database_sequences()
            logger.info("Database sequences fixed successfully")
            
            logger.info("=== Application initialized successfully for cloud platform ===")
        except Exception as e:
            logger.error(f"Database initialization error: {e}", exc_info=True)
            raise
    else:
        logger.info("Running in local environment, executing asynchronous initialization...")
        asyncio.create_task(background_init())
    
    await scheduled_publish_service.start()
    logger.info("Scheduled publish service started")
    
    yield
    
    await scheduled_publish_service.stop()
    logger.info("Scheduled publish service stopped")
    
    logger.info("=== Application shutdown ===")

app = FastAPI(
    title="Futuristic Blog API",
    description="A futuristic personal blog system API",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan
)

logger.info("FastAPI application created")

register_exception_handlers(app)

setup_rate_limiting(app)

app.add_middleware(GZipMiddleware, minimum_size=1000)

class SecurityHeadersMiddleware:
    BLOCKED_PATHS = [
        '/.env', '/.git', '/.svn', '/.hg', '/.htaccess', '/.htpasswd',
        '/wp-admin', '/wp-login', '/wp-content', '/wp-includes', '/wordpress',
        '/admin/config', '/config.php', '/config.yml', '/config.json',
        '/database.yml', '/.DS_Store', '/docker-compose.yml', '/docker-compose.yaml',
        '/package.json', '/composer.json', '/Gemfile', '/.npmrc', '/.bash_history',
        '/server-status', '/server-info', '/.well-known/security.txt',
        '/actuator', '/actuator/env', '/actuator/health',
        '/phpmyadmin', '/pma', '/mysql', '/phpinfo',
        '/.aws/credentials', '/.ssh', '/id_rsa',
    ]

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path = scope.get("path", "")

        if any(path.lower().startswith(bp.lower()) for bp in self.BLOCKED_PATHS):
            await send({
                "type": "http.response.start",
                "status": 403,
                "headers": [
                    (b"content-type", b"application/json"),
                    (b"cache-control", b"no-store"),
                ],
            })
            await send({
                "type": "http.response.body",
                "body": b'{"detail":"Forbidden"}',
            })
            return

        CACHEABLE_PATHS = [
            '/api/articles',
            '/api/categories',
            '/api/tags',
            '/api/resources',
            '/api/resource-categories',
            '/api/site-config',
            '/api/profile',
            '/api/announcements',
            '/api/dashboard/public-stats',
        ]

        method = scope.get("method", "")
        is_cacheable = any(path.startswith(p) for p in CACHEABLE_PATHS) and method == "GET"

        async def send_with_headers(message):
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                headers.append((b"x-content-type-options", b"nosniff"))
                headers.append((b"x-frame-options", b"DENY"))
                headers.append((b"x-xss-protection", b"1; mode=block"))
                headers.append((b"referrer-policy", b"strict-origin-when-cross-origin"))
                headers.append((b"permissions-policy", b"geolocation=(), microphone=(), camera=()"))

                if is_cacheable:
                    headers.append((b"cache-control", b"public, max-age=60, s-maxage=60, stale-while-revalidate=300"))
                    headers.append((b"cdn-cache-control", b"public, max-age=60"))
                elif path.startswith("/api"):
                    headers.append((b"cache-control", b"no-store, no-cache, must-revalidate, proxy-revalidate"))
                    headers.append((b"pragma", b"no-cache"))
                    headers.append((b"expires", b"0"))

                message["headers"] = headers
            await send(message)

        await self.app(scope, receive, send_with_headers)

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

class PerformanceMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        start_time = time.time()
        path = scope.get("path", "")
        method = scope.get("method", "")
        status_code = 200

        async def send_with_timing(message):
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message.get("status", 200)
            await send(message)

        try:
            await self.app(scope, receive, send_with_timing)
        except Exception:
            response_time = (time.time() - start_time) * 1000
            performance_metrics.record_request(
                path=path,
                method=method,
                response_time=response_time,
                status_code=500
            )
            raise

        response_time = (time.time() - start_time) * 1000
        performance_metrics.record_request(
            path=path,
            method=method,
            response_time=response_time,
            status_code=status_code
        )

app.add_middleware(PerformanceMiddleware)

class AccessLogMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path = scope.get("path", "")
        if any(path.startswith(skip) for skip in SKIP_LOG_PATHS):
            await self.app(scope, receive, send)
            return

        start_time = time.time()
        method = scope.get("method", "GET")
        query_string = scope.get("query_string", b"").decode("utf-8", errors="replace")
        headers_dict = dict(
            (k.decode("utf-8", errors="replace"), v.decode("utf-8", errors="replace"))
            for k, v in scope.get("headers", [])
        )
        client = scope.get("client")
        client_host = client[0] if client else None
        status_code = 200
        
        user_id = None
        username = None
        auth_header = headers_dict.get('authorization', '')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            try:
                from app.utils.auth import decode_token
                payload = decode_token(token)
                if payload:
                    username = payload.get('sub')
                    if username:
                        from app.core.database import SessionLocal
                        from app.models import User
                        db = SessionLocal()
                        try:
                            user = db.query(User).filter(User.username == username).first()
                            if user:
                                user_id = user.id
                        finally:
                            db.close()
            except Exception as e:
                logger.debug(f"Failed to decode token for access log: {e}")

        async def send_with_logging(message):
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message.get("status", 200)
            await send(message)

        try:
            await self.app(scope, receive, send_with_logging)
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            logger.error(f"Request processing failed: {method} {path} - {type(e).__name__}: {e}")
            raise

        response_time = (time.time() - start_time) * 1000

        if path.startswith('/api') and response_time > 100:
            try:
                request_info = {
                    'method': method,
                    'url': str(scope.get("scheme", "http")) + "://" + headers_dict.get("host", "localhost") + path + ("?" + query_string if query_string else ""),
                    'path': path,
                    'query_params': query_string,
                    'client_host': client_host,
                    'user_agent': headers_dict.get('user-agent', ''),
                    'user_id': user_id,
                    'username': username
                }
                loop = asyncio.get_running_loop()
                loop.run_in_executor(
                    executor,
                    self._log_access_sync,
                    request_info,
                    status_code,
                    response_time
                )
            except Exception as e:
                logger.warning(f"Failed to schedule access log: {e}")

    def _log_access_sync(self, request_info: dict, response_status: int, response_time: float):
        db = SessionLocal()
        try:
            from app.models import AccessLog
            log_entry = AccessLog(
                user_id=request_info.get('user_id'),
                username=request_info.get('username'),
                request_method=request_info.get('method', 'GET'),
                request_path=request_info.get('path', '/'),
                request_query=request_info.get('query_params', ''),
                ip_address=request_info.get('client_host'),
                user_agent=request_info.get('user_agent', ''),
                response_status=response_status,
                response_time=response_time
            )
            db.add(log_entry)
            db.commit()
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


async def background_init():
    logger.info("Starting background initialization...")
    try:
        logger.info("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        
        migrate_foreign_key_ondelete()
        migrate_add_bookmark_count()
        migrate_add_author_name_and_reply_to_user_name()
        migrate_resources_category_nullable()
        logger.info("Database tables created")
        
        logger.info("Initializing database data...")
        init_database()
        logger.info("Database data initialized")
        
        logger.info("Syncing article comment counts...")
        sync_article_comment_counts()
        logger.info("Article comment counts synced")
        
        logger.info("Syncing article bookmark counts...")
        sync_article_bookmark_counts()
        logger.info("Article bookmark counts synced")
        
        logger.info("Syncing author_name and reply_to_user_name...")
        sync_author_name_and_reply_to_user_name()
        logger.info("author_name and reply_to_user_name synced")
        
        logger.info("Fixing database sequences...")
        fix_database_sequences()
        logger.info("Database sequences fixed")
        
        asyncio.create_task(cleanup_expired_tokens_task())
        asyncio.create_task(cache_cleanup_task())
        asyncio.create_task(performance_report_task())
        logger.info("=== Application initialized successfully ===")
    except Exception as e:
        logger.error(f"Background init error: {e}", exc_info=True)


def migrate_foreign_key_ondelete():
    from sqlalchemy import text, inspect
    
    migrations = [
        {
            'table': 'articles',
            'fk_column': 'author_id',
            'referenced_table': 'users',
            'ondelete': 'SET NULL',
            'nullable': True,
        },
        {
            'table': 'article_files',
            'fk_column': 'uploaded_by',
            'referenced_table': 'users',
            'ondelete': 'SET NULL',
        },
        {
            'table': 'comments',
            'fk_column': 'user_id',
            'referenced_table': 'users',
            'ondelete': 'SET NULL',
        },
        {
            'table': 'comments',
            'fk_column': 'reply_to_user_id',
            'referenced_table': 'users',
            'ondelete': 'SET NULL',
        },
        {
            'table': 'comments',
            'fk_column': 'parent_id',
            'referenced_table': 'comments',
            'ondelete': 'SET NULL',
        },
        {
            'table': 'comment_audit_logs',
            'fk_column': 'operator_id',
            'referenced_table': 'users',
            'ondelete': 'SET NULL',
            'nullable': True,
        },
        {
            'table': 'email_logs',
            'fk_column': 'user_id',
            'referenced_table': 'users',
            'ondelete': 'SET NULL',
        },
        {
            'table': 'operation_logs',
            'fk_column': 'user_id',
            'referenced_table': 'users',
            'ondelete': 'SET NULL',
        },
        {
            'table': 'login_logs',
            'fk_column': 'user_id',
            'referenced_table': 'users',
            'ondelete': 'SET NULL',
        },
        {
            'table': 'access_logs',
            'fk_column': 'user_id',
            'referenced_table': 'users',
            'ondelete': 'SET NULL',
        },
        {
            'table': 'permission_change_logs',
            'fk_column': 'operator_id',
            'referenced_table': 'users',
            'ondelete': 'SET NULL',
        },
        {
            'table': 'user_role_assignments',
            'fk_column': 'assigned_by',
            'referenced_table': 'users',
            'ondelete': 'SET NULL',
        },
    ]
    
    max_retries = 3
    retry_delay = 2
    
    for attempt in range(max_retries):
        db = SessionLocal()
        try:
            inspector = inspect(engine)
            
            if is_sqlite:
                _migrate_sqlite(db, inspector, migrations)
            else:
                _migrate_postgresql(db, inspector, migrations)
            
            db.commit()
            logger.info("Foreign key ondelete migration completed successfully")
            break
        except Exception as e:
            db.rollback()
            error_str = str(e)
            
            if 'deadlock detected' in error_str.lower() and attempt < max_retries - 1:
                logger.warning(f"Deadlock detected during migration, retrying in {retry_delay}s (attempt {attempt + 1}/{max_retries})")
                import time
                time.sleep(retry_delay)
                retry_delay *= 2
            else:
                logger.warning(f"Foreign key migration skipped or partially applied: {e}")
                break
        finally:
            db.close()


def _migrate_postgresql(db, inspector, migrations):
    from sqlalchemy import text
    
    for migration in migrations:
        table = migration['table']
        fk_column = migration['fk_column']
        referenced_table = migration['referenced_table']
        ondelete = migration['ondelete']
        
        if not inspector.has_table(table):
            continue
        
        existing_fks = inspector.get_foreign_keys(table)
        existing_fk = next(
            (fk for fk in existing_fks 
             if fk.get('constrained_columns') == [fk_column] and fk.get('referred_table') == referenced_table),
            None
        )
        
        if existing_fk:
            fk_name = existing_fk.get('name')
            if fk_name:
                db.execute(text(f'ALTER TABLE {table} DROP CONSTRAINT {fk_name}'))
        
        if migration.get('nullable'):
            db.execute(text(f'ALTER TABLE {table} ALTER COLUMN {fk_column} DROP NOT NULL'))
        
        new_fk_name = f'fk_{table}_{fk_column}'
        db.execute(text(
            f'ALTER TABLE {table} ADD CONSTRAINT {new_fk_name} '
            f'FOREIGN KEY ({fk_column}) REFERENCES {referenced_table}(id) ON DELETE {ondelete}'
        ))


def _get_sqlite_fk_ondelete(db, table, fk_column):
    from sqlalchemy import text
    try:
        result = db.execute(text(f'PRAGMA foreign_key_list([{table}])'))
        for row in result:
            if row[3] == fk_column:
                ondelete = row[6]
                return ondelete if ondelete and ondelete != 'NONE' else 'NO ACTION'
    except Exception:
        pass
    return None


def _migrate_sqlite(db, inspector, migrations):
    from sqlalchemy import text
    
    db.execute(text('PRAGMA foreign_keys = OFF'))
    db.execute(text('PRAGMA legacy_alter_table = ON'))
    
    _cleanup_sqlite_temp_tables(db, inspector)
    
    tables_needing_rebuild = set()
    for migration in migrations:
        table = migration['table']
        if not inspector.has_table(table):
            continue
        
        fk_column = migration['fk_column']
        columns = inspector.get_columns(table)
        col_info = next((c for c in columns if c['name'] == fk_column), None)
        
        needs_nullable = migration.get('nullable') and col_info and not col_info.get('nullable', True)
        
        current_ondelete = _get_sqlite_fk_ondelete(db, table, fk_column)
        needs_ondelete = False
        if current_ondelete is not None:
            if current_ondelete != migration['ondelete']:
                needs_ondelete = True
        else:
            needs_ondelete = True
        
        if needs_nullable or needs_ondelete:
            tables_needing_rebuild.add(table)
    
    if not tables_needing_rebuild:
        logger.info("SQLite: no migration needed, all constraints already up to date")
        db.execute(text('PRAGMA foreign_keys = ON'))
        db.execute(text('PRAGMA legacy_alter_table = OFF'))
        return
    
    logger.info(f"SQLite: rebuilding tables {tables_needing_rebuild} to update constraints")
    
    for table in tables_needing_rebuild:
        try:
            _rebuild_sqlite_table(db, inspector, table)
        except Exception as e:
            logger.error(f"SQLite: failed to rebuild table {table}: {e}")
            db.execute(text('PRAGMA foreign_keys = ON'))
            db.execute(text('PRAGMA legacy_alter_table = OFF'))
            raise
    
    _fix_sqlite_bad_fk_references(db, inspector)
    
    db.execute(text('PRAGMA foreign_keys = ON'))
    db.execute(text('PRAGMA legacy_alter_table = OFF'))


def _fix_sqlite_bad_fk_references(db, inspector):
    from sqlalchemy import text
    
    all_tables = inspector.get_table_names()
    tables_with_bad_fk = set()
    
    for table in all_tables:
        if table.startswith('_temp_'):
            continue
        try:
            result = db.execute(text(f'PRAGMA foreign_key_list([{table}])'))
            for row in result:
                ref_table = row[2]
                if ref_table.startswith('_temp_'):
                    tables_with_bad_fk.add(table)
                    break
        except Exception:
            continue
    
    if not tables_with_bad_fk:
        return
    
    logger.info(f"SQLite: fixing bad FK references in tables {tables_with_bad_fk}")
    
    for table in tables_with_bad_fk:
        try:
            _rebuild_sqlite_table(db, inspector, table)
        except Exception as e:
            logger.error(f"SQLite: failed to fix FK references in table {table}: {e}")
            raise


def _cleanup_sqlite_temp_tables(db, inspector):
    from sqlalchemy import text
    
    all_tables = inspector.get_table_names()
    temp_tables = [t for t in all_tables if t.startswith('_temp_')]
    
    if not temp_tables:
        return
    
    logger.info(f"SQLite cleanup: found temp tables {temp_tables}")
    
    for temp_table in temp_tables:
        original_table = temp_table[6:]
        original_exists = original_table in all_tables
        
        if original_exists:
            try:
                orig_count = db.execute(text(f'SELECT COUNT(*) FROM [{original_table}]')).scalar()
                temp_count = db.execute(text(f'SELECT COUNT(*) FROM [{temp_table}]')).scalar()
            except Exception:
                orig_count = 0
                temp_count = 0
            
            if orig_count == 0 and temp_count > 0:
                db.execute(text(f'DROP TABLE IF EXISTS [{original_table}]'))
                db.execute(text(f'ALTER TABLE [{temp_table}] RENAME TO [{original_table}]'))
                logger.info(f"SQLite cleanup: restored {original_table} from {temp_table} ({temp_count} rows)")
            else:
                db.execute(text(f'DROP TABLE IF EXISTS [{temp_table}]'))
                logger.info(f"SQLite cleanup: dropped {temp_table} (original has {orig_count} rows, temp has {temp_count} rows)")
        else:
            db.execute(text(f'ALTER TABLE [{temp_table}] RENAME TO [{original_table}]'))
            logger.info(f"SQLite cleanup: restored missing table {original_table} from {temp_table}")


def _rebuild_sqlite_table(db, inspector, table):
    from sqlalchemy import text, inspect
    
    all_tables = inspector.get_table_names()
    temp_table = f'_temp_{table}'
    
    if temp_table in all_tables and table in all_tables:
        db.execute(text(f'DROP TABLE IF EXISTS [{temp_table}]'))
        db.commit()
    elif temp_table in all_tables and table not in all_tables:
        db.execute(text(f'ALTER TABLE [{temp_table}] RENAME TO [{table}]'))
        db.commit()
        all_tables = inspector.get_table_names()
    
    if table not in all_tables:
        logger.warning(f"SQLite migration: table {table} does not exist, skipping")
        return
    
    columns = inspector.get_columns(table)
    col_names = [c['name'] for c in columns]
    
    indexes = inspector.get_indexes(table)
    for idx in indexes:
        idx_name = idx.get('name')
        if idx_name:
            try:
                db.execute(text(f'DROP INDEX IF EXISTS [{idx_name}]'))
            except Exception:
                pass
    
    db.execute(text(f'DROP TABLE IF EXISTS [{temp_table}]'))
    
    db.execute(text(f'ALTER TABLE [{table}] RENAME TO [{temp_table}]'))
    db.commit()
    
    from app.models.models import Base
    table_obj = Base.metadata.tables.get(table)
    if table_obj is None:
        logger.warning(f"SQLite migration: table {table} not found in metadata, restoring")
        db.execute(text(f'ALTER TABLE [{temp_table}] RENAME TO [{table}]'))
        db.commit()
        return
    
    conn = db.connection()
    
    try:
        table_obj.create(conn, checkfirst=True)
        db.commit()
    except Exception as create_err:
        logger.error(f"SQLite migration: failed to create table {table}: {create_err}, restoring from temp")
        db.execute(text(f'DROP TABLE IF EXISTS [{table}]'))
        db.execute(text(f'ALTER TABLE [{temp_table}] RENAME TO [{table}]'))
        db.commit()
        raise
    
    new_inspector = inspect(conn)
    if table not in new_inspector.get_table_names():
        logger.error(f"SQLite migration: table {table} was not created, restoring from temp")
        db.execute(text(f'ALTER TABLE [{temp_table}] RENAME TO [{table}]'))
        db.commit()
        raise RuntimeError(f"Failed to create table {table}")
    
    new_columns = new_inspector.get_columns(table)
    new_col_names = [c['name'] for c in new_columns]
    common_cols = [c for c in col_names if c in new_col_names]
    common_col_list = ', '.join(f'[{c}]' for c in common_cols)
    
    try:
        db.execute(text(f'INSERT INTO [{table}] ({common_col_list}) SELECT {common_col_list} FROM [{temp_table}]'))
        db.commit()
    except Exception as insert_err:
        logger.error(f"SQLite migration: failed to copy data for table {table}: {insert_err}, restoring from temp")
        db.execute(text(f'DROP TABLE IF EXISTS [{table}]'))
        db.execute(text(f'ALTER TABLE [{temp_table}] RENAME TO [{table}]'))
        db.commit()
        raise
    
    db.execute(text(f'DROP TABLE [{temp_table}]'))
    db.commit()
    
    logger.info(f"SQLite: table {table} rebuilt successfully")


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


def migrate_add_bookmark_count():
    from sqlalchemy import text, inspect
    
    db = SessionLocal()
    try:
        inspector = inspect(db.get_bind())
        columns = [col['name'] for col in inspector.get_columns('articles')]
        if 'bookmark_count' not in columns:
            db.execute(text('ALTER TABLE articles ADD COLUMN bookmark_count INTEGER DEFAULT 0'))
            db.commit()
            logger.info("Migration: bookmark_count column added")
        else:
            logger.info("Migration: bookmark_count column already exists")
    except Exception as e:
        logger.error(f"Error migrating bookmark_count column: {e}")
        db.rollback()
    finally:
        db.close()


def sync_article_bookmark_counts():
    from sqlalchemy import func
    from app.models.models import ArticleBookmark
    
    db = SessionLocal()
    try:
        articles = db.query(Article).all()
        updated_count = 0
        
        for article in articles:
            actual_count = db.query(func.count(ArticleBookmark.id)).filter(
                ArticleBookmark.article_id == article.id
            ).scalar()
            
            if article.bookmark_count != actual_count:
                article.bookmark_count = actual_count
                updated_count += 1
        
        db.commit()
        logger.info(f"Synced bookmark counts for {updated_count} articles")
    except Exception as e:
        logger.error(f"Error syncing bookmark counts: {e}")
    finally:
        db.close()


def migrate_add_author_name_and_reply_to_user_name():
    from sqlalchemy import text, inspect
    
    db = SessionLocal()
    try:
        inspector = inspect(db.get_bind())
        
        article_columns = [col['name'] for col in inspector.get_columns('articles')]
        if 'author_name' not in article_columns:
            db.execute(text('ALTER TABLE articles ADD COLUMN author_name VARCHAR(50)'))
            db.commit()
            logger.info("Migration: author_name column added to articles")
        else:
            logger.info("Migration: author_name column already exists in articles")
        
        comment_columns = [col['name'] for col in inspector.get_columns('comments')]
        
        if 'author_name' not in comment_columns:
            db.execute(text('ALTER TABLE comments ADD COLUMN author_name VARCHAR(50)'))
            db.commit()
            logger.info("Migration: author_name column added to comments")
        else:
            logger.info("Migration: author_name column already exists in comments")
        
        if 'author_email' not in comment_columns:
            db.execute(text('ALTER TABLE comments ADD COLUMN author_email VARCHAR(100)'))
            db.commit()
            logger.info("Migration: author_email column added to comments")
        else:
            logger.info("Migration: author_email column already exists in comments")
        
        if 'author_url' not in comment_columns:
            db.execute(text('ALTER TABLE comments ADD COLUMN author_url VARCHAR(255)'))
            db.commit()
            logger.info("Migration: author_url column added to comments")
        else:
            logger.info("Migration: author_url column already exists in comments")
        
        if 'reply_to_user_name' not in comment_columns:
            db.execute(text('ALTER TABLE comments ADD COLUMN reply_to_user_name VARCHAR(50)'))
            db.commit()
            logger.info("Migration: reply_to_user_name column added to comments")
        else:
            logger.info("Migration: reply_to_user_name column already exists in comments")
        
        if 'deleted_by' not in comment_columns:
            db.execute(text('ALTER TABLE comments ADD COLUMN deleted_by VARCHAR(20)'))
            db.commit()
            logger.info("Migration: deleted_by column added to comments")
        else:
            logger.info("Migration: deleted_by column already exists in comments")
        
        if 'is_deleted' not in comment_columns:
            db.execute(text('ALTER TABLE comments ADD COLUMN is_deleted BOOLEAN DEFAULT 0'))
            db.commit()
            logger.info("Migration: is_deleted column added to comments")
        else:
            logger.info("Migration: is_deleted column already exists in comments")
        
        if 'is_approved' not in comment_columns:
            db.execute(text('ALTER TABLE comments ADD COLUMN is_approved BOOLEAN DEFAULT 1'))
            db.commit()
            logger.info("Migration: is_approved column added to comments")
        else:
            logger.info("Migration: is_approved column already exists in comments")
        
        if 'status' not in comment_columns:
            db.execute(text("ALTER TABLE comments ADD COLUMN status VARCHAR(20) DEFAULT 'approved'"))
            db.commit()
            logger.info("Migration: status column added to comments")
        else:
            logger.info("Migration: status column already exists in comments")
    except Exception as e:
        logger.error(f"Error migrating author_name/reply_to_user_name columns: {e}")
        db.rollback()
    finally:
        db.close()


def migrate_resources_category_nullable():
    from sqlalchemy import text, inspect
    
    db = SessionLocal()
    try:
        inspector = inspect(db.get_bind())
        
        if 'resources' not in inspector.get_table_names():
            logger.info("Migration: resources table does not exist, skipping")
            return
        
        resource_columns = inspector.get_columns('resources')
        category_col = next((col for col in resource_columns if col['name'] == 'category'), None)
        
        if category_col and not category_col.get('nullable', True):
            db_url = str(db.get_bind().url)
            if 'postgresql' in db_url:
                db.execute(text('ALTER TABLE resources ALTER COLUMN category DROP NOT NULL'))
            else:
                db.execute(text('ALTER TABLE resources MODIFY COLUMN category VARCHAR(50) NULL'))
            db.commit()
            logger.info("Migration: resources.category column changed to nullable")
        else:
            logger.info("Migration: resources.category column already nullable or does not exist")
    except Exception as e:
        logger.error(f"Error migrating resources.category nullable: {e}")
        db.rollback()
    finally:
        db.close()


def sync_author_name_and_reply_to_user_name():
    from sqlalchemy import text
    
    db = SessionLocal()
    try:
        db.execute(text(
            "UPDATE articles SET author_name = (SELECT username FROM users WHERE users.id = articles.author_id) "
            "WHERE author_id IS NOT NULL AND author_name IS NULL"
        ))
        
        db.execute(text(
            "UPDATE comments SET author_name = (SELECT username FROM users WHERE users.id = comments.user_id) "
            "WHERE user_id IS NOT NULL AND author_name IS NULL"
        ))
        
        db.execute(text(
            "UPDATE comments SET reply_to_user_name = (SELECT username FROM users WHERE users.id = comments.reply_to_user_id) "
            "WHERE reply_to_user_id IS NOT NULL AND reply_to_user_name IS NULL"
        ))
        
        db.commit()
        logger.info("Synced author_name and reply_to_user_name from existing user records")
    except Exception as e:
        logger.error(f"Error syncing author_name/reply_to_user_name: {e}")
        db.rollback()
    finally:
        db.close()


def fix_database_sequences():
    from sqlalchemy import text, inspect
    from app.utils.db_utils import DatabaseUtils
    
    db = SessionLocal()
    try:
        db_url = str(db.get_bind().url)
        if 'sqlite' in db_url.lower():
            logger.info("SQLite detected, skipping sequence fix (not needed)")
            return
        
        inspector = inspect(db.get_bind())
        table_names = inspector.get_table_names()
        
        fixed_count = 0
        for table_name in sorted(table_names):
            seq_name = f"{table_name}_id_seq"
            try:
                has_id = any(col['name'] == 'id' for col in inspector.get_columns(table_name))
                if not has_id:
                    continue
                
                result = db.execute(text(f"SELECT MAX(id) FROM {table_name}")).scalar()
                max_id = result or 0
                next_val = max_id + 1
                DatabaseUtils.set_sequence_safe(db, seq_name, next_val)
                fixed_count += 1
            except Exception as e:
                logger.warning(f"Skipping {table_name}: {e}")
                db.rollback()
        
        logger.info(f"Fixed {fixed_count} database sequences")
    except Exception as e:
        logger.error(f"Error fixing sequences: {e}")
        db.rollback()
    finally:
        db.close()


@app.api_route("/", methods=["GET", "HEAD"])
async def root():
    return {
        "message": "Welcome to Futuristic Blog API",
        "docs": "/api/docs",
        "version": "1.0.0"
    }


@app.api_route("/health", methods=["GET", "HEAD"])
async def health_check(request: Request):
    logger.info(f"Health check requested from: {request.headers.get('host', 'unknown')}")
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}


@app.api_route("/health/full", methods=["GET", "HEAD"])
async def health_check_full(request: Request):
    logger.info(f"Full health check requested from: {request.headers.get('host', 'unknown')}")
    
    db_healthy = False
    try:
        from sqlalchemy import text
        with SessionLocal() as db:
            db.execute(text("SELECT 1"))
            db_healthy = True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
    
    return {
        "status": "healthy" if db_healthy else "degraded",
        "database": "connected" if db_healthy else "disconnected",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@app.api_route("/health/ready", methods=["GET", "HEAD"])
async def readiness_check_endpoint():
    with SessionLocal() as db:
        return await readiness_check(db)


@app.api_route("/health/live", methods=["GET", "HEAD"])
async def liveness_check_endpoint():
    return await liveness_check()


@app.get("/api/performance")
async def get_performance_stats():
    return performance_monitor.get_full_report()


@app.get("/api/cache-stats")
async def get_cache_stats():
    return cache_manager.get_all_stats()


@app.get("/sitemap.xml")
async def get_sitemap():
    base_url = settings.SITE_URL
    
    db = SessionLocal()
    try:
        urls = []
        
        urls.append({
            'loc': base_url,
            'lastmod': datetime.now(timezone.utc).strftime('%Y-%m-%d'),
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
                'lastmod': datetime.now(timezone.utc).strftime('%Y-%m-%d'),
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
                'lastmod': lastmod.strftime('%Y-%m-%d') if lastmod else datetime.now(timezone.utc).strftime('%Y-%m-%d'),
                'changefreq': 'weekly',
                'priority': '0.9' if article.is_featured else '0.7'
            })
        
        categories = db.query(Category).all()
        for category in categories:
            urls.append({
                'loc': f'{base_url}/categories/{category.slug}',
                'lastmod': datetime.now(timezone.utc).strftime('%Y-%m-%d'),
                'changefreq': 'weekly',
                'priority': '0.6'
            })
        
        tags = db.query(Tag).all()
        for tag in tags:
            urls.append({
                'loc': f'{base_url}/tags/{tag.slug}',
                'lastmod': datetime.now(timezone.utc).strftime('%Y-%m-%d'),
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
    base_url = settings.SITE_URL
    
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
