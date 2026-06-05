"""
时间输入控件
支持去头去尾和绝对起止两种模式
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QRadioButton, QLabel, QLineEdit, QButtonGroup
)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QPalette, QColor

from utils.time_parser import parse_time_input, format_seconds
from core.time_range_calculator import TimeMode


class TimeInputWidget(QGroupBox):
    """
    时间输入控件
    提供两种时间模式切换和对应的时间输入框
    """
    
    # 信号：时间变更 (模式, A值/开始时间, B值/结束时间)
    times_changed = Signal(str, object, object)
    
    def __init__(self, parent=None):
        super().__init__("时间设置", parent)
        self._init_ui()
        self._connect_signals()
    
    def _init_ui(self):
        """初始化界面"""
        main_layout = QVBoxLayout(self)
        
        # 模式选择
        mode_layout = QHBoxLayout()
        self._radio_trim = QRadioButton("去头去尾")
        self._radio_absolute = QRadioButton("绝对起止")
        self._radio_trim.setChecked(True)
        
        self._mode_group = QButtonGroup(self)
        self._mode_group.addButton(self._radio_trim, 0)
        self._mode_group.addButton(self._radio_absolute, 1)
        
        mode_layout.addWidget(self._radio_trim)
        mode_layout.addWidget(self._radio_absolute)
        mode_layout.addStretch()
        main_layout.addLayout(mode_layout)
        
        # 去头去尾模式输入区
        self._trim_widget = QWidget()
        trim_layout = QVBoxLayout(self._trim_widget)
        trim_layout.setContentsMargins(0, 0, 0, 0)
        
        # 去掉开头 A
        head_layout = QHBoxLayout()
        head_layout.addWidget(QLabel("去掉开头 (A):"))
        self._input_a = QLineEdit()
        self._input_a.setPlaceholderText("如: 110 或 00:01:50")
        self._label_a_preview = QLabel("")
        self._label_a_preview.setStyleSheet("color: gray;")
        head_layout.addWidget(self._input_a)
        head_layout.addWidget(self._label_a_preview)
        trim_layout.addLayout(head_layout)
        
        # 去掉结尾 B
        tail_layout = QHBoxLayout()
        tail_layout.addWidget(QLabel("去掉结尾 (B):"))
        self._input_b = QLineEdit()
        self._input_b.setPlaceholderText("如: 50 或 00:00:50")
        self._label_b_preview = QLabel("")
        self._label_b_preview.setStyleSheet("color: gray;")
        tail_layout.addWidget(self._input_b)
        tail_layout.addWidget(self._label_b_preview)
        trim_layout.addLayout(tail_layout)
        
        main_layout.addWidget(self._trim_widget)
        
        # 绝对起止模式输入区
        self._absolute_widget = QWidget()
        absolute_layout = QVBoxLayout(self._absolute_widget)
        absolute_layout.setContentsMargins(0, 0, 0, 0)
        
        # 开始时间
        start_layout = QHBoxLayout()
        start_layout.addWidget(QLabel("开始时间:"))
        self._input_start = QLineEdit()
        self._input_start.setPlaceholderText("留空表示从头开始")
        self._label_start_preview = QLabel("")
        self._label_start_preview.setStyleSheet("color: gray;")
        start_layout.addWidget(self._input_start)
        start_layout.addWidget(self._label_start_preview)
        absolute_layout.addLayout(start_layout)
        
        # 结束时间
        end_layout = QHBoxLayout()
        end_layout.addWidget(QLabel("结束时间:"))
        self._input_end = QLineEdit()
        self._input_end.setPlaceholderText("留空表示到结尾")
        self._label_end_preview = QLabel("")
        self._label_end_preview.setStyleSheet("color: gray;")
        end_layout.addWidget(self._input_end)
        end_layout.addWidget(self._label_end_preview)
        absolute_layout.addLayout(end_layout)
        
        main_layout.addWidget(self._absolute_widget)
        self._absolute_widget.hide()
        
        # 提示信息
        self._label_hint = QLabel("快速模式：剪切点将自动对齐到最近关键帧（误差±几秒）")
        self._label_hint.setStyleSheet("color: gray; font-size: 11px;")
        self._label_hint.setWordWrap(True)
        main_layout.addWidget(self._label_hint)
    
    def _connect_signals(self):
        """连接信号"""
        self._mode_group.idClicked.connect(self._on_mode_changed)
        
        self._input_a.textChanged.connect(self._on_input_changed)
        self._input_b.textChanged.connect(self._on_input_changed)
        self._input_start.textChanged.connect(self._on_input_changed)
        self._input_end.textChanged.connect(self._on_input_changed)
    
    def _on_mode_changed(self, mode_id: int):
        """模式切换"""
        if mode_id == 0:  # 去头去尾
            self._trim_widget.show()
            self._absolute_widget.hide()
        else:  # 绝对起止
            self._trim_widget.hide()
            self._absolute_widget.show()
        
        self._on_input_changed()
    
    def _on_input_changed(self, text: str = ""):
        """输入变更"""
        self._update_previews()
        self._emit_times()
    
    def _update_previews(self):
        """更新预览标签"""
        # A 预览
        a_val = parse_time_input(self._input_a.text())
        if a_val is not None:
            self._label_a_preview.setText(f"= {format_seconds(a_val)}")
            self._set_input_valid(self._input_a, True)
        elif self._input_a.text().strip() == "":
            self._label_a_preview.setText("(从头)")
            self._set_input_valid(self._input_a, True)
        else:
            self._label_a_preview.setText("格式错误")
            self._set_input_valid(self._input_a, False)
        
        # B 预览
        b_val = parse_time_input(self._input_b.text())
        if b_val is not None:
            self._label_b_preview.setText(f"= {format_seconds(b_val)}")
            self._set_input_valid(self._input_b, True)
        elif self._input_b.text().strip() == "":
            self._label_b_preview.setText("(到结尾)")
            self._set_input_valid(self._input_b, True)
        else:
            self._label_b_preview.setText("格式错误")
            self._set_input_valid(self._input_b, False)
        
        # Start 预览
        start_val = parse_time_input(self._input_start.text())
        if start_val is not None:
            self._label_start_preview.setText(f"= {format_seconds(start_val)}")
            self._set_input_valid(self._input_start, True)
        elif self._input_start.text().strip() == "":
            self._label_start_preview.setText("(00:00:00)")
            self._set_input_valid(self._input_start, True)
        else:
            self._label_start_preview.setText("格式错误")
            self._set_input_valid(self._input_start, False)
        
        # End 预览
        end_val = parse_time_input(self._input_end.text())
        if end_val is not None:
            self._label_end_preview.setText(f"= {format_seconds(end_val)}")
            self._set_input_valid(self._input_end, True)
        elif self._input_end.text().strip() == "":
            self._label_end_preview.setText("(到结尾)")
            self._set_input_valid(self._input_end, True)
        else:
            self._label_end_preview.setText("格式错误")
            self._set_input_valid(self._input_end, False)
    
    def _set_input_valid(self, line_edit: QLineEdit, valid: bool):
        """设置输入框样式（有效/无效）"""
        if valid:
            line_edit.setStyleSheet("")
        else:
            line_edit.setStyleSheet("border: 1px solid red;")
    
    def _emit_times(self):
        """发射时间变更信号"""
        mode = self.get_mode()
        value_a, value_b = self.get_values()
        self.times_changed.emit(mode.value, value_a, value_b)
    
    # ==================== 公共方法 ====================
    
    def get_mode(self) -> TimeMode:
        """获取当前时间模式"""
        if self._radio_trim.isChecked():
            return TimeMode.TRIM_HEAD_TAIL
        return TimeMode.ABSOLUTE
    
    def get_values(self) -> tuple:
        """
        获取当前输入值
        
        Returns:
            (value_a, value_b) 
            去头去尾模式: (去掉开头秒数, 去掉结尾秒数)
            绝对模式: (开始时间秒数, 结束时间秒数)
        """
        mode = self.get_mode()
        
        if mode == TimeMode.TRIM_HEAD_TAIL:
            a = parse_time_input(self._input_a.text())
            b = parse_time_input(self._input_b.text())
            return a, b
        else:
            start = parse_time_input(self._input_start.text())
            end = parse_time_input(self._input_end.text())
            return start, end
    
    def is_valid(self) -> bool:
        """检查当前输入是否有效"""
        if self._radio_trim.isChecked():
            a_text = self._input_a.text().strip()
            b_text = self._input_b.text().strip()
            
            if a_text and parse_time_input(a_text) is None:
                return False
            if b_text and parse_time_input(b_text) is None:
                return False
        else:
            start_text = self._input_start.text().strip()
            end_text = self._input_end.text().strip()
            
            if start_text and parse_time_input(start_text) is None:
                return False
            if end_text and parse_time_input(end_text) is None:
                return False
        
        return True
    
    def set_values(self, mode: TimeMode, value_a=None, value_b=None):
        """
        设置时间值（用于应用预设）
        
        Args:
            mode: 时间模式
            value_a: A 值或开始时间
            value_b: B 值或结束时间
        """
        if mode == TimeMode.TRIM_HEAD_TAIL:
            self._radio_trim.setChecked(True)
            self._trim_widget.show()
            self._absolute_widget.hide()
            
            self._input_a.setText(format_seconds(value_a) if value_a is not None else "")
            self._input_b.setText(format_seconds(value_b) if value_b is not None else "")
        else:
            self._radio_absolute.setChecked(True)
            self._trim_widget.hide()
            self._absolute_widget.show()
            
            self._input_start.setText(format_seconds(value_a) if value_a is not None else "")
            self._input_end.setText(format_seconds(value_b) if value_b is not None else "")
        
        self._update_previews()
    
    def set_precision_hint(self, enabled: bool):
        """设置精确模式提示"""
        if enabled:
            self._label_hint.setText("精确模式：将重编码至关键帧完全对齐（速度较慢）")
        else:
            self._label_hint.setText("快速模式：剪切点将自动对齐到最近关键帧（误差±几秒）")
