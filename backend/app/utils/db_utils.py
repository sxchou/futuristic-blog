from contextlib import contextmanager
from typing import Optional, Generator, Any
from sqlalchemy.orm import Session, Query
from sqlalchemy import text
import time
import logging
from app.utils.logger import logger


class QueryOptimizer:
    @staticmethod
    def paginate(query: Query, page: int, page_size: int) -> tuple:
        total = query.count()
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0
        
        page = max(1, min(page, total_pages if total_pages > 0 else 1))
        
        offset = (page - 1) * page_size
        items = query.offset(offset).limit(page_size).all()
        
        return items, total, total_pages
    
    @staticmethod
    def optimize_in_query(query: Query, field: Any, values: list, batch_size: int = 100) -> Query:
        if not values:
            return query.filter(False)
        
        if len(values) <= batch_size:
            return query.filter(field.in_(values))
        
        from sqlalchemy import or_
        conditions = []
        for i in range(0, len(values), batch_size):
            batch = values[i:i + batch_size]
            conditions.append(field.in_(batch))
        
        return query.filter(or_(*conditions))
    
    @staticmethod
    def get_or_create(db: Session, model: Any, defaults: Optional[dict] = None, **kwargs) -> tuple:
        instance = db.query(model).filter_by(**kwargs).first()
        if instance:
            return instance, False
        
        if defaults:
            kwargs.update(defaults)
        
        instance = model(**kwargs)
        db.add(instance)
        db.commit()
        db.refresh(instance)
        return instance, True


class DatabaseUtils:
    @staticmethod
    def execute_safe_sql(db: Session, sql: str, params: Optional[dict] = None) -> Any:
        start_time = time.time()
        try:
            result = db.execute(text(sql), params or {})
            db.commit()
            
            execution_time = (time.time() - start_time) * 1000
            logger.db_query(sql, params, execution_time)
            
            return result
        except Exception as e:
            db.rollback()
            logger.error(f"SQL execution error: {str(e)}")
            raise
    
    @staticmethod
    def set_sequence_safe(db: Session, sequence_name: str, next_value: int) -> bool:
        if not isinstance(next_value, int) or next_value < 0:
            raise ValueError("next_value must be a non-negative integer")
        
        safe_sequence_name = sequence_name.replace("'", "''")
        if not all(c.isalnum() or c == '_' for c in safe_sequence_name):
            raise ValueError("Invalid sequence name")
        
        sql = text("SELECT setval(:seq_name, :next_val)")
        params = {"seq_name": safe_sequence_name, "next_val": next_value}
        
        try:
            db.execute(sql, params)
            db.commit()
            logger.info(f"Sequence {safe_sequence_name} set to {next_value}")
            return True
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to set sequence: {str(e)}")
            raise
    
    @staticmethod
    def bulk_insert(db: Session, model: Any, items: list, batch_size: int = 100) -> int:
        inserted = 0
        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            for item in batch:
                instance = model(**item)
                db.add(instance)
            db.commit()
            inserted += len(batch)
        
        return inserted
    
    @staticmethod
    def bulk_update(db: Session, model: Any, updates: list, id_field: str = "id") -> int:
        updated = 0
        for update in updates:
            if id_field in update:
                db.query(model).filter(
                    getattr(model, id_field) == update[id_field]
                ).update(update)
                updated += 1
        db.commit()
        return updated


@contextmanager
def query_timer(query_name: str) -> Generator[None, None, None]:
    start_time = time.time()
    try:
        yield
    finally:
        execution_time = (time.time() - start_time) * 1000
        if execution_time > 500:
            logger.warning(f"Slow query '{query_name}': {execution_time:.2f}ms")
        else:
            logger.debug(f"Query '{query_name}': {execution_time:.2f}ms")


class QueryBuilder:
    def __init__(self, db: Session, model: Any):
        self.db = db
        self.model = model
        self._query = db.query(model)
        self._filters = []
        self._joins = []
        self._options = []
        self._order_by = None
        self._limit = None
        self._offset = None
    
    def filter(self, *args, **kwargs) -> "QueryBuilder":
        if args:
            self._filters.extend(args)
        if kwargs:
            from sqlalchemy import and_
            conditions = [getattr(self.model, k) == v for k, v in kwargs.items()]
            self._filters.extend(conditions)
        return self
    
    def join(self, target: Any, onclause: Any = None) -> "QueryBuilder":
        self._joins.append((target, onclause))
        return self
    
    def options(self, *args) -> "QueryBuilder":
        self._options.extend(args)
        return self
    
    def order_by(self, *args) -> "QueryBuilder":
        self._order_by = args
        return self
    
    def limit(self, limit: int) -> "QueryBuilder":
        self._limit = limit
        return self
    
    def offset(self, offset: int) -> "QueryBuilder":
        self._offset = offset
        return self
    
    def build(self) -> Query:
        query = self._query
        
        for join_target, onclause in self._joins:
            if onclause:
                query = query.join(join_target, onclause)
            else:
                query = query.join(join_target)
        
        if self._filters:
            from sqlalchemy import and_
            query = query.filter(and_(*self._filters))
        
        if self._options:
            query = query.options(*self._options)
        
        if self._order_by:
            query = query.order_by(*self._order_by)
        
        if self._limit:
            query = query.limit(self._limit)
        
        if self._offset:
            query = query.offset(self._offset)
        
        return query
    
    def all(self) -> list:
        return self.build().all()
    
    def first(self) -> Any:
        return self.build().first()
    
    def count(self) -> int:
        return self.build().count()
    
    def paginate(self, page: int, page_size: int) -> tuple:
        return QueryOptimizer.paginate(self.build(), page, page_size)


query_optimizer = QueryOptimizer()
db_utils = DatabaseUtils()
