# 简单测试脚本
import sys
print(f"Python版本: {sys.version}")

try:
    from config import Config
    print("成功导入Config类")
except Exception as e:
    print(f"导入Config类失败: {e}")

try:
    from src.utils import setup_logger
    print("成功导入setup_logger函数")
except Exception as e:
    print(f"导入setup_logger函数失败: {e}")

try:
    from src.prompt_generator import PromptGenerator
    print("成功导入PromptGenerator类")
except Exception as e:
    print(f"导入PromptGenerator类失败: {e}")

try:
    from src.riot_api import RiotAPI
    print("成功导入RiotAPI类")
except Exception as e:
    print(f"导入RiotAPI类失败: {e}")

try:
    from src.game_analyzer import GameAnalyzer
    print("成功导入GameAnalyzer类")
except Exception as e:
    print(f"导入GameAnalyzer类失败: {e}")

try:
    from src.ai_analyzer import AIAnalyzer
    print("成功导入AIAnalyzer类")
except Exception as e:
    print(f"导入AIAnalyzer类失败: {e}")

try:
    from src.wechat_sender import WeChatSender
    print("成功导入WeChatSender类")
except Exception as e:
    print(f"导入WeChatSender类失败: {e}")