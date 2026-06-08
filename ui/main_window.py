"""
主窗口
v1.1.2: 支持每文件独立时间、配置持久化、Ctrl+S 保存
"""
import os
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QMenuBar, QMenu, QMessageBox, QStatusBar, QLabel
)
from PySide6.QtCore import Qt, Slot, Signal
from PySide6.QtGui import QAction, QKeySequence, QIcon

from ui.file_list_widget import FileListWidget
from ui.cutter_control_panel import CutterControlPanel
from ui.settings_dialog import SettingsDialog
from ui.custom_time_dialog import CustomTimeDialog
from core.video_cutter_manager import VideoCutterManager, FileItem
from core.preset_manager import PresetManager
from core.overwrite_policy import ConflictStrategy
from core.time_range_calculator import TimeMode
from utils.config_manager import ConfigManager
from utils.ffprobe_helper import FFprobeHelper
from utils.platform_helper import get_icon_path


class _ClickableLabel(QLabel):
    """可点击的 QLabel，用于状态栏 ffmpeg 状态"""
    clicked = Signal()
    
    def mousePressEvent(self, event):
        self.clicked.emit()
        super().mousePressEvent(event)


class MainWindow(QMainWindow):
    """
    主窗口
    组装各控件，连接信号，处理全局事件
    v1.1.2: 新增每文件独立时间配置、配置持久化
    """
    
    def __init__(self, config_manager: ConfigManager):
        super().__init__()
        self._config = config_manager
        
        self.setWindowTitle("视频极简裁剪工具 v1.1.2")
        self.setMinimumSize(950, 650)
        self.resize(1050, 720)
        
        # 设置窗口图标
        icon_path = get_icon_path()
        if icon_path:
            self.setWindowIcon(QIcon(icon_path))
        
        self._init_components()
        self._init_ui()
        self._init_menu()
        self._connect_signals()
        
        self._ffmpeg_available = False
        self._check_ffmpeg()
        
        # 恢复窗口状态和配置
        self._restore_window_state()
        self._load_project_config()
    
    def _init_components(self):
        """初始化核心组件"""
        self._ffprobe = FFprobeHelper(self._config.ffprobe_path)
        self._preset_manager = PresetManager(self._config.presets_path)
        
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
        
        self._status_ffmpeg = _ClickableLabel("ffmpeg: 检测中...")
        self._status_ffmpeg.clicked.connect(self._show_settings)
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
        
        # v1.1.2: 保存配置
        action_save = QAction("保存配置(&S)", self)
        action_save.setShortcut(QKeySequence("Ctrl+S"))
        action_save.triggered.connect(self._save_project_config)
        file_menu.addAction(action_save)
        
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
        self._file_list.request_custom_time.connect(self._on_request_custom_time)
        
        # 控制面板信号
        self._control_panel.start_cutting.connect(self._on_start_cutting)
        self._control_panel.cancel_cutting.connect(self._on_cancel_cutting)
        self._control_panel.apply_default_to_all.connect(self._on_apply_default_to_all)
        
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
        """检查 ffmpeg 可用性（不阻塞启动，未找到时在状态栏提示）"""
        ffmpeg_path = self._config.ffmpeg_path
            
        from PySide6.QtCore import QProcess
        process = QProcess()
        process.start(ffmpeg_path, ["-version"])
            
        if process.waitForFinished(3000) and process.exitCode() == 0:
            self._status_ffmpeg.setText(f"ffmpeg: \u2713 ({ffmpeg_path})")
            self._status_ffmpeg.setStyleSheet("color: green;")
            self._ffmpeg_available = True
        else:
            self._status_ffmpeg.setText(f"ffmpeg: \u2717 未找到 (点击设置)")
            self._status_ffmpeg.setStyleSheet("color: red; text-decoration: underline; cursor: pointer;")
            self._ffmpeg_available = False
                
            # 状态栏显示提示信息（不弹对话框）
            self._status_bar.showMessage(
                "FFmpeg 未找到，请点击状态栏右侧“ffmpeg: \u2717 未找到”设置路径，"
                "或通过菜单 文件→设置 配置",
                15000
            )
    
    # ==================== v1.1.2 配置持久化 ====================
    
    def _save_project_config(self):
        """保存项目配置（默认时间 + 文件自定义时间）"""
        # 获取当前默认时间
        mode, value_a, value_b = self._control_panel.get_time_values()
        default_time = {
            "mode": mode.value,
            "A": value_a,
            "B": value_b
        }
        
        # 获取文件自定义时间
        file_custom_times = self._file_list.get_custom_times()
        
        self._config.save_project_config(default_time, file_custom_times)
        self._status_bar.showMessage("配置已保存", 3000)
    
    def _load_project_config(self):
        """启动时加载项目配置"""
        config = self._config.load_project_config()
        if not config:
            return
        
        # 恢复默认时间到 UI
        default_time = config.get("default_time", {})
        if default_time:
            mode_str = default_time.get("mode", "trim")
            mode = TimeMode(mode_str)
            a = default_time.get("A")
            b = default_time.get("B")
            self._control_panel._time_input.set_values(mode, a, b)
        
        # v1.1.2: 保存文件自定义时间映射，添加文件时自动恢复
        self._saved_custom_times = config.get("file_custom_times", {})
        self._file_list._saved_custom_times = self._saved_custom_times
    
    # ==================== v1.1.2 自定义时间对话框 ====================
    
    @Slot(list)
    def _on_request_custom_time(self, paths: list):
        """打开自定义时间设置对话框"""
        # 获取文件名列表
        file_names = [os.path.basename(p) for p in paths]
        
        # 获取当前文件的已有自定义值（如果有）
        current_mode = None
        current_a = None
        current_b = None
        
        if len(paths) == 1:
            item = self._file_list.get_file_item(paths[0])
            if item and not item.use_default and item.custom_mode:
                current_mode = item.custom_mode
                current_a = item.custom_A
                current_b = item.custom_B
        
        # 如果没有已有值，用当前默认值
        if current_mode is None:
            current_mode, current_a, current_b = self._control_panel.get_time_values()
        
        dialog = CustomTimeDialog(
            file_names=file_names,
            current_mode=current_mode,
            current_a=current_a,
            current_b=current_b,
            presets=self._preset_manager.presets,
            parent=self
        )
        
        if dialog.exec_():
            mode, value_a, value_b = dialog.get_result()
            self._file_list.set_file_custom_time(paths, mode, value_a, value_b)
            
            # 更新时间列显示
            default_mode, default_a, default_b = self._control_panel.get_time_values()
            self._file_list.update_all_time_column(default_mode, default_a, default_b)
    
    @Slot()
    def _on_apply_default_to_all(self):
        """将默认时间应用到所有文件"""
        reply = QMessageBox.question(
            self, "确认",
            "确定要将所有文件的时间重置为当前默认值吗？\n"
            "这会清除所有文件的自定义时间设置。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            all_paths = self._file_list.get_file_paths()
            self._file_list.reset_files_to_default(all_paths)
            
            default_mode, default_a, default_b = self._control_panel.get_time_values()
            self._file_list.update_all_time_column(default_mode, default_a, default_b)
            self._control_panel.log("已将所有文件重置为默认时间")
    
    # ==================== 槽函数 ====================
    
    @Slot()
    def _on_files_changed(self):
        """文件列表变更"""
        count = len(self._file_list.get_file_paths())
        self._status_files.setText(f"文件: {count}")
        self._control_panel.update_preview(count)
        
        # v1.1.2: 更新时间列显示
        default_mode, default_a, default_b = self._control_panel.get_time_values()
        self._file_list.update_all_time_column(default_mode, default_a, default_b)
    
    @Slot(str, object, object)
    def _on_start_cutting(self, mode_str: str, value_a, value_b):
        """开始裁剪（v1.1.2: 使用每文件独立时间参数）"""
        # 获取待处理的 FileItem 列表
        file_items = self._file_list.get_file_items()
        
        if not file_items:
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
        
        default_mode = TimeMode(mode_str)
        durations = self._file_list.get_durations()
        
        # 更新管理器配置
        self._cutter_manager.set_ffmpeg_path(self._config.ffmpeg_path)
        self._cutter_manager.set_suffix(self._config.suffix)
        self._cutter_manager.set_conflict_strategy(ConflictStrategy(self._config.conflict_strategy))
        self._cutter_manager.set_precision_mode(
            self._config.precision_mode or self._control_panel.is_precision_mode()
        )
        
        # 清空日志并设置运行状态
        self._control_panel.clear_log()
        self._control_panel.set_running(True)
        
        # v1.1.2: 传入 FileItem 列表（含自定义时间信息）
        self._cutter_manager.start_batch(file_items, default_mode, value_a, value_b, durations)
    
    @Slot()
    def _on_cancel_cutting(self):
        reply = QMessageBox.question(
            self, "确认取消",
            "确定要取消当前裁剪任务吗？\n已生成的文件将保留。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._cutter_manager.cancel_all()
    
    @Slot(int, int)
    def _on_progress_changed(self, current: int, total: int):
        self._control_panel.update_progress(current, total)
    
    @Slot(str, str, str)
    def _on_file_status_changed(self, path: str, status: str, message: str):
        self._file_list.update_file_status(path, status, message)
        self._file_list._update_count()  # 实时更新计数显示
    
    @Slot(str)
    def _on_file_started(self, path: str):
        filename = os.path.basename(path)
        self._status_bar.showMessage(f"正在处理: {filename}")
    
    @Slot(str, bool, str)
    def _on_file_finished(self, path: str, success: bool, message: str):
        pass
    
    @Slot(int, int, int)
    def _on_all_finished(self, success: int, failed: int, skipped: int):
        self._control_panel.set_running(False)
        self._status_bar.showMessage(f"完成: 成功 {success}, 失败 {failed}, 跳过 {skipped}", 10000)
        
        msg = f"裁剪完成！\n\n成功: {success}\n失败: {failed}\n跳过: {skipped}"
        if failed > 0:
            QMessageBox.warning(self, "裁剪完成", msg)
        else:
            QMessageBox.information(self, "裁剪完成", msg)
    
    @Slot(str)
    def _on_log_message(self, message: str):
        self._control_panel.log(message)
    
    @Slot(str)
    def _on_config_changed(self, key: str):
        if key == "ffmpeg_path":
            self._check_ffmpeg()
            self._ffprobe._ffprobe_path = self._config.ffprobe_path
    
    # ==================== 菜单操作 ====================
    
    def _show_settings(self):
        dialog = SettingsDialog(self._config, self)
        dialog.exec_()
        # 设置对话框关闭后重新检查 ffmpeg
        self._check_ffmpeg()
        self._ffprobe._ffprobe_path = self._config.ffprobe_path
    
    def _show_about(self):
        QMessageBox.about(
            self, "关于",
            "视频极简裁剪工具 v1.1.2\n\n"
            "一款极简的视频裁剪工具，\n"
            "支持快速去除片头片尾或按任意起止点截取。\n\n"
            "新增功能：\n"
            "• 每个文件可设置独立的裁剪时间\n"
            "• 默认时间配置持久化保存\n"
            "• Ctrl+S 手动保存配置\n\n"
            "技术栈: Python + PySide6 + FFmpeg\n"
            "裁剪模式: 流复制（无损）/ 精确模式（重编码）"
        )
    
    # ==================== 窗口事件 ====================
    
    def _restore_window_state(self):
        geometry = self._config.window_geometry
        if geometry:
            self.restoreGeometry(geometry)
    
    def _save_window_state(self):
        self._config.window_geometry = self.saveGeometry()
        self._config.sync()
    
    def closeEvent(self, event):
        """关闭窗口事件（v1.1.2: 自动保存配置）"""
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
        
        # v1.1.2: 自动保存配置
        self._save_project_config()
        self._save_window_state()
        event.accept()
    
    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
            if not self._cutter_manager.is_running:
                self._control_panel._on_start_clicked()
        elif event.key() == Qt.Key.Key_Escape:
            if self._cutter_manager.is_running:
                self._on_cancel_cutting()
        else:
            super().keyPressEvent(event)
