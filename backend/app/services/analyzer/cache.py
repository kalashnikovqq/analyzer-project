from functools import lru_cache
from typing import Any, Optional, Tuple, List
import hashlib

class AspectCache:
    """Кэш для результатов извлечения аспектов"""
    
    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self._cache = {}
    
    @staticmethod
    def _hash_text(text: str) -> str:
        """Создает хэш для текста"""
        return hashlib.md5(text.encode('utf-8')).hexdigest()
    
    def get(self, text: str) -> Optional[Tuple[List[str], List[str]]]:
        """Получает результат из кэша"""
        key = self._hash_text(text)
        return self._cache.get(key)
    
    def set(self, text: str, result: Tuple[List[str], List[str]]) -> None:
        """Сохраняет результат в кэш"""
        if len(self._cache) >= self.max_size:
            keys_to_remove = list(self._cache.keys())[:len(self._cache) // 2]
            for key in keys_to_remove:
                del self._cache[key]
        
        key = self._hash_text(text)
        self._cache[key] = result
    
    def clear(self) -> None:
        """Очищает кэш"""
        self._cache.clear() 