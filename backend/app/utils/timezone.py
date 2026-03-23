from datetime import datetime
from zoneinfo import ZoneInfo
from app.core.config import settings


def get_now() -> datetime:
    return datetime.now(settings.tz)


def get_utc_now() -> datetime:
    return datetime.now(ZoneInfo("UTC"))


def to_local(dt: datetime) -> datetime:
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=settings.tz)
    return dt.astimezone(settings.tz)


def to_utc(dt: datetime) -> datetime:
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=settings.tz)
    return dt.astimezone(ZoneInfo("UTC")).replace(tzinfo=None)


def format_datetime(dt: datetime, fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
    if dt is None:
        return ""
    local_dt = to_local(dt) if dt.tzinfo else dt
    return local_dt.strftime(fmt)


def get_today_start() -> datetime:
    now = get_now()
    return now.replace(hour=0, minute=0, second=0, microsecond=0)


def get_today_end() -> datetime:
    now = get_now()
    return now.replace(hour=23, minute=59, second=59, microsecond=999999)
