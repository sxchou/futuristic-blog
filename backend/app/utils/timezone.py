from datetime import datetime
import logging

logger = logging.getLogger(__name__)

try:
    from zoneinfo import ZoneInfo
except ImportError:
    try:
        from backports.zoneinfo import ZoneInfo
    except ImportError:
        ZoneInfo = None

from app.core.config import settings


def get_now() -> datetime:
    if ZoneInfo:
        return datetime.now(settings.tz)
    return datetime.now()


def get_utc_now() -> datetime:
    if ZoneInfo:
        return datetime.now(ZoneInfo("UTC"))
    return datetime.utcnow()


def get_db_now() -> datetime:
    return datetime.utcnow()


def to_local(dt: datetime) -> datetime:
    if dt is None:
        return None
    if ZoneInfo is None:
        return dt
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=ZoneInfo("UTC"))
    return dt.astimezone(settings.tz)


def to_utc(dt: datetime) -> datetime:
    if dt is None:
        return None
    if ZoneInfo is None:
        return dt
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=settings.tz)
    return dt.astimezone(ZoneInfo("UTC")).replace(tzinfo=None)


def format_datetime(dt: datetime, fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
    if dt is None:
        return ""
    local_dt = to_local(dt)
    return local_dt.strftime(fmt)


def get_today_start() -> datetime:
    now = get_now()
    return now.replace(hour=0, minute=0, second=0, microsecond=0)


def get_today_end() -> datetime:
    now = get_now()
    return now.replace(hour=23, minute=59, second=59, microsecond=999999)
