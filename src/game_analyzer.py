import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from math import ceil

class GameAnalyzer:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        # 位置权重配置
        self.role_weights = {
            "TOP": {
                "kda": 0.2,
                "damage": 0.2,
                "gold": 0.15,
                "cs": 0.15,
                "vision": 0.1,
                "kill_participation": 0.1,
                "damage_share": 0.1
            },
            "JUNGLE": {
                "kda": 0.2,
                "damage": 0.15,
                "gold": 0.15,
                "cs": 0.1,
                "vision": 0.15,
                "kill_participation": 0.2,
                "damage_share": 0.05
            },
            "MIDDLE": {
                "kda": 0.2,
                "damage": 0.25,
                "gold": 0.15,
                "cs": 0.15,
                "vision": 0.1,
                "kill_participation": 0.1,
                "damage_share": 0.05
            },
            "BOTTOM": {
                "kda": 0.2,
                "damage": 0.25,
                "gold": 0.2,
                "cs": 0.15,
                "vision": 0.05,
                "kill_participation": 0.1,
                "damage_share": 0.05
            },
            "UTILITY": {
                "kda": 0.15,
                "damage": 0.1,
                "gold": 0.1,
                "cs": 0.05,
                "vision": 0.3,
                "kill_participation": 0.2,
                "damage_share": 0.1
            },
            "UNKNOWN": {
                "kda": 0.2,
                "damage": 0.2,
                "gold": 0.15,
                "cs": 0.15,
                "vision": 0.1,
                "kill_participation": 0.1,
                "damage_share": 0.1
            }
        }

    def analyze_match(self, match_data: Dict) -> Optional[Dict]:
        """
        分析单局游戏数据
        """
        try:
            if not match_data or 'info' not in match_data:
                self.logger.warning("无效的对局数据: 缺少'info'字段")
                return None
                
            info = match_data['info']
            participants = info.get('participants', [])
            match_id = info.get('gameId')
            
            self.logger.debug(f"开始分析对局 {match_id}，共有 {len(participants)} 名玩家")
            
            # 先进行团队分析，获取团队数据用于玩家分析
            team_analysis = self._analyze_teams(participants)
            
            # 分析每个玩家，传入团队数据
            player_analysis = []
            for participant in participants:
                team_id = participant.get('teamId', 100)
                team_name = "蓝队" if team_id == 100 else "红队"
                team_data = team_analysis.get(team_name, {})
                
                analysis = self._analyze_player(participant, team_data)
                if analysis:
                    player_analysis.append(analysis)
            
            self.logger.debug(f"完成玩家分析，共分析 {len(player_analysis)} 名玩家")
            
            # 计算额外的对局统计数据
            total_kills = sum(p.get('stats', {}).get('kills', 0) for p in participants)
            total_deaths = sum(p.get('stats', {}).get('deaths', 0) for p in participants)
            total_assists = sum(p.get('stats', {}).get('assists', 0) for p in participants)
            
            # 计算对局的平均数据
            avg_gpm = sum(p.get('gold_per_minute', 0) for p in player_analysis) / max(len(player_analysis), 1)
            avg_dpm = sum(p.get('damage_per_minute', 0) for p in player_analysis) / max(len(player_analysis), 1)
            avg_cspm = sum(p.get('cs_per_minute', 0) for p in player_analysis) / max(len(player_analysis), 1)
            
            result = {
                'match_id': match_id,
                'game_duration': info.get('gameDuration', 0),
                'game_duration_minutes': round(info.get('gameDuration', 0) / 60, 2),
                'game_mode': info.get('gameMode', ''),
                'game_type': info.get('gameType', ''),
                'timestamp': datetime.fromtimestamp(info.get('gameCreation', 0) / 1000),
                'player_analysis': player_analysis,
                'team_analysis': team_analysis,
                'total_kills': total_kills,
                'total_deaths': total_deaths,
                'total_assists': total_assists,
                'avg_gold_per_minute': round(avg_gpm, 2),
                'avg_damage_per_minute': round(avg_dpm, 2),
                'avg_cs_per_minute': round(avg_cspm, 2),
                'total_minions_killed': sum(p.get('stats', {}).get('totalMinionsKilled', 0) for p in participants),
                'total_neutral_minions_killed': sum(p.get('stats', {}).get('neutralMinionsKilled', 0) for p in participants)
            }
            
            self.logger.info(f"成功完成对局 {match_id} 的分析")
            return result
            
        except Exception as e:
            self.logger.error(f"对局分析失败: {str(e)}", exc_info=True)
            return None

    def _analyze_player(self, participant: Dict, team_data: Optional[Dict] = None) -> Optional[Dict]:
        """
        分析单个玩家表现
        
        Args:
            participant: 玩家数据
            team_data: 团队数据（用于计算占比等指标）
        """
        try:
            summoner_name = participant.get('summonerName', '未知')
            champion_name = participant.get('championName', '未知')
            
            self.logger.debug(f"分析玩家 {summoner_name} ({champion_name})")
            
            stats = participant.get('stats', {})
            
            # 基础数据
            kills = stats.get('kills', 0)
            deaths = stats.get('deaths', 0)
            assists = stats.get('assists', 0)
            
            # 计算KDA
            kda = self._calculate_kda(kills, deaths, assists)
            
            # 计算每分钟数据
            time_played = max(participant.get('timePlayed', 1), 1)  # 避免除以0
            minutes = time_played / 60
            
            # 经济表现
            gold_earned = stats.get('goldEarned', 0)
            gold_per_minute = gold_earned / minutes
            
            # 伤害表现
            total_damage = stats.get('totalDamageDealtToChampions', 0)
            damage_per_minute = total_damage / minutes
            
            # 视野控制
            wards_placed = stats.get('wardsPlaced', 0)
            wards_killed = stats.get('wardsKilled', 0)
            vision_score = stats.get('visionScore', 0)
            vision_per_minute = vision_score / minutes
            
            # 补刀表现
            total_cs = stats.get('totalMinionsKilled', 0) + stats.get('neutralMinionsKilled', 0)
            cs_per_minute = total_cs / minutes
            
            # 目标控制
            turret_kills = stats.get('turretKills', 0)
            inhibitor_kills = stats.get('inhibitorKills', 0)
            baron_kills = stats.get('baronKills', 0)
            dragon_kills = stats.get('dragonKills', 0)
            objective_control = turret_kills + inhibitor_kills + baron_kills + dragon_kills
            
            # 计算团队占比指标
            damage_share = 0
            gold_share = 0
            kill_participation = 0
            
            if team_data:
                if team_data['total_damage'] > 0:
                    damage_share = (total_damage / team_data['total_damage']) * 100
                
                if team_data['total_gold'] > 0:
                    gold_share = (gold_earned / team_data['total_gold']) * 100
                
                if team_data['total_kills_assists'] > 0:
                    kill_participation = ((kills + assists) / team_data['total_kills_assists']) * 100
            
            # 获取玩家位置
            role = (participant.get('individualPosition') or 
                   participant.get('teamPosition') or 
                   participant.get('role') or 
                   participant.get('lane') or "UNKNOWN").upper()
            
            # 表现评分
            performance_score = self._calculate_performance_score({
                'kda': kda,
                'gold_per_minute': gold_per_minute,
                'damage_per_minute': damage_per_minute,
                'vision_score': vision_score,
                'vision_per_minute': vision_per_minute,
                'objective_control': objective_control,
                'kill_participation': kill_participation,
                'damage_share': damage_share,
                'cs_per_minute': cs_per_minute
            }, role)
            
            # 识别优势和不足
            strengths, weaknesses = self._identify_strengths_and_weaknesses({
                'kda': kda,
                'gold_per_minute': gold_per_minute,
                'damage_per_minute': damage_per_minute,
                'vision_per_minute': vision_per_minute,
                'cs_per_minute': cs_per_minute,
                'kill_participation': kill_participation,
                'damage_share': damage_share
            }, role)
            
            return {
                'summoner_name': participant.get('summonerName', ''),
                'role': role,
                'champion_name': participant.get('championName', ''),
                'team_id': participant.get('teamId', 0),
                'win': stats.get('win', False),
                'kills': kills,
                'deaths': deaths,
                'assists': assists,
                'kda': kda,
                'gold_earned': gold_earned,
                'gold_per_minute': round(gold_per_minute, 2),
                'gold_share': round(gold_share, 2),
                'total_damage': total_damage,
                'damage_per_minute': round(damage_per_minute, 2),
                'damage_share': round(damage_share, 2),
                'kill_participation': round(kill_participation, 2),
                'wards_placed': wards_placed,
                'wards_killed': wards_killed,
                'vision_score': vision_score,
                'vision_per_minute': round(vision_per_minute, 2),
                'cs': total_cs,
                'cs_per_minute': round(cs_per_minute, 2),
                'turret_kills': turret_kills,
                'inhibitor_kills': inhibitor_kills,
                'baron_kills': baron_kills,
                'dragon_kills': dragon_kills,
                'objective_control': objective_control,
                'performance_score': performance_score,
                'performance_grade': self._get_grade(performance_score),
                'strengths': strengths,
                'weaknesses': weaknesses,
                'time_played': time_played
            }
            
        except Exception as e:
            self.logger.error(f"玩家分析失败: {str(e)}", exc_info=True)
            return None

    def _calculate_kda(self, kills: int, deaths: int, assists: int) -> float:
        """
        计算KDA
        """
        if deaths == 0:
            return kills + assists
        return round((kills + assists) / deaths, 2)

    def _calculate_performance_score(self, metrics: Dict, role: str) -> float:
        """
        计算综合表现评分 (0-100)，考虑位置权重
        
        Args:
            metrics: 统计指标字典
            role: 玩家位置
        """
        # 获取位置对应的权重
        weights = self.role_weights.get(role, self.role_weights["UNKNOWN"])
        
        # 计算各项得分
        kda_score = self._calculate_kda_score(metrics.get('kda', 0))
        gold_score = self._calculate_gold_score(metrics.get('gold_per_minute', 0))
        damage_score = self._calculate_damage_score(metrics.get('damage_per_minute', 0))
        vision_score = self._calculate_vision_score(metrics.get('vision_per_minute', 0))
        cs_score = self._calculate_cs_score(metrics.get('cs_per_minute', 0))
        kill_participation_score = self._calculate_kill_participation_score(metrics.get('kill_participation', 0))
        damage_share_score = self._calculate_damage_share_score(metrics.get('damage_share', 0))
        
        # 根据权重计算综合得分
        total_score = (
            kda_score * weights["kda"] +
            gold_score * weights["gold"] +
            damage_score * weights["damage"] +
            vision_score * weights["vision"] +
            cs_score * weights["cs"] +
            kill_participation_score * weights["kill_participation"] +
            damage_share_score * weights["damage_share"]
        )
        
        return min(round(total_score, 2), 100)
    
    def _calculate_kda_score(self, kda: float) -> float:
        """
        计算KDA得分 (0-100)
        """
        if kda >= 15:
            return 100
        elif kda >= 12:
            return 95
        elif kda >= 10:
            return 90
        elif kda >= 8:
            return 85
        elif kda >= 7:
            return 80
        elif kda >= 6:
            return 75
        elif kda >= 5:
            return 70
        elif kda >= 4:
            return 65
        elif kda >= 3:
            return 60
        elif kda >= 2:
            return 50
        elif kda >= 1:
            return 40
        elif kda >= 0.5:
            return 30
        else:
            return 20
    
    def _calculate_gold_score(self, gold_per_minute: float) -> float:
        """
        计算经济得分 (0-100)
        """
        if gold_per_minute >= 450:
            return 100
        elif gold_per_minute >= 400:
            return 90
        elif gold_per_minute >= 350:
            return 80
        elif gold_per_minute >= 300:
            return 70
        elif gold_per_minute >= 250:
            return 60
        elif gold_per_minute >= 200:
            return 50
        elif gold_per_minute >= 150:
            return 40
        else:
            return 30
    
    def _calculate_damage_score(self, damage_per_minute: float) -> float:
        """
        计算伤害得分 (0-100)
        """
        if damage_per_minute >= 800:
            return 100
        elif damage_per_minute >= 700:
            return 90
        elif damage_per_minute >= 600:
            return 80
        elif damage_per_minute >= 500:
            return 70
        elif damage_per_minute >= 400:
            return 60
        elif damage_per_minute >= 300:
            return 50
        elif damage_per_minute >= 200:
            return 40
        else:
            return 30
    
    def _calculate_vision_score(self, vision_per_minute: float) -> float:
        """
        计算视野得分 (0-100)
        """
        if vision_per_minute >= 2.5:
            return 100
        elif vision_per_minute >= 2:
            return 90
        elif vision_per_minute >= 1.5:
            return 80
        elif vision_per_minute >= 1:
            return 70
        elif vision_per_minute >= 0.8:
            return 60
        elif vision_per_minute >= 0.5:
            return 50
        else:
            return 30
    
    def _calculate_cs_score(self, cs_per_minute: float) -> float:
        """
        计算补刀得分 (0-100)
        """
        if cs_per_minute >= 9:
            return 100
        elif cs_per_minute >= 8:
            return 90
        elif cs_per_minute >= 7:
            return 80
        elif cs_per_minute >= 6:
            return 70
        elif cs_per_minute >= 5:
            return 60
        elif cs_per_minute >= 4:
            return 50
        elif cs_per_minute >= 3:
            return 40
        else:
            return 30
    
    def _calculate_kill_participation_score(self, kill_participation: float) -> float:
        """
        计算参与击杀率得分 (0-100)
        """
        if kill_participation >= 90:
            return 100
        elif kill_participation >= 80:
            return 90
        elif kill_participation >= 70:
            return 80
        elif kill_participation >= 60:
            return 70
        elif kill_participation >= 50:
            return 60
        elif kill_participation >= 40:
            return 50
        elif kill_participation >= 30:
            return 40
        else:
            return 30
    
    def _calculate_damage_share_score(self, damage_share: float) -> float:
        """
        计算伤害占比得分 (0-100)
        """
        if damage_share >= 40:
            return 100
        elif damage_share >= 35:
            return 90
        elif damage_share >= 30:
            return 80
        elif damage_share >= 25:
            return 70
        elif damage_share >= 20:
            return 60
        elif damage_share >= 15:
            return 50
        elif damage_share >= 10:
            return 40
        else:
            return 30
    
    def _identify_strengths_and_weaknesses(self, metrics: Dict, role: str) -> Tuple[List[str], List[str]]:
        """
        识别玩家的优势和不足
        
        Args:
            metrics: 统计指标字典
            role: 玩家位置
        
        Returns:
            (优势列表, 不足列表)
        """
        strengths = []
        weaknesses = []
        
        # KDA分析
        if metrics['kda'] >= 10:
            strengths.append("极高的KDA表现")
        elif metrics['kda'] >= 7:
            strengths.append("优秀的KDA表现")
        elif metrics['kda'] <= 1:
            weaknesses.append("KDA表现不佳，需要注意生存")
        
        # 经济分析
        if metrics['gold_per_minute'] >= 400:
            strengths.append("优秀的经济发育")
        elif metrics['gold_per_minute'] <= 200:
            weaknesses.append("经济发育需要提高")
        
        # 伤害分析
        if metrics['damage_per_minute'] >= 700:
            strengths.append("极高的伤害输出")
        elif metrics['damage_per_minute'] >= 500:
            strengths.append("优秀的伤害输出")
        elif metrics['damage_per_minute'] <= 300:
            weaknesses.append("伤害输出需要提高")
        
        # 补刀分析
        if metrics['cs_per_minute'] >= 8:
            strengths.append("优秀的补刀节奏")
        elif metrics['cs_per_minute'] <= 4:
            weaknesses.append("补刀节奏需要提高")
        
        # 视野分析
        if metrics['vision_per_minute'] >= 2:
            strengths.append("优秀的视野控制")
        elif metrics['vision_per_minute'] <= 0.5:
            weaknesses.append("视野控制需要加强")
        
        # 击杀参与度分析
        if metrics['kill_participation'] >= 80:
            strengths.append("极高的团队参与度")
        elif metrics['kill_participation'] <= 40:
            weaknesses.append("团队参与度需要提高")
        
        # 伤害占比分析
        if metrics['damage_share'] >= 35:
            strengths.append("团队核心输出")
        elif metrics['damage_share'] <= 15:
            weaknesses.append("伤害贡献需要提高")
        
        return strengths, weaknesses
    
    def _get_grade(self, score: float) -> str:
        """
        根据得分获取等级评价
        """
        if score >= 95:
            return "S+"
        elif score >= 90:
            return "S"
        elif score >= 85:
            return "A+"
        elif score >= 80:
            return "A"
        elif score >= 75:
            return "B+"
        elif score >= 70:
            return "B"
        elif score >= 65:
            return "C+"
        elif score >= 60:
            return "C"
        elif score >= 50:
            return "D"
        else:
            return "F"

    def _analyze_teams(self, participants: List[Dict]) -> Dict:
        """
        分析团队数据
        """
        teams = {100: [], 200: []}  # 100蓝队, 200红队
        
        for participant in participants:
            team_id = participant.get('teamId', 100)
            if team_id in teams:
                teams[team_id].append(participant)
                
        team_stats = {}
        for team_id, team_participants in teams.items():
            team_name = "蓝队" if team_id == 100 else "红队"
            
            # 计算基础数据
            total_kills = sum(p.get('stats', {}).get('kills', 0) for p in team_participants)
            total_deaths = sum(p.get('stats', {}).get('deaths', 0) for p in team_participants)
            total_assists = sum(p.get('stats', {}).get('assists', 0) for p in team_participants)
            total_gold = sum(p.get('stats', {}).get('goldEarned', 0) for p in team_participants)
            total_damage = sum(p.get('stats', {}).get('totalDamageDealtToChampions', 0) for p in team_participants)
            total_vision = sum(p.get('stats', {}).get('visionScore', 0) for p in team_participants)
            total_cs = sum(p.get('stats', {}).get('totalMinionsKilled', 0) + p.get('stats', {}).get('neutralMinionsKilled', 0) for p in team_participants)
            
            # 计算团队KDA
            team_kda = self._calculate_kda(total_kills, total_deaths, total_assists)
            
            # 计算目标控制数据
            turret_kills = sum(p.get('stats', {}).get('turretKills', 0) for p in team_participants)
            inhibitor_kills = sum(p.get('stats', {}).get('inhibitorKills', 0) for p in team_participants)
            baron_kills = sum(p.get('stats', {}).get('baronKills', 0) for p in team_participants)
            dragon_kills = sum(p.get('stats', {}).get('dragonKills', 0) for p in team_participants)
            
            # 计算每分钟数据（假设团队所有成员游戏时长相同）
            if team_participants:
                game_duration = max(team_participants[0].get('timePlayed', 1), 1)
                minutes = game_duration / 60
            else:
                game_duration = 0
                minutes = 1
            
            team_stats[team_name] = {
                'team_id': team_id,
                'total_kills': total_kills,
                'total_deaths': total_deaths,
                'total_assists': total_assists,
                'team_kda': team_kda,
                'total_gold': total_gold,
                'gold_per_minute': round(total_gold / minutes, 2),
                'total_damage': total_damage,
                'damage_per_minute': round(total_damage / minutes, 2),
                'total_vision': total_vision,
                'vision_per_minute': round(total_vision / minutes, 2),
                'total_cs': total_cs,
                'cs_per_minute': round(total_cs / minutes, 2),
                'turret_kills': turret_kills,
                'inhibitor_kills': inhibitor_kills,
                'baron_kills': baron_kills,
                'dragon_kills': dragon_kills,
                'total_objectives': turret_kills + inhibitor_kills + baron_kills + dragon_kills,
                'players': [p.get('summonerName', '') for p in team_participants],
                'champions': [p.get('championName', '') for p in team_participants],
                'win': any(p.get('stats', {}).get('win', False) for p in team_participants),
                # 添加额外的团队数据用于玩家分析
                'total_kills_assists': total_kills + total_assists
            }
            
        return team_stats