import aiohttp
import logging
import json
import re
from typing import Dict, Optional
from datetime import datetime
from config import Config


class AIAnalyzer:
    def __init__(self):
        self.api_key = Config.AI_API_KEY
        self.api_base_url = Config.AI_API_BASE_URL
        self.model = Config.AI_MODEL
        self.logger = logging.getLogger(__name__)
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
            self.session = None

    async def analyze_performance(self, prompt: str) -> Optional[Dict]:
        """使用AI分析游戏表现并返回解析后的结构化JSON（字典）。"""
        if not prompt:
            return None

        try:
            # 构建AI请求
            messages = [
                {
                    "role": "system",
                    "content": "你是一个专业的英雄联盟游戏分析师，擅长基于数据识别比赛的关键影响者并用结构化JSON返回结果。严格按照我们给定的JSON schema返回，不要添加任何多余文字。"
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]

            # 发送AI请求（文本形式）
            text_result = await self._send_ai_request(messages)

            if not text_result:
                return None

            # 尝试从模型返回的文本中抽取JSON并解析
            parsed = self._extract_json_from_text(text_result)

            if parsed is None:
                # 如果解析失败，返回原始文本以便上层查看
                return {
                    'raw': text_result,
                    'parsed': None,
                    'timestamp': datetime.now().isoformat(),
                    'model': self.model
                }

            return {
                'raw': text_result,
                'parsed': parsed,
                'timestamp': datetime.now().isoformat(),
                'model': self.model
            }

        except Exception as e:
            self.logger.error(f"AI分析失败: {str(e)}")
            return None

    async def _send_ai_request(self, messages: list, max_retries: int = 3) -> Optional[str]:
        """发送AI API请求，返回模型文本响应，支持重试机制。"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        data = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.2,
            "max_tokens": 1500
        }

        retry_delay = 1  # 初始重试延迟（秒）

        for retry in range(max_retries + 1):
            try:
                # 使用现有的会话或创建新会话
                if self.session:
                    async with self.session.post(
                        f"{self.api_base_url}/chat/completions",
                        headers=headers,
                        json=data
                    ) as response:
                        if response.status == 200:
                            result = await response.json()
                            return result.get('choices', [{}])[0].get('message', {}).get('content', '')
                        elif response.status == 429:
                            # API速率限制
                            retry_after = int(response.headers.get("Retry-After", retry_delay))
                            self.logger.warning(f"AI API速率限制，等待 {retry_after} 秒后重试 (剩余次数: {max_retries - retry})")
                            await asyncio.sleep(retry_after)
                            retry_delay *= 2  # 指数退避
                        elif response.status in [500, 502, 503, 504]:
                            # 服务器错误，重试
                            self.logger.warning(f"AI服务器错误 {response.status}，等待 {retry_delay} 秒后重试 (剩余次数: {max_retries - retry})")
                            await asyncio.sleep(retry_delay)
                            retry_delay *= 2  # 指数退避
                        else:
                            self.logger.error(f"AI API请求失败: {response.status}")
                            return None
                else:
                    # 作为后备，创建临时会话
                    async with aiohttp.ClientSession() as session:
                        async with session.post(
                            f"{self.api_base_url}/chat/completions",
                            headers=headers,
                            json=data
                        ) as response:
                            if response.status == 200:
                                result = await response.json()
                                return result.get('choices', [{}])[0].get('message', {}).get('content', '')
                            elif response.status == 429:
                                # API速率限制
                                retry_after = int(response.headers.get("Retry-After", retry_delay))
                                self.logger.warning(f"AI API速率限制，等待 {retry_after} 秒后重试 (剩余次数: {max_retries - retry})")
                                await asyncio.sleep(retry_after)
                                retry_delay *= 2  # 指数退避
                            elif response.status in [500, 502, 503, 504]:
                                # 服务器错误，重试
                                self.logger.warning(f"AI服务器错误 {response.status}，等待 {retry_delay} 秒后重试 (剩余次数: {max_retries - retry})")
                                await asyncio.sleep(retry_delay)
                                retry_delay *= 2  # 指数退避
                            else:
                                self.logger.error(f"AI API请求失败: {response.status}")
                                return None

            except aiohttp.ClientError as e:
                self.logger.warning(f"AI API请求网络异常: {str(e)}，等待 {retry_delay} 秒后重试 (剩余次数: {max_retries - retry})")
                await asyncio.sleep(retry_delay)
                retry_delay *= 2  # 指数退避
            except Exception as e:
                self.logger.error(f"AI API请求异常: {str(e)}")
                return None

        self.logger.error("AI API请求重试次数耗尽")
        return None

    def _extract_json_from_text(self, text: str) -> Optional[Dict]:
        """从模型返回的文本中提取第一个JSON对象并解析。

        该函数会处理模型返回时可能带的代码块标记（```）、前后说明文字等。
        """
        if not text:
            return None

        # 去掉常见的代码块包裹
        # 找到第一个{ 和最后一个} 并尝试解析
        # 也尝试查找 ```json ... ``` 或 ``` ... ``` 中的内容
        try:
            # 首先查找 ```json ... ``` 或 ``` ... ``` 块
            code_block = re.search(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", text, re.IGNORECASE)
            candidate = None
            if code_block:
                candidate = code_block.group(1)
            else:
                # 没有代码块，尝试从首个 '{' 到最后一个 '}'
                first = text.find('{')
                last = text.rfind('}')
                if first != -1 and last != -1 and last > first:
                    candidate = text[first:last+1]

            if not candidate:
                return None

            # 尝试解析
            parsed = json.loads(candidate)
            return parsed

        except Exception as e:
            self.logger.error(f"解析AI返回JSON失败: {str(e)}; 原始文本前200字符: {text[:200]}")
            return None
