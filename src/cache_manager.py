import json
import hashlib
import os
import shutil
from datetime import datetime, timedelta
import logging
from typing import Dict, Optional, Any

logger = logging.getLogger(__name__)

class CacheManager:
    def __init__(self, cache_dir: str = ".cache", default_ttl: int = 3600, max_cache_size: int = 1000):
        """
        初始化缓存管理器
        
        Args:
            cache_dir: 缓存文件存储目录
            default_ttl: 默认缓存过期时间（秒）
            max_cache_size: 最大缓存文件数量，超过则清理最旧的缓存
        """
        self.cache_dir = cache_dir
        self.default_ttl = default_ttl
        self.max_cache_size = max_cache_size
        
        # 创建缓存目录
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # 初始化时清理过期缓存
        self._clean_expired_cache()
    
    def _get_cache_key(self, url: str, params: Optional[dict] = None) -> str:
        """
        根据URL和参数生成缓存键
        
        Args:
            url: API请求URL
            params: 请求参数
            
        Returns:
            缓存键（SHA256哈希值，比MD5更安全）
        """
        if params:
            # 对参数进行排序，确保相同参数生成相同的键
            sorted_params = sorted(params.items())
            # 将参数转换为JSON字符串，确保格式一致性
            params_str = json.dumps(sorted_params, sort_keys=True)
            cache_string = f"{url}{params_str}"
        else:
            cache_string = url
        
        # 使用SHA256生成缓存键，比MD5更安全
        return hashlib.sha256(cache_string.encode('utf-8')).hexdigest()
    
    def _get_cache_file(self, cache_key: str) -> str:
        """
        获取缓存文件路径
        
        Args:
            cache_key: 缓存键
            
        Returns:
            缓存文件路径
        """
        return os.path.join(self.cache_dir, f"{cache_key}.json")
    
    def get(self, url: str, params: Optional[dict] = None) -> Optional[dict]:
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
        except json.JSONDecodeError:
            logger.error(f"缓存文件JSON格式错误: {cache_file}")
            # 删除损坏的缓存文件
            try:
                os.remove(cache_file)
            except:
                pass
        except Exception as e:
            logger.error(f"读取缓存失败: {str(e)}")
        
        return None
    
    def set(self, url: str, data: Any, params: Optional[dict] = None, ttl: Optional[int] = None) -> bool:
        """
        将数据存入缓存
        
        Args:
            url: API请求URL
            data: 要缓存的数据
            params: 请求参数
            ttl: 缓存过期时间（秒），如果为None则使用默认值
            
        Returns:
            是否成功存入缓存
        """
        try:
            # 检查缓存目录是否存在，不存在则创建
            if not os.path.exists(self.cache_dir):
                os.makedirs(self.cache_dir, exist_ok=True)
                
            cache_key = self._get_cache_key(url, params)
            cache_file = self._get_cache_file(cache_key)
            
            # 准备缓存数据
            cache_data = {
                'created_at': datetime.now().isoformat(),
                'ttl': ttl or self.default_ttl,
                'data': data
            }
            
            # 写入缓存文件
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
                
            logger.debug(f"缓存设置: {url}")
            
            # 检查并清理缓存数量
            self._clean_oldest_cache()
            
            return True
            
        except Exception as e:
            logger.error(f"设置缓存失败: {str(e)}")
            return False
    
    def _clean_expired_cache(self) -> None:
        """
        清理所有过期的缓存文件
        """
        try:
            if not os.path.exists(self.cache_dir):
                return
                
            for filename in os.listdir(self.cache_dir):
                if not filename.endswith('.json'):
                    continue
                    
                cache_file = os.path.join(self.cache_dir, filename)
                try:
                    with open(cache_file, 'r', encoding='utf-8') as f:
                        cache_data = json.load(f)
                    
                    created_at = datetime.fromisoformat(cache_data['created_at'])
                    ttl = cache_data.get('ttl', self.default_ttl)
                    
                    if datetime.now() - created_at >= timedelta(seconds=ttl):
                        os.remove(cache_file)
                        logger.debug(f"清理过期缓存: {cache_file}")
                except Exception:
                    # 删除损坏的缓存文件
                    os.remove(cache_file)
                    logger.debug(f"清理损坏缓存: {cache_file}")
        except Exception as e:
            logger.error(f"清理过期缓存失败: {str(e)}")
    
    def _clean_oldest_cache(self) -> None:
        """
        当缓存文件数量超过限制时，清理最旧的缓存文件
        """
        try:
            if not os.path.exists(self.cache_dir):
                return
                
            # 获取所有缓存文件
            cache_files = []
            for filename in os.listdir(self.cache_dir):
                if not filename.endswith('.json'):
                    continue
                    
                cache_file = os.path.join(self.cache_dir, filename)
                try:
                    mtime = os.path.getmtime(cache_file)
                    cache_files.append((mtime, cache_file))
                except Exception:
                    # 忽略无法访问的文件
                    continue
            
            # 按修改时间排序
            cache_files.sort()
            
            # 删除超过限制的最旧文件
            while len(cache_files) > self.max_cache_size:
                _, cache_file = cache_files.pop(0)
                try:
                    os.remove(cache_file)
                    logger.debug(f"清理最旧缓存: {cache_file}")
                except Exception:
                    # 忽略删除失败的文件
                    continue
        except Exception as e:
            logger.error(f"清理最旧缓存失败: {str(e)}")
    
    def clear(self) -> bool:
        """
        清空所有缓存
        
        Returns:
            是否成功清空缓存
        """
        try:
            if os.path.exists(self.cache_dir):
                shutil.rmtree(self.cache_dir)
                os.makedirs(self.cache_dir, exist_ok=True)
                logger.info(f"缓存已清空: {self.cache_dir}")
            return True
        except Exception as e:
            logger.error(f"清空缓存失败: {str(e)}")
            return False
    
    def get_cache_size(self) -> int:
        """
        获取当前缓存文件数量
        
        Returns:
            缓存文件数量
        """
        try:
            if not os.path.exists(self.cache_dir):
                return 0
                
            count = 0
            for filename in os.listdir(self.cache_dir):
                if filename.endswith('.json'):
                    count += 1
            return count
        except Exception as e:
            logger.error(f"获取缓存大小失败: {str(e)}")
            return 0
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