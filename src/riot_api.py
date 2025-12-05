import aiohttp
import asyncio
import logging
from typing import Dict, List, Optional
from config import Config
from src.cache_manager import CacheManager

class RiotAPI:
    def __init__(self):
        self.api_key = Config.RIOT_API_KEY
        self.base_url = Config.RIOT_API_BASE_URL
        self.session = None
        self.logger = logging.getLogger(__name__)
        self.cache = CacheManager()
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
            
    async def _make_request(self, endpoint: str, params: Dict = None, max_retries: int = 3, ttl: int = None) -> Optional[Dict]:
        """
        发送API请求，支持重试机制和缓存
        
        Args:
            endpoint: API端点路径
            params: 请求参数
            max_retries: 最大重试次数
            ttl: 缓存有效期（秒）
        
        Returns:
            API响应数据字典，如果请求失败返回None
        """
        if not self.session:
            self.session = aiohttp.ClientSession()
            
        headers = {"X-Riot-Token": self.api_key}
        url = f"{self.base_url}{endpoint}"
        
        # 检查缓存
        cached_result = self.cache.get(url, params)
        if cached_result:
            self.logger.info(f"从缓存获取数据: {url}")
            return cached_result
        
        retry_delay = 1  # 初始重试延迟（秒）
        
        for retry in range(max_retries + 1):
            try:
                self.logger.info(f"发送API请求: {url}, 参数: {params}")
                async with self.session.get(url, headers=headers, params=params) as response:
                    if response.status == 200:
                        result = await response.json()
                        self.logger.info(f"API请求成功: {url}")
                        # 缓存结果
                        self.cache.set(url, result, params, ttl)
                        return result
                    elif response.status == 429:
                        # API速率限制处理
                        retry_after = int(response.headers.get("Retry-After", retry_delay))
                        # 指数退避并限制最大等待时间为30秒
                        retry_after = min(retry_after, 30)
                        self.logger.warning(f"API速率限制，等待 {retry_after} 秒后重试 (剩余次数: {max_retries - retry})")
                        await asyncio.sleep(retry_after)
                        retry_delay = min(retry_delay * 2, 30)  # 指数退避并设置上限
                    elif 400 <= response.status < 500 and response.status != 429:
                        # 客户端错误（如400, 404），不重试
                        self.logger.error(f"客户端错误 {response.status}: {url}")
                        return None
                    elif 500 <= response.status < 600:
                        # 服务器错误，进行重试
                        self.logger.warning(f"服务器错误 {response.status}，等待 {retry_delay} 秒后重试 (剩余次数: {max_retries - retry})")
                        await asyncio.sleep(retry_delay)
                        retry_delay = min(retry_delay * 2, 30)  # 指数退避并设置上限
                    else:
                        self.logger.error(f"API请求失败: {response.status}，URL: {url}")
                        return None
            except aiohttp.ClientConnectionError as e:
                self.logger.warning(f"连接错误: {str(e)}，等待 {retry_delay} 秒后重试 (剩余次数: {max_retries - retry})")
                await asyncio.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, 30)
            except aiohttp.ClientError as e:
                self.logger.warning(f"网络请求错误: {str(e)}，等待 {retry_delay} 秒后重试 (剩余次数: {max_retries - retry})")
                await asyncio.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, 30)
            except Exception as e:
                self.logger.error(f"API请求异常: {str(e)}，URL: {url}")
                return None
                
        self.logger.error(f"API请求重试次数耗尽，URL: {url}")
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
