from fastapi import Request, status
from fastapi.responses import JSONResponse
from typing import Dict, Optional
from collections import defaultdict
from datetime import datetime, timedelta
import time
import asyncio
from app.utils.logger import logger


class RateLimiter:
    def __init__(
        self,
        requests_per_minute: int = 60,
        requests_per_hour: int = 1000,
        burst_size: int = 10
    ):
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        self.burst_size = burst_size
        
        self._minute_buckets: Dict[str, list] = defaultdict(list)
        self._hour_buckets: Dict[str, list] = defaultdict(list)
        self._burst_buckets: Dict[str, list] = defaultdict(list)
        
        self._lock = asyncio.Lock()
        
        self._whitelist_paths = {
            "/health",
            "/health/full",
            "/api/docs",
            "/api/redoc",
            "/api/openapi.json",
            "/favicon.ico",
        }
        
        self._whitelist_prefixes = {
            "/uploads/",
        }
    
    def _get_client_key(self, request: Request) -> str:
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            ip = forwarded.split(",")[0].strip()
        elif request.client:
            ip = request.client.host
        else:
            ip = "unknown"
        
        user_id = getattr(request.state, "user_id", None)
        if user_id:
            return f"user:{user_id}"
        return f"ip:{ip}"
    
    def _is_whitelisted(self, path: str) -> bool:
        if path in self._whitelist_paths:
            return True
        return any(path.startswith(prefix) for prefix in self._whitelist_prefixes)
    
    async def _cleanup_old_requests(self, bucket: list, window_seconds: int) -> int:
        current_time = time.time()
        cutoff = current_time - window_seconds
        while bucket and bucket[0] < cutoff:
            bucket.pop(0)
        return len(bucket)
    
    async def check_rate_limit(self, request: Request) -> Optional[JSONResponse]:
        if self._is_whitelisted(request.url.path):
            return None
        
        key = self._get_client_key(request)
        current_time = time.time()
        
        async with self._lock:
            burst_count = await self._cleanup_old_requests(
                self._burst_buckets[key], 1
            )
            if burst_count >= self.burst_size:
                logger.info(f"Rate limit exceeded (burst): {key}")
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={"detail": "请求过于频繁，请稍后再试"},
                    headers={"Retry-After": "1"}
                )
            
            minute_count = await self._cleanup_old_requests(
                self._minute_buckets[key], 60
            )
            if minute_count >= self.requests_per_minute:
                logger.info(f"Rate limit exceeded (minute): {key}")
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={"detail": "请求次数超过限制，请稍后再试"},
                    headers={"Retry-After": "60"}
                )
            
            hour_count = await self._cleanup_old_requests(
                self._hour_buckets[key], 3600
            )
            if hour_count >= self.requests_per_hour:
                logger.info(f"Rate limit exceeded (hour): {key}")
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={"detail": "小时请求次数超过限制"},
                    headers={"Retry-After": "3600"}
                )
            
            self._burst_buckets[key].append(current_time)
            self._minute_buckets[key].append(current_time)
            self._hour_buckets[key].append(current_time)
        
        return None
    
    async def cleanup_all(self):
        async with self._lock:
            current_time = time.time()
            
            for key in list(self._burst_buckets.keys()):
                await self._cleanup_old_requests(self._burst_buckets[key], 1)
                if not self._burst_buckets[key]:
                    del self._burst_buckets[key]
            
            for key in list(self._minute_buckets.keys()):
                await self._cleanup_old_requests(self._minute_buckets[key], 60)
                if not self._minute_buckets[key]:
                    del self._minute_buckets[key]
            
            for key in list(self._hour_buckets.keys()):
                await self._cleanup_old_requests(self._hour_buckets[key], 3600)
                if not self._hour_buckets[key]:
                    del self._hour_buckets[key]
    
    def get_stats(self) -> dict:
        return {
            "active_clients_minute": len(self._minute_buckets),
            "active_clients_hour": len(self._hour_buckets),
            "total_requests_minute": sum(len(b) for b in self._minute_buckets.values()),
            "total_requests_hour": sum(len(b) for b in self._hour_buckets.values()),
        }


rate_limiter = RateLimiter(
    requests_per_minute=120,
    requests_per_hour=3000,
    burst_size=30
)


def setup_rate_limiting(app):
    from starlette.middleware.base import BaseHTTPMiddleware
    
    @app.middleware("http")
    async def rate_limit_middleware(request: Request, call_next):
        response = await rate_limiter.check_rate_limit(request)
        if response:
            return response
        
        response = await call_next(request)
        
        key = rate_limiter._get_client_key(request)
        response.headers["X-RateLimit-Limit"] = str(rate_limiter.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(
            max(0, rate_limiter.requests_per_minute - len(rate_limiter._minute_buckets.get(key, [])))
        )
        
        return response
    
    logger.info("Rate limiting middleware configured")
