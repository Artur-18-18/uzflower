"""
Запуск Telegram-бота UzFlower.

Использование:
    python run_bot.py

Или:
    python -m app.telegram_bot.bot
"""

import asyncio
import logging
from app.telegram_bot import start_bot

# Настройка логгирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("bot_debug.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


async def main():
    """Запустить бота."""
    logger.info("=" * 50)
    logger.info("🌸 UzFlower Telegram Bot")
    logger.info("=" * 50)
    
    try:
        await start_bot()
    except KeyboardInterrupt:
        logger.info("👋 Бот остановлен пользователем")
    except Exception as e:
        logger.error("❌ Критическая ошибка: %s", e, exc_info=True)
        raise


if __name__ == "__main__":
    asyncio.run(main())
