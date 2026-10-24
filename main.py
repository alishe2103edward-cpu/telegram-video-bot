import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from config import TELEGRAM_BOT_TOKEN
from database import init_db
from handlers import router

# Loglarni yoqamiz (Railway'da qanday ishlayotganini ko'rib turish uchun)
logging.basicConfig(level=logging.INFO)

async def main():
    # 1. Ma'lumotlar bazasini ishga tushiramiz
    logging.info("Ma'lumotlar bazasi tekshirilmoqda...")
    await init_db()
    
    # 2. Bot va Dispatcherni sozlaymiz
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    
    # 3. Barcha menyu va buyruqlarni ulaymiz
    dp.include_router(router)
    
    # 4. Botni ishga tushiramiz
    logging.info("🚀 AI Video Marketing Bot muvaffaqiyatli ishga tushdi!")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot to'xtatildi.")
