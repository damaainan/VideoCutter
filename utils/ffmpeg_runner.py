"""
FFmpeg 运行器模块
封装 QProcess 执行 ffmpeg 命令
"""
from PySide6.QtCore import QObject, QProcess, Signal, Slot
from typing import Optional, List


class FFmpegRunner(QObject):
    """
    FFmpeg 命令执行器
    使用 QProcess 异步运行 ffmpeg 命令，支持取消操作
    """
    
    # 信号定义
    started = Signal()  # 任务开始
    finished = Signal(int, str)  # (返回码, 错误输出)
    output_received = Signal(str)  # 标准输出
    error_received = Signal(str)  # 标准错误
    
    def __init__(self, ffmpeg_path: str = "ffmpeg", parent: Optional[QObject] = None):
        super().__init__(parent)
        self._ffmpeg_path = ffmpeg_path
        self._process: Optional[QProcess] = None
        self._error_output = ""
        self._is_running = False
    
    @property
    def is_running(self) -> bool:
        """是否正在运行"""
        return self._is_running
    
    def start(self, args: List[str]) -> bool:
        """
        启动 ffmpeg 进程
        
        Args:
            args: ffmpeg 参数列表（不包含 ffmpeg 本身）
            
        Returns:
            是否成功启动
        """
        if self._is_running:
            return False
        
        self._process = QProcess(self)
        self._process.setProcessChannelMode(QProcess.ProcessChannelMode.SeparateChannels)
        
        # 连接信号
        self._process.readyReadStandardOutput.connect(self._on_stdout)
        self._process.readyReadStandardError.connect(self._on_stderr)
        self._process.finished.connect(self._on_finished)
        self._process.errorOccurred.connect(self._on_error)
        
        self._error_output = ""
        self._is_running = True
        
        self._process.start(self._ffmpeg_path, args)
        
        if not self._process.waitForStarted(3000):
            self._is_running = False
            self.finished.emit(-1, "无法启动 ffmpeg 进程")
            return False
        
        self.started.emit()
        return True
    
    def cancel(self):
        """取消当前进程"""
        if self._process and self._is_running:
            self._process.terminate()
            if not self._process.waitForFinished(3000):
                self._process.kill()
    
    def wait(self, msecs: int = -1) -> bool:
        """
        等待进程完成
        
        Args:
            msecs: 等待毫秒数，-1 表示无限等待
            
        Returns:
            进程是否正常结束
        """
        if self._process:
            return self._process.waitForFinished(msecs)
        return True
    
    @Slot()
    def _on_stdout(self):
        """处理标准输出"""
        if self._process:
            data = self._process.readAllStandardOutput().data().decode("utf-8", errors="replace")
            self.output_received.emit(data)
    
    @Slot()
    def _on_stderr(self):
        """处理标准错误"""
        if self._process:
            data = self._process.readAllStandardError().data().decode("utf-8", errors="replace")
            self._error_output += data
            self.error_received.emit(data)
    
    @Slot(int, QProcess.ExitStatus)
    def _on_finished(self, exit_code: int, exit_status: QProcess.ExitStatus):
        """进程完成回调"""
        self._is_running = False
        self.finished.emit(exit_code, self._error_output)
    
    @Slot(QProcess.ProcessError)
    def _on_error(self, error: QProcess.ProcessError):
        """进程错误回调"""
        if error == QProcess.ProcessError.FailedToStart:
            self._is_running = False
            self.finished.emit(-1, f"无法启动 ffmpeg: 请检查路径是否正确 ({self._ffmpeg_path})")
        elif error == QProcess.ProcessError.Crashed:
            # 进程崩溃，但 finished 信号仍会被触发
            pass


class FFmpegWorker(QObject):
    """
    FFmpeg 工作线程对象
    用于在 QThread 中执行 ffmpeg 命令
    """
    
    started = Signal()
    finished = Signal(int, str, str)  # (返回码, 输出路径, 错误信息)
    progress = Signal(str)  # 进度信息
    
    def __init__(self, ffmpeg_path: str, args: List[str], output_path: str, 
                 parent: Optional[QObject] = None):
        super().__init__(parent)
        self._ffmpeg_path = ffmpeg_path
        self._args = args
        self._output_path = output_path
        self._cancelled = False
    
    @Slot()
    def run(self):
        """执行 ffmpeg 命令"""
        self._exit_code = -1
        self._error_text = ""
        self.started.emit()
        
        process = QProcess()
        process.setProcessChannelMode(QProcess.ProcessChannelMode.SeparateChannels)
        
        process.start(self._ffmpeg_path, self._args)
        
        if not process.waitForStarted(3000):
            self._exit_code = -1
            self._error_text = "无法启动 ffmpeg 进程"
            self.finished.emit(-1, self._output_path, self._error_text)
            return
        
        # 等待完成，期间检查取消标志
        while not process.waitForFinished(100):
            if self._cancelled:
                process.terminate()
                if not process.waitForFinished(3000):
                    process.kill()
                self._exit_code = -2
                self._error_text = "用户取消"
                self.finished.emit(-2, self._output_path, self._error_text)
                return
        
        self._exit_code = process.exitCode()
        error_data = process.readAllStandardError()
        self._error_text = bytes(error_data).decode("utf-8", errors="replace") if error_data else ""
        
        self.finished.emit(self._exit_code, self._output_path,
                           self._error_text if self._exit_code != 0 else "")
    
    def cancel(self):
        """标记取消"""
        self._cancelled = True
