import pytest
import sys
import os

# 添加src目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from game_analyzer import GameAnalyzer

class TestGameAnalyzer:
    def setup_method(self):
        self.analyzer = GameAnalyzer()
        
    def test_calculate_kda_normal(self):
        """测试正常KDA计算"""
        assert self.analyzer._calculate_kda(10, 5, 15) == 5.0
        
    def test_calculate_kda_zero_deaths(self):
        """测试零死亡KDA计算"""
        assert self.analyzer._calculate_kda(10, 0, 5) == 15
        
    def test_calculate_performance_score_perfect(self):
        """测试完美表现评分"""
        metrics = {
            'kda': 10,
            'gold_per_minute': 500,
            'damage_per_minute': 1500,
            'vision_score': 60,
            'objective_control': 10
        }
        score = self.analyzer._calculate_performance_score(metrics)
        assert score == 100
        
    def test_calculate_performance_score_average(self):
        """测试平均表现评分"""
        metrics = {
            'kda': 2.5,
            'gold_per_minute': 250,
            'damage_per_minute': 500,
            'vision_score': 20,
            'objective_control': 2
        }
        score = self.analyzer._calculate_performance_score(metrics)
        assert 50 <= score <= 70
        
    def test_analyze_player_valid_data(self):
        """测试有效玩家数据分析"""
        participant = {
            'summonerName': 'TestPlayer',
            'championName': 'Ahri',
            'teamId': 100,
            'stats': {
                'kills': 8,
                'deaths': 3,
                'assists': 12,
                'goldEarned': 15000,
                'totalDamageDealtToChampions': 25000,
                'wardsPlaced': 15,
                'wardsKilled': 8,
                'visionScore': 25,
                'turretKills': 2,
                'inhibitorKills': 1,
                'baronKills': 1,
                'dragonKills': 3,
                'win': True,
                'totalMinionsKilled': 200,
                'neutralMinionsKilled': 50
            },
            'timePlayed': 1800
        }
        
        result = self.analyzer._analyze_player(participant)
        
        assert result is not None
        assert result['summoner_name'] == 'TestPlayer'
        assert result['champion_name'] == 'Ahri'
        assert result['kills'] == 8
        assert result['deaths'] == 3
        assert result['assists'] == 12
        assert result['win'] is True
        
    def test_analyze_teams_balanced_data(self):
        """测试平衡团队数据分析"""
        participants = [
            {
                'summonerName': 'Player1',
                'teamId': 100,
                'stats': {'kills': 5, 'deaths': 3, 'assists': 8, 'goldEarned': 12000, 'totalDamageDealtToChampions': 18000, 'win': True}
            },
            {
                'summonerName': 'Player2',
                'teamId': 100,
                'stats': {'kills': 7, 'deaths': 2, 'assists': 10, 'goldEarned': 14000, 'totalDamageDealtToChampions': 22000, 'win': True}
            },
            {
                'summonerName': 'Player3',
                'teamId': 200,
                'stats': {'kills': 3, 'deaths': 6, 'assists': 5, 'goldEarned': 10000, 'totalDamageDealtToChampions': 15000, 'win': False}
            },
            {
                'summonerName': 'Player4',
                'teamId': 200,
                'stats': {'kills': 4, 'deaths': 8, 'assists': 7, 'goldEarned': 11000, 'totalDamageDealtToChampions': 16000, 'win': False}
            }
        ]
        
        result = self.analyzer._analyze_teams(participants)
        
        assert '蓝队' in result
        assert '红队' in result
        assert result['蓝队']['total_kills'] == 12
        assert result['红队']['total_kills'] == 7
        assert result['蓝队']['win'] is True
        assert result['红队']['win'] is False
