"""
配置管理器模块
基于 QSettings 封装应用配置
v1.1.2: 新增 JSON 配置文件支持（默认时间 + 文件自定义时间）
"""
import json
import os
from PySide6.QtCore import QSettings, QObject, Signal
from typing import Optional, Dict, Any, List


class ConfigManager(QObject):
    """
    应用配置管理器
    使用 QSettings 持久化存储用户设置
    """
    
    config_changed = Signal(str)  # 配置项名称
    
    # 默认值
    DEFAULT_SUFFIX = "_1"
    DEFAULT_CONFLICT_STRATEGY = "ask"  # ask / rename / skip
    DEFAULT_PRECISION_MODE = False
    
    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        self._settings = QSettings("VideoCutter", "VideoCutter")
    
    # ==================== ffmpeg 路径 ====================
    
    @property
    def ffmpeg_path(self) -> str:
        """获取 ffmpeg 可执行文件路径（支持自动检测）"""
        path = self._settings.value("ffmpeg/path", "", str)
        if not path:
            path = self._auto_detect_ffmpeg("ffmpeg")
            if path:
                self._settings.setValue("ffmpeg/path", path)
        return path or "ffmpeg"
    
    @ffmpeg_path.setter
    def ffmpeg_path(self, value: str):
        """设置 ffmpeg 可执行文件路径"""
        self._settings.setValue("ffmpeg/path", value)
        self.config_changed.emit("ffmpeg_path")
    
    @property
    def ffprobe_path(self) -> str:
        """获取 ffprobe 可执行文件路径（支持自动检测）"""
        path = self._settings.value("ffmpeg/ffprobe_path", "", str)
        if not path:
            path = self._auto_detect_ffmpeg("ffprobe")
            if path:
                self._settings.setValue("ffmpeg/ffprobe_path", path)
        return path or "ffprobe"
    
    @ffprobe_path.setter
    def ffprobe_path(self, value: str):
        """设置 ffprobe 可执行文件路径"""
        self._settings.setValue("ffmpeg/ffprobe_path", value)
        self.config_changed.emit("ffprobe_path")
    
    # ==================== 输出设置 ====================
    
    @property
    def suffix(self) -> str:
        """获取输出文件后缀"""
        return self._settings.value("output/suffix", self.DEFAULT_SUFFIX, str)
    
    @suffix.setter
    def suffix(self, value: str):
        """设置输出文件后缀"""
        self._settings.setValue("output/suffix", value)
        self.config_changed.emit("suffix")
    
    @property
    def conflict_strategy(self) -> str:
        """
        获取文件冲突策略
        返回值: "ask" / "rename" / "skip"
        """
        return self._settings.value("output/conflict_strategy", 
                                     self.DEFAULT_CONFLICT_STRATEGY, str)
    
    @conflict_strategy.setter
    def conflict_strategy(self, value: str):
        """设置文件冲突策略"""
        if value in ("ask", "rename", "skip"):
            self._settings.setValue("output/conflict_strategy", value)
            self.config_changed.emit("conflict_strategy")
    
    # ==================== 精确模式 ====================
    
    @property
    def precision_mode(self) -> bool:
        """获取是否启用精确模式"""
        return self._settings.value("cut/precision_mode", 
                                     self.DEFAULT_PRECISION_MODE, bool)
    
    @precision_mode.setter
    def precision_mode(self, value: bool):
        """设置是否启用精确模式"""
        self._settings.setValue("cut/precision_mode", value)
        self.config_changed.emit("precision_mode")
    
    @property
    def movflags_faststart(self) -> bool:
        """获取是否启用 movflags +faststart"""
        return self._settings.value("cut/movflags_faststart", True, bool)
    
    @movflags_faststart.setter
    def movflags_faststart(self, value: bool):
        """设置是否启用 movflags +faststart"""
        self._settings.setValue("cut/movflags_faststart", value)
        self.config_changed.emit("movflags_faststart")
    
    # ==================== 窗口状态 ====================
    
    @property
    def window_geometry(self) -> bytes:
        """获取窗口位置和大小"""
        return self._settings.value("window/geometry", b"", bytes)
    
    @window_geometry.setter
    def window_geometry(self, value: bytes):
        """保存窗口位置和大小"""
        self._settings.setValue("window/geometry", value)
    
    @property
    def window_state(self) -> bytes:
        """获取窗口状态"""
        return self._settings.value("window/state", b"", bytes)
    
    @window_state.setter
    def window_state(self, value: bytes):
        """保存窗口状态"""
        self._settings.setValue("window/state", value)
    
    # ==================== 预设路径 ====================
    
    @property
    def presets_path(self) -> str:
        """获取预设文件存储路径"""
        import os as _os
        settings_file = self._settings.fileName()
        # 跨平台：替换任意扩展名（.ini/.plist/.conf）为 _presets.json
        base, _ = _os.path.splitext(settings_file)
        default_path = base + "_presets.json"
        return self._settings.value("presets/path", default_path, str)
    
    @presets_path.setter
    def presets_path(self, value: str):
        """设置预设文件存储路径"""
        self._settings.setValue("presets/path", value)
        self.config_changed.emit("presets_path")
    
    # ==================== 默认预设 ====================
    
    @property
    def default_preset_name(self) -> str:
        """获取默认预设名称"""
        return self._settings.value("presets/default", "", str)
    
    @default_preset_name.setter
    def default_preset_name(self, value: str):
        """设置默认预设名称"""
        self._settings.setValue("presets/default", value)
        self.config_changed.emit("default_preset")
    
    # ==================== 历史记录 ====================
    
    @property
    def history_count(self) -> int:
        """获取历史记录保留数量"""
        return self._settings.value("history/count", 10, int)
    
    @history_count.setter
    def history_count(self, value: int):
        """设置历史记录保留数量"""
        self._settings.setValue("history/count", max(1, value))
    
    # ==================== 通用方法 ====================
    
    def sync(self):
        """立即同步配置到磁盘"""
        self._settings.sync()
    
    def clear_all(self):
        """清除所有配置"""
        self._settings.clear()
    
    # ==================== ffmpeg 自动检测 ====================
    
    @staticmethod
    def _auto_detect_ffmpeg(name: str = "ffmpeg") -> str:
        """
        自动检测 ffmpeg/ffprobe 路径
        检测顺序：打包内嵌 → PATH → 常见安装路径
        """
        import shutil
        import sys as _sys
        
        # 0. 检查打包后内嵌的 ffmpeg（打包时可将 ffmpeg 放入包内）
        if getattr(_sys, 'frozen', False):
            base_dir = _sys._MEIPASS if hasattr(_sys, '_MEIPASS') else os.path.dirname(_sys.executable)
            bundled_candidates = []
            
            # PyInstaller --onefile: _MEIPASS 目录
            bundled_candidates.append(os.path.join(base_dir, name))
            bundled_candidates.append(os.path.join(base_dir, "bin", name))
            
            # macOS .app 包: Contents/MacOS/
            if hasattr(_sys, 'frozen') and os.path.isdir(os.path.join(os.path.dirname(_sys.executable), "..")):
                macos_dir = os.path.dirname(_sys.executable)
                bundled_candidates.append(os.path.join(macos_dir, name))
            
            # Windows: 与 exe 同目录
            import platform as _platform
            if _platform.system() == "Windows":
                bundled_candidates.append(os.path.join(base_dir, f"{name}.exe"))
                bundled_candidates.append(os.path.join(base_dir, "bin", f"{name}.exe"))
            
            for path in bundled_candidates:
                if os.path.isfile(path) and os.access(path, os.X_OK):
                    return path
        
        # 1. PATH 中查找
        found = shutil.which(name)
        if found:
            return found
        
        # 2. 检查常见安装路径
        import platform
        candidates = []
        system = platform.system()
        
        if system == "Darwin":  # macOS
            candidates = [
                f"/opt/homebrew/bin/{name}",       # Apple Silicon Homebrew
                f"/usr/local/bin/{name}",           # Intel Homebrew
                f"/opt/local/bin/{name}",           # MacPorts
                f"/usr/bin/{name}",
            ]
        elif system == "Windows":
            home = os.path.expanduser("~")
            candidates = [
                f"C:\\ffmpeg\\bin\\{name}.exe",
                f"C:\\Program Files\\ffmpeg\\bin\\{name}.exe",
                f"C:\\Program Files (x86)\\ffmpeg\\bin\\{name}.exe",
                f"C:\\tools\\ffmpeg\\bin\\{name}.exe",
                os.path.join(home, "scoop", "shims", f"{name}.exe"),
                os.path.join(home, "ffmpeg", "bin", f"{name}.exe"),
            ]
        else:  # Linux
            candidates = [
                f"/usr/bin/{name}",
                f"/usr/local/bin/{name}",
                f"/snap/bin/{name}",
            ]
        
        for path in candidates:
            if os.path.isfile(path) and os.access(path, os.X_OK):
                return path
        
        return ""
    
    # ==================== v1.1.2 JSON 配置文件 ====================
    
    @property
    def json_config_path(self) -> str:
        """v1.1.2: JSON 配置文件路径"""
        base, _ = os.path.splitext(self._settings.fileName())
        default = base + "_config.json"
        return self._settings.value("config/json_path", default, str)
    
    def save_project_config(self, default_time: Dict[str, Any], 
                            file_custom_times: Dict[str, Dict[str, Any]]):
        """
        v1.1.2: 保存项目配置到 JSON 文件
        
        Args:
            default_time: 默认时间配置 {"mode": str, "A": float|None, "B": float|None}
            file_custom_times: 文件自定义时间 {path: {"mode": str, "A": float, "B": float}}
        """
        config = {
            "version": "1.1.2",
            "default_time": default_time,
            "file_custom_times": file_custom_times
        }
        try:
            dir_path = os.path.dirname(self.json_config_path)
            if dir_path and not os.path.exists(dir_path):
                os.makedirs(dir_path, exist_ok=True)
            with open(self.json_config_path, "w", encoding="utf-8") as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except IOError:
            pass
    
    def load_project_config(self) -> Optional[Dict[str, Any]]:
        """
        v1.1.2: 从 JSON 文件加载项目配置
        
        Returns:
            配置字典，不存在或失败返回 None
        """
        if not os.path.exists(self.json_config_path):
            return None
        try:
            with open(self.json_config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError, UnicodeDecodeError, ValueError):
            return None
