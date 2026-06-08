"""
自定义时间设置对话框 (v1.1.2)
为单个或多个文件设置独立的裁剪时间
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QRadioButton, QButtonGroup, QLineEdit,
    QGroupBox, QWidget, QComboBox, QMessageBox
)
from PySide6.QtCore import Qt

from utils.time_parser import parse_time_input, format_seconds
from core.time_range_calculator import TimeMode


class CustomTimeDialog(QDialog):
    """
    自定义时间设置对话框
    支持为选中文件设置独立的时间模式和参数
    支持从已保存的预设中快速选择
    """
    
    def __init__(self, file_names: list, current_mode: TimeMode = None,
                 current_a=None, current_b=None, presets=None, parent=None):
        """
        Args:
            file_names: 文件名列表
            current_mode: 当前模式
            current_a: 当前 A 值
            current_b: 当前 B 值
            presets: Preset 对象列表（从 PresetManager 获取）
            parent: 父窗口
        """
        super().__init__(parent)
        self.setWindowTitle("设置自定义时间")
        self.setMinimumWidth(440)
        
        self._file_names = file_names
        self._result_mode = None
        self._result_a = None
        self._result_b = None
        self._presets = presets or []
        
        self._init_ui()
        
        # 设置初始值
        if current_mode is not None:
            self._set_mode(current_mode)
        if current_a is not None:
            self._input_a.setText(format_seconds(current_a))
            self._input_start.setText(format_seconds(current_a))
        if current_b is not None:
            self._input_b.setText(format_seconds(current_b))
            self._input_end.setText(format_seconds(current_b))
    
    def _init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout(self)
        
        # 文件名显示
        count = len(self._file_names)
        if count == 1:
            name_text = self._file_names[0]
            if len(name_text) > 40:
                name_text = name_text[:37] + "..."
            file_label = QLabel(f"文件: {name_text}")
        else:
            file_label = QLabel(f"已选中 {count} 个文件（将统一设置）")
        file_label.setStyleSheet("font-weight: bold; margin-bottom: 5px;")
        layout.addWidget(file_label)
        
        # 预设快速选择（仅在有预设时显示）
        if self._presets:
            preset_group = QGroupBox("从已保存的预设选择")
            preset_layout = QHBoxLayout()
            
            self._combo_preset = QComboBox()
            self._combo_preset.addItem("-- 手动输入 --", None)
            for p in self._presets:
                from utils.time_parser import format_seconds as fs
                mode_label = "去头去尾" if p.mode == TimeMode.TRIM_HEAD_TAIL else "绝对起止"
                a_str = fs(p.value_a) if p.value_a is not None else "空"
                b_str = fs(p.value_b) if p.value_b is not None else "空"
                display = f"{p.name}  ({mode_label}: A={a_str}, B={b_str})"
                self._combo_preset.addItem(display, p)
            
            self._combo_preset.currentIndexChanged.connect(self._on_preset_selected)
            preset_layout.addWidget(self._combo_preset, stretch=1)
            preset_group.setLayout(preset_layout)
            layout.addWidget(preset_group)
        
        # 模式选择
        mode_group = QGroupBox("时间模式")
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
        mode_group.setLayout(mode_layout)
        layout.addWidget(mode_group)
        
        # 去头去尾输入
        self._trim_widget = QWidget()
        trim_layout = QVBoxLayout(self._trim_widget)
        trim_layout.setContentsMargins(0, 0, 0, 0)
        
        head_layout = QHBoxLayout()
        head_layout.addWidget(QLabel("去掉开头 (A):"))
        self._input_a = QLineEdit()
        self._input_a.setPlaceholderText("如: 110 或 00:01:50（留空=不去头）")
        self._preview_a = QLabel("")
        self._preview_a.setStyleSheet("color: gray;")
        head_layout.addWidget(self._input_a, stretch=2)
        head_layout.addWidget(self._preview_a, stretch=1)
        trim_layout.addLayout(head_layout)
        
        tail_layout = QHBoxLayout()
        tail_layout.addWidget(QLabel("去掉结尾 (B):"))
        self._input_b = QLineEdit()
        self._input_b.setPlaceholderText("如: 50 或 00:00:50（留空=不去尾）")
        self._preview_b = QLabel("")
        self._preview_b.setStyleSheet("color: gray;")
        tail_layout.addWidget(self._input_b, stretch=2)
        tail_layout.addWidget(self._preview_b, stretch=1)
        trim_layout.addLayout(tail_layout)
        
        layout.addWidget(self._trim_widget)
        
        # 绝对起止输入
        self._absolute_widget = QWidget()
        abs_layout = QVBoxLayout(self._absolute_widget)
        abs_layout.setContentsMargins(0, 0, 0, 0)
        
        start_layout = QHBoxLayout()
        start_layout.addWidget(QLabel("开始时间:"))
        self._input_start = QLineEdit()
        self._input_start.setPlaceholderText("留空表示从头开始")
        self._preview_start = QLabel("")
        self._preview_start.setStyleSheet("color: gray;")
        start_layout.addWidget(self._input_start, stretch=2)
        start_layout.addWidget(self._preview_start, stretch=1)
        abs_layout.addLayout(start_layout)
        
        end_layout = QHBoxLayout()
        end_layout.addWidget(QLabel("结束时间:"))
        self._input_end = QLineEdit()
        self._input_end.setPlaceholderText("留空表示到结尾")
        self._preview_end = QLabel("")
        self._preview_end.setStyleSheet("color: gray;")
        end_layout.addWidget(self._input_end, stretch=2)
        end_layout.addWidget(self._preview_end, stretch=1)
        abs_layout.addLayout(end_layout)
        
        layout.addWidget(self._absolute_widget)
        self._absolute_widget.hide()
        
        # 按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        btn_ok = QPushButton("确定")
        btn_ok.clicked.connect(self._on_accept)
        btn_layout.addWidget(btn_ok)
        
        btn_cancel = QPushButton("取消")
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_cancel)
        
        layout.addLayout(btn_layout)
        
        # 连接信号
        self._mode_group.idClicked.connect(self._on_mode_changed)
        self._input_a.textChanged.connect(self._update_previews)
        self._input_b.textChanged.connect(self._update_previews)
        self._input_start.textChanged.connect(self._update_previews)
        self._input_end.textChanged.connect(self._update_previews)
    
    def _set_mode(self, mode: TimeMode):
        """设置模式"""
        if mode == TimeMode.TRIM_HEAD_TAIL:
            self._radio_trim.setChecked(True)
            self._trim_widget.show()
            self._absolute_widget.hide()
        else:
            self._radio_absolute.setChecked(True)
            self._trim_widget.hide()
            self._absolute_widget.show()
    
    def _on_mode_changed(self, mode_id: int):
        """模式切换"""
        if mode_id == 0:
            self._trim_widget.show()
            self._absolute_widget.hide()
        else:
            self._trim_widget.hide()
            self._absolute_widget.show()
    
    def _on_preset_selected(self, index: int):
        """从预设下拉框选择预设，自动填充时间字段"""
        preset = self._combo_preset.itemData(index)
        if preset is None:
            return  # "手动输入" 选项
        
        # 设置模式
        self._set_mode(preset.mode)
        
        # 填充时间字段
        if preset.mode == TimeMode.TRIM_HEAD_TAIL:
            self._input_a.setText(format_seconds(preset.value_a) if preset.value_a is not None else "")
            self._input_b.setText(format_seconds(preset.value_b) if preset.value_b is not None else "")
        else:
            self._input_start.setText(format_seconds(preset.value_a) if preset.value_a is not None else "")
            self._input_end.setText(format_seconds(preset.value_b) if preset.value_b is not None else "")
        
        self._update_previews()
    
    def _update_previews(self):
        """更新预览"""
        for input_edit, preview_label in [
            (self._input_a, self._preview_a),
            (self._input_b, self._preview_b),
            (self._input_start, self._preview_start),
            (self._input_end, self._preview_end),
        ]:
            text = input_edit.text().strip()
            if not text:
                preview_label.setText("(空)")
                input_edit.setStyleSheet("")
            else:
                val = parse_time_input(text)
                if val is not None:
                    preview_label.setText(f"= {format_seconds(val)}")
                    input_edit.setStyleSheet("")
                else:
                    preview_label.setText("格式错误")
                    input_edit.setStyleSheet("border: 1px solid red;")
    
    def _on_accept(self):
        """确认"""
        # 验证输入
        if not self._validate():
            return
        
        # 获取结果
        if self._radio_trim.isChecked():
            self._result_mode = TimeMode.TRIM_HEAD_TAIL
            self._result_a = parse_time_input(self._input_a.text())
            self._result_b = parse_time_input(self._input_b.text())
        else:
            self._result_mode = TimeMode.ABSOLUTE
            self._result_a = parse_time_input(self._input_start.text())
            self._result_b = parse_time_input(self._input_end.text())
        
        self.accept()
    
    def _validate(self) -> bool:
        """验证输入"""
        if self._radio_trim.isChecked():
            for edit in [self._input_a, self._input_b]:
                text = edit.text().strip()
                if text and parse_time_input(text) is None:
                    from PySide6.QtWidgets import QMessageBox
                    QMessageBox.warning(self, "输入错误", "请检查时间格式是否正确")
                    return False
        else:
            for edit in [self._input_start, self._input_end]:
                text = edit.text().strip()
                if text and parse_time_input(text) is None:
                    from PySide6.QtWidgets import QMessageBox
                    QMessageBox.warning(self, "输入错误", "请检查时间格式是否正确")
                    return False
        return True
    
    def get_result(self):
        """
        获取用户设置的结果
        
        Returns:
            (mode, value_a, value_b)
        """
        return self._result_mode, self._result_a, self._result_b
