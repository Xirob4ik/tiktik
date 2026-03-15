import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession
from config import BOT_TOKEN, PROXY_URL
from handlers import router
from queue_worker import start_workers

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def main():
    if PROXY_URL:
        session = AiohttpSession(proxy=PROXY_URL)
        bot = Bot(token=BOT_TOKEN, session=session)
        logger.info(f"Using proxy: {PROXY_URL}")
    else:
        bot = Bot(token=BOT_TOKEN)
        
    dp = Dispatcher()
    
    dp.include_router(router)
    
    # Start workers in the background
    # Max 5 concurrent downloads as requested
    asyncio.create_task(start_workers(bot, num_workers=5))
    
    logger.info("Starting bot...")
    # Удаляем вебхук и пропускаем старые апдейты, чтобы бот не зависал
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped.")
