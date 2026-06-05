"""
主窗口
应用程序的主界面
"""
import os
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QMenuBar, QMenu, QMessageBox, QStatusBar, QLabel
)
from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QAction, QKeySequence

from ui.file_list_widget import FileListWidget
from ui.cutter_control_panel import CutterControlPanel
from ui.settings_dialog import SettingsDialog
from core.video_cutter_manager import VideoCutterManager
from core.preset_manager import PresetManager
from core.overwrite_policy import ConflictStrategy
from core.time_range_calculator import TimeMode
from utils.config_manager import ConfigManager
from utils.ffprobe_helper import FFprobeHelper


class MainWindow(QMainWindow):
    """
    主窗口
    组装各控件，连接信号，处理全局事件
    """
    
    def __init__(self, config_manager: ConfigManager):
        super().__init__()
        self._config = config_manager
        
        self.setWindowTitle("视频极简裁剪工具")
        self.setMinimumSize(900, 600)
        self.resize(1000, 700)
        
        # 初始化核心组件
        self._init_components()
        self._init_ui()
        self._init_menu()
        self._connect_signals()
        self._check_ffmpeg()
        
        # 恢复窗口状态
        self._restore_window_state()
    
    def _init_components(self):
        """初始化核心组件"""
        # FFprobe 辅助器
        self._ffprobe = FFprobeHelper(self._config.ffprobe_path)
        
        # 预设管理器
        self._preset_manager = PresetManager(self._config.presets_path)
        
        # 裁剪管理器
        conflict_strategy = ConflictStrategy(self._config.conflict_strategy)
        self._cutter_manager = VideoCutterManager(
            ffmpeg_path=self._config.ffmpeg_path,
            suffix=self._config.suffix,
            conflict_strategy=conflict_strategy,
            precision_mode=self._config.precision_mode,
            movflags_faststart=self._config.movflags_faststart
        )
    
    def _init_ui(self):
        """初始化界面"""
        # 中心部件
        central = QWidget()
        self.setCentralWidget(central)
        
        main_layout = QHBoxLayout(central)
        
        # 左侧文件列表
        self._file_list = FileListWidget(self._ffprobe)
        main_layout.addWidget(self._file_list, stretch=3)
        
        # 右侧控制面板
        self._control_panel = CutterControlPanel(self._preset_manager)
        main_layout.addWidget(self._control_panel, stretch=2)
        
        # 状态栏
        self._status_bar = QStatusBar()
        self.setStatusBar(self._status_bar)
        
        self._status_ffmpeg = QLabel("ffmpeg: 检测中...")
        self._status_bar.addPermanentWidget(self._status_ffmpeg)
        
        self._status_files = QLabel("文件: 0")
        self._status_bar.addPermanentWidget(self._status_files)
    
    def _init_menu(self):
        """初始化菜单栏"""
        menu_bar = self.menuBar()
        
        # 文件菜单
        file_menu = menu_bar.addMenu("文件(&F)")
        
        action_add = QAction("添加文件(&A)", self)
        action_add.setShortcut(QKeySequence("Ctrl+O"))
        action_add.triggered.connect(self._file_list._on_add_clicked)
        file_menu.addAction(action_add)
        
        file_menu.addSeparator()
        
        action_settings = QAction("设置(&S)", self)
        action_settings.setShortcut(QKeySequence("Ctrl+,"))
        action_settings.triggered.connect(self._show_settings)
        file_menu.addAction(action_settings)
        
        file_menu.addSeparator()
        
        action_exit = QAction("退出(&Q)", self)
        action_exit.setShortcut(QKeySequence("Ctrl+Q"))
        action_exit.triggered.connect(self.close)
        file_menu.addAction(action_exit)
        
        # 帮助菜单
        help_menu = menu_bar.addMenu("帮助(&H)")
        
        action_about = QAction("关于(&A)", self)
        action_about.triggered.connect(self._show_about)
        help_menu.addAction(action_about)
    
    def _connect_signals(self):
        """连接信号"""
        # 文件列表信号
        self._file_list.files_changed.connect(self._on_files_changed)
        
        # 控制面板信号
        self._control_panel.start_cutting.connect(self._on_start_cutting)
        self._control_panel.cancel_cutting.connect(self._on_cancel_cutting)
        
        # 裁剪管理器信号
        self._cutter_manager.progress_changed.connect(self._on_progress_changed)
        self._cutter_manager.file_status_changed.connect(self._on_file_status_changed)
        self._cutter_manager.file_started.connect(self._on_file_started)
        self._cutter_manager.file_finished.connect(self._on_file_finished)
        self._cutter_manager.all_finished.connect(self._on_all_finished)
        self._cutter_manager.log_message.connect(self._on_log_message)
        
        # 配置变更信号
        self._config.config_changed.connect(self._on_config_changed)
    
    def _check_ffmpeg(self):
        """检查 ffmpeg 可用性"""
        ffmpeg_path = self._config.ffmpeg_path
        
        from PySide6.QtCore import QProcess
        process = QProcess()
        process.start(ffmpeg_path, ["-version"])
        
        if process.waitForFinished(3000) and process.exitCode() == 0:
            self._status_ffmpeg.setText(f"ffmpeg: ✓ ({ffmpeg_path})")
            self._status_ffmpeg.setStyleSheet("color: green;")
        else:
            self._status_ffmpeg.setText(f"ffmpeg: ✗ (未找到)")
            self._status_ffmpeg.setStyleSheet("color: red;")
            
            QMessageBox.warning(
                self, "FFmpeg 未找到",
                f"无法找到 ffmpeg ({ffmpeg_path})。\n\n"
                "请在设置中配置正确的 ffmpeg 路径。\n"
                "下载地址: https://ffmpeg.org/download.html"
            )
    
    # ==================== 槽函数 ====================
    
    @Slot()
    def _on_files_changed(self):
        """文件列表变更"""
        count = len(self._file_list.get_file_paths())
        self._status_files.setText(f"文件: {count}")
        self._control_panel.update_preview(count)
    
    @Slot(str, object, object)
    def _on_start_cutting(self, mode_str: str, value_a, value_b):
        """开始裁剪"""
        # 获取待处理文件
        files = self._file_list.get_pending_files()
        
        if not files:
            QMessageBox.information(self, "提示", "没有待处理的文件")
            return
        
        # 检查 ffmpeg
        ffmpeg_path = self._config.ffmpeg_path
        from PySide6.QtCore import QProcess
        process = QProcess()
        process.start(ffmpeg_path, ["-version"])
        if not (process.waitForFinished(3000) and process.exitCode() == 0):
            QMessageBox.critical(self, "错误", "ffmpeg 不可用，请先在设置中配置正确路径")
            return
        
        # 设置裁剪参数
        mode = TimeMode(mode_str)
        durations = self._file_list.get_durations()
        
        # 更新管理器配置
        self._cutter_manager.set_ffmpeg_path(self._config.ffmpeg_path)
        self._cutter_manager.set_suffix(self._config.suffix)
        self._cutter_manager.set_conflict_strategy(ConflictStrategy(self._config.conflict_strategy))
        self._cutter_manager.set_precision_mode(self._control_panel.is_precision_mode())
        self._cutter_manager.set_precision_mode(self._config.precision_mode or self._control_panel.is_precision_mode())
        
        # 清空日志并设置运行状态
        self._control_panel.clear_log()
        self._control_panel.set_running(True)
        
        # 开始批量处理
        self._cutter_manager.start_batch(files, mode, value_a, value_b, durations)
    
    @Slot()
    def _on_cancel_cutting(self):
        """取消裁剪"""
        reply = QMessageBox.question(
            self, "确认取消",
            "确定要取消当前裁剪任务吗？\n已生成的文件将保留。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self._cutter_manager.cancel_all()
    
    @Slot(int, int)
    def _on_progress_changed(self, current: int, total: int):
        """进度变更"""
        self._control_panel.update_progress(current, total)
    
    @Slot(str, str, str)
    def _on_file_status_changed(self, path: str, status: str, message: str):
        """文件状态变更"""
        self._file_list.update_file_status(path, status, message)
    
    @Slot(str)
    def _on_file_started(self, path: str):
        """文件开始处理"""
        filename = os.path.basename(path)
        self._status_bar.showMessage(f"正在处理: {filename}")
    
    @Slot(str, bool, str)
    def _on_file_finished(self, path: str, success: bool, message: str):
        """文件处理完成"""
        pass
    
    @Slot(int, int, int)
    def _on_all_finished(self, success: int, failed: int, skipped: int):
        """全部完成"""
        self._control_panel.set_running(False)
        self._status_bar.showMessage(f"完成: 成功 {success}, 失败 {failed}, 跳过 {skipped}", 10000)
        
        # 显示完成对话框
        msg = f"裁剪完成！\n\n成功: {success}\n失败: {failed}\n跳过: {skipped}"
        
        if failed > 0:
            QMessageBox.warning(self, "裁剪完成", msg)
        else:
            QMessageBox.information(self, "裁剪完成", msg)
    
    @Slot(str)
    def _on_log_message(self, message: str):
        """日志消息"""
        self._control_panel.log(message)
    
    @Slot(str)
    def _on_config_changed(self, key: str):
        """配置变更"""
        if key == "ffmpeg_path":
            self._check_ffmpeg()
            self._ffprobe._ffprobe_path = self._config.ffprobe_path
    
    # ==================== 菜单操作 ====================
    
    def _show_settings(self):
        """显示设置对话框"""
        dialog = SettingsDialog(self._config, self)
        dialog.exec_()
    
    def _show_about(self):
        """显示关于对话框"""
        QMessageBox.about(
            self, "关于",
            "视频极简裁剪工具 v1.0\n\n"
            "一款极简的视频裁剪工具，\n"
            "支持快速去除片头片尾或按任意起止点截取。\n\n"
            "技术栈: Python + PySide6 + FFmpeg\n"
            "裁剪模式: 流复制（无损）/ 精确模式（重编码）"
        )
    
    # ==================== 窗口事件 ====================
    
    def _restore_window_state(self):
        """恢复窗口状态"""
        geometry = self._config.window_geometry
        if geometry:
            self.restoreGeometry(geometry)
    
    def _save_window_state(self):
        """保存窗口状态"""
        self._config.window_geometry = self.saveGeometry()
        self._config.sync()
    
    def closeEvent(self, event):
        """关闭窗口事件"""
        # 如果正在裁剪，确认关闭
        if self._cutter_manager.is_running:
            reply = QMessageBox.question(
                self, "确认退出",
                "裁剪任务正在进行中，确定要退出吗？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.No:
                event.ignore()
                return
            
            self._cutter_manager.cancel_all()
        
        # 保存窗口状态
        self._save_window_state()
        event.accept()
    
    def keyPressEvent(self, event):
        """键盘事件"""
        # Enter 开始裁剪
        if event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
            if not self._cutter_manager.is_running:
                self._control_panel._on_start_clicked()
        # Escape 取消
        elif event.key() == Qt.Key.Key_Escape:
            if self._cutter_manager.is_running:
                self._on_cancel_cutting()
        else:
            super().keyPressEvent(event)
