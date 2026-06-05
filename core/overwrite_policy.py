"""
文件覆盖策略模块
处理输出文件冲突
"""
import os
from typing import Optional, Tuple
from enum import Enum
from PySide6.QtCore import QObject, Signal


class ConflictStrategy(Enum):
    """冲突处理策略"""
    ASK = "ask"  # 询问用户
    RENAME = "rename"  # 自动重命名
    SKIP = "skip"  # 跳过
    OVERWRITE = "overwrite"  # 覆盖


class ConflictAction(Enum):
    """用户选择的冲突处理动作"""
    OVERWRITE = "overwrite"
    RENAME = "rename"
    SKIP = "skip"
    CANCEL = "cancel"  # 取消整个操作


class OverwritePolicy(QObject):
    """
    文件覆盖策略处理器
    根据配置和用户选择决定输出文件路径
    """
    
    # 需要询问用户时发射此信号
    ask_user = Signal(str, str)  # (原路径, 冲突路径)
    
    def __init__(self, default_strategy: ConflictStrategy = ConflictStrategy.ASK,
                 parent: Optional[QObject] = None):
        super().__init__(parent)
        self._default_strategy = default_strategy
        self._user_response: Optional[ConflictAction] = None
    
    @property
    def default_strategy(self) -> ConflictStrategy:
        """获取默认策略"""
        return self._default_strategy
    
    @default_strategy.setter
    def default_strategy(self, value: ConflictStrategy):
        """设置默认策略"""
        self._default_strategy = value
    
    def set_user_response(self, action: ConflictAction):
        """设置用户响应（用于异步询问）"""
        self._user_response = action
    
    def get_output_path(
        self,
        input_path: str,
        suffix: str = "_1",
        strategy: Optional[ConflictStrategy] = None
    ) -> Tuple[Optional[str], str]:
        """
        获取实际输出路径
        
        Args:
            input_path: 输入文件路径
            suffix: 输出文件后缀
            strategy: 使用的策略，None 使用默认策略
            
        Returns:
            (输出路径, 状态)
            状态: "ok" / "skipped" / "cancelled"
        """
        # 构造初始输出路径
        base, ext = os.path.splitext(input_path)
        output_path = f"{base}{suffix}{ext}"
        
        # 文件不存在，直接使用
        if not os.path.exists(output_path):
            return output_path, "ok"
        
        # 使用指定策略或默认策略
        used_strategy = strategy or self._default_strategy
        
        if used_strategy == ConflictStrategy.OVERWRITE:
            return output_path, "ok"
        
        elif used_strategy == ConflictStrategy.SKIP:
            return None, "skipped"
        
        elif used_strategy == ConflictStrategy.RENAME:
            # 自动重命名
            return self._auto_rename(base, ext, suffix), "ok"
        
        elif used_strategy == ConflictStrategy.ASK:
            # 需要同步等待用户响应
            self._user_response = None
            self.ask_user.emit(input_path, output_path)
            
            # 这里简化处理，默认自动重命名
            # 实际应用中应该通过对话框同步获取用户选择
            return self._auto_rename(base, ext, suffix), "ok"
        
        return output_path, "ok"
    
    def _auto_rename(self, base: str, ext: str, suffix: str) -> str:
        """
        自动重命名，尝试 _1, _2, _3... 直到无冲突
        
        Args:
            base: 文件基础名（不含扩展名）
            ext: 扩展名
            suffix: 初始后缀
            
        Returns:
            无冲突的文件路径
        """
        # 提取后缀中的数字部分
        import re
        match = re.match(r'^(.*?)(\d+)$', suffix)
        if match:
            prefix = match.group(1)
            start_num = int(match.group(2))
        else:
            prefix = suffix
            start_num = 1
        
        # 尝试不同的数字
        for num in range(start_num, 1000):
            new_path = f"{base}{prefix}{num}{ext}"
            if not os.path.exists(new_path):
                return new_path
        
        # 极端情况，使用时间戳
        import time
        return f"{base}_{int(time.time())}{ext}"
    
    @staticmethod
    def generate_output_path(input_path: str, suffix: str = "_1") -> str:
        """
        静态方法：生成输出路径（不检查冲突）
        
        Args:
            input_path: 输入文件路径
            suffix: 后缀
            
        Returns:
            输出文件路径
        """
        base, ext = os.path.splitext(input_path)
        return f"{base}{suffix}{ext}"
