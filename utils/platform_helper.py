"""
跨平台工具模块
统一处理平台检测、字体、图标、路径等跨平台兼容性问题

支持平台：
- Windows (x64)
- macOS arm64 (Apple Silicon)
- macOS x86_64 (Intel)
- Linux
"""
import os
import sys
import platform
from typing import Optional


# ==================== 平台检测 ====================

def get_platform() -> str:
    """
    获取当前平台标识
    
    Returns:
        'windows' | 'macos-arm64' | 'macos-intel' | 'linux'
    """
    system = platform.system()
    if system == "Windows":
        return "windows"
    elif system == "Darwin":
        machine = platform.machine()
        if machine == "arm64":
            return "macos-arm64"
        else:
            return "macos-intel"
    else:
        return "linux"


def is_frozen() -> bool:
    """是否以打包后的可执行文件运行"""
    return getattr(sys, 'frozen', False)


def get_app_dir() -> str:
    """
    获取应用资源目录
    - 开发环境：项目根目录
    - PyInstaller 打包后：_MEIPASS 或可执行文件目录
    """
    if is_frozen():
        # PyInstaller 打包
        if hasattr(sys, '_MEIPASS'):
            return sys._MEIPASS
        return os.path.dirname(sys.executable)
    else:
        # 开发环境：返回项目根目录（main.py 所在目录）
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# ==================== 图标 ====================

def get_icon_path() -> Optional[str]:
    """
    获取应用图标路径
    根据平台返回对应格式的图标文件：
    - Windows: .ico
    - macOS: .icns
    - 开发环境: .ico 或 .png
    
    Returns:
        图标文件绝对路径，不存在返回 None
    """
    app_dir = get_app_dir()
    resources_dir = os.path.join(app_dir, "resources")
    
    system = platform.system()
    
    # 按优先级尝试的图标文件名
    if system == "Darwin":
        candidates = ["icon.icns", "icon.png", "icon.ico"]
    elif system == "Windows":
        candidates = ["icon.ico", "icon.png"]
    else:
        candidates = ["icon.png", "icon.ico"]
    
    for name in candidates:
        path = os.path.join(resources_dir, name)
        if os.path.isfile(path):
            return path
    
    return None


# ==================== 字体 ====================

def get_monospace_font() -> str:
    """
    获取当前平台最佳等宽字体名称
    
    Returns:
        CSS font-family 字符串（不含引号，逗号分隔）
    """
    plat = get_platform()
    
    font_map = {
        "windows": "'Consolas', 'Courier New', monospace",
        "macos-arm64": "'Menlo', 'Courier New', monospace",
        "macos-intel": "'Menlo', 'Courier New', monospace",
        "linux": "'Ubuntu Mono', 'DejaVu Sans Mono', 'Courier New', monospace",
    }
    
    return font_map.get(plat, "'Courier New', monospace")


def get_log_font_style() -> str:
    """获取日志区域 QTextEdit 的完整字体样式"""
    font = get_monospace_font()
    return f"font-family: {font}; font-size: 12px;"


# ==================== 路径分隔 ====================

def normalize_path(path: str) -> str:
    """统一路径分隔符为当前平台格式"""
    return os.path.normpath(path)


def get_ffmpeg_executable_name(name: str = "ffmpeg") -> str:
    """
    获取 ffmpeg 可执行文件名（含平台扩展名）
    
    Args:
        name: 'ffmpeg' 或 'ffprobe'
    
    Returns:
        'ffmpeg' | 'ffmpeg.exe' | 'ffprobe' | 'ffprobe.exe'
    """
    if platform.system() == "Windows":
        return f"{name}.exe"
    return name
