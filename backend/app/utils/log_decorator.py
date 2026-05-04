import functools
from typing import Optional, Callable
from fastapi import Request
from app.core.database import SessionLocal
from app.services.log_service import LogService


def log_operation(
    action: str,
    module: str,
    description: Optional[str] = None,
    target_type: Optional[str] = None
):
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            request = None
            current_user = None
            target_id = None
            status = "success"
            error_message = None
            
            for arg in args:
                if hasattr(arg, 'method'):
                    request = arg
                if hasattr(arg, 'id') and hasattr(arg, 'username'):
                    current_user = arg
            
            if 'request' in kwargs:
                request = kwargs['request']
            if 'current_user' in kwargs:
                current_user = kwargs['current_user']
            
            try:
                result = await func(*args, **kwargs)
                if isinstance(result, dict) and 'id' in result:
                    target_id = result['id']
                return result
            except Exception as e:
                status = "failed"
                error_message = str(e)
                raise
            finally:
                db = SessionLocal()
                try:
                    LogService.log_operation(
                        db=db,
                        user_id=current_user.id if current_user else None,
                        username=current_user.username if current_user else None,
                        action=action,
                        module=module,
                        description=description,
                        target_type=target_type,
                        target_id=target_id,
                        request=request,
                        status=status,
                        error_message=error_message
                    )
                except Exception as log_error:
                    print(f"Failed to log operation: {log_error}")
                finally:
                    db.close()
        
        return wrapper
    return decorator
