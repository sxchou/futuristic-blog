import logging
import threading
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from collections import deque


class ErrorLogEmailHandler(logging.Handler):
    """
    自定义日志处理器，当出现 WARNING 或 ERROR 级别的日志时，发送邮件给管理员
    
    特性：
    - 异步发送邮件，不阻塞主线程
    - 防止邮件轰炸：同一错误在冷却时间内只发送一次
    - 批量发送：收集一段时间内的错误，合并发送
    - 支持配置最低日志级别
    """
    
    MIN_LEVEL = logging.WARNING
    
    COOLDOWN_SECONDS = 300
    
    BATCH_SECONDS = 60
    
    MAX_BATCH_SIZE = 10
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(
        self,
        min_level: int = logging.WARNING,
        cooldown_seconds: int = 300,
        batch_seconds: int = 60,
        max_batch_size: int = 10
    ):
        if self._initialized:
            return
            
        super().__init__()
        self.min_level = min_level
        self.cooldown_seconds = cooldown_seconds
        self.batch_seconds = batch_seconds
        self.max_batch_size = max_batch_size
        
        self._error_cache: Dict[str, float] = {}
        self._pending_logs: deque = deque(maxlen=100)
        self._last_send_time: float = 0
        self._email_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        
        self._initialized = True
        
        self.setLevel(min_level)
    
    def emit(self, record: logging.LogRecord) -> None:
        if record.levelno < self.min_level:
            return
        
        try:
            error_key = self._get_error_key(record)
            
            current_time = time.time()
            
            if error_key in self._error_cache:
                last_sent = self._error_cache[error_key]
                if current_time - last_sent < self.cooldown_seconds:
                    return
            
            self._pending_logs.append({
                'key': error_key,
                'time': current_time,
                'level': record.levelname,
                'logger': record.name,
                'message': self.format(record),
                'file': record.pathname,
                'line': record.lineno,
                'function': record.funcName
            })
            
            if self._should_send_email(current_time):
                self._trigger_email_send()
                
        except Exception:
            self.handleError(record)
    
    def _get_error_key(self, record: logging.LogRecord) -> str:
        message = record.getMessage()
        key_message = message[:100] if len(message) > 100 else message
        return f"{record.name}:{record.levelname}:{key_message}"
    
    def _should_send_email(self, current_time: float) -> bool:
        if len(self._pending_logs) >= self.max_batch_size:
            return True
        
        if current_time - self._last_send_time >= self.batch_seconds and self._pending_logs:
            return True
        
        return False
    
    def _trigger_email_send(self) -> None:
        if self._email_thread and self._email_thread.is_alive():
            return
        
        logs_to_send = list(self._pending_logs)
        self._pending_logs.clear()
        
        if not logs_to_send:
            return
        
        self._email_thread = threading.Thread(
            target=self._send_error_notification,
            args=(logs_to_send,),
            daemon=True
        )
        self._email_thread.start()
    
    def _send_error_notification(self, logs: List[Dict[str, Any]]) -> None:
        try:
            from app.core.database import SessionLocal
            from app.services.email_service import EmailService
            import logging
            
            error_logger = logging.getLogger(__name__)
            
            db = SessionLocal()
            try:
                self._last_send_time = time.time()
                
                current_time = time.time()
                for log in logs:
                    self._error_cache[log['key']] = current_time
                
                self._cleanup_cache(current_time)
                
                error_logger.info(f"Attempting to send error notification email with {len(logs)} error(s)")
                
                result = EmailService.send_error_log_notification_db(
                    db=db,
                    error_logs=logs
                )
                
                if result:
                    error_logger.info(f"Error notification email sent successfully")
                else:
                    error_logger.warning(f"Error notification email returned False")
                
            except Exception as inner_e:
                error_logger.error(f"Exception during email send: {inner_e}", exc_info=True)
            finally:
                db.close()
                
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Failed to send error notification: {e}", exc_info=True)
    
    def _cleanup_cache(self, current_time: float) -> None:
        expired_keys = [
            key for key, timestamp in self._error_cache.items()
            if current_time - timestamp > self.cooldown_seconds * 2
        ]
        for key in expired_keys:
            del self._error_cache[key]
    
    def stop(self) -> None:
        self._stop_event.set()
        if self._email_thread and self._email_thread.is_alive():
            self._email_thread.join(timeout=5)


error_email_handler: Optional[ErrorLogEmailHandler] = None


def setup_error_email_handler(
    min_level: int = logging.WARNING,
    cooldown_seconds: int = 300,
    batch_seconds: int = 60,
    max_batch_size: int = 10
) -> ErrorLogEmailHandler:
    global error_email_handler
    
    if error_email_handler is None:
        error_email_handler = ErrorLogEmailHandler(
            min_level=min_level,
            cooldown_seconds=cooldown_seconds,
            batch_seconds=batch_seconds,
            max_batch_size=max_batch_size
        )
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        error_email_handler.setFormatter(formatter)
        
        root_logger = logging.getLogger()
        root_logger.addHandler(error_email_handler)
    
    return error_email_handler


def get_error_email_handler() -> Optional[ErrorLogEmailHandler]:
    return error_email_handler
