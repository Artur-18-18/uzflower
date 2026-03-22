"""
Запуск Telegram-бота UzFlower.

Использование:
    # Локально (polling):
    python run_bot.py

    # Production (webhook):
    python run_bot.py --mode webhook --webhook-url https://your-app.onrender.com/api/telegram/webhook

Или:
    python -m app.telegram_bot.runner --mode polling
"""

import argparse
import asyncio
import logging
import sys

from app.telegram_bot.runner import start_polling, start_webhook

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
    parser = argparse.ArgumentParser(description="Запуск Telegram-бота UzFlower")
    parser.add_argument(
        "--mode",
        choices=["polling", "webhook"],
        default="polling",
        help="Режим запуска: polling (локально) или webhook (production)"
    )
    parser.add_argument(
        "--webhook-url",
        type=str,
        default=None,
        help="URL webhook для режима webhook"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8001,
        help="Порт для webhook сервера"
    )

    args = parser.parse_args()

    logger.info("=" * 50)
    logger.info("🌸 UzFlower Telegram Bot")
    logger.info("=" * 50)
    logger.info("📋 Режим: %s", args.mode)

    try:
        if args.mode == "webhook":
            if not args.webhook_url:
                logger.error("❌ Для режима webhook необходимо указать --webhook-url")
                sys.exit(1)
            await start_webhook(args.webhook_url, args.port)
        else:
            await start_polling()
    except KeyboardInterrupt:
        logger.info("👋 Бот остановлен пользователем")
    except Exception as e:
        logger.error("❌ Критическая ошибка: %s", e, exc_info=True)
        raise


if __name__ == "__main__":
    asyncio.run(main())
