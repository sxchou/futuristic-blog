"""
头像持久化存储测试脚本
用于验证 Railway Volume 配置是否正确
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.avatar_service import AvatarFileService


def test_avatar_storage():
    """测试头像存储配置"""
    print("=" * 60)
    print("头像持久化存储测试")
    print("=" * 60)
    
    avatar_path = AvatarFileService.get_avatar_base_path()
    print(f"\n头像存储路径: {avatar_path}")
    print(f"路径是否存在: {avatar_path.exists()}")
    
    env_path = os.getenv("AVATAR_STORAGE_PATH")
    print(f"\n环境变量 AVATAR_STORAGE_PATH: {env_path or '未设置'}")
    
    if env_path:
        print("✓ 使用自定义存储路径（持久化 Volume）")
    else:
        print("⚠ 使用默认路径（部署时会丢失）")
    
    AvatarFileService.ensure_avatar_directory()
    print(f"\n头像目录已创建: {avatar_path}")
    
    stats = AvatarFileService.get_storage_stats()
    print(f"\n存储统计:")
    print(f"  - 文件数量: {stats['total_files']}")
    print(f"  - 总大小: {stats['total_size_bytes']} bytes ({stats['total_size_mb']} MB)")
    
    test_file = avatar_path / "test_persistence.txt"
    try:
        with open(test_file, "w") as f:
            f.write("This is a test file to verify persistence.\n")
        print(f"\n✓ 测试文件创建成功: {test_file}")
        print("  请重新部署后检查此文件是否仍然存在")
    except Exception as e:
        print(f"\n✗ 测试文件创建失败: {e}")
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)
    
    if not env_path:
        print("\n⚠️  警告: 未配置 AVATAR_STORAGE_PATH 环境变量")
        print("   请在 Railway 中配置 Volume 并设置环境变量")
        print("   详见 DEPLOYMENT.md 文档")
    else:
        print("\n✓ 配置正确，头像文件将被持久化保存")


if __name__ == "__main__":
    test_avatar_storage()
