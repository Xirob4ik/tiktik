import aiohttp
import os
import uuid
import logging
from config import DOWNLOADS_DIR, PROXY_URL

logger = logging.getLogger(__name__)

async def get_tiktok_video_url(tiktok_url: str) -> str | None:
    # 1. Попытка через основной API (tikwm)
    url = await _get_from_tikwm(tiktok_url)
    if url:
        return url
        
    logger.warning("TikWM failed, trying fallback API (Lolik/TiklyDown)...")
    
    # 2. Попытка через запасной API (Lolik / TiklyDown)
    url = await _get_from_fallback_api(tiktok_url)
    if url:
        return url
        
    return None

async def _get_from_tikwm(tiktok_url: str) -> str | None:
    api_url = "https://www.tikwm.com/api/"
    params = {
        "url": tiktok_url,
        "hd": 1
    }
    
    # Попытка 1: С прокси
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(api_url, data=params, timeout=15, proxy=PROXY_URL) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("code") == 0:
                        # Возвращаем обычный play, так как hdplay часто использует кодек HEVC (H.265), 
                        # который Telegram не может нормально отобразить (белый/черный экран со звуком)
                        return data["data"]["play"]
                else:
                    logger.error(f"API proxy request failed with status {response.status}")
    except Exception as e:
        logger.error(f"Error fetching video URL from API with proxy: {type(e).__name__} - {e}")

    # Попытка 2: Без прокси
    if PROXY_URL:
        logger.info("Retrying API request without proxy...")
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(api_url, data=params, timeout=15) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("code") == 0:
                            return data["data"]["play"]
                    else:
                        logger.error(f"API direct request failed with status {response.status}")
        except Exception as e:
            logger.error(f"Error fetching video URL from API directly: {type(e).__name__} - {e}")

    return None

async def _get_from_fallback_api(tiktok_url: str) -> str | None:
    # Запасной бесплатный API (TiklyDown / Lolik API mirror)
    api_url = f"https://api.tiklydown.eu.org/api/download"
    params = {"url": tiktok_url}
    
    try:
        async with aiohttp.ClientSession() as session:
            # Пробуем без прокси, так как запасные API часто блокируют датацентровые IP
            async with session.get(api_url, params=params, timeout=15) as response:
                if response.status == 200:
                    data = await response.json()
                    # Ищем ссылку на видео без водяного знака
                    if "video" in data and "noWatermark" in data["video"]:
                        return data["video"]["noWatermark"]
                else:
                    logger.error(f"Fallback API failed with status {response.status}")
    except Exception as e:
        logger.error(f"Error fetching video URL from Fallback API: {type(e).__name__} - {e}")
        
    return None

async def download_video(video_url: str) -> str | None:
    file_path = os.path.join(DOWNLOADS_DIR, f"{uuid.uuid4()}.mp4")
    
    # Попытка 1: С прокси (если указан)
    try:
        async with aiohttp.ClientSession() as session:
            # Увеличиваем таймаут до 300 секунд (5 минут), так как через прокси видео может качаться медленно
            async with session.get(video_url, timeout=300, proxy=PROXY_URL) as response:
                if response.status == 200:
                    with open(file_path, 'wb') as f:
                        while True:
                            chunk = await response.content.read(1024 * 1024)
                            if not chunk:
                                break
                            f.write(chunk)
                    return file_path
                else:
                    logger.error(f"Proxy download failed with status {response.status}")
    except Exception as e:
        logger.error(f"Error downloading video file with proxy: {type(e).__name__} - {e}")
        if os.path.exists(file_path):
            os.remove(file_path)

    # Попытка 2: Без прокси (если первая провалилась или прокси медленный/заблокировал CDN)
    if PROXY_URL:
        logger.info("Retrying download without proxy...")
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(video_url, timeout=300) as response:
                    if response.status == 200:
                        with open(file_path, 'wb') as f:
                            while True:
                                chunk = await response.content.read(1024 * 1024)
                                if not chunk:
                                    break
                                f.write(chunk)
                        return file_path
                    else:
                        logger.error(f"Direct download failed with status {response.status}")
        except Exception as e:
            logger.error(f"Error downloading video file directly: {type(e).__name__} - {e}")
            if os.path.exists(file_path):
                os.remove(file_path)

    return None
