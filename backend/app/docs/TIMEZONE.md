# Timezone Configuration Documentation

## Overview

This document describes the timezone configuration and handling strategy for the Futuristic Blog system. The system is designed to store all times in UTC and convert to the configured timezone for display.

## Configuration

### Environment Variable

The timezone is configured via the `TIMEZONE` environment variable:

```bash
TIMEZONE=Asia/Shanghai
```

### Default Timezone

If no environment variable is set, the system defaults to `Asia/Shanghai`.

### Configuration Location

- **File**: `backend/app/core/config.py`
- **Property**: `Settings.TIMEZONE`
- **Type**: `str` (IANA timezone identifier)

## Time Handling Strategy

### Database Storage

All datetime values in the database are stored as **UTC naive datetime** (without timezone info).

```
┌─────────────────────────────────────────────────────────────┐
│                    DATABASE LAYER                           │
│                                                             │
│  All times stored as UTC naive datetime                     │
│  Example: 2024-01-01 06:00:00 (represents 14:00 Shanghai)  │
└─────────────────────────────────────────────────────────────┘
```

### API Response

When returning datetime values through API responses, the system:

1. Reads the UTC naive datetime from database
2. Converts to local timezone using `to_local()`
3. Returns as ISO format string with timezone info

```
┌─────────────────────────────────────────────────────────────┐
│                    API LAYER                                │
│                                                             │
│  Input:  2024-01-01 06:00:00 (UTC naive)                   │
│  Output: 2024-01-01T14:00:00+08:00 (Asia/Shanghai)         │
└─────────────────────────────────────────────────────────────┘
```

### Frontend Display

The frontend receives ISO format strings with timezone info and formats them using the browser's `Intl.DateTimeFormat` API with explicit timezone setting.

## Utility Functions

### Backend (`app/utils/timezone.py`)

| Function | Description | Returns |
|----------|-------------|---------|
| `get_db_now()` | Current UTC time for database storage | `datetime` (naive, UTC) |
| `get_now()` | Current time in configured timezone | `datetime` (timezone-aware) |
| `get_utc_now()` | Current UTC time with timezone info | `datetime` (timezone-aware, UTC) |
| `to_local(dt)` | Convert UTC datetime to local timezone | `datetime` (timezone-aware) |
| `to_utc(dt)` | Convert local datetime to UTC | `datetime` (naive, UTC) |
| `format_datetime(dt, fmt)` | Format datetime for display | `str` |
| `get_today_start()` | Start of today in local timezone | `datetime` (timezone-aware) |
| `get_today_end()` | End of today in local timezone | `datetime` (timezone-aware) |

### Frontend (`src/utils/date.ts`)

| Function | Description | Returns |
|----------|-------------|---------|
| `formatDate(date, includeTime)` | Format date with Asia/Shanghai timezone | `str` |
| `formatDateShort(date)` | Format date only (no time) | `str` |
| `formatDateTime(date)` | Format date with time | `str` |

## Time Comparison Rules

### Critical Rule: Always Compare Like with Like

When comparing times:
- **Database times** are compared with `get_db_now()` (UTC naive)
- **Local times** are compared with `get_now()` (timezone-aware)

```python
# CORRECT: Compare UTC with UTC
expires_at = get_db_now() + timedelta(hours=24)
if expires_at < get_db_now():
    # Token expired

# WRONG: Comparing timezone-aware with naive
# This will cause incorrect results!
```

## Affected Modules

### 1. User Authentication
- **File**: `app/api/v1/auth.py`
- **Operations**: 
  - Email verification token expiry
  - Password reset token expiry
  - Session management

### 2. Email Service
- **File**: `app/services/email_service.py`
- **Operations**:
  - Verification token generation
  - Email log timestamps
  - OAuth temp token expiry

### 3. Token Management
- **File**: `app/utils/auth.py`
- **Operations**:
  - Refresh token creation
  - Token expiry validation
  - Token revocation timestamps

### 4. Logging
- **File**: `app/services/log_service.py`
- **Operations**:
  - Operation logs
  - Login logs
  - Access logs

### 5. Dashboard Statistics
- **File**: `app/api/v1/dashboard.py`
- **Operations**:
  - Daily statistics calculation
  - Trend data aggregation

### 6. File Upload
- **File**: `app/api/v1/files.py`
- **Operations**:
  - Filename timestamp generation (display only)

## Database Models

All datetime columns use `get_db_now` as the default value:

```python
class User(Base):
    created_at = Column(DateTime, default=get_db_now)
    updated_at = Column(DateTime, default=get_db_now, onupdate=get_db_now)
```

## Schema Serialization

All datetime fields in Pydantic schemas use `serialize_datetime`:

```python
@field_validator('created_at', mode='before')
@classmethod
def serialize_created_at(cls, v):
    return serialize_datetime(v)
```

## Testing

Run timezone tests:

```bash
cd backend
pytest app/tests/test_timezone.py -v
```

## Common Issues and Solutions

### Issue: Time appears 8 hours off

**Cause**: Database storing local time instead of UTC

**Solution**: Ensure all database writes use `get_db_now()`

### Issue: Verification token always expired

**Cause**: Comparing timezone-aware datetime with naive datetime

**Solution**: Use `get_db_now()` for all database time comparisons

### Issue: Inconsistent times across components

**Cause**: Some components not using centralized date utilities

**Solution**: Import and use `formatDate` from `@/utils/date.ts`

## Deployment Configuration

### Railway

Set the environment variable in Railway dashboard:

```
TIMEZONE=Asia/Shanghai
```

### Docker

Add to `docker-compose.yml` or Dockerfile:

```yaml
environment:
  - TIMEZONE=Asia/Shanghai
```

## Change Log

| Date | Change | Files |
|------|--------|-------|
| 2024-03 | Initial timezone standardization | All backend files |
| 2024-03 | Added timezone test suite | `app/tests/test_timezone.py` |
| 2024-03 | Created documentation | `app/docs/TIMEZONE.md` |
