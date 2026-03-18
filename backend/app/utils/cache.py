import time
from typing import Any, Optional, Callable, Dict
from functools import wraps
import threading
import hashlib
import json


class MemoryCache:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._cache: Dict[str, Dict[str, Any]] = {}
                    cls._instance._cache_lock = threading.RLock()
        return cls._instance
    
    def get(self, key: str) -> Optional[Any]:
        with self._cache_lock:
            item = self._cache.get(key)
            if item is None:
                return None
            if time.time() > item['expires_at']:
                del self._cache[key]
                return None
            return item['value']
    
    def set(self, key: str, value: Any, ttl: int = 60) -> None:
        with self._cache_lock:
            self._cache[key] = {
                'value': value,
                'expires_at': time.time() + ttl
            }
    
    def delete(self, key: str) -> None:
        with self._cache_lock:
            self._cache.pop(key, None)
    
    def clear(self) -> None:
        with self._cache_lock:
            self._cache.clear()
    
    def delete_pattern(self, pattern: str) -> None:
        with self._cache_lock:
            keys_to_delete = [k for k in self._cache.keys() if k.startswith(pattern)]
            for key in keys_to_delete:
                del self._cache[key]


cache = MemoryCache()


def cache_result(ttl: int = 60, key_prefix: str = ""):
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = f"{key_prefix}:{func.__name__}:{hashlib.md5(json.dumps([str(args), str(kwargs)], default=str).encode()).hexdigest()}"
            
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl)
            return result
        return wrapper
    return decorator


def cache_async(ttl: int = 60, key_prefix: str = ""):
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache_key = f"{key_prefix}:{func.__name__}:{hashlib.md5(json.dumps([str(args), str(kwargs)], default=str).encode()).hexdigest()}"
            
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            result = await func(*args, **kwargs)
            cache.set(cache_key, result, ttl)
            return result
        return wrapper
    return decorator
