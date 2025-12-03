# 创建 main.py
import asyncio
import logging
from datetime import datetime
from src.riot_api import RiotAPI
from src.game_analyzer import GameAnalyzer
from src.prompt_generator import PromptGenerator
from src.ai_analyzer import AIAnalyzer
from src.wechat_sender import WeChatSender
from src.utils import setup_logger
from config import Config

async def main():
    """主程序入口"""
    setup_logger()
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("开始英雄联盟对局复盘分析...")
        
        # 初始化各模块
        game_analyzer = GameAnalyzer()
        prompt_generator = PromptGenerator()
        
        # 使用上下文管理器管理所有API会话
        async with RiotAPI() as riot_api, AIAnalyzer() as ai_analyzer, WeChatSender() as wechat_sender:
                # 获取最新对局数据
                for summoner_name in Config.SUMMONER_NAMES:
                    if not summoner_name.strip():
                        continue
                        
                    logger.info(f"分析召唤师: {summoner_name}")
                    
                    # 获取最近对局
                    matches = await riot_api.get_recent_matches(summoner_name)
                    
                    for match in matches:
                        match_id = match['matchId']
                        logger.info(f"分析对局: {match_id}")
                        
                        # 获取对局详情
                        match_detail = await riot_api.get_match_detail(match_id)
                        if not match_detail:
                            continue
                        
                        # 分析对局数据
                        analysis_result = game_analyzer.analyze_match(match_detail)
                        if not analysis_result:
                            continue
                        
                        # 生成提示词
                        prompt = prompt_generator.generate_prompt(analysis_result)
                        if not prompt:
                            continue
                        
                        # AI分析评分
                        ai_result = await ai_analyzer.analyze_performance(prompt)
                        if not ai_result:
                            continue
                        
                        # 发送到微信群
                        success = await wechat_sender.send_analysis_result(ai_result)
                        if success:
                            logger.info(f"对局 {match_id} 分析完成并发送成功")
                        else:
                            logger.error(f"对局 {match_id} 分析完成但发送失败")
                
    except Exception as e:
        logger.error(f"程序执行失败: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
