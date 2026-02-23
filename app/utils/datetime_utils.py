"""
日期时间相关工具函数
"""

import calendar
from datetime import datetime, date, timedelta, time
from typing import List, Tuple, Optional

import pytz


def get_current_datetime(timezone_str: str = "Asia/Shanghai") -> datetime:
    """
    获取指定时区的当前时间
    
    Args:
        timezone_str: 时区字符串，默认为亚洲/上海
        
    Returns:
        当前时区的datetime对象
    """
    tz = pytz.timezone(timezone_str)
    return datetime.now(tz)


def datetime_to_str(dt: datetime, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    将datetime对象转换为字符串
    
    Args:
        dt: datetime对象
        format_str: 格式字符串
        
    Returns:
        格式化后的时间字符串
    """
    return dt.strftime(format_str)


def str_to_datetime(date_str: str, format_str: str = "%Y-%m-%d %H:%M:%S") -> datetime:
    """
    将字符串转换为datetime对象
    
    Args:
        date_str: 日期字符串
        format_str: 格式字符串
        
    Returns:
        datetime对象
    """
    return datetime.strptime(date_str, format_str)


def date_to_str(dt: date, format_str: str = "%Y-%m-%d") -> str:
    """
    将date对象转换为字符串
    
    Args:
        dt: date对象
        format_str: 格式字符串
        
    Returns:
        格式化后的日期字符串
    """
    return dt.strftime(format_str)


def str_to_date(date_str: str, format_str: str = "%Y-%m-%d") -> date:
    """
    将字符串转换为date对象
    
    Args:
        date_str: 日期字符串
        format_str: 格式字符串
        
    Returns:
        date对象
    """
    return datetime.strptime(date_str, format_str).date()


def get_week_range(dt: Optional[date] = None) -> Tuple[date, date]:
    """
    获取指定日期所在周的开始和结束日期
    
    Args:
        dt: 日期对象，默认为当前日期
        
    Returns:
        (周开始日期, 周结束日期)
    """
    if dt is None:
        dt = date.today()
    
    # 获取本周的第一天（周一）
    start_of_week = dt - timedelta(days=dt.weekday())
    # 获取本周的最后一天（周日）
    end_of_week = start_of_week + timedelta(days=6)
    
    return start_of_week, end_of_week


def get_month_range(dt: Optional[date] = None) -> Tuple[date, date]:
    """
    获取指定日期所在月的开始和结束日期
    
    Args:
        dt: 日期对象，默认为当前日期
        
    Returns:
        (月开始日期, 月结束日期)
    """
    if dt is None:
        dt = date.today()
    
    # 获取本月的第一天
    start_of_month = date(dt.year, dt.month, 1)
    # 获取本月的最后一天
    _, last_day = calendar.monthrange(dt.year, dt.month)
    end_of_month = date(dt.year, dt.month, last_day)
    
    return start_of_month, end_of_month


def get_year_range(dt: Optional[date] = None) -> Tuple[date, date]:
    """
    获取指定日期所在年的开始和结束日期
    
    Args:
        dt: 日期对象，默认为当前日期
        
    Returns:
        (年开始日期, 年结束日期)
    """
    if dt is None:
        dt = date.today()
    
    # 获取本年的第一天
    start_of_year = date(dt.year, 1, 1)
    # 获取本年的最后一天
    end_of_year = date(dt.year, 12, 31)
    
    return start_of_year, end_of_year


def get_workdays_in_month(year: int, month: int) -> List[date]:
    """
    获取指定月份的所有工作日（周一到周五）
    
    Args:
        year: 年份
        month: 月份
        
    Returns:
        工作日日期列表
    """
    workdays = []
    _, last_day = calendar.monthrange(year, month)
    
    for day in range(1, last_day + 1):
        current_date = date(year, month, day)
        # 0-6表示周一到周日
        if current_date.weekday() < 5:
            workdays.append(current_date)
    
    return workdays


def is_holiday(dt: date) -> bool:
    """
    判断是否是节假日（简化版，仅检查周末）
    
    Args:
        dt: 日期对象
        
    Returns:
        是否是节假日
    """
    # 5和6表示周六和周日
    return dt.weekday() >= 5


def calculate_work_hours(start_time: time, end_time: time) -> float:
    """
    计算工作小时数
    
    Args:
        start_time: 开始时间
        end_time: 结束时间
        
    Returns:
        工作小时数
    """
    start_datetime = datetime.combine(date.today(), start_time)
    end_datetime = datetime.combine(date.today(), end_time)
    
    # 处理跨天情况
    if end_time < start_time:
        end_datetime = datetime.combine(date.today() + timedelta(days=1), end_time)
    
    delta = end_datetime - start_datetime
    return delta.total_seconds() / 3600


def get_time_periods() -> List[Tuple[time, time]]:
    """
    获取常用的时间段
    
    Returns:
        时间段列表，每个元素为(开始时间, 结束时间)
    """
    return [
        (time(9, 0), time(12, 0)),    # 上午
        (time(13, 0), time(18, 0)),   # 下午
        (time(9, 0), time(18, 0)),    # 全天
    ]


def format_duration(seconds: float) -> str:
    """
    格式化时长
    
    Args:
        seconds: 秒数
        
    Returns:
        格式化后的时长字符串
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = int(seconds % 60)
    
    if hours > 0:
        return f"{hours}小时{minutes}分钟{seconds}秒"
    elif minutes > 0:
        return f"{minutes}分钟{seconds}秒"
    else:
        return f"{seconds}秒"