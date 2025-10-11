# main.py
import os
import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage

from db import init_db
# импорт роутеров — сейчас только стартовый, позже будут добавляться другие
from handlers.start import router as start_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise RuntimeError("Установи переменную окружения BOT_TOKEN (BOT_TOKEN)")

# создаём бота с Markdown по умолчанию
bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode="Markdown"))
storage = MemoryStorage()
dp = Dispatcher(storage=storage)


async def main():
    logger.info("Инициализация БД...")
    await init_db()  # один раз при старте
    # регистрируем роутеры (по мере разработки будут добавляться новые)
    dp.include_router(start_router)
    logger.info("Запуск polling...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Бот остановлен")
