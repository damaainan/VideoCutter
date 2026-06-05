#!/usr/bin/env python3
"""
视频极简裁剪工具
主程序入口

功能：
- 批量视频文件导入（拖拽/按钮添加）
- 两种时间模式：去头去尾 / 绝对起止时间
- 预设配置管理
- 无损流复制裁剪（FFmpeg -c copy）
- 精确模式（重编码）
- 批量处理和进度跟踪

使用方法：
    python main.py

依赖：
    - PySide6
    - FFmpeg（需要单独安装）
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from config import get_config
from ui.main_window import MainWindow


def check_dependencies():
    """检查依赖"""
    try:
        import PySide6
        print(f"PySide6 版本: {PySide6.__version__}")
    except ImportError:
        print("错误: 未安装 PySide6")
        print("请运行: pip install PySide6")
        return False
    return True


def setup_application():
    """配置应用程序"""
    app = QApplication(sys.argv)
    
    # 应用信息
    app.setApplicationName("视频极简裁剪工具")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("VideoCutter")
    
    # 全局样式
    app.setStyle("Fusion")
    
    # 可选：设置全局样式表
    app.setStyleSheet("""
        QMainWindow {
            background-color: #f5f5f5;
        }
        QGroupBox {
            font-weight: bold;
            border: 1px solid #ccc;
            border-radius: 5px;
            margin-top: 10px;
            padding-top: 10px;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px;
        }
        QPushButton {
            padding: 5px 15px;
            border-radius: 3px;
        }
        QLineEdit {
            padding: 5px;
            border: 1px solid #ccc;
            border-radius: 3px;
        }
        QLineEdit:focus {
            border-color: #4CAF50;
        }
        QTableWidget {
            gridline-color: #ddd;
        }
        QHeaderView::section {
            background-color: #e0e0e0;
            padding: 5px;
            border: 1px solid #ccc;
        }
        QProgressBar {
            border: 1px solid #ccc;
            border-radius: 3px;
            text-align: center;
        }
        QProgressBar::chunk {
            background-color: #4CAF50;
        }
        QTextEdit {
            background-color: #2b2b2b;
            color: #e0e0e0;
            border: 1px solid #ccc;
        }
    """)
    
    return app


def main():
    """主函数"""
    print("=" * 40)
    print("视频极简裁剪工具 v1.0")
    print("=" * 40)
    
    # 检查依赖
    if not check_dependencies():
        sys.exit(1)
    
    # 创建应用
    app = setup_application()
    
    # 获取配置
    config = get_config()
    print(f"配置文件路径: {config._settings.fileName()}")
    
    # 创建并显示主窗口
    window = MainWindow(config)
    window.show()
    
    print("\n应用程序已启动，请按 Ctrl+C 退出。")
    print("-" * 40)
    
    # 运行事件循环
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
