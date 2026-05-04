from functools import wraps
from typing import Callable, Optional, Any, TypeVar, ParamSpec
from fastapi import HTTPException, status
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from pydantic import ValidationError
import asyncio
import traceback
from app.utils.logger import logger

P = ParamSpec("P")
T = TypeVar("T")


class AppException(Exception):
    def __init__(
        self,
        message: str,
        code: Optional[str] = None,
        status_code: int = 500,
        details: Optional[dict] = None
    ):
        self.message = message
        self.code = code or "INTERNAL_ERROR"
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class NotFoundException(AppException):
    def __init__(self, message: str = "Resource not found", details: Optional[dict] = None):
        super().__init__(
            message=message,
            code="NOT_FOUND",
            status_code=404,
            details=details
        )


class BadRequestException(AppException):
    def __init__(self, message: str = "Bad request", details: Optional[dict] = None):
        super().__init__(
            message=message,
            code="BAD_REQUEST",
            status_code=400,
            details=details
        )


class UnauthorizedException(AppException):
    def __init__(self, message: str = "Unauthorized", details: Optional[dict] = None):
        super().__init__(
            message=message,
            code="UNAUTHORIZED",
            status_code=401,
            details=details
        )


class ForbiddenException(AppException):
    def __init__(self, message: str = "Forbidden", details: Optional[dict] = None):
        super().__init__(
            message=message,
            code="FORBIDDEN",
            status_code=403,
            details=details
        )


class ConflictException(AppException):
    def __init__(self, message: str = "Conflict", details: Optional[dict] = None):
        super().__init__(
            message=message,
            code="CONFLICT",
            status_code=409,
            details=details
        )


class RateLimitException(AppException):
    def __init__(self, message: str = "Too many requests", details: Optional[dict] = None):
        super().__init__(
            message=message,
            code="RATE_LIMIT_EXCEEDED",
            status_code=429,
            details=details
        )


def handle_exceptions(
    default_message: str = "An error occurred",
    log_errors: bool = True,
    reraise: bool = True
):
    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @wraps(func)
        async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            try:
                return await func(*args, **kwargs)
            except AppException as e:
                if log_errors:
                    logger.warning(f"App exception in {func.__name__}: {e.message}")
                raise
            except HTTPException:
                raise
            except IntegrityError as e:
                if log_errors:
                    logger.error(f"Integrity error in {func.__name__}: {str(e)}")
                if reraise:
                    raise ConflictException(
                        message="数据冲突，可能已存在相同记录",
                        details={"original_error": str(e)}
                    )
                raise
            except SQLAlchemyError as e:
                if log_errors:
                    logger.error(f"Database error in {func.__name__}: {str(e)}")
                if reraise:
                    raise AppException(
                        message="数据库操作失败",
                        code="DATABASE_ERROR",
                        status_code=500,
                        details={"original_error": str(e)}
                    )
                raise
            except ValidationError as e:
                if log_errors:
                    logger.warning(f"Validation error in {func.__name__}: {str(e)}")
                if reraise:
                    raise BadRequestException(
                        message="数据验证失败",
                        details={"errors": e.errors()}
                    )
                raise
            except Exception as e:
                if log_errors:
                    logger.exception(f"Unexpected error in {func.__name__}: {str(e)}")
                if reraise:
                    raise AppException(
                        message=default_message,
                        code="INTERNAL_ERROR",
                        status_code=500,
                        details={"original_error": str(e)}
                    )
                raise
        
        @wraps(func)
        def sync_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            try:
                return func(*args, **kwargs)
            except AppException as e:
                if log_errors:
                    logger.warning(f"App exception in {func.__name__}: {e.message}")
                raise
            except HTTPException:
                raise
            except IntegrityError as e:
                if log_errors:
                    logger.error(f"Integrity error in {func.__name__}: {str(e)}")
                if reraise:
                    raise ConflictException(
                        message="数据冲突，可能已存在相同记录",
                        details={"original_error": str(e)}
                    )
                raise
            except SQLAlchemyError as e:
                if log_errors:
                    logger.error(f"Database error in {func.__name__}: {str(e)}")
                if reraise:
                    raise AppException(
                        message="数据库操作失败",
                        code="DATABASE_ERROR",
                        status_code=500,
                        details={"original_error": str(e)}
                    )
                raise
            except ValidationError as e:
                if log_errors:
                    logger.warning(f"Validation error in {func.__name__}: {str(e)}")
                if reraise:
                    raise BadRequestException(
                        message="数据验证失败",
                        details={"errors": e.errors()}
                    )
                raise
            except Exception as e:
                if log_errors:
                    logger.exception(f"Unexpected error in {func.__name__}: {str(e)}")
                if reraise:
                    raise AppException(
                        message=default_message,
                        code="INTERNAL_ERROR",
                        status_code=500,
                        details={"original_error": str(e)}
                    )
                raise
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


def handle_db_errors(func: Callable[P, T]) -> Callable[P, T]:
    @wraps(func)
    async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        try:
            return await func(*args, **kwargs)
        except IntegrityError as e:
            logger.error(f"Integrity error: {str(e)}")
            raise ConflictException("数据冲突")
        except SQLAlchemyError as e:
            logger.error(f"Database error: {str(e)}")
            raise AppException("数据库操作失败", code="DATABASE_ERROR")
    
    @wraps(func)
    def sync_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        try:
            return func(*args, **kwargs)
        except IntegrityError as e:
            logger.error(f"Integrity error: {str(e)}")
            raise ConflictException("数据冲突")
        except SQLAlchemyError as e:
            logger.error(f"Database error: {str(e)}")
            raise AppException("数据库操作失败", code="DATABASE_ERROR")
    
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    return sync_wrapper


def safe_commit(db, success_message: Optional[str] = None):
    try:
        db.commit()
        if success_message:
            logger.info(success_message)
        return True
    except IntegrityError as e:
        db.rollback()
        logger.error(f"Commit failed - Integrity error: {str(e)}")
        raise ConflictException("数据冲突，操作失败")
    except Exception as e:
        db.rollback()
        logger.error(f"Commit failed: {str(e)}")
        raise AppException("操作失败，请重试")


def safe_delete(db, model, item_id: int, item_name: str = "资源") -> bool:
    try:
        item = db.query(model).filter(model.id == item_id).first()
        if not item:
            raise NotFoundException(f"{item_name}不存在")
        
        db.delete(item)
        db.commit()
        logger.info(f"Deleted {item_name} with id {item_id}")
        return True
    except NotFoundException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to delete {item_name}: {str(e)}")
        raise AppException(f"删除{item_name}失败")
