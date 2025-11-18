import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Riot API配置
    RIOT_API_KEY = os.getenv('RIOT_API_KEY', '')
    RIOT_API_BASE_URL = 'https://kr.api.riotgames.com'
    
    # AI模型配置
    AI_API_KEY = os.getenv('AI_API_KEY', '')
    AI_API_BASE_URL = os.getenv('AI_API_BASE_URL', 'https://api.openai.com/v1')
    AI_MODEL = os.getenv('AI_MODEL', 'gpt-3.5-turbo')
    
    # 微信配置
    WECHAT_WEBHOOK_URL = os.getenv('WECHAT_WEBHOOK_URL', '')
    WECHAT_GROUP_NAME = os.getenv('WECHAT_GROUP_NAME', '')
    
    # 游戏配置
    GAME_REGION = os.getenv('GAME_REGION', 'KR')
    SUMMONER_NAMES = os.getenv('SUMMONER_NAMES', '').split(',')
    
    # 日志配置
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = 'logs/lol_analysis.log'
    
    # 数据配置
    DATA_DIR = 'data'
    CACHE_EXPIRY = 3600  # 缓存过期时间（秒）
