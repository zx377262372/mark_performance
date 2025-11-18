import aiohttp
import logging
from typing import Dict, Optional
from config import Config

class WeChatSender:
    def __init__(self):
        self.webhook_url = Config.WECHAT_WEBHOOK_URL
        self.group_name = Config.WECHAT_GROUP_NAME
        self.logger = logging.getLogger(__name__)
        
    async def send_analysis_result(self, analysis_result: Dict) -> bool:
        """发送分析结果到微信群"""
        if not analysis_result or not self.webhook_url:
            return False
            
        try:
            # 格式化消息内容
            message = self._format_message(analysis_result)
            
            if not message:
                return False
                
            # 发送消息
            success = await self._send_to_wechat(message)
            
            if success:
                self.logger.info("分析结果发送成功")
            else:
                self.logger.error("分析结果发送失败")
                
            return success
            
        except Exception as e:
            self.logger.error(f"微信发送失败: {str(e)}")
            return False
            
    def _format_message(self, analysis_result: Dict) -> Optional[str]:
        """格式化分析结果消息"""
        if not analysis_result:
            return None
            
        try:
            # 支持新的结构化返回：优先使用 parsed 字段
            parsed = analysis_result.get('parsed') or analysis_result.get('analysis')
            timestamp = analysis_result.get('timestamp', '')

            message_parts = []
            message_parts.append("🎮 英雄联盟对局复盘分析")
            message_parts.append("=" * 28)

            if isinstance(parsed, dict):
                # summary
                summary = parsed.get('summary', '')
                overall = parsed.get('overall_score')
                if summary:
                    message_parts.append(summary)
                if overall is not None:
                    message_parts.append(f"🔢 综合评分: {overall}/100")

                # key moments (optional)
                km = parsed.get('key_moments', [])
                if km:
                    message_parts.append("")
                    message_parts.append("关键时刻:")
                    for m in km[:3]:
                        message_parts.append(f"- {m}")

                # influencers
                influencers = parsed.get('influencers', [])
                if influencers:
                    # sort by absolute impact descending
                    try:
                        influencers_sorted = sorted(influencers, key=lambda x: abs(x.get('impact_score', 0)), reverse=True)
                    except Exception:
                        influencers_sorted = influencers

                    message_parts.append("")
                    message_parts.append("主要影响者:")
                    for inf in influencers_sorted[:5]:
                        name = inf.get('summoner_name', '')
                        role = inf.get('role', '')
                        label = inf.get('label', '')
                        impact = inf.get('impact_score', 0)
                        conf = inf.get('confidence', 0)
                        reason = inf.get('reason', '')
                        # concise line
                        message_parts.append(f"- {name} ({role}) [{label}] 影响:{impact} 置信度:{conf}%")
                        if reason:
                            message_parts.append(f"  原因: {reason}")

                # player insights (short)
                insights = parsed.get('player_insights', {})
                if insights:
                    message_parts.append("")
                    message_parts.append("简短建议:")
                    cnt = 0
                    for pname, info in insights.items():
                        if cnt >= 5:
                            break
                        short = info.get('short') or ''
                        advice = info.get('advice') or info.get('advice', '') or info.get('suggestion', '')
                        line = f"- {pname}: {short}"
                        if advice:
                            line += f" 建议: {advice}"
                        message_parts.append(line)
                        cnt += 1

                message_parts.append("")
                message_parts.append(f"📊 分析时间: {timestamp}")
                message_parts.append("💡 本分析由AI自动生成，仅供参考")
                return "\n".join(message_parts)

            else:
                # fallback: treat parsed as plain text
                message_parts.append(str(parsed))
                message_parts.append("")
                message_parts.append(f"📊 分析时间: {timestamp}")
                return "\n".join(message_parts)
            
        except Exception as e:
            self.logger.error(f"消息格式化失败: {str(e)}")
            return None
            
    async def _send_to_wechat(self, message: str) -> bool:
        """发送到微信群"""
        if not self.webhook_url:
            self.logger.warning("未配置微信Webhook URL")
            return False
            
        try:
            data = {
                "msgtype": "text",
                "text": {
                    "content": message
                }
            }
            
            # 如果有群名，添加到消息中
            if self.group_name:
                data["text"]["mentioned_list"] = ["@all"]
                
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.webhook_url,
                    json=data,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    
                    if response.status == 200:
                        result = await response.json()
                        return result.get('errcode', -1) == 0
                    else:
                        self.logger.error(f"微信API请求失败: {response.status}")
                        return False
                        
        except Exception as e:
            self.logger.error(f"微信API请求异常: {str(e)}")
            return False
