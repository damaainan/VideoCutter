"""
视频极简裁剪工具 - 配置文件入口
此模块为 ConfigManager 的便捷别名
"""
from utils.config_manager import ConfigManager

# 全局配置实例
_config_instance = None


def get_config() -> ConfigManager:
    """获取全局配置实例（单例）"""
    global _config_instance
    if _config_instance is None:
        _config_instance = ConfigManager()
    return _config_instance
