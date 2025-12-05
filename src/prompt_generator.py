import logging
from typing import Dict, Optional


class PromptGenerator:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def generate_prompt(self, analysis_result: Dict) -> Optional[str]:
        """生成AI分析提示词（请求严格JSON输出）

        目标：让大模型识别并标注出对本局输赢影响最大的玩家（例如："carried"、"fed"（送）、"trolling"（混）、"neutral"），给出原因、影响分（-100 ~ 100）和置信度。
        要求模型只返回一个纯JSON对象，不要添加说明性文字。

        返回格式（JSON schema 示例）：
        {
          "match_id": "...",
          "summary": "简短中文一句话概述",
          "overall_score": 75,
          "key_moments": ["XX分钟 小规模团战 A被抓 死亡 导致一塔丢失"],
          "influencers": [
            {
              "summoner_name": "玩家A",
              "role": "中单",
              "label": "carried|fed|trolling|neutral",
              "reason": "短句说明为何判定",
              "impact_score": 40,          # 正数为正向影响，负数为负向影响
              "confidence": 92            # 0-100
            }
          ],
          "player_insights": {
            "玩家A": {"label":"carried","short":"进行了多次关键击杀","advice":"继续保持对视野的控制"}
          }
        }

        """
        try:
            if not analysis_result:
                return None

            # 提取关键数据，构建结构化提示词
            match_id = analysis_result.get("match_id", "unknown")
            game_duration = analysis_result.get("game_duration", 0)
            game_mode = analysis_result.get("game_mode", "unknown")
            player_analysis = analysis_result.get("player_analysis", [])
            team_analysis = analysis_result.get("team_analysis", {})

            # 创建玩家数据列表
            players_data = []
            for p in player_analysis:
                players_data.append({
                    "summoner_name": p.get("summoner_name", ""),
                    "champion": p.get("champion_name", ""),
                    "role": p.get("role", "unknown"),
                    "kills": p.get("kills", 0),
                    "deaths": p.get("deaths", 0),
                    "assists": p.get("assists", 0),
                    "kda": p.get("kda", 0),
                    "gold_per_minute": p.get("gold_per_minute", 0),
                    "damage_per_minute": p.get("damage_per_minute", 0),
                    "vision_score": p.get("vision_score", 0),
                    "performance_score": p.get("performance_score", 0)
                })

            # 创建团队数据
            teams_data = {}
            for tname, tdata in team_analysis.items():
                teams_data[tname] = {
                    "total_kills": tdata.get("total_kills", 0),
                    "total_deaths": tdata.get("total_deaths", 0),
                    "win": bool(tdata.get("win"))
                }

            # 构建完整数据对象
            data = {
                "match_id": match_id,
                "game_duration": game_duration,
                "game_mode": game_mode,
                "players": players_data,
                "teams": teams_data
            }

            # 使用json模块格式化数据，确保格式正确
            import json
            formatted_data = json.dumps(data, ensure_ascii=False, indent=2)

            # 构建提示词
            prompt_parts = [
                "数据如下（JSON）：",
                formatted_data,
                "",
                "请基于上述数据，严格返回一个单独的JSON对象（不要在前后添加任何多余文字）。",
                "JSON必须包含字段：match_id, summary, overall_score(0-100), key_moments(list), influencers(list of objects), player_insights(object)。",
                "对每个influencer对象，必须包含：summoner_name, role, label（carried|fed|trolling|neutral）, reason, impact_score(-100~100), confidence(0-100)。",
                "请用中文短句给出reason和summary。尽量保持JSON紧凑。",
                "如果无法判断某玩家，使用label=\"neutral\"并给出简短说明。"
            ]

            return "\n".join(prompt_parts)

        except Exception as e:
            self.logger.error(f"提示词生成失败: {str(e)}")
            return None

    def _format_duration(self, seconds: int) -> str:
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{minutes}分{seconds}秒"
