"""
Запуск Admin Telegram-бота.
"""

import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from .config import settings
from .handlers import router

logger = logging.getLogger(__name__)

# Создаём бота и диспетчер с памятью для FSM
storage = MemoryStorage()
bot = Bot(
    token=settings.bot_token,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)

dp = Dispatcher(storage=storage)

# Включаем роутер с обработчиками
dp.include_router(router)


async def start_admin_bot():
    """
    Запустить админ-бота в режиме polling.
    Используется для локальной разработки.
    """
    logger.info("🤖 Запуск Admin Telegram-бота...")
    logger.info("📡 Токен: %s...", settings.bot_token[:20])
    logger.info("👤 Admin IDs: %s", settings.admin_ids)

    try:
        # Удаляем webhook для использования polling
        await bot.delete_webhook(drop_pending_updates=True)

        # Запускаем polling
        await dp.start_polling(bot)
    except Exception as e:
        logger.error("❌ Ошибка при запуске админ-бота: %s", e)
        raise
    finally:
        await bot.session.close()


async def stop_admin_bot():
    """Остановить админ-бота."""
    try:
        await bot.session.close()
        logger.info("🛑 Админ-бот остановлен")
    except Exception as e:
        logger.error("Ошибка при остановке админ-бота: %s", e)


def get_admin_bot_token() -> str:
    """Получить токен админ-бота."""
    return settings.bot_token


def get_admin_bot() -> Bot:
    """Получить экземпляр бота."""
    return bot
