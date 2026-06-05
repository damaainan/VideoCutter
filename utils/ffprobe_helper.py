"""
FFprobe 辅助模块
获取视频元数据信息
"""
from PySide6.QtCore import QObject, QProcess, Signal, Slot, QThreadPool, QRunnable
from typing import Optional, List, Dict
import os


class FFprobeHelper(QObject):
    """
    FFprobe 辅助类
    用于获取视频时长等元数据
    """
    
    # 信号定义
    duration_received = Signal(str, float)  # (文件路径, 时长秒数)
    duration_failed = Signal(str, str)  # (文件路径, 错误信息)
    batch_finished = Signal()  # 批量查询完成
    
    def __init__(self, ffprobe_path: str = "ffprobe", parent: Optional[QObject] = None):
        super().__init__(parent)
        self._ffprobe_path = ffprobe_path
        self._thread_pool = QThreadPool()
        self._thread_pool.setMaxThreadCount(4)
        self._pending_count = 0
    
    def get_duration(self, file_path: str) -> Optional[float]:
        """
        同步获取视频时长
        
        Args:
            file_path: 视频文件路径
            
        Returns:
            时长（秒），失败返回 None
        """
        process = QProcess()
        args = [
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            file_path
        ]
        
        process.start(self._ffprobe_path, args)
        
        if not process.waitForFinished(10000):
            process.kill()
            return None
        
        if process.exitCode() != 0:
            return None
        
        output = process.readAllStandardOutput().data().decode("utf-8", errors="replace").strip()
        
        try:
            duration = float(output)
            return duration if duration >= 0 else None
        except (ValueError, TypeError):
            return None
    
    def get_duration_async(self, file_path: str):
        """
        异步获取视频时长
        结果通过信号 duration_received 或 duration_failed 返回
        
        Args:
            file_path: 视频文件路径
        """
        runnable = _FFprobeRunnable(self._ffprobe_path, file_path)
        runnable.signals.duration_received.connect(self._on_duration_received)
        runnable.signals.duration_failed.connect(self._on_duration_failed)
        
        self._pending_count += 1
        self._thread_pool.start(runnable)
    
    def get_durations_batch(self, file_paths: List[str]):
        """
        批量异步获取视频时长
        
        Args:
            file_paths: 视频文件路径列表
        """
        self._pending_count = len(file_paths)
        
        for file_path in file_paths:
            self.get_duration_async(file_path)
    
    @Slot(str, float)
    def _on_duration_received(self, file_path: str, duration: float):
        """时长获取成功回调"""
        self.duration_received.emit(file_path, duration)
        self._check_batch_finished()
    
    @Slot(str, str)
    def _on_duration_failed(self, file_path: str, error: str):
        """时长获取失败回调"""
        self.duration_failed.emit(file_path, error)
        self._check_batch_finished()
    
    def _check_batch_finished(self):
        """检查批量查询是否完成"""
        self._pending_count -= 1
        if self._pending_count <= 0:
            self._pending_count = 0
            self.batch_finished.emit()
    
    @staticmethod
    def check_ffprobe(ffprobe_path: str = "ffprobe") -> bool:
        """
        检查 ffprobe 是否可用
        
        Args:
            ffprobe_path: ffprobe 可执行文件路径
            
        Returns:
            是否可用
        """
        process = QProcess()
        process.start(ffprobe_path, ["-version"])
        
        if not process.waitForFinished(3000):
            process.kill()
            return False
        
        return process.exitCode() == 0


class _FFprobeRunnableSignals(QObject):
    """FFprobe Runnable 信号"""
    duration_received = Signal(str, float)
    duration_failed = Signal(str, str)


class _FFprobeRunnable(QRunnable):
    """FFprobe 可运行任务"""
    
    def __init__(self, ffprobe_path: str, file_path: str):
        super().__init__()
        self._ffprobe_path = ffprobe_path
        self._file_path = file_path
        self.signals = _FFprobeRunnableSignals()
    
    def run(self):
        """执行 ffprobe 获取时长"""
        if not os.path.exists(self._file_path):
            self.signals.duration_failed.emit(self._file_path, "文件不存在")
            return
        
        process = QProcess()
        args = [
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            self._file_path
        ]
        
        process.start(self._ffprobe_path, args)
        
        if not process.waitForFinished(10000):
            process.kill()
            self.signals.duration_failed.emit(self._file_path, "获取超时")
            return
        
        if process.exitCode() != 0:
            error = process.readAllStandardError().data().decode("utf-8", errors="replace")
            self.signals.duration_failed.emit(self._file_path, error or "获取失败")
            return
        
        output = process.readAllStandardOutput().data().decode("utf-8", errors="replace").strip()
        
        try:
            duration = float(output)
            if duration >= 0:
                self.signals.duration_received.emit(self._file_path, duration)
            else:
                self.signals.duration_failed.emit(self._file_path, "无效的时长值")
        except (ValueError, TypeError):
            self.signals.duration_failed.emit(self._file_path, "无法解析时长")
