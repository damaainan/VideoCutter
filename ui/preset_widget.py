"""
预设控件
预设下拉框、保存/删除按钮
"""
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QComboBox, QPushButton, QMessageBox, QSizePolicy
)
from PySide6.QtCore import Signal

from core.preset_manager import PresetManager, Preset
from core.time_range_calculator import TimeMode


class PresetWidget(QWidget):
    """
    预设控件
    包含预设下拉框和操作按钮
    """
    
    # 信号：预设应用 (模式, A值, B值)
    preset_applied = Signal(str, object, object)
    
    def __init__(self, preset_manager: PresetManager, parent=None):
        super().__init__(parent)
        self._preset_manager = preset_manager
        self._init_ui()
        self._connect_signals()
        self._refresh_list()
    
    def _init_ui(self):
        """初始化界面"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 预设下拉框
        self._combo = QComboBox()
        self._combo.setMinimumWidth(120)
        # self._combo.setSizePolicy(QComboBox.Policy.Expanding, QComboBox.Policy.Fixed)
        # self._combo.setSizePolicy(QComboBox.SizePolicy.Expanding, QComboBox.SizePolicy.Fixed)
        self._combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        layout.addWidget(self._combo)
        
        # 应用按钮
        self._btn_apply = QPushButton("应用")
        self._btn_apply.setToolTip("应用选中的预设")
        layout.addWidget(self._btn_apply)
        
        # 保存按钮
        self._btn_save = QPushButton("保存")
        self._btn_save.setToolTip("保存当前设置为预设")
        layout.addWidget(self._btn_save)
        
        # 删除按钮
        self._btn_delete = QPushButton("删除")
        self._btn_delete.setToolTip("删除选中的预设")
        layout.addWidget(self._btn_delete)
    
    def _connect_signals(self):
        """连接信号"""
        self._btn_apply.clicked.connect(self._on_apply)
        self._btn_save.clicked.connect(self._on_save)
        self._btn_delete.clicked.connect(self._on_delete)
        self._preset_manager.presets_changed.connect(self._refresh_list)
    
    def _refresh_list(self):
        """刷新预设列表"""
        self._combo.clear()
        self._combo.addItem("-- 选择预设 --")
        
        for preset in self._preset_manager.presets:
            name = preset.name
            if preset.is_default:
                name = f"★ {name}"
            self._combo.addItem(name)
    
    def _on_apply(self):
        """应用预设"""
        name = self._combo.currentText()
        name = name.replace("★ ", "")
        
        if name == "-- 选择预设 --" or not name:
            QMessageBox.information(self, "提示", "请先选择一个预设")
            return
        
        preset = self._preset_manager.get_preset(name)
        if preset:
            self.preset_applied.emit(preset.mode.value, preset.value_a, preset.value_b)
    
    def _on_save(self):
        """保存预设（需要外部提供数据）"""
        # 发出保存请求信号
        self.save_requested.emit()
    
    def _on_delete(self):
        """删除预设"""
        name = self._combo.currentText()
        name = name.replace("★ ", "")
        
        if name == "-- 选择预设 --" or not name:
            QMessageBox.information(self, "提示", "请先选择一个预设")
            return
        
        reply = QMessageBox.question(
            self, "确认删除",
            f"确定要删除预设 \"{name}\" 吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self._preset_manager.remove_preset(name)
    
    # 保存请求信号
    save_requested = Signal()
    
    def get_selected_name(self) -> str:
        """获取当前选中的预设名称"""
        name = self._combo.currentText()
        return name.replace("★ ", "")
    
    def set_default_preset(self, name: str):
        """设置默认预设"""
        self._preset_manager.set_default(name)
