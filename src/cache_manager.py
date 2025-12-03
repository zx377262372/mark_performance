import json
import hashlib
import os
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class CacheManager:
    def __init__(self, cache_dir: str = ".cache", default_ttl: int = 3600):
        """
        初始化缓存管理器
        
        Args:
            cache_dir: 缓存文件存储目录
            default_ttl: 默认缓存过期时间（秒）
        """
        self.cache_dir = cache_dir
        self.default_ttl = default_ttl
        
        # 创建缓存目录
        os.makedirs(self.cache_dir, exist_ok=True)
    
    def _get_cache_key(self, url: str, params: dict = None) -> str:
        """
        根据URL和参数生成缓存键
        
        Args:
            url: API请求URL
            params: 请求参数
            
        Returns:
            缓存键（MD5哈希值）
        """
        if params:
            # 对参数进行排序，确保相同参数生成相同的键
            sorted_params = sorted(params.items())
            cache_string = f"{url}{sorted_params}"
        else:
            cache_string = url
        
        # 使用MD5生成缓存键
        return hashlib.md5(cache_string.encode('utf-8')).hexdigest()
    
    def _get_cache_file(self, cache_key: str) -> str:
        """
        获取缓存文件路径
        
        Args:
            cache_key: 缓存键
            
        Returns:
            缓存文件路径
        """
        return os.path.join(self.cache_dir, f"{cache_key}.json")
    
    def get(self, url: str, params: dict = None) -> dict or None:
        """
        从缓存中获取数据
        
        Args:
            url: API请求URL
            params: 请求参数
            
        Returns:
            缓存的数据（如果存在且未过期），否则返回None
        """
        cache_key = self._get_cache_key(url, params)
        cache_file = self._get_cache_file(cache_key)
        
        try:
            if os.path.exists(cache_file):
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                
                # 检查缓存是否过期
                created_at = datetime.fromisoformat(cache_data['created_at'])
                ttl = cache_data.get('ttl', self.default_ttl)
                
                if datetime.now() - created_at < timedelta(seconds=ttl):
                    logger.debug(f"缓存命中: {url}")
                    return cache_data['data']
                else:
                    logger.debug(f"缓存过期: {url}")
                    # 删除过期缓存
                    os.remove(cache_file)
        except Exception as e:
            logger.error(f"读取缓存失败: {str(e)}")
        
        return None
    
    def set(self, url: str, params: dict = None, data: dict, ttl: int = None) -> bool:
        """
        将数据存入缓存
        
        Args:
            url: API请求URL
            params: 请求参数
            data: 要缓存的数据
            ttl: 缓存过期时间（秒），如果为None则使用默认值
            
        Returns:
            是否成功存入缓存
        """
        cache_key = self._get_cache_key(url, params)
        cache_file = self._get_cache_file(cache_key)
        
        try:
            cache_data = {
                'created_at': datetime.now().isoformat(),
                'ttl': ttl or self.default_ttl,
                'data': data
            }
            
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
            
            logger.debug(f"缓存写入成功: {url}")
            return True
        except Exception as e:
            logger.error(f"写入缓存失败: {str(e)}")
            return False
    
    def clear(self) -> bool:
        """
        清空所有缓存
        
        Returns:
            是否成功清空缓存
        """
        try:
            for filename in os.listdir(self.cache_dir):
                if filename.endswith('.json'):
                    os.remove(os.path.join(self.cache_dir, filename))
            logger.info("缓存已清空")
            return True
        except Exception as e:
            logger.error(f"清空缓存失败: {str(e)}")
            return False
    
    def remove(self, url: str, params: dict = None) -> bool:
        """
        删除指定URL的缓存
        
        Args:
            url: API请求URL
            params: 请求参数
            
        Returns:
            是否成功删除缓存
        """
        cache_key = self._get_cache_key(url, params)
        cache_file = self._get_cache_file(cache_key)
        
        try:
            if os.path.exists(cache_file):
                os.remove(cache_file)
                logger.debug(f"缓存删除成功: {url}")
                return True
            return False
        except Exception as e:
            logger.error(f"删除缓存失败: {str(e)}")
            return False