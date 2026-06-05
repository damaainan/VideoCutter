"""
时间范围计算器模块
根据模式计算 ffmpeg 的 -ss 和 -to 参数
"""
from typing import Optional, Tuple, NamedTuple
from enum import Enum


class TimeMode(Enum):
    """时间模式枚举"""
    TRIM_HEAD_TAIL = "trim"  # 去头去尾模式
    ABSOLUTE = "absolute"  # 绝对起止时间模式


class CutResult(NamedTuple):
    """裁剪计算结果"""
    ss: Optional[float]  # -ss 参数值（秒），None 表示不指定
    to: Optional[float]  # -to 参数值（秒），None 表示不指定
    output_duration: float  # 预计输出时长
    valid: bool  # 是否有效
    error_message: str  # 错误信息（有效时为空）


class TimeRangeCalculator:
    """
    时间范围计算器
    根据用户输入和视频总时长，计算 ffmpeg 裁剪参数
    """
    
    @staticmethod
    def calculate(
        video_duration: float,
        mode: TimeMode,
        value_a: Optional[float] = None,
        value_b: Optional[float] = None
    ) -> CutResult:
        """
        计算裁剪参数
        
        Args:
            video_duration: 视频总时长（秒）
            mode: 时间模式
            value_a: 模式一为去掉开头时长，模式二为开始时间
            value_b: 模式一为去掉结尾时长，模式二为结束时间
            
        Returns:
            CutResult 包含 -ss, -to 参数和预计输出时长
        """
        if video_duration <= 0:
            return CutResult(None, None, 0, False, "视频时长无效")
        
        if mode == TimeMode.TRIM_HEAD_TAIL:
            return TimeRangeCalculator._calculate_trim(video_duration, value_a, value_b)
        elif mode == TimeMode.ABSOLUTE:
            return TimeRangeCalculator._calculate_absolute(video_duration, value_a, value_b)
        else:
            return CutResult(None, None, 0, False, "未知的时间模式")
    
    @staticmethod
    def _calculate_trim(
        video_duration: float,
        trim_head: Optional[float],
        trim_tail: Optional[float]
    ) -> CutResult:
        """
        去头去尾模式计算
        
        Args:
            video_duration: 视频总时长
            trim_head: 去掉开头的时长（A），None 表示不去头
            trim_tail: 去掉结尾的时长（B），None 表示不去尾
            
        Returns:
            计算结果
        """
        head = trim_head if trim_head is not None and trim_head > 0 else 0
        tail = trim_tail if trim_tail is not None and trim_tail > 0 else 0
        
        # 验证约束：A + B < 视频总时长
        if head + tail >= video_duration:
            return CutResult(
                None, None, 0, False,
                f"去头去尾总时长 ({head + tail:.1f}s) 大于等于视频时长 ({video_duration:.1f}s)"
            )
        
        # 计算 -ss 和 -to
        ss = head if head > 0 else None
        to = video_duration - tail if tail > 0 else None
        
        # 计算输出时长
        output_duration = video_duration - head - tail
        
        return CutResult(ss, to, output_duration, True, "")
    
    @staticmethod
    def _calculate_absolute(
        video_duration: float,
        start_time: Optional[float],
        end_time: Optional[float]
    ) -> CutResult:
        """
        绝对起止时间模式计算
        
        Args:
            video_duration: 视频总时长
            start_time: 开始时间，None 表示从头
            end_time: 结束时间，None 表示到结尾
            
        Returns:
            计算结果
        """
        start = start_time if start_time is not None and start_time >= 0 else 0
        end = end_time if end_time is not None else video_duration
        
        # 限制不超过视频时长
        if start > video_duration:
            return CutResult(
                None, None, 0, False,
                f"开始时间 ({start:.1f}s) 超过视频时长 ({video_duration:.1f}s)"
            )
        
        if end > video_duration:
            end = video_duration
        
        # 验证约束：Start < End
        if start >= end:
            return CutResult(
                None, None, 0, False,
                f"开始时间 ({start:.1f}s) 必须小于结束时间 ({end:.1f}s)"
            )
        
        # 计算 -ss 和 -to
        ss = start if start > 0 else None
        to = end if end < video_duration else None
        
        # 计算输出时长
        output_duration = end - start
        
        return CutResult(ss, to, output_duration, True, "")
    
    @staticmethod
    def estimate_output_duration(
        video_duration: float,
        mode: TimeMode,
        value_a: Optional[float] = None,
        value_b: Optional[float] = None
    ) -> Optional[float]:
        """
        估算输出时长（不验证有效性）
        
        Args:
            video_duration: 视频总时长
            mode: 时间模式
            value_a: A 值或开始时间
            value_b: B 值或结束时间
            
        Returns:
            预计输出时长，无法计算时返回 None
        """
        result = TimeRangeCalculator.calculate(video_duration, mode, value_a, value_b)
        return result.output_duration if result.valid else None
