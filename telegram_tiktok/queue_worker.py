import asyncio
import logging
import os
from aiogram import Bot
from aiogram.types import FSInputFile
import task_queue
import cache
import downloader

logger = logging.getLogger(__name__)

async def process_task(bot: Bot, task: dict):
    user_id = task["user_id"]
    message_id = task["message_id"]
    url = task["url"]
    status_msg_id = task.get("status_msg_id")
    
    caption_text = "📥 Скачано с @tik_down_jaja_1_bot"

    try:
        # Check cache again just in case
        cached_file_id = await cache.get_cached_video(url)
        if cached_file_id:
            await bot.send_video(chat_id=user_id, video=cached_file_id, reply_to_message_id=message_id, caption=caption_text)
            return

        # 1. Get direct video URL
        direct_url = await downloader.get_tiktok_video_url(url)
        if not direct_url:
            await bot.send_message(chat_id=user_id, text="❌ Не удалось получить ссылку на видео. Возможно, оно приватное или удалено.", reply_to_message_id=message_id)
            return

        # 2. Download video
        file_path = await downloader.download_video(direct_url)
        if not file_path:
            await bot.send_message(chat_id=user_id, text="❌ Ошибка при скачивании видео.", reply_to_message_id=message_id)
            return

        # 3. Send video to user
        video_file = FSInputFile(file_path)
        
        # Для мобильных клиентов Telegram важно явно указывать размеры, 
        # иначе длинные вертикальные видео могут обрезаться в квадрат.
        # Стандартное разрешение TikTok - 1080x1920 (или 720x1280)
        sent_message = await bot.send_video(
            chat_id=user_id, 
            video=video_file, 
            reply_to_message_id=message_id, 
            caption=caption_text,
            supports_streaming=True,
            width=1080,
            height=1920
        )
        
        # 4. Cache file_id
        file_id = sent_message.video.file_id
        await cache.set_cached_video(url, file_id)

        # 5. Clean up
        if os.path.exists(file_path):
            os.remove(file_path)

    except Exception as e:
        logger.error(f"Error processing task for {url}: {e}")
        try:
            await bot.send_message(chat_id=user_id, text="❌ Произошла непредвиденная ошибка.", reply_to_message_id=message_id)
        except:
            pass
    finally:
        # Ensure cleanup in case of error
        if 'file_path' in locals() and file_path and os.path.exists(file_path):
            os.remove(file_path)
            
        # Delete status message
        if status_msg_id:
            try:
                await bot.delete_message(chat_id=user_id, message_id=status_msg_id)
            except Exception as e:
                logger.error(f"Failed to delete status message: {e}")

async def worker_main(bot: Bot, worker_id: int):
    logger.info(f"Worker {worker_id} started.")
    while True:
        try:
            task = await task_queue.get_from_queue()
            logger.info(f"Worker {worker_id} processing task: {task['url']}")
            await process_task(bot, task)
            task_queue.task_done()
        except Exception as e:
            logger.error(f"Worker {worker_id} error: {e}")
            await asyncio.sleep(5)

async def start_workers(bot: Bot, num_workers: int = 5):
    tasks = []
    for i in range(num_workers):
        tasks.append(asyncio.create_task(worker_main(bot, i)))
    await asyncio.gather(*tasks)
