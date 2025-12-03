import logging
import os
from datetime import datetime
from config import Config

def setup_logger():
    """设置日志系统"""
    # 确保日志目录存在
    log_dir = os.path.dirname(Config.LOG_FILE)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)
        
    # 配置日志格式，增加更多上下文信息
    log_format = '%(asctime)s - %(name)s - %(funcName)s - %(levelname)s - %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'
    
    # 配置日志处理器
    handlers = []
    
    # 文件处理器
    file_handler = logging.FileHandler(Config.LOG_FILE, encoding='utf-8')
    file_handler.setLevel(getattr(logging, Config.LOG_LEVEL))
    file_handler.setFormatter(logging.Formatter(log_format, date_format))
    handlers.append(file_handler)
    
    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, Config.LOG_LEVEL))
    console_handler.setFormatter(logging.Formatter(log_format, date_format))
    handlers.append(console_handler)
    
    # 配置根日志器
    logging.basicConfig(
        level=getattr(logging, Config.LOG_LEVEL),
        format=log_format,
        datefmt=date_format,
        handlers=handlers
    )
    
    # 设置特定模块的日志级别
    logging.getLogger('aiohttp').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    
def format_duration(seconds: int) -> str:
    """格式化时长"""
    if seconds < 60:
        return f"{seconds}秒"
    minutes = seconds // 60
    seconds = seconds % 60
    if minutes < 60:
        return f"{minutes}分{seconds}秒"
    hours = minutes // 60
    minutes = minutes % 60
    return f"{hours}小时{minutes}分{seconds}秒"

def format_number(num: int) -> str:
    """格式化大数字"""
    if num >= 1000000:
        return f"{num / 1000000:.1f}M"
    elif num >= 1000:
        return f"{num / 1000:.1f}K"
    return str(num)

def save_json_data(data: dict, filename: str) -> bool:
    """保存JSON数据"""
    try:
        import json
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logging.getLogger(__name__).error(f"保存JSON数据失败: {str(e)}")
        return False

def load_json_data(filename: str) -> dict:
    """加载JSON数据"""
    try:
        import json
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    except Exception as e:
        logging.getLogger(__name__).error(f"加载JSON数据失败: {str(e)}")
        return {}
