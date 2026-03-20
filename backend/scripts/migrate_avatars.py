"""
头像文件迁移脚本
用于将现有头像文件迁移到持久化存储中
"""
import os
import shutil
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


def migrate_avatar_files():
    """
    迁移头像文件到持久化存储目录
    在 Railway 部署时自动执行
    """
    backend_dir = Path(__file__).parent.parent.parent
    source_dir = backend_dir / "uploads" / "avatars"
    
    target_path = os.getenv("AVATAR_STORAGE_PATH")
    if not target_path:
        logger.info("No AVATAR_STORAGE_PATH set, skipping migration")
        return
    
    target_dir = Path(target_path) / "avatars"
    
    if not source_dir.exists():
        logger.info(f"Source directory {source_dir} does not exist, skipping migration")
        return
    
    target_dir.mkdir(parents=True, exist_ok=True)
    
    migrated_count = 0
    for file_path in source_dir.iterdir():
        if file_path.is_file() and file_path.name != ".gitkeep":
            target_file = target_dir / file_path.name
            if not target_file.exists():
                shutil.copy2(file_path, target_file)
                migrated_count += 1
                logger.info(f"Migrated avatar file: {file_path.name}")
    
    logger.info(f"Migration completed. Total files migrated: {migrated_count}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    migrate_avatar_files()
