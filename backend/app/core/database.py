from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
from app.core.config import settings
import logging
import os

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

engine = create_engine(
    database_url,
    connect_args=connect_args,
    echo=False,
    pool_pre_ping=False,
    pool_recycle=1800,
    pool_size=5,
    max_overflow=10,
    pool_timeout=60,
    poolclass=QueuePool,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

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
        cursor.close()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
