"""
Migration script to add missing columns to article_files table.
Run this script once to update the database schema.
"""
import asyncio
from sqlalchemy import text
from app.core.database import engine, SessionLocal
import logging

logger = logging.getLogger(__name__)

def migrate():
    """Add missing columns to article_files table."""
    db = SessionLocal()
    try:
        # Check if columns exist
        result = db.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'article_files'
        """))
        existing_columns = [row[0] for row in result.fetchall()]
        
        logger.info(f"Existing columns: {existing_columns}")
        
        # Add view_count column if missing
        if 'view_count' not in existing_columns:
            logger.info("Adding view_count column...")
            db.execute(text("""
                ALTER TABLE article_files 
                ADD COLUMN view_count INTEGER DEFAULT 0
            """))
            logger.info("view_count column added successfully")
        
        # Add order column if missing
        if 'order' not in existing_columns:
            logger.info("Adding order column...")
            db.execute(text("""
                ALTER TABLE article_files 
                ADD COLUMN "order" INTEGER DEFAULT 0
            """))
            logger.info("order column added successfully")
        
        # Create indexes if they don't exist
        try:
            db.execute(text("""
                CREATE INDEX IF NOT EXISTS ix_article_files_article_order 
                ON article_files (article_id, "order")
            """))
            db.execute(text("""
                CREATE INDEX IF NOT EXISTS ix_article_files_created 
                ON article_files (created_at)
            """))
            logger.info("Indexes created successfully")
        except Exception as e:
            logger.warning(f"Index creation warning: {e}")
        
        db.commit()
        logger.info("Migration completed successfully!")
        
    except Exception as e:
        db.rollback()
        logger.error(f"Migration failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    migrate()
