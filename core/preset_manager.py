"""
预设管理器模块
管理裁剪预设的增删改查和持久化
"""
import json
import os
from typing import Optional, List, Dict, Any
from PySide6.QtCore import QObject, Signal
from core.time_range_calculator import TimeMode


class Preset:
    """预设数据类"""
    
    def __init__(
        self,
        name: str,
        mode: TimeMode,
        value_a: Optional[float] = None,
        value_b: Optional[float] = None,
        is_default: bool = False
    ):
        self.name = name
        self.mode = mode
        self.value_a = value_a
        self.value_b = value_b
        self.is_default = is_default
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "mode": self.mode.value,
            "value_a": self.value_a,
            "value_b": self.value_b,
            "is_default": self.is_default
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Preset":
        """从字典创建"""
        mode = TimeMode(data.get("mode", "trim"))
        return cls(
            name=data.get("name", ""),
            mode=mode,
            value_a=data.get("value_a"),
            value_b=data.get("value_b"),
            is_default=data.get("is_default", False)
        )
    
    def __repr__(self) -> str:
        return f"Preset({self.name}, {self.mode.value}, a={self.value_a}, b={self.value_b})"


class PresetManager(QObject):
    """
    预设管理器
    管理预设的增删改查，支持 JSON 文件持久化
    """
    
    preset_added = Signal(str)  # 预设名称
    preset_removed = Signal(str)  # 预设名称
    preset_updated = Signal(str)  # 预设名称
    presets_changed = Signal()  # 预设列表变更
    default_changed = Signal(str)  # 新的默认预设名称
    
    def __init__(self, presets_path: str, parent: Optional[QObject] = None):
        super().__init__(parent)
        self._presets_path = presets_path
        self._presets: Dict[str, Preset] = {}
        self._load()
    
    @property
    def presets(self) -> List[Preset]:
        """获取所有预设列表"""
        return list(self._presets.values())
    
    @property
    def preset_names(self) -> List[str]:
        """获取所有预设名称"""
        return list(self._presets.keys())
    
    @property
    def default_preset(self) -> Optional[Preset]:
        """获取默认预设"""
        for preset in self._presets.values():
            if preset.is_default:
                return preset
        return None
    
    def get_preset(self, name: str) -> Optional[Preset]:
        """获取指定名称的预设"""
        return self._presets.get(name)
    
    def add_preset(self, preset: Preset) -> bool:
        """
        添加预设
        
        Args:
            preset: 预设对象
            
        Returns:
            是否添加成功
        """
        if not preset.name:
            return False
        
        # 如果已有同名预设，更新它
        if preset.name in self._presets:
            self._presets[preset.name] = preset
            self.preset_updated.emit(preset.name)
        else:
            self._presets[preset.name] = preset
            self.preset_added.emit(preset.name)
        
        # 如果设为默认，取消其他默认
        if preset.is_default:
            self._clear_other_defaults(preset.name)
        
        self._save()
        self.presets_changed.emit()
        return True
    
    def remove_preset(self, name: str) -> bool:
        """
        删除预设
        
        Args:
            name: 预设名称
            
        Returns:
            是否删除成功
        """
        if name not in self._presets:
            return False
        
        del self._presets[name]
        self.preset_removed.emit(name)
        self._save()
        self.presets_changed.emit()
        return True
    
    def rename_preset(self, old_name: str, new_name: str) -> bool:
        """
        重命名预设
        
        Args:
            old_name: 原名称
            new_name: 新名称
            
        Returns:
            是否重命名成功
        """
        if old_name not in self._presets or not new_name:
            return False
        
        if new_name in self._presets and new_name != old_name:
            return False
        
        preset = self._presets.pop(old_name)
        preset.name = new_name
        self._presets[new_name] = preset
        
        self.preset_removed.emit(old_name)
        self.preset_added.emit(new_name)
        self._save()
        self.presets_changed.emit()
        return True
    
    def set_default(self, name: str) -> bool:
        """
        设置默认预设
        
        Args:
            name: 预设名称，空字符串清除默认
            
        Returns:
            是否设置成功
        """
        if not name:
            # 清除所有默认
            for preset in self._presets.values():
                preset.is_default = False
            self.default_changed.emit("")
            self._save()
            return True
        
        if name not in self._presets:
            return False
        
        self._clear_other_defaults(name)
        self._presets[name].is_default = True
        self.default_changed.emit(name)
        self._save()
        return True
    
    def _clear_other_defaults(self, except_name: str):
        """清除其他预设的默认标记"""
        for name, preset in self._presets.items():
            if name != except_name:
                preset.is_default = False
    
    def _load(self):
        """从文件加载预设"""
        if not os.path.exists(self._presets_path):
            return
        
        try:
            with open(self._presets_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            if isinstance(data, list):
                for item in data:
                    preset = Preset.from_dict(item)
                    if preset.name:
                        self._presets[preset.name] = preset
        except (json.JSONDecodeError, IOError, KeyError):
            pass
    
    def _save(self):
        """保存预设到文件"""
        try:
            # 确保目录存在
            dir_path = os.path.dirname(self._presets_path)
            if dir_path and not os.path.exists(dir_path):
                os.makedirs(dir_path, exist_ok=True)
            
            data = [preset.to_dict() for preset in self._presets.values()]
            
            with open(self._presets_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except IOError:
            pass
