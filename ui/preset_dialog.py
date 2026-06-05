"""
预设对话框
用于输入预设名称
"""
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton
from PySide6.QtCore import Qt


class PresetDialog(QDialog):
    """
    预设名称输入对话框
    用于保存或重命名预设
    """
    
    def __init__(self, title: str = "保存预设", label: str = "预设名称:", 
                 default_value: str = "", parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(300)
        
        layout = QVBoxLayout(self)
        
        # 标签和输入框
        input_layout = QHBoxLayout()
        input_layout.addWidget(QLabel(label))
        
        self._input = QLineEdit(default_value)
        self._input.setPlaceholderText("输入预设名称")
        input_layout.addWidget(self._input)
        layout.addLayout(input_layout)
        
        # 按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self._btn_ok = QPushButton("确定")
        self._btn_ok.clicked.connect(self.accept)
        btn_layout.addWidget(self._btn_ok)
        
        self._btn_cancel = QPushButton("取消")
        self._btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(self._btn_cancel)
        
        layout.addLayout(btn_layout)
        
        # 回车确定
        self._input.returnPressed.connect(self.accept)
        
        # 聚焦输入框
        self._input.setFocus()
    
    def get_name(self) -> str:
        """获取输入的预设名称"""
        return self._input.text().strip()
    
    def accept(self):
        """确认"""
        if not self.get_name():
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "提示", "请输入预设名称")
            return
        super().accept()
