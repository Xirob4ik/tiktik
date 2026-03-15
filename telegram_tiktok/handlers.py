from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
import logging
import utils
import task_queue
import cache

logger = logging.getLogger(__name__)
router = Router()

@router.message(Command("start"))
async def cmd_start(message: Message):
    logger.info(f"Received /start from {message.from_user.id}")
    await message.answer("Привет! Отправь ссылку на TikTok видео, и я бесплатно скачаю его без водяного знака.")

@router.message(F.text)
async def handle_message(message: Message):
    url = message.text.strip()
    logger.info(f"Received message: {url} from {message.from_user.id}")
    
    if not utils.is_tiktok_url(url):
        await message.answer("❌ Похоже, это не ссылка TikTok.")
        return

    user_id = message.from_user.id
    
    # Check rate limit
    is_allowed = await cache.check_rate_limit(user_id)
    if not is_allowed:
        await message.answer("⚠️ Вы превысили лимит скачиваний (5 в минуту). Подождите немного.")
        return

    # Check cache
    cached_file_id = await cache.get_cached_video(url)
    if cached_file_id:
        await message.answer_video(video=cached_file_id, caption="📥 Скачано с @tik_down_jaja_1_bot")
        return

    # Add to queue
    status_msg = await message.answer("⏳ Скачиваю видео, подождите...", reply_to_message_id=message.message_id)
    await task_queue.add_to_queue(user_id, message.message_id, url, status_msg.message_id)
