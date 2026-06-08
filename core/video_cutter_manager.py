"""
视频裁剪管理器模块
核心任务调度、队列管理、进度跟踪
"""
import os
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from enum import Enum

from PySide6.QtCore import QObject, Signal, Slot, QThread, QProcess, Qt

from core.time_range_calculator import TimeRangeCalculator, TimeMode, CutResult
from core.overwrite_policy import OverwritePolicy, ConflictStrategy
from utils.ffmpeg_runner import FFmpegWorker


class FileStatus(Enum):
    """文件处理状态"""
    PENDING = "pending"  # 等待处理
    PROCESSING = "processing"  # 处理中
    SUCCESS = "success"  # 成功
    FAILED = "failed"  # 失败
    SKIPPED = "skipped"  # 跳过
    CANCELLED = "cancelled"  # 已取消


@dataclass
class FileItem:
    """文件项目数据"""
    path: str
    duration: Optional[float] = None
    status: FileStatus = FileStatus.PENDING
    output_path: Optional[str] = None
    error_message: str = ""
    # v1.1.2 新增：每文件独立时间配置
    use_default: bool = True
    custom_mode: Optional[TimeMode] = None
    custom_A: Optional[float] = None
    custom_B: Optional[float] = None

    def get_effective_params(self, default_mode: TimeMode, default_a, default_b):
        """获取实际生效的裁剪参数（自定义优先，否则用默认）"""
        if self.use_default:
            return default_mode, default_a, default_b
        mode = self.custom_mode if self.custom_mode is not None else default_mode
        a = self.custom_A
        b = self.custom_B
        return mode, a, b

    def get_time_summary(self, default_mode: TimeMode, default_a, default_b) -> str:
        """获取时间概要字符串（用于列表显示）"""
        from utils.time_parser import format_seconds
        if self.use_default:
            mode, a, b = default_mode, default_a, default_b
            label = "默认"
        else:
            mode, a, b = self.get_effective_params(default_mode, default_a, default_b)
            label = "自定义"
        
        if mode == TimeMode.TRIM_HEAD_TAIL:
            parts = []
            if a is not None and a > 0:
                parts.append(f"头{format_seconds(a)}")
            if b is not None and b > 0:
                parts.append(f"尾{format_seconds(b)}")
            detail = "+".join(parts) if parts else "无裁剪"
        else:
            start_str = format_seconds(a) if a is not None else "00:00:00"
            end_str = format_seconds(b) if b is not None else "结尾"
            detail = f"{start_str}~{end_str}"
        return f"{label}({detail})"


class VideoCutterManager(QObject):
    """
    视频裁剪管理器
    负责批量裁剪任务的调度和执行
    """
    
    # 信号定义
    progress_changed = Signal(int, int)  # (当前索引, 总数)
    file_status_changed = Signal(str, str, str)  # (文件路径, 状态, 消息)
    file_started = Signal(str)  # 文件开始处理
    file_finished = Signal(str, bool, str)  # (文件路径, 是否成功, 消息)
    all_finished = Signal(int, int, int)  # (成功数, 失败数, 跳过数)
    log_message = Signal(str)  # 日志消息
    cancel_completed = Signal()  # 取消完成
    
    def __init__(
        self,
        ffmpeg_path: str = "ffmpeg",
        suffix: str = "_1",
        conflict_strategy: ConflictStrategy = ConflictStrategy.RENAME,
        precision_mode: bool = False,
        movflags_faststart: bool = True,
        parent: Optional[QObject] = None
    ):
        super().__init__(parent)
        
        self._ffmpeg_path = ffmpeg_path
        self._suffix = suffix
        self._conflict_strategy = conflict_strategy
        self._precision_mode = precision_mode
        self._movflags_faststart = movflags_faststart
        
        self._files: List[FileItem] = []
        self._current_index = -1
        self._is_running = False
        self._is_cancelled = False
        
        self._current_thread: Optional[QThread] = None
        self._current_worker: Optional[FFmpegWorker] = None
        self._old_threads: List[QThread] = []   # 保留旧线程引用，批次结束后统一清理
        self._old_workers: List[FFmpegWorker] = []
        
        self._success_count = 0
        self._failed_count = 0
        self._skipped_count = 0
    
    @property
    def is_running(self) -> bool:
        """是否正在运行"""
        return self._is_running
    
    @property
    def files(self) -> List[FileItem]:
        """获取文件列表"""
        return self._files
    
    def set_ffmpeg_path(self, path: str):
        """设置 ffmpeg 路径"""
        self._ffmpeg_path = path
    
    def set_suffix(self, suffix: str):
        """设置输出后缀"""
        self._suffix = suffix
    
    def set_conflict_strategy(self, strategy: ConflictStrategy):
        """设置冲突策略"""
        self._conflict_strategy = strategy
    
    def set_precision_mode(self, enabled: bool):
        """设置精确模式"""
        self._precision_mode = enabled
    
    def start_batch(
        self,
        file_items: List[FileItem],
        default_mode: TimeMode,
        default_a: Optional[float],
        default_b: Optional[float],
        durations: Optional[Dict[str, float]] = None
    ):
        """
        开始批量裁剪任务
        
        Args:
            file_items: 文件项列表（含自定义时间信息）
            default_mode: 默认时间模式
            default_a: 默认 A 值或开始时间
            default_b: 默认 B 值或结束时间
            durations: 文件时长字典（路径 -> 时长）
        """
        if self._is_running:
            return
        
        # 使用传入的文件项（保留自定义时间信息）
        self._files = []
        for item in file_items:
            duration = durations.get(item.path) if durations else None
            item.duration = duration
            item.status = FileStatus.PENDING
            item.error_message = ""
            self._files.append(item)
        
        self._current_index = -1
        self._is_running = True
        self._is_cancelled = False
        self._success_count = 0
        self._failed_count = 0
        self._skipped_count = 0
        
        self.log_message.emit(f"开始批量裁剪，共 {len(self._files)} 个文件")
        self.log_message.emit(f"默认模式: {default_mode.value}, A={default_a}, B={default_b}")
        
        # 统计自定义数量
        custom_count = sum(1 for f in self._files if not f.use_default)
        if custom_count > 0:
            self.log_message.emit(f"其中 {custom_count} 个文件使用自定义时间")
        
        # 处理下一个文件
        self._process_next(default_mode, default_a, default_b)
    
    def cancel_all(self):
        """取消所有任务"""
        if not self._is_running:
            return
        
        self._is_cancelled = True
        self.log_message.emit("正在取消...")
        
        # 取消当前正在运行的任务
        if self._current_worker:
            self._current_worker.cancel()
    
    def _process_next(self, default_mode: TimeMode, default_a: Optional[float], default_b: Optional[float]):
        """处理下一个文件"""
        self._current_index += 1
        
        # 检查取消
        if self._is_cancelled:
            self._finish_batch()
            return
        
        # 检查完成
        if self._current_index >= len(self._files):
            self._finish_batch()
            return
        
        file_item = self._files[self._current_index]
        
        # 发射进度信号
        self.progress_changed.emit(self._current_index + 1, len(self._files))
        
        # 更新状态
        file_item.status = FileStatus.PROCESSING
        self.file_status_changed.emit(file_item.path, FileStatus.PROCESSING.value, "处理中...")
        self.file_started.emit(file_item.path)
        
        # 获取每个文件实际生效的时间参数
        mode, value_a, value_b = file_item.get_effective_params(default_mode, default_a, default_b)
        time_src = "默认" if file_item.use_default else "自定义"
        
        self.log_message.emit(f"\n处理 ({self._current_index + 1}/{len(self._files)}): {os.path.basename(file_item.path)} [{time_src}]")
        
        # 计算裁剪参数
        if file_item.duration is None or file_item.duration <= 0:
            file_item.duration = 0
        
        result = TimeRangeCalculator.calculate(file_item.duration, mode, value_a, value_b)
        
        if not result.valid:
            file_item.status = FileStatus.FAILED
            file_item.error_message = result.error_message
            self._failed_count += 1
            self.file_status_changed.emit(file_item.path, FileStatus.FAILED.value, result.error_message)
            self.file_finished.emit(file_item.path, False, result.error_message)
            self.log_message.emit(f"  错误: {result.error_message}")
            self._process_next(default_mode, default_a, default_b)
            return
        
        # 构造输出路径
        overwrite_policy = OverwritePolicy(self._conflict_strategy)
        output_path, status = overwrite_policy.get_output_path(file_item.path, self._suffix)
        
        if status == "skipped":
            file_item.status = FileStatus.SKIPPED
            self._skipped_count += 1
            self.file_status_changed.emit(file_item.path, FileStatus.SKIPPED.value, "已跳过")
            self.file_finished.emit(file_item.path, True, "已跳过（文件已存在）")
            self.log_message.emit(f"  已跳过（文件已存在）")
            self._process_next(default_mode, default_a, default_b)
            return
        
        file_item.output_path = output_path
        args = self._build_ffmpeg_args(file_item.path, output_path, result)
        
        self.log_message.emit(f"  输出: {os.path.basename(output_path)}")
        self.log_message.emit(f"  命令: ffmpeg {' '.join(args)}")
        
        # 创建工作线程
        # 将旧线程移到清理列表（不在此处 wait/delete，避免死锁）
        if self._current_thread is not None:
            self._old_threads.append(self._current_thread)
        if self._current_worker is not None:
            self._old_workers.append(self._current_worker)
        
        self._current_thread = QThread()
        self._current_worker = FFmpegWorker(self._ffmpeg_path, args, output_path)
        self._current_worker.moveToThread(self._current_thread)
        
        # 用局部变量捕获，避免被下次覆盖
        cur_worker = self._current_worker
        cur_thread = self._current_thread
        
        # 1) thread.started → worker.run
        cur_thread.started.connect(cur_worker.run)
        
        # 2) worker.finished → thread.quit（DirectConnection，在 worker 线程上立即执行）
        cur_worker.finished.connect(
            cur_thread.quit, Qt.ConnectionType.DirectConnection
        )
        
        # 3) QThread.finished → _on_file_finished（QueuedConnection，确保在主线程执行，且线程已停止）
        cur_thread.finished.connect(
            lambda: self._on_file_finished_safe(cur_worker, default_mode, default_a, default_b),
            Qt.ConnectionType.QueuedConnection
        )
        
        # 4) 不在此处 deleteLater，统一由 _cleanup_all_threads 管理
        
        self._current_thread.start()
    
    def _build_ffmpeg_args(self, input_path: str, output_path: str, result: CutResult) -> List[str]:
        """构造 ffmpeg 命令参数"""
        args = []
        
        if self._precision_mode:
            # 精确模式：-ss 在 -i 之后，重编码
            args.extend(["-i", input_path])
            
            if result.ss is not None:
                args.extend(["-ss", str(result.ss)])
            if result.to is not None:
                args.extend(["-to", str(result.to)])
            
            # 重编码（不使用 -c copy）
            args.extend(["-c:v", "libx264", "-c:a", "aac"])
        else:
            # 快速模式：-ss 在 -i 之前，流复制
            if result.ss is not None:
                args.extend(["-ss", str(result.ss)])
            
            args.extend(["-i", input_path])
            
            if result.to is not None:
                args.extend(["-to", str(result.to)])
            
            args.extend(["-c", "copy", "-map", "0"])
            args.extend(["-avoid_negative_ts", "make_zero"])
        
        # movflags
        if self._movflags_faststart and output_path.lower().endswith(".mp4"):
            args.extend(["-movflags", "+faststart"])
        
        # 覆盖输出
        args.append("-y")
        args.append(output_path)
        
        return args
    
    @Slot(int, str, str, TimeMode, object, object)
    def _on_file_finished(self, exit_code: int, output_path: str, error: str,
                          default_mode: TimeMode, default_a: Optional[float], default_b: Optional[float]):
        """文件处理完成回调（必须在主线程执行）"""
        if self._current_index >= len(self._files):
            return
        
        file_item = self._files[self._current_index]
        
        if exit_code == 0:
            file_item.status = FileStatus.SUCCESS
            file_item.output_path = output_path
            self._success_count += 1
            self.file_status_changed.emit(file_item.path, FileStatus.SUCCESS.value, f"输出: {os.path.basename(output_path)}")
            self.file_finished.emit(file_item.path, True, f"输出: {os.path.basename(output_path)}")
            self.log_message.emit(f"  完成 ✓")
        elif exit_code == -2:
            file_item.status = FileStatus.CANCELLED
            self.file_status_changed.emit(file_item.path, FileStatus.CANCELLED.value, "已取消")
            self.log_message.emit(f"  已取消")
        else:
            file_item.status = FileStatus.FAILED
            file_item.error_message = error
            self._failed_count += 1
            error_summary = error[:200] if len(error) > 200 else error
            self.file_status_changed.emit(file_item.path, FileStatus.FAILED.value, error_summary)
            self.file_finished.emit(file_item.path, False, error_summary)
            self.log_message.emit(f"  失败: {error_summary[:100]}")
        
        # 直接处理下一个文件
        self._process_next(default_mode, default_a, default_b)
    
    def _on_file_finished_safe(self, worker: FFmpegWorker, default_mode: TimeMode,
                                default_a: Optional[float], default_b: Optional[float]):
        """
        从 QThread.finished 触发的安全回调
        从 worker 对象获取退出码和结果，转发到 _on_file_finished
        通过 QueuedConnection 确保在主线程执行
        """
        # 安全检查：批次可能已被取消/结束，此时不再处理
        if not self._is_running:
            return
        
        exit_code = getattr(worker, '_exit_code', -1)
        output_path = getattr(worker, '_output_path', '')
        error = getattr(worker, '_error_text', '')
        self._on_file_finished(exit_code, output_path, error, default_mode, default_a, default_b)
    
    def _finish_batch(self):
        """完成批量任务"""
        self._is_running = False
        
        # 等待并清理所有旧线程
        self._cleanup_all_threads()
        
        if self._is_cancelled:
            # 标记剩余文件为已取消
            for i in range(self._current_index + 1, len(self._files)):
                if self._files[i].status == FileStatus.PENDING:
                    self._files[i].status = FileStatus.CANCELLED
                    self.file_status_changed.emit(
                        self._files[i].path, FileStatus.CANCELLED.value, "已取消"
                    )
            
            self.log_message.emit("\n任务已取消")
            self.cancel_completed.emit()
        
        self.log_message.emit(f"\n========== 完成 ==========")
        self.log_message.emit(f"成功: {self._success_count}")
        self.log_message.emit(f"失败: {self._failed_count}")
        self.log_message.emit(f"跳过: {self._skipped_count}")
        
        self.all_finished.emit(self._success_count, self._failed_count, self._skipped_count)
    
    def _cleanup_all_threads(self):
        """批次结束后统一清理所有旧线程"""
        # 等待并清理当前线程
        if self._current_thread is not None:
            try:
                if self._current_thread.isRunning():
                    self._current_thread.wait(5000)
            except RuntimeError:
                pass
        
        # 等待并清理所有旧线程
        for t in self._old_threads:
            try:
                if t is not None and t.isRunning():
                    t.wait(5000)
            except RuntimeError:
                pass  # C++ 对象已被删除
        
        # 显式删除所有 worker 和 thread
        for w in self._old_workers:
            try:
                if w is not None:
                    w.deleteLater()
            except RuntimeError:
                pass
        
        for t in self._old_threads:
            try:
                if t is not None:
                    t.deleteLater()
            except RuntimeError:
                pass
        
        if self._current_worker is not None:
            try:
                self._current_worker.deleteLater()
            except RuntimeError:
                pass
        if self._current_thread is not None:
            try:
                self._current_thread.deleteLater()
            except RuntimeError:
                pass
        
        self._old_threads.clear()
        self._old_workers.clear()
        self._current_thread = None
        self._current_worker = None
