import logging
from typing import Dict, List, Optional
from datetime import datetime

class GameAnalyzer:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def analyze_match(self, match_data: Dict) -> Optional[Dict]:
        """分析单局游戏数据"""
        try:
            if not match_data or 'info' not in match_data:
                return None
                
            info = match_data['info']
            participants = info.get('participants', [])
            
            # 分析每个玩家
            player_analysis = []
            for participant in participants:
                analysis = self._analyze_player(participant)
                if analysis:
                    player_analysis.append(analysis)
                    
            # 团队分析
            team_analysis = self._analyze_teams(participants)
            
            return {
                'match_id': info.get('gameId'),
                'game_duration': info.get('gameDuration', 0),
                'game_mode': info.get('gameMode', ''),
                'game_type': info.get('gameType', ''),
                'timestamp': datetime.fromtimestamp(info.get('gameCreation', 0) / 1000),
                'player_analysis': player_analysis,
                'team_analysis': team_analysis,
                'total_kills': sum(p.get('kills', 0) for p in participants),
                'total_deaths': sum(p.get('deaths', 0) for p in participants),
                'total_assists': sum(p.get('assists', 0) for p in participants)
            }
            
        except Exception as e:
            self.logger.error(f"对局分析失败: {str(e)}")
            return None
            
    def _analyze_player(self, participant: Dict) -> Optional[Dict]:
        """分析单个玩家表现"""
        try:
            stats = participant.get('stats', {})
            
            # 基础数据
            kills = stats.get('kills', 0)
            deaths = stats.get('deaths', 0)
            assists = stats.get('assists', 0)
            
            # 计算KDA
            kda = self._calculate_kda(kills, deaths, assists)
            
            # 经济表现
            gold_earned = stats.get('goldEarned', 0)
            gold_per_minute = gold_earned / max(participant.get('timePlayed', 1) / 60, 1)
            
            # 伤害表现
            total_damage = stats.get('totalDamageDealtToChampions', 0)
            damage_per_minute = total_damage / max(participant.get('timePlayed', 1) / 60, 1)
            
            # 视野控制
            wards_placed = stats.get('wardsPlaced', 0)
            wards_killed = stats.get('wardsKilled', 0)
            vision_score = stats.get('visionScore', 0)
            
            # 目标控制
            turret_kills = stats.get('turretKills', 0)
            inhibitor_kills = stats.get('inhibitorKills', 0)
            baron_kills = stats.get('baronKills', 0)
            dragon_kills = stats.get('dragonKills', 0)
            
            # 表现评分
            performance_score = self._calculate_performance_score({
                'kda': kda,
                'gold_per_minute': gold_per_minute,
                'damage_per_minute': damage_per_minute,
                'vision_score': vision_score,
                'objective_control': turret_kills + inhibitor_kills + baron_kills + dragon_kills
            })
            
            return {
                'summoner_name': participant.get('summonerName', ''),
                'role': participant.get('individualPosition') or participant.get('teamPosition') or participant.get('role') or participant.get('lane'),
                'champion_name': participant.get('championName', ''),
                'team_id': participant.get('teamId', 0),
                'win': stats.get('win', False),
                'kills': kills,
                'deaths': deaths,
                'assists': assists,
                'kda': kda,
                'gold_earned': gold_earned,
                'gold_per_minute': round(gold_per_minute, 2),
                'total_damage': total_damage,
                'damage_per_minute': round(damage_per_minute, 2),
                'wards_placed': wards_placed,
                'wards_killed': wards_killed,
                'vision_score': vision_score,
                'turret_kills': turret_kills,
                'inhibitor_kills': inhibitor_kills,
                'baron_kills': baron_kills,
                'dragon_kills': dragon_kills,
                'performance_score': performance_score,
                'cs': stats.get('totalMinionsKilled', 0) + stats.get('neutralMinionsKilled', 0),
                'cs_per_minute': round((stats.get('totalMinionsKilled', 0) + stats.get('neutralMinionsKilled', 0)) / max(participant.get('timePlayed', 1) / 60, 1), 2)
            }
            
        except Exception as e:
            self.logger.error(f"玩家分析失败: {str(e)}")
            return None
            
    def _calculate_kda(self, kills: int, deaths: int, assists: int) -> float:
        """计算KDA"""
        if deaths == 0:
            return kills + assists
        return round((kills + assists) / deaths, 2)
        
    def _calculate_performance_score(self, metrics: Dict) -> float:
        """计算综合表现评分 (0-100)"""
        score = 0
        
        # KDA评分 (30分)
        kda = metrics.get('kda', 0)
        if kda >= 5:
            score += 30
        elif kda >= 3:
            score += 25
        elif kda >= 2:
            score += 20
        elif kda >= 1:
            score += 15
        else:
            score += 10
            
        # 经济评分 (20分)
        gpm = metrics.get('gold_per_minute', 0)
        if gpm >= 400:
            score += 20
        elif gpm >= 300:
            score += 15
        elif gpm >= 200:
            score += 10
        else:
            score += 5
            
        # 伤害评分 (20分)
        dpm = metrics.get('damage_per_minute', 0)
        if dpm >= 1000:
            score += 20
        elif dpm >= 600:
            score += 15
        elif dpm >= 300:
            score += 10
        else:
            score += 5
            
        # 视野评分 (15分)
        vision = metrics.get('vision_score', 0)
        if vision >= 50:
            score += 15
        elif vision >= 30:
            score += 12
        elif vision >= 15:
            score += 8
        else:
            score += 4
            
        # 目标控制评分 (15分)
        objectives = metrics.get('objective_control', 0)
        if objectives >= 5:
            score += 15
        elif objectives >= 3:
            score += 12
        elif objectives >= 1:
            score += 8
        else:
            score += 4
            
        return min(score, 100)
        
    def _analyze_teams(self, participants: List[Dict]) -> Dict:
        """分析团队数据"""
        teams = {100: [], 200: []}  # 100蓝队, 200红队
        
        for participant in participants:
            team_id = participant.get('teamId', 100)
            if team_id in teams:
                teams[team_id].append(participant)
                
        team_stats = {}
        for team_id, team_participants in teams.items():
            team_name = "蓝队" if team_id == 100 else "红队"
            
            total_kills = sum(p.get('stats', {}).get('kills', 0) for p in team_participants)
            total_deaths = sum(p.get('stats', {}).get('deaths', 0) for p in team_participants)
            total_assists = sum(p.get('stats', {}).get('assists', 0) for p in team_participants)
            total_gold = sum(p.get('stats', {}).get('goldEarned', 0) for p in team_participants)
            total_damage = sum(p.get('stats', {}).get('totalDamageDealtToChampions', 0) for p in team_participants)
            
            # 计算团队KDA
            team_kda = self._calculate_kda(total_kills, total_deaths, total_assists)
            
            team_stats[team_name] = {
                'team_id': team_id,
                'total_kills': total_kills,
                'total_deaths': total_deaths,
                'total_assists': total_assists,
                'team_kda': team_kda,
                'total_gold': total_gold,
                'total_damage': total_damage,
                'players': [p.get('summonerName', '') for p in team_participants],
                'win': any(p.get('stats', {}).get('win', False) for p in team_participants)
            }
            
        return team_stats
