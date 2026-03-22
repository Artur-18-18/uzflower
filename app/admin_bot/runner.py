"""
Универсальный запуск Admin Telegram-бота (polling или webhook).

Использование:
    - Локально (polling): python -m app.admin_bot.runner --mode polling
    - Production (webhook): python -m app.admin_bot.runner --mode webhook --webhook-url https://your-app.onrender.com/api/admin-telegram/webhook
"""

import argparse
import asyncio
import logging
import os
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web

from .config import settings
from .handlers import router

logger = logging.getLogger(__name__)


def create_bot_and_dp():
    """Создать экземпляр бота и диспетчера."""
    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)
    return bot, dp


async def start_polling():
    """Запустить бота в режиме polling (для локальной разработки)."""
    logger.info("🤖 Запуск Admin Telegram-бота в режиме polling...")
    logger.info("📡 Токен: %s...", settings.bot_token[:20])
    logger.info("👤 Admin IDs: %s", settings.admin_ids)

    bot, dp = create_bot_and_dp()

    try:
        # Удаляем webhook для использования polling
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("✅ Webhook удалён, запускаем polling...")

        # Запускаем polling
        await dp.start_polling(bot)
    except Exception as e:
        logger.error("❌ Ошибка при запуске бота: %s", e)
        raise
    finally:
        await bot.session.close()


async def start_webhook(webhook_url: str, port: int = 8002):
    """
    Запустить бота в режиме webhook (для production).

    Args:
        webhook_url: Полный URL webhook (например, https://your-app.onrender.com/api/admin-telegram/webhook)
        port: Порт для внутреннего сервера
    """
    logger.info("🤖 Запуск Admin Telegram-бота в режиме webhook...")
    logger.info("📡 Токен: %s...", settings.bot_token[:20])
    logger.info("🔗 Webhook URL: %s", webhook_url)

    bot, dp = create_bot_and_dp()

    # Создаём aiohttp приложение для webhook
    app = web.Application()

    # Регистрируем роутер
    dp.include_router(router)

    # Создаём обработчик запросов
    handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
        secret_token=settings.api_secret  # Секретный токен для проверки запросов
    )

    # Регистрируем обработчик на путь /api/admin-telegram/webhook
    handler.register(app, path="/api/admin-telegram/webhook")

    # Настраиваем приложение
    setup_application(app, dp, bot=bot)

    # Устанавливаем webhook
    await bot.set_webhook(
        url=webhook_url,
        secret_token=settings.api_secret,
        drop_pending_updates=True
    )
    logger.info("✅ Webhook установлен")

    # Запускаем внутренний сервер
    runner = web.AppRunner(app)
    await runner.setup()

    site = web.TCPSite(runner, host="0.0.0.0", port=port)
    await site.start()

    logger.info(f"🌐 Webhook сервер запущен на порту {port}")

    # Держим сервер запущенным
    while True:
        await asyncio.sleep(3600)


def main():
    """Точка входа для запуска бота."""
    parser = argparse.ArgumentParser(description="Запуск Admin Telegram-бота")
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
        help="URL webhook для режима webhook (обязательно для webhook режима)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8002,
        help="Порт для webhook сервера"
    )

    args = parser.parse_args()

    # Настройка логирования
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

    if args.mode == "webhook" and not args.webhook_url:
        logger.error("❌ Для режима webhook необходимо указать --webhook-url")
        sys.exit(1)

    try:
        if args.mode == "polling":
            asyncio.run(start_polling())
        else:
            asyncio.run(start_webhook(args.webhook_url, args.port))
    except KeyboardInterrupt:
        logger.info("👋 Бот остановлен пользователем")
    except Exception as e:
        logger.error("❌ Критическая ошибка: %s", e, exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
