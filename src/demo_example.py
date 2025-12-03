import asyncio
from datetime import datetime

from .game_analyzer import GameAnalyzer
from .prompt_generator import PromptGenerator
from .wechat_sender import WeChatSender


def build_sample_match():
    # Minimal sample match data following the structure used in GameAnalyzer tests
    return {
        'info': {
            'gameId': 123456,
            'gameDuration': 1800,
            'gameMode': 'CLASSIC',
            'gameCreation': int(datetime.now().timestamp() * 1000),
            'participants': [
                {
                    'summonerName': '玩家A',
                    'championName': 'Ezreal',
                    'teamId': 100,
                    'individualPosition': 'BOTTOM',
                    'stats': {
                        'kills': 10,
                        'deaths': 2,
                        'assists': 8,
                        'goldEarned': 14000,
                        'totalDamageDealtToChampions': 22000,
                        'wardsPlaced': 8,
                        'wardsKilled': 2,
                        'visionScore': 20,
                        'turretKills': 2,
                        'inhibitorKills': 0,
                        'baronKills': 0,
                        'dragonKills': 1,
                        'win': True,
                        'totalMinionsKilled': 200,
                        'neutralMinionsKilled': 10
                    },
                    'timePlayed': 1800
                },
                {
                    'summonerName': '玩家B',
                    'championName': 'LeeSin',
                    'teamId': 100,
                    'individualPosition': 'JUNGLE',
                    'stats': {
                        'kills': 2,
                        'deaths': 8,
                        'assists': 3,
                        'goldEarned': 9000,
                        'totalDamageDealtToChampions': 8000,
                        'visionScore': 10,
                        'win': True,
                        'totalMinionsKilled': 20,
                        'neutralMinionsKilled': 80
                    },
                    'timePlayed': 1800
                }
            ]
        }
    }


def demo():
    ga = GameAnalyzer()
    pg = PromptGenerator()
    ws = WeChatSender()

    match = build_sample_match()
    analysis = ga.analyze_match(match)
    prompt = pg.generate_prompt(analysis)

    print("--- GENERATED PROMPT (preview) ---")
    print(prompt[:800])
    print("--- END PROMPT ---\n")

    # Simulate a model parsed JSON response for demonstration
    fake_parsed = {
        'match_id': analysis.get('match_id'),
        'summary': '红队中下节奏掌控较好，蓝队打野多次团战失误导致节奏丢失。',
        'overall_score': 68,
        'key_moments': ['10分 小规模团战 蓝队打野被击杀，导致一塔丢失'],
        'influencers': [
            {'summoner_name': '玩家A', 'role': 'BOTTOM', 'label': 'carried', 'reason': '多次关键补刀和团战输出', 'impact_score': 45, 'confidence': 90},
            {'summoner_name': '玩家B', 'role': 'JUNGLE', 'label': 'fed', 'reason': '前期多次被抓死亡，影响节奏', 'impact_score': -35, 'confidence': 88}
        ],
        'player_insights': {
            '玩家A': {'label': 'carried', 'short': '输出和发育优秀', 'advice': '继续关注视野'},
            '玩家B': {'label': 'fed', 'short': '多次被抓', 'advice': '注意打野路径与视野'}
        }
    }

    result = {'parsed': fake_parsed, 'timestamp': datetime.now().isoformat()}
    message = ws._format_message(result)
    print("--- FORMATTED MESSAGE TO WECHAT ---")
    print(message)


if __name__ == '__main__':
    demo()
