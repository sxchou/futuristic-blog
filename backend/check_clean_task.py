from app.core.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()

result = db.execute(text("""
    SELECT id, task_name, status, error_message, output_data
    FROM task_logs
    WHERE task_name = 'clean_old_logs'
    ORDER BY id DESC
    LIMIT 3
"""))

print("clean_old_logs 任务日志:")
for row in result:
    print(f"\nID: {row[0]}")
    print(f"  状态: {row[2]}")
    print(f"  错误: {row[3]}")
    print(f"  输出: {row[4]}")

db.close()
