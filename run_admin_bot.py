"""
Запуск Admin Telegram-бота UzFlower.

Использование:
    python run_admin_bot.py

Или:
    python -m app.admin_bot.bot
"""

import asyncio
import logging

from app.admin_bot.bot import start_admin_bot

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("admin_bot.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


async def main():
    """Запустить админ-бота."""
    logger.info("=" * 50)
    logger.info("👮 UzFlower Admin Bot")
    logger.info("=" * 50)

    try:
        await start_admin_bot()
    except KeyboardInterrupt:
        logger.info("👋 Админ-бот остановлен пользователем")
    except Exception as e:
        logger.error("❌ Критическая ошибка: %s", e, exc_info=True)
        raise


if __name__ == "__main__":
    asyncio.run(main())
