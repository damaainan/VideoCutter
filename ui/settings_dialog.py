"""
设置对话框
配置 ffmpeg 路径、输出后缀、冲突策略等
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QPushButton, QComboBox, QCheckBox,
    QFileDialog, QGroupBox, QMessageBox
)
from PySide6.QtCore import QProcess

from utils.config_manager import ConfigManager


class SettingsDialog(QDialog):
    """
    设置对话框
    提供应用配置修改界面
    """
    
    def __init__(self, config_manager: ConfigManager, parent=None):
        super().__init__(parent)
        self._config = config_manager
        self.setWindowTitle("设置")
        self.setMinimumWidth(450)
        self._init_ui()
        self._load_values()
    
    def _init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout(self)
        
        # FFmpeg 设置组
        ffmpeg_group = QGroupBox("FFmpeg 设置")
        ffmpeg_layout = QFormLayout()
        
        # ffmpeg 路径
        ffmpeg_path_layout = QHBoxLayout()
        self._edit_ffmpeg = QLineEdit()
        ffmpeg_path_layout.addWidget(self._edit_ffmpeg)
        
        self._btn_browse_ffmpeg = QPushButton("浏览...")
        self._btn_browse_ffmpeg.clicked.connect(self._browse_ffmpeg)
        ffmpeg_path_layout.addWidget(self._btn_browse_ffmpeg)
        
        self._btn_test_ffmpeg = QPushButton("测试")
        self._btn_test_ffmpeg.clicked.connect(self._test_ffmpeg)
        ffmpeg_path_layout.addWidget(self._btn_test_ffmpeg)
        
        ffmpeg_layout.addRow("ffmpeg 路径:", ffmpeg_path_layout)
        
        # ffprobe 路径
        ffprobe_path_layout = QHBoxLayout()
        self._edit_ffprobe = QLineEdit()
        ffprobe_path_layout.addWidget(self._edit_ffprobe)
        
        self._btn_browse_ffprobe = QPushButton("浏览...")
        self._btn_browse_ffprobe.clicked.connect(self._browse_ffprobe)
        ffprobe_path_layout.addWidget(self._btn_browse_ffprobe)
        
        self._btn_test_ffprobe = QPushButton("测试")
        self._btn_test_ffprobe.clicked.connect(self._test_ffprobe)
        ffprobe_path_layout.addWidget(self._btn_test_ffprobe)
        
        ffmpeg_layout.addRow("ffprobe 路径:", ffprobe_path_layout)
        
        ffmpeg_group.setLayout(ffmpeg_layout)
        layout.addWidget(ffmpeg_group)
        
        # 输出设置组
        output_group = QGroupBox("输出设置")
        output_layout = QFormLayout()
        
        # 后缀
        self._edit_suffix = QLineEdit()
        output_layout.addRow("输出文件后缀:", self._edit_suffix)
        
        # 冲突策略
        self._combo_conflict = QComboBox()
        self._combo_conflict.addItem("询问", "ask")
        self._combo_conflict.addItem("自动重命名", "rename")
        self._combo_conflict.addItem("跳过", "skip")
        self._combo_conflict.addItem("覆盖", "overwrite")
        output_layout.addRow("文件已存在时:", self._combo_conflict)
        
        output_group.setLayout(output_layout)
        layout.addWidget(output_group)
        
        # 裁剪设置组
        cut_group = QGroupBox("裁剪设置")
        cut_layout = QVBoxLayout()
        
        self._check_precision = QCheckBox("精确模式（重编码至关键帧完全对齐，速度较慢）")
        cut_layout.addWidget(self._check_precision)
        
        self._check_faststart = QCheckBox("MP4 文件启用 faststart（便于网络播放）")
        cut_layout.addWidget(self._check_faststart)
        
        cut_group.setLayout(cut_layout)
        layout.addWidget(cut_group)
        
        # 按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self._btn_ok = QPushButton("确定")
        self._btn_ok.clicked.connect(self._on_accept)
        btn_layout.addWidget(self._btn_ok)
        
        self._btn_cancel = QPushButton("取消")
        self._btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(self._btn_cancel)
        
        self._btn_apply = QPushButton("应用")
        self._btn_apply.clicked.connect(self._on_apply)
        btn_layout.addWidget(self._btn_apply)
        
        layout.addLayout(btn_layout)
    
    def _load_values(self):
        """加载当前配置"""
        self._edit_ffmpeg.setText(self._config.ffmpeg_path)
        self._edit_ffprobe.setText(self._config.ffprobe_path)
        self._edit_suffix.setText(self._config.suffix)
        self._check_precision.setChecked(self._config.precision_mode)
        self._check_faststart.setChecked(self._config.movflags_faststart)
        
        # 设置冲突策略下拉框
        strategy = self._config.conflict_strategy
        for i in range(self._combo_conflict.count()):
            if self._combo_conflict.itemData(i) == strategy:
                self._combo_conflict.setCurrentIndex(i)
                break
    
    def _save_values(self):
        """保存配置"""
        self._config.ffmpeg_path = self._edit_ffmpeg.text().strip()
        self._config.ffprobe_path = self._edit_ffprobe.text().strip()
        
        suffix = self._edit_suffix.text().strip()
        if suffix and not suffix.startswith("_"):
            suffix = "_" + suffix
        self._config.suffix = suffix or "_1"
        
        self._config.conflict_strategy = self._combo_conflict.currentData()
        self._config.precision_mode = self._check_precision.isChecked()
        self._config.movflags_faststart = self._check_faststart.isChecked()
        self._config.sync()
    
    def _browse_ffmpeg(self):
        """浏览选择 ffmpeg"""
        path, _ = QFileDialog.getOpenFileName(self, "选择 ffmpeg", "", "可执行文件 (*)")
        if path:
            self._edit_ffmpeg.setText(path)
    
    def _browse_ffprobe(self):
        """浏览选择 ffprobe"""
        path, _ = QFileDialog.getOpenFileName(self, "选择 ffprobe", "", "可执行文件 (*)")
        if path:
            self._edit_ffprobe.setText(path)
    
    def _test_ffmpeg(self):
        """测试 ffmpeg"""
        path = self._edit_ffmpeg.text().strip() or "ffmpeg"
        process = QProcess()
        process.start(path, ["-version"])
        
        if process.waitForFinished(3000) and process.exitCode() == 0:
            QMessageBox.information(self, "测试成功", f"ffmpeg 可用\n{path}")
        else:
            QMessageBox.warning(self, "测试失败", f"ffmpeg 不可用\n{path}")
    
    def _test_ffprobe(self):
        """测试 ffprobe"""
        path = self._edit_ffprobe.text().strip() or "ffprobe"
        process = QProcess()
        process.start(path, ["-version"])
        
        if process.waitForFinished(3000) and process.exitCode() == 0:
            QMessageBox.information(self, "测试成功", f"ffprobe 可用\n{path}")
        else:
            QMessageBox.warning(self, "测试失败", f"ffprobe 不可用\n{path}")
    
    def _on_accept(self):
        """确定按钮"""
        self._save_values()
        self.accept()
    
    def _on_apply(self):
        """应用按钮"""
        self._save_values()
