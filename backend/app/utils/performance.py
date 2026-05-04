import time
import logging
import threading
from typing import Dict, List, Optional, Any
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from functools import wraps
import json

logger = logging.getLogger(__name__)


class PerformanceMetrics:
    def __init__(self):
        self._lock = threading.RLock()
        self._request_times: Dict[str, List[float]] = defaultdict(list)
        self._request_counts: Dict[str, int] = defaultdict(int)
        self._error_counts: Dict[str, int] = defaultdict(int)
        self._slow_requests: List[Dict[str, Any]] = []
        self._max_slow_requests = 100
        self._start_time = time.time()
    
    def record_request(self, path: str, method: str, response_time: float, status_code: int):
        with self._lock:
            key = f"{method}:{path}"
            self._request_times[key].append(response_time)
            self._request_counts[key] += 1
            
            if len(self._request_times[key]) > 1000:
                self._request_times[key] = self._request_times[key][-500:]
            
            if status_code >= 400:
                self._error_counts[key] += 1
            
            if response_time > 1000:
                self._slow_requests.append({
                    'path': path,
                    'method': method,
                    'response_time': response_time,
                    'status_code': status_code,
                    'timestamp': datetime.now(timezone.utc).isoformat()
                })
                
                if len(self._slow_requests) > self._max_slow_requests:
                    self._slow_requests = self._slow_requests[-self._max_slow_requests:]
    
    def get_stats(self) -> Dict[str, Any]:
        with self._lock:
            total_requests = sum(self._request_counts.values())
            total_errors = sum(self._error_counts.values())
            
            all_times = []
            for times in self._request_times.values():
                all_times.extend(times)
            
            avg_response_time = sum(all_times) / len(all_times) if all_times else 0
            
            endpoint_stats = {}
            for key, times in self._request_times.items():
                if times:
                    endpoint_stats[key] = {
                        'count': self._request_counts[key],
                        'avg_time': round(sum(times) / len(times), 2),
                        'max_time': round(max(times), 2),
                        'min_time': round(min(times), 2),
                        'errors': self._error_counts.get(key, 0)
                    }
            
            uptime = time.time() - self._start_time
            requests_per_second = total_requests / uptime if uptime > 0 else 0
            
            return {
                'uptime_seconds': round(uptime, 2),
                'total_requests': total_requests,
                'total_errors': total_errors,
                'error_rate': round((total_errors / total_requests * 100) if total_requests > 0 else 0, 2),
                'avg_response_time_ms': round(avg_response_time, 2),
                'requests_per_second': round(requests_per_second, 4),
                'slow_requests_count': len(self._slow_requests),
                'endpoints': endpoint_stats
            }
    
    def get_slow_requests(self, limit: int = 20) -> List[Dict[str, Any]]:
        with self._lock:
            return sorted(self._slow_requests, key=lambda x: x['response_time'], reverse=True)[:limit]
    
    def get_top_endpoints(self, limit: int = 10, sort_by: str = 'count') -> List[Dict[str, Any]]:
        with self._lock:
            endpoint_list = []
            for key, stats in self.get_stats()['endpoints'].items():
                method, path = key.split(':', 1)
                endpoint_list.append({
                    'method': method,
                    'path': path,
                    **stats
                })
            
            reverse = True
            if sort_by == 'path':
                reverse = False
            
            return sorted(endpoint_list, key=lambda x: x.get(sort_by, 0), reverse=reverse)[:limit]
    
    def reset(self):
        with self._lock:
            self._request_times.clear()
            self._request_counts.clear()
            self._error_counts.clear()
            self._slow_requests.clear()
            self._start_time = time.time()


performance_metrics = PerformanceMetrics()


class QueryMetrics:
    def __init__(self):
        self._lock = threading.RLock()
        self._query_times: Dict[str, List[float]] = defaultdict(list)
        self._query_counts: Dict[str, int] = defaultdict(int)
        self._slow_queries: List[Dict[str, Any]] = []
        self._max_slow_queries = 50
    
    def record_query(self, query: str, execution_time: float, params: Optional[Dict] = None):
        with self._lock:
            query_key = query[:100] if len(query) > 100 else query
            self._query_times[query_key].append(execution_time)
            self._query_counts[query_key] += 1
            
            if len(self._query_times[query_key]) > 500:
                self._query_times[query_key] = self._query_times[query_key][-200:]
            
            if execution_time > 500:
                self._slow_queries.append({
                    'query': query,
                    'execution_time': execution_time,
                    'params': params,
                    'timestamp': datetime.now(timezone.utc).isoformat()
                })
                
                if len(self._slow_queries) > self._max_slow_queries:
                    self._slow_queries = self._slow_queries[-self._max_slow_queries:]
    
    def get_stats(self) -> Dict[str, Any]:
        with self._lock:
            total_queries = sum(self._query_counts.values())
            
            all_times = []
            for times in self._query_times.values():
                all_times.extend(times)
            
            avg_time = sum(all_times) / len(all_times) if all_times else 0
            
            return {
                'total_queries': total_queries,
                'unique_queries': len(self._query_counts),
                'avg_execution_time_ms': round(avg_time, 2),
                'slow_queries_count': len(self._slow_queries)
            }
    
    def get_slow_queries(self, limit: int = 10) -> List[Dict[str, Any]]:
        with self._lock:
            return sorted(self._slow_queries, key=lambda x: x['execution_time'], reverse=True)[:limit]


query_metrics = QueryMetrics()


def track_performance(func):
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            return result
        finally:
            execution_time = (time.time() - start_time) * 1000
            logger.debug(f"{func.__name__} executed in {execution_time:.2f}ms")
    
    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            execution_time = (time.time() - start_time) * 1000
            logger.debug(f"{func.__name__} executed in {execution_time:.2f}ms")
    
    import asyncio
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    return sync_wrapper


class PerformanceMonitor:
    @staticmethod
    def get_full_report() -> Dict[str, Any]:
        return {
            'performance': performance_metrics.get_stats(),
            'queries': query_metrics.get_stats(),
            'slow_requests': performance_metrics.get_slow_requests(),
            'slow_queries': query_metrics.get_slow_queries(),
            'top_endpoints': performance_metrics.get_top_endpoints()
        }
    
    @staticmethod
    def log_report():
        stats = performance_metrics.get_stats()
        query_stats = query_metrics.get_stats()
        
        logger.info("=== Performance Report ===")
        logger.info(f"Uptime: {stats['uptime_seconds']}s")
        logger.info(f"Total Requests: {stats['total_requests']}")
        logger.info(f"Error Rate: {stats['error_rate']}%")
        logger.info(f"Avg Response Time: {stats['avg_response_time_ms']}ms")
        logger.info(f"Requests/sec: {stats['requests_per_second']}")
        logger.info(f"Total Queries: {query_stats['total_queries']}")
        logger.info(f"Avg Query Time: {query_stats['avg_execution_time_ms']}ms")
        logger.info("=========================")


performance_monitor = PerformanceMonitor()
