import aiohttp
import asyncio
import logging
from typing import Dict, List, Optional
from config import Config

class RiotAPI:
    def __init__(self):
        self.api_key = Config.RIOT_API_KEY
        self.base_url = Config.RIOT_API_BASE_URL
        self.session = None
        self.logger = logging.getLogger(__name__)
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
            
    async def _make_request(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """发送API请求"""
        if not self.session:
            self.session = aiohttp.ClientSession()
            
        headers = {"X-Riot-Token": self.api_key}
        url = f"{self.base_url}{endpoint}"
        
        try:
            async with self.session.get(url, headers=headers, params=params) as response:
                if response.status == 200:
                    return await response.json()
                elif response.status == 429:
                    self.logger.warning("API速率限制，等待重试...")
                    await asyncio.sleep(1)
                    return await self._make_request(endpoint, params)
                else:
                    self.logger.error(f"API请求失败: {response.status}")
                    return None
        except Exception as e:
            self.logger.error(f"API请求异常: {str(e)}")
            return None
            
    async def get_summoner_by_name(self, summoner_name: str) -> Optional[Dict]:
        """通过召唤师名称获取召唤师信息"""
        endpoint = f"/lol/summoner/v4/summoners/by-name/{summoner_name}"
        return await self._make_request(endpoint)
        
    async def get_recent_matches(self, summoner_name: str, count: int = 5) -> List[Dict]:
        """获取召唤师最近对局"""
        summoner = await self.get_summoner_by_name(summoner_name)
        if not summoner:
            return []
            
        puuid = summoner.get('puuid')
        if not puuid:
            return []
            
        # 获取对局列表
        endpoint = f"/lol/match/v5/matches/by-puuid/{puuid}/ids"
        params = {'count': count}
        match_ids = await self._make_request(endpoint, params)
        
        if not match_ids:
            return []
            
        # 获取对局详情
        matches = []
        for match_id in match_ids:
            match_detail = await self.get_match_detail(match_id)
            if match_detail:
                matches.append(match_detail)
                
        return matches
        
    async def get_match_detail(self, match_id: str) -> Optional[Dict]:
        """获取对局详情"""
        endpoint = f"/lol/match/v5/matches/{match_id}"
        return await self._make_request(endpoint)
