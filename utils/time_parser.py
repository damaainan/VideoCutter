"""
时间解析工具模块
支持多种时间格式的解析和格式化
"""
import re
from typing import Optional


def parse_time_input(text: str) -> Optional[float]:
    """
    解析时间输入字符串，返回总秒数
    
    支持格式:
    - 纯数字（秒）: "110", "50.5"
    - HH:MM:SS: "01:30:00"
    - HH:MM:SS.sss: "01:30:00.500"
    - MM:SS: "05:30"
    
    Args:
        text: 时间输入字符串
        
    Returns:
        总秒数（浮点），解析失败返回 None
    """
    if not text or not text.strip():
        return None
    
    text = text.strip()
    
    # 纯数字格式（秒）
    try:
        value = float(text)
        if value >= 0:
            return value
        return None
    except ValueError:
        pass
    
    # HH:MM:SS 或 HH:MM:SS.sss 格式
    pattern_hms = r'^(\d+):(\d{1,2}):(\d{1,2})(?:\.(\d+))?$'
    match = re.match(pattern_hms, text)
    if match:
        hours = int(match.group(1))
        minutes = int(match.group(2))
        seconds = int(match.group(3))
        ms_str = match.group(4)
        
        if minutes >= 60 or seconds >= 60:
            return None
        
        milliseconds = 0.0
        if ms_str:
            milliseconds = int(ms_str) / (10 ** len(ms_str))
        
        return hours * 3600 + minutes * 60 + seconds + milliseconds
    
    # MM:SS 格式
    pattern_ms = r'^(\d+):(\d{1,2})$'
    match = re.match(pattern_ms, text)
    if match:
        minutes = int(match.group(1))
        seconds = int(match.group(2))
        
        if seconds >= 60:
            return None
        
        return minutes * 60 + seconds
    
    return None


def format_seconds(secs: float) -> str:
    """
    将秒数格式化为 HH:MM:SS 显示格式
    
    Args:
        secs: 秒数
        
    Returns:
        格式化后的时间字符串
    """
    if secs < 0:
        secs = 0
    
    total_seconds = int(secs)
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def format_seconds_with_ms(secs: float) -> str:
    """
    将秒数格式化为 HH:MM:SS.sss 显示格式
    
    Args:
        secs: 秒数
        
    Returns:
        格式化后的时间字符串（含毫秒）
    """
    if secs < 0:
        secs = 0
    
    total_seconds = int(secs)
    milliseconds = int((secs - total_seconds) * 1000)
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    
    if milliseconds > 0:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}.{milliseconds:03d}"
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
