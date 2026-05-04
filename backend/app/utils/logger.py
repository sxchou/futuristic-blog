import logging
import sys
from datetime import datetime, timezone
from typing import Any, Optional
from functools import wraps
import traceback


class LogFormatter(logging.Formatter):
    grey = "\x1b[38;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    
    def __init__(self, fmt: str, datefmt: str = None):
        super().__init__(fmt, datefmt)
        self.FORMATS = {
            logging.DEBUG: self.grey + fmt + self.reset,
            logging.INFO: fmt,
            logging.WARNING: self.yellow + fmt + self.reset,
            logging.ERROR: self.red + fmt + self.reset,
            logging.CRITICAL: self.bold_red + fmt + self.reset,
        }
    
    def format(self, record: logging.LogRecord) -> str:
        log_fmt = self.FORMATS.get(record.levelno, self._fmt)
        formatter = logging.Formatter(log_fmt, self.datefmt)
        return formatter.format(record)


class Logger:
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if Logger._initialized:
            return
        
        self._logger = logging.getLogger("futuristic_blog")
        self._logger.setLevel(logging.INFO)
        
        if not self._logger.handlers:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.INFO)
            
            formatter = LogFormatter(
                fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S"
            )
            console_handler.setFormatter(formatter)
            self._logger.addHandler(console_handler)
        
        Logger._initialized = True
    
    def debug(self, message: str, **kwargs):
        self._logger.debug(message, **kwargs)
    
    def info(self, message: str, **kwargs):
        self._logger.info(message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        self._logger.warning(message, **kwargs)
    
    def error(self, message: str, exc_info: bool = False, **kwargs):
        self._logger.error(message, exc_info=exc_info, **kwargs)
    
    def critical(self, message: str, exc_info: bool = True, **kwargs):
        self._logger.critical(message, exc_info=exc_info, **kwargs)
    
    def exception(self, message: str, **kwargs):
        self._logger.exception(message, **kwargs)
    
    def request(
        self,
        method: str,
        path: str,
        status_code: int,
        response_time: float,
        user_id: Optional[int] = None,
        ip_address: Optional[str] = None
    ):
        log_data = {
            "method": method,
            "path": path,
            "status_code": status_code,
            "response_time_ms": round(response_time, 2),
            "user_id": user_id,
            "ip_address": ip_address,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        if status_code >= 500:
            self.error(f"Request failed: {log_data}")
        elif status_code >= 400:
            self.warning(f"Request error: {log_data}")
        else:
            self.info(f"Request: {method} {path} - {status_code} - {response_time:.2f}ms")
    
    def db_query(
        self,
        query: str,
        params: Optional[dict] = None,
        execution_time: Optional[float] = None
    ):
        log_data = {
            "query": query[:200] if len(query) > 200 else query,
            "params": params,
            "execution_time_ms": execution_time
        }
        
        if execution_time and execution_time > 1000:
            self.warning(f"Slow query: {log_data}")
        else:
            self.debug(f"Query: {log_data}")
    
    def security(
        self,
        event: str,
        user_id: Optional[int] = None,
        ip_address: Optional[str] = None,
        details: Optional[dict] = None
    ):
        log_data = {
            "event": event,
            "user_id": user_id,
            "ip_address": ip_address,
            "details": details,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        self.warning(f"Security event: {log_data}")


logger = Logger()


def log_function(func):
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        func_name = func.__qualname__
        logger.debug(f"Entering {func_name}")
        try:
            result = await func(*args, **kwargs)
            logger.debug(f"Exiting {func_name}")
            return result
        except Exception as e:
            logger.exception(f"Error in {func_name}: {str(e)}")
            raise
    
    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        func_name = func.__qualname__
        logger.debug(f"Entering {func_name}")
        try:
            result = func(*args, **kwargs)
            logger.debug(f"Exiting {func_name}")
            return result
        except Exception as e:
            logger.exception(f"Error in {func_name}: {str(e)}")
            raise
    
    import asyncio
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    return sync_wrapper


def log_errors(message: str = "An error occurred"):
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                logger.exception(f"{message}: {str(e)}")
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.exception(f"{message}: {str(e)}")
                raise
        
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    return decorator
