"""
删除 mobile_article_layout 配置项的迁移脚本
运行方式: python scripts/remove_mobile_article_layout.py
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from app.core.config import settings
from app.core.database import SessionLocal
from app.models.models import SiteConfig

def remove_mobile_article_layout():
    db = SessionLocal()
    try:
        result = db.query(SiteConfig).filter(SiteConfig.key == "mobile_article_layout").first()
        if result:
            db.delete(result)
            db.commit()
            print("成功删除 mobile_article_layout 配置项")
        else:
            print("mobile_article_layout 配置项不存在，无需删除")
    except Exception as e:
        db.rollback()
        print(f"删除失败: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    remove_mobile_article_layout()
