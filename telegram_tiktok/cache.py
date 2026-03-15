import time

# Словари для хранения данных в оперативной памяти
video_cache = {}  # Формат: {"url": "file_id"}
user_rate_limits = {}  # Формат: {"user_id": [timestamp1, timestamp2, ...]}

async def check_rate_limit(user_id: int, limit: int = 5, window: int = 60) -> bool:
    """Returns True if user is allowed, False if rate limited."""
    current_time = time.time()
    
    if user_id not in user_rate_limits:
        user_rate_limits[user_id] = []
        
    # Очищаем старые запросы, которые вышли за пределы окна (60 сек)
    user_rate_limits[user_id] = [
        ts for ts in user_rate_limits[user_id] 
        if current_time - ts < window
    ]
    
    if len(user_rate_limits[user_id]) >= limit:
        return False
        
    # Добавляем текущий запрос
    user_rate_limits[user_id].append(current_time)
    return True

async def get_cached_video(url: str) -> str | None:
    """Returns cached file_id if exists."""
    return video_cache.get(url)

async def set_cached_video(url: str, file_id: str):
    """Caches file_id for a URL."""
    video_cache[url] = file_id
