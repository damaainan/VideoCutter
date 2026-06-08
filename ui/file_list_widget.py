"""
文件列表控件
v1.1.2: 支持每文件独立时间设置、时间列显示、双击编辑
"""
import os
from typing import List, Optional, Dict
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QHeaderView, QAbstractItemView, QMenu, QMessageBox, QLabel
)
from PySide6.QtCore import Signal, Qt, QMimeData
from PySide6.QtGui import QDragEnterEvent, QDropEvent, QAction, QColor

from utils.time_parser import format_seconds
from utils.ffprobe_helper import FFprobeHelper
from core.video_cutter_manager import FileItem
from core.time_range_calculator import TimeMode


# 支持的视频扩展名
VIDEO_EXTENSIONS = {
    ".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv", ".webm",
    ".m4v", ".mpg", ".mpeg", ".3gp", ".ts", ".vob", ".mts"
}


class FileListWidget(QWidget):
    """
    文件列表控件
    显示待处理视频文件，支持拖放和批量操作
    v1.1.2: 新增时间列、右键自定义时间、双击编辑
    """
    
    # 信号
    files_added = Signal(list)  # 文件路径列表
    file_removed = Signal(str)  # 移除的文件路径
    files_changed = Signal()  # 文件列表变更
    request_custom_time = Signal(list)  # 请求设置自定义时间（文件路径列表）
    request_reset_time = Signal(list)  # 请求重置为默认时间（文件路径列表）
    
    def __init__(self, ffprobe_helper: Optional[FFprobeHelper] = None, parent=None):
        super().__init__(parent)
        self._ffprobe_helper = ffprobe_helper
        self._files: Dict[str, FileItem] = {}  # path -> FileItem
        self._saved_custom_times: Dict[str, dict] = {}  # v1.1.2: 从配置加载的自定义时间
        self._init_ui()
        self._connect_signals()
        self.setAcceptDrops(True)
    
    def _init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout(self)
        
        # 按钮栏（统一样式）
        btn_layout = QHBoxLayout()
        
        btn_style = """
            QPushButton {
                padding: 5px 12px;
                border-radius: 4px;
                border: 1px solid #ccc;
                background-color: #f8f8f8;
                min-width: 70px;
            }
            QPushButton:hover {
                background-color: #e8e8e8;
                border-color: #999;
            }
            QPushButton:pressed {
                background-color: #d8d8d8;
            }
        """
        
        self._btn_add = QPushButton("添加文件")
        self._btn_add.setToolTip("Ctrl+O")
        self._btn_add.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; border: none; font-weight: bold; }"
                                     "QPushButton:hover { background-color: #45a049; }")
        btn_layout.addWidget(self._btn_add)
        
        self._btn_remove = QPushButton("移除选中")
        self._btn_remove.setStyleSheet(btn_style)
        btn_layout.addWidget(self._btn_remove)
        
        self._btn_clear = QPushButton("清空列表")
        self._btn_clear.setStyleSheet(btn_style)
        btn_layout.addWidget(self._btn_clear)
        
        self._btn_clear_done = QPushButton("清除已完成")
        self._btn_clear_done.setStyleSheet(btn_style)
        btn_layout.addWidget(self._btn_clear_done)
        
        btn_layout.addStretch()
        
        self._label_count = QLabel("共 0 个文件")
        self._label_count.setStyleSheet("color: #666; font-size: 12px;")
        btn_layout.addWidget(self._label_count)
        
        layout.addLayout(btn_layout)
        
        # 表格（v1.1.2: 增加"时间"列为第5列）
        self._table = QTableWidget()
        self._table.setColumnCount(5)
        self._table.setHorizontalHeaderLabels(["文件名", "目录", "时长", "时间", "状态"])
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._table.verticalHeader().setVisible(False)
        
        # 列宽设置
        header = self._table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        
        layout.addWidget(self._table)
        
        self._table.setAcceptDrops(True)
        self._table.installEventFilter(self)
    
    def _connect_signals(self):
        """连接信号"""
        self._btn_add.clicked.connect(self._on_add_clicked)
        self._btn_remove.clicked.connect(self._on_remove_clicked)
        self._btn_clear.clicked.connect(self._on_clear_clicked)
        self._btn_clear_done.clicked.connect(self._on_clear_done_clicked)
        self._table.customContextMenuRequested.connect(self._on_context_menu)
        self._table.doubleClicked.connect(self._on_double_click)
        
        if self._ffprobe_helper:
            self._ffprobe_helper.duration_received.connect(self._on_duration_received)
            self._ffprobe_helper.duration_failed.connect(self._on_duration_failed)
    
    # ==================== 拖放支持 ====================
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()
    
    def dropEvent(self, event: QDropEvent):
        if event.mimeData().hasUrls():
            paths = []
            for url in event.mimeData().urls():
                path = url.toLocalFile()
                if os.path.isfile(path):
                    ext = os.path.splitext(path)[1].lower()
                    if ext in VIDEO_EXTENSIONS:
                        paths.append(path)
            if paths:
                self.add_files(paths)
                event.acceptProposedAction()
            else:
                event.ignore()
        else:
            event.ignore()
    
    def eventFilter(self, obj, event):
        if obj == self._table:
            if event.type() == event.Type.DragEnter:
                self.dragEnterEvent(event)
                return True
            elif event.type() == event.Type.Drop:
                self.dropEvent(event)
                return True
        return super().eventFilter(obj, event)
    
    # ==================== 按钮事件 ====================
    
    def _on_add_clicked(self):
        from PySide6.QtWidgets import QFileDialog
        file_filter = "视频文件 (*.mp4 *.avi *.mkv *.mov *.wmv *.flv *.webm *.m4v *.mpg *.mpeg *.ts);;所有文件 (*)"
        paths, _ = QFileDialog.getOpenFileNames(self, "选择视频文件", "", file_filter)
        if paths:
            self.add_files(paths)
    
    def _on_remove_clicked(self):
        rows = set()
        for item in self._table.selectedItems():
            rows.add(item.row())
        paths_to_remove = []
        for row in sorted(rows, reverse=True):
            path_item = self._table.item(row, 0)
            if path_item and path_item.data(Qt.ItemDataRole.UserRole):
                paths_to_remove.append(path_item.data(Qt.ItemDataRole.UserRole))
        for path in paths_to_remove:
            self.remove_file(path)
    
    def _on_clear_clicked(self):
        if self._files:
            reply = QMessageBox.question(
                self, "确认清空", "确定要清空所有文件吗？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.clear_files()
    
    def _on_clear_done_clicked(self):
        paths_to_remove = [
            path for path, item in self._files.items()
            if item.status.value in ("success", "skipped")
        ]
        for path in paths_to_remove:
            self.remove_file(path)
        self._update_count()  # 更新计数显示
    
    def _on_context_menu(self, pos):
        """右键菜单（v1.1.2: 新增自定义时间、重置时间选项）"""
        menu = QMenu(self)
        
        action_remove = QAction("移除选中", self)
        action_remove.triggered.connect(self._on_remove_clicked)
        menu.addAction(action_remove)
        
        # v1.1.2: 选中文件操作
        selected_paths = self._get_selected_paths()
        if selected_paths:
            menu.addSeparator()
            
            action_custom = QAction("设置自定义时间", self)
            action_custom.triggered.connect(
                lambda: self.request_custom_time.emit(selected_paths)
            )
            menu.addAction(action_custom)
            
            action_reset = QAction("重置为默认时间", self)
            action_reset.triggered.connect(
                lambda: self._reset_selected_time(selected_paths)
            )
            menu.addAction(action_reset)
            
            menu.addSeparator()
            
            # 第一个选中文件的额外操作
            path = selected_paths[0]
            action_open_dir = QAction("打开所在目录", self)
            action_open_dir.triggered.connect(lambda: self._open_directory(path))
            menu.addAction(action_open_dir)
            
            file_item = self._files.get(path)
            if file_item and file_item.status.value == "failed":
                action_retry = QAction("重试", self)
                action_retry.triggered.connect(lambda: self._retry_file(path))
                menu.addAction(action_retry)
        
        menu.exec_(self._table.mapToGlobal(pos))
    
    def _on_double_click(self, index):
        """v1.1.2: 双击文件条目打开自定义时间对话框"""
        row = index.row()
        path_item = self._table.item(row, 0)
        if path_item:
            path = path_item.data(Qt.ItemDataRole.UserRole)
            if path:
                self.request_custom_time.emit([path])
    
    # ==================== 时长回调 ====================
    
    def _on_duration_received(self, path: str, duration: float):
        if path in self._files:
            self._files[path].duration = duration
            self._update_row_duration(path)
    
    def _on_duration_failed(self, path: str, error: str):
        if path in self._files:
            self._files[path].duration = None
            self._update_row_duration(path, failed=True)
    
    # ==================== 公共方法 ====================
    
    def add_files(self, paths: List[str], custom_times: Optional[Dict[str, dict]] = None):
        """
        添加文件到列表
        v1.1.2: 支持从配置恢复自定义时间
        """
        new_paths = []
        
        # 合并传入的 custom_times 和已保存的
        merged_ct = dict(self._saved_custom_times)
        if custom_times:
            merged_ct.update(custom_times)
        
        for path in paths:
            if path not in self._files:
                file_item = FileItem(path=path)
                
                # v1.1.2: 恢复已保存的自定义时间
                if path in merged_ct:
                    ct = merged_ct[path]
                    file_item.use_default = False
                    file_item.custom_mode = TimeMode(ct.get("mode", "trim"))
                    file_item.custom_A = ct.get("A")
                    file_item.custom_B = ct.get("B")
                
                self._files[path] = file_item
                new_paths.append(path)
                self._add_row(path)
        
        if new_paths:
            self._update_count()
            self.files_added.emit(new_paths)
            self.files_changed.emit()
            
            if self._ffprobe_helper:
                self._ffprobe_helper.get_durations_batch(new_paths)
    
    def remove_file(self, path: str):
        if path in self._files:
            del self._files[path]
            self._rebuild_table()
            self._update_count()  # 更新计数显示
            self.file_removed.emit(path)
            self.files_changed.emit()
    
    def clear_files(self):
        self._files.clear()
        self._table.setRowCount(0)
        self._update_count()
        self.files_changed.emit()
    
    def get_file_paths(self) -> List[str]:
        return list(self._files.keys())
    
    def get_pending_files(self) -> List[str]:
        return [
            path for path, item in self._files.items()
            if item.status.value == "pending"
        ]
    
    def get_file_items(self) -> List[FileItem]:
        """v1.1.2: 获取所有 FileItem 对象（待处理的）"""
        return [
            item for item in self._files.values()
            if item.status.value == "pending"
        ]
    
    def get_all_file_items(self) -> List[FileItem]:
        """v1.1.2: 获取所有 FileItem 对象"""
        return list(self._files.values())
    
    def get_durations(self) -> Dict[str, float]:
        return {
            path: item.duration
            for path, item in self._files.items()
            if item.duration is not None
        }
    
    def get_custom_times(self) -> Dict[str, dict]:
        """v1.1.2: 获取所有自定义文件的配置（用于保存）"""
        result = {}
        for path, item in self._files.items():
            if not item.use_default:
                result[path] = {
                    "mode": item.custom_mode.value if item.custom_mode else "trim",
                    "A": item.custom_A,
                    "B": item.custom_B
                }
        return result
    
    def update_file_status(self, path: str, status: str, message: str = ""):
        if path in self._files:
            from core.video_cutter_manager import FileStatus
            try:
                self._files[path].status = FileStatus(status)
            except ValueError:
                pass
            self._files[path].error_message = message
            self._update_row_status(path)
    
    def set_file_custom_time(self, paths: List[str], mode: TimeMode, 
                              value_a, value_b):
        """v1.1.2: 为指定文件设置自定义时间"""
        for path in paths:
            if path in self._files:
                item = self._files[path]
                item.use_default = False
                item.custom_mode = mode
                item.custom_A = value_a
                item.custom_B = value_b
                self._update_row_time(path)
    
    def reset_files_to_default(self, paths: List[str]):
        """v1.1.2: 将指定文件重置为默认时间"""
        for path in paths:
            if path in self._files:
                item = self._files[path]
                item.use_default = True
                item.custom_mode = None
                item.custom_A = None
                item.custom_B = None
                self._update_row_time(path)
    
    def update_all_time_column(self, default_mode: TimeMode, default_a, default_b):
        """v1.1.2: 更新所有文件的时间列显示"""
        for path in self._files:
            self._update_row_time(path, default_mode, default_a, default_b)
    
    def set_ffprobe_helper(self, helper: FFprobeHelper):
        self._ffprobe_helper = helper
        helper.duration_received.connect(self._on_duration_received)
        helper.duration_failed.connect(self._on_duration_failed)
    
    def get_file_item(self, path: str) -> Optional[FileItem]:
        """v1.1.2: 获取单个文件项"""
        return self._files.get(path)
    
    # ==================== 内部方法 ====================
    
    def _get_selected_paths(self) -> List[str]:
        """获取所有选中行的文件路径"""
        rows = set()
        for item in self._table.selectedItems():
            rows.add(item.row())
        paths = []
        for row in sorted(rows):
            path_item = self._table.item(row, 0)
            if path_item and path_item.data(Qt.ItemDataRole.UserRole):
                paths.append(path_item.data(Qt.ItemDataRole.UserRole))
        return paths
    
    def _reset_selected_time(self, paths: List[str]):
        """重置选中文件的时间为默认"""
        self.reset_files_to_default(paths)
    
    def _add_row(self, path: str):
        """添加一行到表格"""
        row = self._table.rowCount()
        self._table.insertRow(row)
        
        # 文件名
        filename = os.path.basename(path)
        name_item = QTableWidgetItem(filename)
        name_item.setData(Qt.ItemDataRole.UserRole, path)
        name_item.setToolTip(path)
        self._table.setItem(row, 0, name_item)
        
        # 目录
        dir_path = os.path.dirname(path)
        dir_item = QTableWidgetItem(dir_path)
        dir_item.setToolTip(dir_path)
        self._table.setItem(row, 1, dir_item)
        
        # 时长
        duration_item = QTableWidgetItem("获取中...")
        self._table.setItem(row, 2, duration_item)
        
        # v1.1.2: 时间列
        time_item = QTableWidgetItem("默认")
        time_item.setForeground(QColor("gray"))
        self._table.setItem(row, 3, time_item)
        
        # 状态
        status_item = QTableWidgetItem("等待")
        self._table.setItem(row, 4, status_item)
    
    def _rebuild_table(self):
        self._table.setRowCount(0)
        for path in self._files:
            self._add_row(path)
            self._update_row_duration(path)
            self._update_row_status(path)
            self._update_row_time(path)
    
    def _update_row_duration(self, path: str, failed: bool = False):
        if path not in self._files:
            return
        for row in range(self._table.rowCount()):
            item = self._table.item(row, 0)
            if item and item.data(Qt.ItemDataRole.UserRole) == path:
                duration = self._files[path].duration
                duration_item = self._table.item(row, 2)
                if failed:
                    duration_item.setText("未知")
                    duration_item.setForeground(QColor("gray"))
                elif duration is not None:
                    duration_item.setText(format_seconds(duration))
                    duration_item.setForeground(QColor("black"))
                else:
                    duration_item.setText("获取中...")
                    duration_item.setForeground(QColor("gray"))
                break
    
    def _update_row_time(self, path: str, default_mode=None, default_a=None, default_b=None):
        """v1.1.2: 更新时间列显示"""
        if path not in self._files:
            return
        
        file_item = self._files[path]
        
        for row in range(self._table.rowCount()):
            item = self._table.item(row, 0)
            if item and item.data(Qt.ItemDataRole.UserRole) == path:
                time_item = self._table.item(row, 3)
                if file_item.use_default:
                    if default_mode is not None:
                        text = file_item.get_time_summary(default_mode, default_a, default_b)
                    else:
                        text = "默认"
                    time_item.setForeground(QColor("gray"))
                else:
                    mode = file_item.custom_mode or TimeMode.TRIM_HEAD_TAIL
                    text = file_item.get_time_summary(mode, file_item.custom_A, file_item.custom_B)
                    time_item.setForeground(QColor("#2196F3"))  # 蓝色表示自定义
                time_item.setText(text)
                time_item.setToolTip(text)
                break
    
    def _update_row_status(self, path: str):
        if path not in self._files:
            return
        
        status_map = {
            "pending": ("等待", QColor("gray")),
            "processing": ("处理中...", QColor("blue")),
            "success": ("成功", QColor("green")),
            "failed": ("失败", QColor("red")),
            "skipped": ("跳过", QColor("orange")),
            "cancelled": ("已取消", QColor("gray")),
        }
        
        file_item = self._files[path]
        status_text = file_item.status.value
        text, color = status_map.get(status_text, ("未知", QColor("gray")))
        
        if file_item.error_message:
            text = f"{text} - {file_item.error_message[:30]}"
        
        for row in range(self._table.rowCount()):
            item = self._table.item(row, 0)
            if item and item.data(Qt.ItemDataRole.UserRole) == path:
                status_item = self._table.item(row, 4)
                status_item.setText(text)
                status_item.setForeground(color)
                break
    
    def _update_count(self):
        total = len(self._files)
        if total == 0:
            self._label_count.setText("共 0 个文件")
            return
        
        pending = sum(1 for item in self._files.values() if item.status.value == "pending")
        success = sum(1 for item in self._files.values() if item.status.value == "success")
        failed = sum(1 for item in self._files.values() if item.status.value == "failed")
        skipped = sum(1 for item in self._files.values() if item.status.value == "skipped")
        processing = sum(1 for item in self._files.values() if item.status.value == "processing")
        custom = sum(1 for item in self._files.values() if not item.use_default)
        
        parts = [f"共 {total} 个文件"]
        if processing > 0:
            parts.append(f"{processing} 个处理中")
        if success > 0:
            parts.append(f"{success} 个已完成")
        if failed > 0:
            parts.append(f"{failed} 个失败")
        if skipped > 0:
            parts.append(f"{skipped} 个跳过")
        if pending > 0:
            parts.append(f"{pending} 个待处理")
        if custom > 0:
            parts.append(f"{custom} 个自定义")
        
        self._label_count.setText("，".join(parts))
    
    def _open_directory(self, path: str):
        import subprocess
        import platform
        dir_path = os.path.dirname(path)
        if platform.system() == "Windows":
            os.startfile(dir_path)
        elif platform.system() == "Darwin":
            subprocess.Popen(["open", dir_path])
        else:
            subprocess.Popen(["xdg-open", dir_path])
    
    def _retry_file(self, path: str):
        if path in self._files:
            from core.video_cutter_manager import FileStatus
            self._files[path].status = FileStatus.PENDING
            self._update_row_status(path)
