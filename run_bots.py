"""
Запуск обоих Telegram-ботов UzFlower.

Использование:
    - Локально (polling): python run_bots.py --mode polling
    - Production (webhook): python run_bots.py --mode webhook --base-url https://your-app.onrender.com

Для локальной разработки рекомендуется запускать ботов по отдельности:
    python run_bot.py      # Основной бот
    python run_admin_bot.py  # Админ-бот
"""

import argparse
import asyncio
import logging
import os
import sys
from typing import Optional

from aiohttp import web

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


async def run_bots_polling():
    """
    Запустить оба бота в режиме polling.
    ВАЖНО: Используйте только с разными токенами!
    """
    logger.info("=" * 60)
    logger.info("🌸👮 Запуск обоих Telegram-ботов в режиме polling")
    logger.info("=" * 60)

    # Импортируем ботов
    from app.telegram_bot.bot import start_bot as start_main_bot
    from app.admin_bot.bot import start_admin_bot

    # Запускаем оба бота параллельно
    try:
        await asyncio.gather(
            start_main_bot(),
            start_admin_bot(),
            return_exceptions=False
        )
    except Exception as e:
        logger.error("❌ Ошибка при запуске ботов: %s", e)
        raise


async def run_bots_webhook(base_url: str):
    """
    Запустить оба бота в режиме webhook на одном сервере.

    Args:
        base_url: Базовый URL приложения (например, https://your-app.onrender.com)
    """
    logger.info("=" * 60)
    logger.info("🌸👮 Запуск обоих Telegram-ботов в режиме webhook")
    logger.info("=" * 60)
    logger.info("📡 Base URL: %s", base_url)

    from aiogram import Bot, Dispatcher
    from aiogram.client.default import DefaultBotProperties
    from aiogram.enums import ParseMode
    from aiogram.fsm.storage.memory import MemoryStorage
    from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

    # Импортируем настройки
    from app.telegram_bot.config import settings as main_bot_settings
    from app.admin_bot.config import settings as admin_bot_settings

    # Создаём ботов и диспетчеров
    main_bot = Bot(
        token=main_bot_settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    main_dp = Dispatcher()

    admin_bot = Bot(
        token=admin_bot_settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    admin_dp = Dispatcher(storage=MemoryStorage())

    # Импортируем и подключаем роутеры
    from app.telegram_bot.handlers import router as main_router
    from app.admin_bot.handlers import router as admin_router

    main_dp.include_router(main_router)
    admin_dp.include_router(admin_router)

    # Создаём aiohttp приложение
    app = web.Application()

    # Создаём обработчики для каждого бота
    main_handler = SimpleRequestHandler(
        dispatcher=main_dp,
        bot=main_bot,
        secret_token=main_bot_settings.api_secret
    )
    admin_handler = SimpleRequestHandler(
        dispatcher=admin_dp,
        bot=admin_bot,
        secret_token=admin_bot_settings.api_secret
    )

    # Регистрируем обработчики на разные пути
    main_handler.register(app, path="/api/telegram/webhook")
    admin_handler.register(app, path="/api/admin-telegram/webhook")

    # Настраиваем приложения
    setup_application(app, main_dp, bot=main_bot)
    setup_application(app, admin_dp, bot=admin_bot)

    # Устанавливаем webhook для обоих ботов
    main_webhook_url = f"{base_url}/api/telegram/webhook"
    admin_webhook_url = f"{base_url}/api/admin-telegram/webhook"

    await main_bot.set_webhook(
        url=main_webhook_url,
        secret_token=main_bot_settings.api_secret,
        drop_pending_updates=True
    )
    logger.info("✅ Webhook установлен для основного бота: %s", main_webhook_url)

    await admin_bot.set_webhook(
        url=admin_webhook_url,
        secret_token=admin_bot_settings.api_secret,
        drop_pending_updates=True
    )
    logger.info("✅ Webhook установлен для админ-бота: %s", admin_webhook_url)

    # Запускаем сервер на порту 8000 (основной порт приложения)
    # В production этот сервер будет интегрирован в основное FastAPI приложение
    runner = web.AppRunner(app)
    await runner.setup()

    # Определяем порт из переменной окружения или используем 8000
    port = int(os.getenv("PORT", "8000"))
    site = web.TCPSite(runner, host="0.0.0.0", port=port)
    await site.start()

    logger.info(f"🌐 Webhook сервер запущен на порту {port}")
    logger.info("   - Основной бот: /api/telegram/webhook")
    logger.info("   - Админ-бот: /api/admin-telegram/webhook")

    # Держим сервер запущенным
    while True:
        await asyncio.sleep(3600)


def main():
    """Точка входа для запуска ботов."""
    parser = argparse.ArgumentParser(description="Запуск Telegram-ботов UzFlower")
    parser.add_argument(
        "--mode",
        choices=["polling", "webhook"],
        default="polling",
        help="Режим запуска: polling (локально) или webhook (production)"
    )
    parser.add_argument(
        "--base-url",
        type=str,
        default=None,
        help="Базовый URL приложения для webhook режима (например, https://your-app.onrender.com)"
    )

    args = parser.parse_args()

    if args.mode == "webhook" and not args.base_url:
        logger.error("❌ Для режима webhook необходимо указать --base-url")
        logger.error("   Пример: python run_bots.py --mode webhook --base-url https://your-app.onrender.com")
        sys.exit(1)

    try:
        if args.mode == "polling":
            logger.info("🚀 Запуск в режиме polling...")
            asyncio.run(run_bots_polling())
        else:
            logger.info("🚀 Запуск в режиме webhook...")
            asyncio.run(run_bots_webhook(args.base_url))
    except KeyboardInterrupt:
        logger.info("👋 Боты остановлены пользователем")
    except Exception as e:
        logger.error("❌ Критическая ошибка: %s", e, exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
