"""
文件列表控件
支持拖放添加、多选、状态显示
"""
import os
from typing import List, Optional, Dict
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QHeaderView, QAbstractItemView, QMenu, QMessageBox
)
from PySide6.QtCore import Signal, Qt, QMimeData
from PySide6.QtGui import QDragEnterEvent, QDropEvent, QAction, QColor

from utils.time_parser import format_seconds
from utils.ffprobe_helper import FFprobeHelper


# 支持的视频扩展名
VIDEO_EXTENSIONS = {
    ".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv", ".webm",
    ".m4v", ".mpg", ".mpeg", ".3gp", ".ts", ".vob", ".mts"
}


class FileListWidget(QWidget):
    """
    文件列表控件
    显示待处理视频文件，支持拖放和批量操作
    """
    
    # 信号
    files_added = Signal(list)  # 文件路径列表
    file_removed = Signal(str)  # 移除的文件路径
    files_changed = Signal()  # 文件列表变更
    
    def __init__(self, ffprobe_helper: Optional[FFprobeHelper] = None, parent=None):
        super().__init__(parent)
        self._ffprobe_helper = ffprobe_helper
        self._files: Dict[str, dict] = {}  # path -> {duration, status}
        self._init_ui()
        self._connect_signals()
        
        # 启用拖放
        self.setAcceptDrops(True)
    
    def _init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout(self)
        
        # 按钮栏
        btn_layout = QHBoxLayout()
        
        self._btn_add = QPushButton("添加文件")
        self._btn_add.setToolTip("Ctrl+O")
        btn_layout.addWidget(self._btn_add)
        
        self._btn_remove = QPushButton("移除选中")
        btn_layout.addWidget(self._btn_remove)
        
        self._btn_clear = QPushButton("清空列表")
        btn_layout.addWidget(self._btn_clear)
        
        self._btn_clear_done = QPushButton("清除已完成")
        btn_layout.addWidget(self._btn_clear_done)
        
        btn_layout.addStretch()
        
        self._label_count = QLabel("共 0 个文件")
        btn_layout.addWidget(self._label_count)
        
        layout.addLayout(btn_layout)
        
        # 表格
        self._table = QTableWidget()
        self._table.setColumnCount(4)
        self._table.setHorizontalHeaderLabels(["文件名", "目录", "时长", "状态"])
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
        
        layout.addWidget(self._table)
        
        # 设置接受拖放
        self._table.setAcceptDrops(True)
        self._table.installEventFilter(self)
    
    def _connect_signals(self):
        """连接信号"""
        self._btn_add.clicked.connect(self._on_add_clicked)
        self._btn_remove.clicked.connect(self._on_remove_clicked)
        self._btn_clear.clicked.connect(self._on_clear_clicked)
        self._btn_clear_done.clicked.connect(self._on_clear_done_clicked)
        self._table.customContextMenuRequested.connect(self._on_context_menu)
        
        if self._ffprobe_helper:
            self._ffprobe_helper.duration_received.connect(self._on_duration_received)
            self._ffprobe_helper.duration_failed.connect(self._on_duration_failed)
    
    # ==================== 拖放支持 ====================
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        """拖拽进入事件"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()
    
    def dropEvent(self, event: QDropEvent):
        """拖放事件"""
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
        """事件过滤器（处理表格的拖放）"""
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
        """添加文件按钮点击"""
        from PySide6.QtWidgets import QFileDialog
        
        file_filter = "视频文件 (*.mp4 *.avi *.mkv *.mov *.wmv *.flv *.webm *.m4v *.mpg *.mpeg *.ts);;所有文件 (*)"
        paths, _ = QFileDialog.getOpenFileNames(self, "选择视频文件", "", file_filter)
        
        if paths:
            self.add_files(paths)
    
    def _on_remove_clicked(self):
        """移除选中按钮点击"""
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
        """清空列表按钮点击"""
        if self._files:
            reply = QMessageBox.question(
                self, "确认清空",
                "确定要清空所有文件吗？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.clear_files()
    
    def _on_clear_done_clicked(self):
        """清除已完成按钮点击"""
        paths_to_remove = [
            path for path, data in self._files.items()
            if data.get("status") in ("success", "skipped")
        ]
        for path in paths_to_remove:
            self.remove_file(path)
    
    def _on_context_menu(self, pos):
        """右键菜单"""
        menu = QMenu(self)
        
        action_remove = QAction("移除选中", self)
        action_remove.triggered.connect(self._on_remove_clicked)
        menu.addAction(action_remove)
        
        item = self._table.itemAt(pos)
        if item:
            row = item.row()
            path_item = self._table.item(row, 0)
            if path_item:
                path = path_item.data(Qt.ItemDataRole.UserRole)
                
                action_open_dir = QAction("打开所在目录", self)
                action_open_dir.triggered.connect(
                    lambda: self._open_directory(path)
                )
                menu.addAction(action_open_dir)
                
                status = self._files.get(path, {}).get("status", "")
                if status == "failed":
                    action_retry = QAction("重试", self)
                    action_retry.triggered.connect(
                        lambda: self._retry_file(path)
                    )
                    menu.addAction(action_retry)
        
        menu.exec_(self._table.mapToGlobal(pos))
    
    def _open_directory(self, path: str):
        """打开文件所在目录"""
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
        """重试失败的文件"""
        if path in self._files:
            self._files[path]["status"] = "pending"
            self._update_row_status(path)
    
    # ==================== 时长回调 ====================
    
    def _on_duration_received(self, path: str, duration: float):
        """时长获取成功"""
        if path in self._files:
            self._files[path]["duration"] = duration
            self._update_row_duration(path)
    
    def _on_duration_failed(self, path: str, error: str):
        """时长获取失败"""
        if path in self._files:
            self._files[path]["duration"] = None
            self._update_row_duration(path, failed=True)
    
    # ==================== 公共方法 ====================
    
    def add_files(self, paths: List[str]):
        """
        添加文件到列表
        
        Args:
            paths: 文件路径列表
        """
        new_paths = []
        
        for path in paths:
            if path not in self._files:
                self._files[path] = {
                    "duration": None,
                    "status": "pending"
                }
                new_paths.append(path)
                self._add_row(path)
        
        if new_paths:
            self._update_count()
            self.files_added.emit(new_paths)
            self.files_changed.emit()
            
            # 异步获取时长
            if self._ffprobe_helper:
                self._ffprobe_helper.get_durations_batch(new_paths)
    
    def remove_file(self, path: str):
        """
        移除文件
        
        Args:
            path: 文件路径
        """
        if path in self._files:
            del self._files[path]
            self._rebuild_table()
            self.file_removed.emit(path)
            self.files_changed.emit()
    
    def clear_files(self):
        """清空所有文件"""
        self._files.clear()
        self._table.setRowCount(0)
        self._update_count()
        self.files_changed.emit()
    
    def get_file_paths(self) -> List[str]:
        """获取所有文件路径"""
        return list(self._files.keys())
    
    def get_pending_files(self) -> List[str]:
        """获取待处理的文件路径"""
        return [
            path for path, data in self._files.items()
            if data.get("status") == "pending"
        ]
    
    def get_durations(self) -> Dict[str, float]:
        """获取所有文件的时长字典"""
        return {
            path: data["duration"]
            for path, data in self._files.items()
            if data["duration"] is not None
        }
    
    def update_file_status(self, path: str, status: str, message: str = ""):
        """
        更新文件状态
        
        Args:
            path: 文件路径
            status: 状态值
            message: 状态消息
        """
        if path in self._files:
            self._files[path]["status"] = status
            self._files[path]["message"] = message
            self._update_row_status(path)
    
    def set_ffprobe_helper(self, helper: FFprobeHelper):
        """设置 ffprobe 辅助器"""
        self._ffprobe_helper = helper
        helper.duration_received.connect(self._on_duration_received)
        helper.duration_failed.connect(self._on_duration_failed)
    
    # ==================== 内部方法 ====================
    
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
        
        # 状态
        status_item = QTableWidgetItem("等待")
        self._table.setItem(row, 3, status_item)
    
    def _rebuild_table(self):
        """重建表格"""
        self._table.setRowCount(0)
        for path in self._files:
            self._add_row(path)
            self._update_row_duration(path)
            self._update_row_status(path)
    
    def _update_row_duration(self, path: str, failed: bool = False):
        """更新行的时长显示"""
        if path not in self._files:
            return
        
        for row in range(self._table.rowCount()):
            item = self._table.item(row, 0)
            if item and item.data(Qt.ItemDataRole.UserRole) == path:
                duration = self._files[path]["duration"]
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
    
    def _update_row_status(self, path: str):
        """更新行的状态显示"""
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
        
        status = self._files[path].get("status", "pending")
        text, color = status_map.get(status, ("未知", QColor("gray")))
        
        # 添加消息
        message = self._files[path].get("message", "")
        if message:
            text = f"{text} - {message[:30]}"
        
        for row in range(self._table.rowCount()):
            item = self._table.item(row, 0)
            if item and item.data(Qt.ItemDataRole.UserRole) == path:
                status_item = self._table.item(row, 3)
                status_item.setText(text)
                status_item.setForeground(color)
                break
    
    def _update_count(self):
        """更新文件计数"""
        total = len(self._files)
        pending = len([1 for d in self._files.values() if d.get("status") == "pending"])
        self._label_count.setText(f"共 {total} 个文件，{pending} 个待处理")


# 为了 QLabel 引用
from PySide6.QtWidgets import QLabel
