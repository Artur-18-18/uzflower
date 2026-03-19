"""
Запуск Telegram-бота.
"""

import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from .config import settings
from .handlers import router

logger = logging.getLogger(__name__)

# Создаём бота и диспетчер
bot = Bot(
    token=settings.bot_token,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)

dp = Dispatcher()

# Включаем роутер с обработчиками
dp.include_router(router)


async def start_bot():
    """
    Запустить бота в режиме polling.
    Используется для локальной разработки.
    """
    logger.info("🤖 Запуск Telegram-бота...")
    logger.info("📡 Токен: %s...", settings.bot_token[:20])

    try:
        # Удаляем webhook для использования polling
        await bot.delete_webhook(drop_pending_updates=True)

        # Запускаем polling
        await dp.start_polling(bot)
    except Exception as e:
        logger.error("❌ Ошибка при запуске бота: %s", e)
        raise
    finally:
        await bot.session.close()


async def stop_bot():
    """Остановить бота."""
    try:
        await bot.session.close()
        logger.info("🛑 Бот остановлен")
    except Exception as e:
        logger.error("Ошибка при остановке бота: %s", e)


def get_bot_token() -> str:
    """Получить токен бота."""
    return settings.bot_token
