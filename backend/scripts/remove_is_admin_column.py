"""
删除 users 表中 is_admin 列的迁移脚本
运行方式: python scripts/remove_is_admin_column.py
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from app.core.config import settings

def remove_is_admin_column():
    engine = create_engine(settings.DATABASE_URL)
    
    with engine.connect() as conn:
        try:
            result = conn.execute(text("PRAGMA table_info(users)"))
            columns = [row[1] for row in result.fetchall()]
            
            if 'is_admin' not in columns:
                print("is_admin 列不存在，无需删除")
                return
            
            print("开始迁移：移除 is_admin 列...")
            
            conn.execute(text("BEGIN TRANSACTION"))
            
            columns_without_is_admin = [col for col in columns if col != 'is_admin']
            columns_str = ', '.join(columns_without_is_admin)
            
            conn.execute(text(f"""
                CREATE TABLE users_new AS SELECT {columns_str} FROM users
            """))
            
            conn.execute(text("DROP TABLE users"))
            
            conn.execute(text("ALTER TABLE users_new RENAME TO users"))
            
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_users_username ON users(username)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_users_email ON users(email)"))
            
            conn.execute(text("COMMIT"))
            
            print("成功删除 is_admin 列")
            
        except Exception as e:
            conn.execute(text("ROLLBACK"))
            print(f"删除失败: {e}")
            raise

if __name__ == "__main__":
    remove_is_admin_column()
