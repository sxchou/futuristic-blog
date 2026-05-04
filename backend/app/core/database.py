from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
from app.core.config import settings
import logging
import os
import time
from contextlib import contextmanager

logger = logging.getLogger(__name__)

database_url = settings.get_database_url
is_sqlite = "sqlite" in database_url

connect_args = {}
if is_sqlite:
    connect_args = {"check_same_thread": False}
elif "planetscale.com" in database_url or "mysql" in database_url:
    connect_args = {"ssl": {"ssl_verify_cert": True}}
elif "postgresql" in database_url:
    connect_args = {"connect_timeout": 10}

logger.info(f"Database type: {'SQLite' if is_sqlite else 'PostgreSQL/MySQL'}")
logger.info(f"Database URL: {database_url[:50]}...")

pool_size = int(os.getenv("DB_POOL_SIZE", "10"))
max_overflow = int(os.getenv("DB_MAX_OVERFLOW", "20"))
pool_timeout = int(os.getenv("DB_POOL_TIMEOUT", "60"))
pool_recycle = int(os.getenv("DB_POOL_RECYCLE", "1800"))

engine = create_engine(
    database_url,
    connect_args=connect_args,
    echo=False,
    pool_pre_ping=True,
    pool_recycle=pool_recycle,
    pool_size=pool_size,
    max_overflow=max_overflow,
    pool_timeout=pool_timeout,
    poolclass=QueuePool,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

_pool_stats = {
    "total_connections": 0,
    "active_connections": 0,
    "failed_connections": 0
}

@event.listens_for(engine, "connect")
def receive_connect(dbapi_connection, connection_record):
    _pool_stats["total_connections"] += 1
    logger.debug(f"Database connection created: total={_pool_stats['total_connections']}")

@event.listens_for(engine, "checkout")
def receive_checkout(dbapi_connection, connection_record, connection_proxy):
    _pool_stats["active_connections"] += 1

@event.listens_for(engine, "checkin")
def receive_checkin(dbapi_connection, connection_record):
    _pool_stats["active_connections"] -= 1

if is_sqlite:
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA cache_size=-64000")
        cursor.execute("PRAGMA busy_timeout=5000")
        cursor.execute("PRAGMA temp_store=MEMORY")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA mmap_size=268435456")
        cursor.execute("PRAGMA page_size=4096")
        cursor.close()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_pool_stats():
    return {
        **_pool_stats,
        "pool_size": pool_size,
        "max_overflow": max_overflow,
        "pool_timeout": pool_timeout,
        "pool_recycle": pool_recycle,
        "engine_pool_size": engine.pool.size() if hasattr(engine, 'pool') else 0,
        "engine_pool_checked_out": engine.pool.checkedout() if hasattr(engine, 'pool') else 0,
    }

@contextmanager
def get_db_context():
    db = SessionLocal()
    start_time = time.time()
    try:
        yield db
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Database transaction error: {e}")
        raise
    finally:
        execution_time = (time.time() - start_time) * 1000
        if execution_time > 100:
            logger.warning(f"Slow database operation: {execution_time:.2f}ms")
        db.close()
