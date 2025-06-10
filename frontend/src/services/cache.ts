const DEFAULT_CACHE_TTL = 5 * 60 * 1000; 
const DEFAULT_CACHE_PREFIX = 'app_cache_';

interface CacheItem<T> {
  data: T;
  expiry: number;
}


class CacheService {
  private prefix: string;
  private defaultTtl: number;
  
  constructor(prefix: string = DEFAULT_CACHE_PREFIX, defaultTtl: number = DEFAULT_CACHE_TTL) {
    this.prefix = prefix;
    this.defaultTtl = defaultTtl;
  }
  

  set<T>(key: string, data: T, ttl: number = this.defaultTtl): void {
    const cacheKey = this.getCacheKey(key);
    const expiry = Date.now() + ttl;
    
    const cacheItem: CacheItem<T> = {
      data,
      expiry
    };
    
    try {
      localStorage.setItem(cacheKey, JSON.stringify(cacheItem));
    } catch (error) {
      console.error('Ошибка при сохранении в кеш:', error);
    }
  }
  
 
  get<T>(key: string): T | null {
    const cacheKey = this.getCacheKey(key);
    
    try {
      const cachedData = localStorage.getItem(cacheKey);
      
      if (!cachedData) {
        return null;
      }
      
      const cacheItem: CacheItem<T> = JSON.parse(cachedData);
      
      // не устарел ли кеш
      if (Date.now() > cacheItem.expiry) {
        this.remove(key);
        return null;
      }
      
      return cacheItem.data;
    } catch (error) {
      console.error('Ошибка при получении данных из кеша:', error);
      return null;
    }
  }
  
 
  remove(key: string): void {
    const cacheKey = this.getCacheKey(key);
    localStorage.removeItem(cacheKey);
  }
  
 
  clear(): void {
    Object.keys(localStorage)
      .filter(key => key.startsWith(this.prefix))
      .forEach(key => localStorage.removeItem(key));
  }
  
  
  clearExpired(): void {
    const now = Date.now();
    
    Object.keys(localStorage)
      .filter(key => key.startsWith(this.prefix))
      .forEach(key => {
        try {
          const cachedData = localStorage.getItem(key);
          if (!cachedData) return;
          
          const cacheItem = JSON.parse(cachedData);
          if (now > cacheItem.expiry) {
            localStorage.removeItem(key);
          }
        } catch (error) {
        }
      });
  }
  

  private getCacheKey(key: string): string {
    return `${this.prefix}${key}`;
  }
}

export default new CacheService(); 