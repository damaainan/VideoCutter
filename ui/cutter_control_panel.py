"""
裁剪控制面板
整合时间输入、预设、裁剪按钮、进度和日志
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QProgressBar,
    QTextEdit, QGroupBox, QLabel, QMessageBox, QCheckBox
)
from PySide6.QtCore import Signal, Qt

from ui.time_input_widget import TimeInputWidget
from ui.preset_widget import PresetWidget
from ui.preset_dialog import PresetDialog
from core.preset_manager import PresetManager, Preset
from core.time_range_calculator import TimeMode
from utils.time_parser import format_seconds


class CutterControlPanel(QWidget):
    """
    裁剪控制面板
    整合所有裁剪相关的控件
    """
    
    # 信号
    start_cutting = Signal(str, object, object)  # (模式, A值, B值)
    cancel_cutting = Signal()
    
    def __init__(self, preset_manager: PresetManager, parent=None):
        super().__init__(parent)
        self._preset_manager = preset_manager
        self._init_ui()
        self._connect_signals()
    
    def _init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout(self)
        
        # 时间输入区
        self._time_input = TimeInputWidget()
        layout.addWidget(self._time_input)
        
        # 预设区
        preset_group = QGroupBox("预设")
        preset_layout = QVBoxLayout()
        self._preset_widget = PresetWidget(self._preset_manager)
        preset_layout.addWidget(self._preset_widget)
        preset_group.setLayout(preset_layout)
        layout.addWidget(preset_group)
        
        # 精确模式复选框
        self._check_precision = QCheckBox("精确到帧（慢，重编码）")
        self._check_precision.setToolTip("勾选后将重编码至关键帧完全对齐，速度较慢但精确")
        layout.addWidget(self._check_precision)
        
        # 预览信息
        self._label_preview = QLabel("")
        self._label_preview.setStyleSheet("color: #555; font-size: 12px;")
        self._label_preview.setWordWrap(True)
        layout.addWidget(self._label_preview)
        
        # 按钮区
        btn_layout = QHBoxLayout()
        
        self._btn_start = QPushButton("开始裁剪")
        self._btn_start.setMinimumHeight(40)
        self._btn_start.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-size: 16px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        btn_layout.addWidget(self._btn_start)
        
        self._btn_cancel = QPushButton("取消")
        self._btn_cancel.setMinimumHeight(40)
        self._btn_cancel.setEnabled(False)
        self._btn_cancel.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                font-size: 14px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        btn_layout.addWidget(self._btn_cancel)
        
        layout.addLayout(btn_layout)
        
        # 进度条
        self._progress = QProgressBar()
        self._progress.setVisible(False)
        layout.addWidget(self._progress)
        
        self._label_progress = QLabel("")
        self._label_progress.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._label_progress)
        
        # 日志区
        log_group = QGroupBox("日志")
        log_layout = QVBoxLayout()
        
        self._log_text = QTextEdit()
        self._log_text.setReadOnly(True)
        self._log_text.setMinimumHeight(100)
        self._log_text.setStyleSheet("font-family: 'Consolas', 'Courier New', monospace; font-size: 12px;")
        log_layout.addWidget(self._log_text)
        
        log_group.setLayout(log_layout)
        layout.addWidget(log_group)
        
        layout.addStretch()
    
    def _connect_signals(self):
        """连接信号"""
        self._btn_start.clicked.connect(self._on_start_clicked)
        self._btn_cancel.clicked.connect(self._on_cancel_clicked)
        self._preset_widget.preset_applied.connect(self._on_preset_applied)
        self._preset_widget.save_requested.connect(self._on_save_preset)
        self._time_input.times_changed.connect(self._on_times_changed)
        self._check_precision.toggled.connect(
            lambda checked: self._time_input.set_precision_hint(checked)
        )
    
    def _on_start_clicked(self):
        """开始裁剪"""
        if not self._time_input.is_valid():
            QMessageBox.warning(self, "输入错误", "请检查时间输入格式是否正确")
            return
        
        mode = self._time_input.get_mode()
        value_a, value_b = self._time_input.get_values()
        
        self.start_cutting.emit(mode.value, value_a, value_b)
    
    def _on_cancel_clicked(self):
        """取消裁剪"""
        self.cancel_cutting.emit()
    
    def _on_preset_applied(self, mode_str: str, value_a, value_b):
        """应用预设"""
        mode = TimeMode(mode_str)
        self._time_input.set_values(mode, value_a, value_b)
        self._log(f"已应用预设: {mode.value}")
    
    def _on_save_preset(self):
        """保存预设"""
        dialog = PresetDialog(parent=self)
        if dialog.exec_():
            name = dialog.get_name()
            if name:
                mode = self._time_input.get_mode()
                value_a, value_b = self._time_input.get_values()
                
                preset = Preset(
                    name=name,
                    mode=mode,
                    value_a=value_a,
                    value_b=value_b
                )
                self._preset_manager.add_preset(preset)
                self._log(f"已保存预设: {name}")
    
    def _on_times_changed(self, mode: str, value_a, value_b):
        """时间变更"""
        # 更新预览信息（需要文件时长信息）
        pass
    
    # ==================== 公共方法 ====================
    
    def set_running(self, running: bool):
        """设置运行状态"""
        self._btn_start.setEnabled(not running)
        self._btn_cancel.setEnabled(running)
        self._progress.setVisible(running)
        
        if running:
            self._progress.setValue(0)
            self._progress.setFormat("准备中...")
        else:
            self._label_progress.setText("")
    
    def update_progress(self, current: int, total: int):
        """更新进度"""
        self._progress.setMaximum(total)
        self._progress.setValue(current)
        self._progress.setFormat(f"{current} / {total}")
        self._label_progress.setText(f"正在处理第 {current} 个，共 {total} 个")
    
    def log(self, message: str):
        """添加日志"""
        self._log(message)
    
    def clear_log(self):
        """清空日志"""
        self._log_text.clear()
    
    def is_precision_mode(self) -> bool:
        """是否精确模式"""
        return self._check_precision.isChecked()
    
    def set_precision_mode(self, enabled: bool):
        """设置精确模式"""
        self._check_precision.setChecked(enabled)
    
    def get_time_values(self):
        """获取时间模式和值"""
        mode = self._time_input.get_mode()
        value_a, value_b = self._time_input.get_values()
        return mode, value_a, value_b
    
    def update_preview(self, file_count: int, total_duration: float = 0):
        """更新预览信息"""
        if file_count > 0:
            self._label_preview.setText(f"待处理文件: {file_count} 个")
        else:
            self._label_preview.setText("")
    
    # ==================== 内部方法 ====================
    
    def _log(self, message: str):
        """添加日志"""
        self._log_text.append(message)
        # 滚动到底部
        scrollbar = self._log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
