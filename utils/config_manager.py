"""
配置管理器模块
基于 QSettings 封装应用配置
"""
from PySide6.QtCore import QSettings, QObject, Signal
from typing import Optional


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
        """获取 ffmpeg 可执行文件路径"""
        return self._settings.value("ffmpeg/path", "ffmpeg", str)
    
    @ffmpeg_path.setter
    def ffmpeg_path(self, value: str):
        """设置 ffmpeg 可执行文件路径"""
        self._settings.setValue("ffmpeg/path", value)
        self.config_changed.emit("ffmpeg_path")
    
    @property
    def ffprobe_path(self) -> str:
        """获取 ffprobe 可执行文件路径"""
        return self._settings.value("ffmpeg/ffprobe_path", "ffprobe", str)
    
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
        default_path = self._settings.value(
            "presets/path", 
            self._settings.fileName().replace(".ini", "_presets.json"),
            str
        )
        return default_path
    
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
