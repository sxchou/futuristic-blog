from fastapi import Request
from fastapi.responses import JSONResponse
from datetime import datetime, timezone
from typing import Dict, Any, Optional
import asyncio
import psutil
import os
from app.utils.logger import logger
from app.utils.cache import cache_manager
from app.utils.performance import performance_metrics


class HealthChecker:
    def __init__(self):
        self.start_time = datetime.now(timezone.utc)
        self._last_check = None
        self._check_history = []
    
    async def check_database(self, db) -> Dict[str, Any]:
        from sqlalchemy import text
        
        try:
            start = datetime.now()
            db.execute(text("SELECT 1"))
            latency = (datetime.now() - start).total_seconds() * 1000
            
            return {
                "status": "healthy",
                "latency_ms": round(latency, 2)
            }
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    async def check_cache(self) -> Dict[str, Any]:
        try:
            stats = cache_manager.get_all_stats()
            return {
                "status": "healthy",
                "stats": stats
            }
        except Exception as e:
            logger.error(f"Cache health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    def check_memory(self) -> Dict[str, Any]:
        try:
            process = psutil.Process(os.getpid())
            memory_info = process.memory_info()
            
            return {
                "status": "healthy",
                "rss_mb": round(memory_info.rss / 1024 / 1024, 2),
                "vms_mb": round(memory_info.vms / 1024 / 1024, 2),
                "percent": round(process.memory_percent(), 2)
            }
        except Exception as e:
            return {
                "status": "unknown",
                "error": str(e)
            }
    
    def check_cpu(self) -> Dict[str, Any]:
        try:
            process = psutil.Process(os.getpid())
            cpu_percent = process.cpu_percent(interval=0.1)
            
            return {
                "status": "healthy",
                "percent": round(cpu_percent, 2)
            }
        except Exception as e:
            return {
                "status": "unknown",
                "error": str(e)
            }
    
    def check_disk(self) -> Dict[str, Any]:
        try:
            disk = psutil.disk_usage("/")
            
            return {
                "status": "healthy" if disk.percent < 90 else "warning",
                "total_gb": round(disk.total / 1024 / 1024 / 1024, 2),
                "used_gb": round(disk.used / 1024 / 1024 / 1024, 2),
                "free_gb": round(disk.free / 1024 / 1024 / 1024, 2),
                "percent": disk.percent
            }
        except Exception as e:
            return {
                "status": "unknown",
                "error": str(e)
            }
    
    def get_uptime(self) -> Dict[str, Any]:
        now = datetime.now(timezone.utc)
        uptime = now - self.start_time
        
        return {
            "started_at": self.start_time.isoformat(),
            "uptime_seconds": int(uptime.total_seconds()),
            "uptime_human": str(uptime).split(".")[0]
        }
    
    async def full_check(self, db=None) -> Dict[str, Any]:
        checks = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "uptime": self.get_uptime(),
            "memory": self.check_memory(),
            "cpu": self.check_cpu(),
            "disk": self.check_disk(),
            "cache": await self.check_cache(),
            "performance": performance_metrics.get_stats()
        }
        
        if db:
            checks["database"] = await self.check_database(db)
        
        all_healthy = all(
            v.get("status") in ["healthy", "unknown"]
            for k, v in checks.items()
            if isinstance(v, dict) and "status" in v
        )
        
        checks["status"] = "healthy" if all_healthy else "degraded"
        
        return checks
    
    async def quick_check(self) -> Dict[str, Any]:
        return {
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "uptime": self.get_uptime()
        }


health_checker = HealthChecker()


async def health_check_endpoint(request: Request):
    return await health_checker.quick_check()


async def health_check_full_endpoint(request: Request, db):
    return await health_checker.full_check(db)


async def readiness_check(db) -> Dict[str, Any]:
    db_check = await health_checker.check_database(db)
    cache_check = await health_checker.check_cache()
    
    is_ready = (
        db_check["status"] == "healthy" and
        cache_check["status"] == "healthy"
    )
    
    return {
        "ready": is_ready,
        "checks": {
            "database": db_check,
            "cache": cache_check
        },
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


async def liveness_check() -> Dict[str, Any]:
    return {
        "alive": True,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
