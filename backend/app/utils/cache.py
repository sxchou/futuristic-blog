import time
from typing import Any, Optional, Callable, Dict, List
from functools import wraps
import threading
import hashlib
import json
from datetime import datetime, timedelta
from collections import OrderedDict


class LRUCache:
    def __init__(self, max_size: int = 1000):
        self._cache: OrderedDict[str, Dict[str, Any]] = OrderedDict()
        self._max_size = max_size
        self._lock = threading.RLock()
        self._hits = 0
        self._misses = 0
    
    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            item = self._cache.get(key)
            if item is None:
                self._misses += 1
                return None
            
            if time.time() > item['expires_at']:
                del self._cache[key]
                self._misses += 1
                return None
            
            self._cache.move_to_end(key)
            self._hits += 1
            return item['value']
    
    def set(self, key: str, value: Any, ttl: int = 60) -> None:
        with self._lock:
            if key in self._cache:
                del self._cache[key]
            
            while len(self._cache) >= self._max_size:
                self._cache.popitem(last=False)
            
            self._cache[key] = {
                'value': value,
                'expires_at': time.time() + ttl,
                'created_at': time.time()
            }
    
    def delete(self, key: str) -> bool:
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False
    
    def delete_pattern(self, pattern: str) -> int:
        with self._lock:
            keys_to_delete = [k for k in self._cache.keys() if pattern in k]
            for key in keys_to_delete:
                del self._cache[key]
            return len(keys_to_delete)
    
    def clear(self) -> None:
        with self._lock:
            self._cache.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        with self._lock:
            total_requests = self._hits + self._misses
            hit_rate = (self._hits / total_requests * 100) if total_requests > 0 else 0
            
            return {
                'size': len(self._cache),
                'max_size': self._max_size,
                'hits': self._hits,
                'misses': self._misses,
                'hit_rate': round(hit_rate, 2),
                'total_requests': total_requests
            }
    
    def cleanup_expired(self) -> int:
        with self._lock:
            current_time = time.time()
            expired_keys = [
                k for k, v in self._cache.items()
                if v['expires_at'] < current_time
            ]
            for key in expired_keys:
                del self._cache[key]
            return len(expired_keys)


class CacheManager:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._caches: Dict[str, LRUCache] = {}
                    cls._instance._default_ttl: Dict[str, int] = {
                        'articles': 60,
                        'article_detail': 300,
                        'categories': 300,
                        'tags': 300,
                        'resources': 120,
                        'site_config': 600,
                        'profile': 300,
                        'dashboard': 30,
                        'public_stats': 60,
                        'search': 30,
                    }
        return cls._instance
    
    def get_cache(self, name: str, max_size: int = 500) -> LRUCache:
        if name not in self._caches:
            self._caches[name] = LRUCache(max_size=max_size)
        return self._caches[name]
    
    def get(self, cache_name: str, key: str) -> Optional[Any]:
        cache = self.get_cache(cache_name)
        return cache.get(key)
    
    def set(self, cache_name: str, key: str, value: Any, ttl: Optional[int] = None) -> None:
        cache = self.get_cache(cache_name)
        if ttl is None:
            ttl = self._default_ttl.get(cache_name, 60)
        cache.set(key, value, ttl)
    
    def delete(self, cache_name: str, key: str) -> bool:
        cache = self.get_cache(cache_name)
        return cache.delete(key)
    
    def delete_pattern(self, cache_name: str, pattern: str) -> int:
        cache = self.get_cache(cache_name)
        return cache.delete_pattern(pattern)
    
    def clear_cache(self, cache_name: str) -> None:
        if cache_name in self._caches:
            self._caches[cache_name].clear()
    
    def clear_all(self) -> None:
        for cache in self._caches.values():
            cache.clear()
    
    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        return {name: cache.get_stats() for name, cache in self._caches.items()}
    
    def cleanup_all_expired(self) -> Dict[str, int]:
        return {name: cache.cleanup_expired() for name, cache in self._caches.items()}


cache_manager = CacheManager()


def get_cache_key(*args, **kwargs) -> str:
    key_data = json.dumps([str(arg) for arg in args], sort_keys=True, default=str)
    kwargs_data = json.dumps(kwargs, sort_keys=True, default=str)
    combined = key_data + kwargs_data
    return hashlib.md5(combined.encode()).hexdigest()


def cached(cache_name: str, ttl: Optional[int] = None, key_builder: Optional[Callable] = None):
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if key_builder:
                cache_key = key_builder(*args, **kwargs)
            else:
                cache_key = f"{func.__name__}:{get_cache_key(*args, **kwargs)}"
            
            cached_value = cache_manager.get(cache_name, cache_key)
            if cached_value is not None:
                return cached_value
            
            result = func(*args, **kwargs)
            cache_manager.set(cache_name, cache_key, result, ttl)
            return result
        return wrapper
    return decorator


def cached_async(cache_name: str, ttl: Optional[int] = None, key_builder: Optional[Callable] = None):
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            if key_builder:
                cache_key = key_builder(*args, **kwargs)
            else:
                cache_key = f"{func.__name__}:{get_cache_key(*args, **kwargs)}"
            
            cached_value = cache_manager.get(cache_name, cache_key)
            if cached_value is not None:
                return cached_value
            
            result = await func(*args, **kwargs)
            cache_manager.set(cache_name, cache_key, result, ttl)
            return result
        return wrapper
    return decorator


def invalidate_cache(cache_name: str, pattern: str = ""):
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            if pattern:
                cache_manager.delete_pattern(cache_name, pattern)
            else:
                cache_manager.clear_cache(cache_name)
            return result
        return wrapper
    return decorator


def invalidate_cache_async(cache_name: str, pattern: str = ""):
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            result = await func(*args, **kwargs)
            if pattern:
                cache_manager.delete_pattern(cache_name, pattern)
            else:
                cache_manager.clear_cache(cache_name)
            return result
        return wrapper
    return decorator


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
