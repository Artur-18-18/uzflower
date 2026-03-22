"""
Конфигурация Telegram-бота.
"""

import os
from dotenv import load_dotenv

from app.internal_api_url import get_internal_api_base_url

# Загружаем переменные из .env файла
load_dotenv()


class TelegramBotSettings:
    """Настройки Telegram-бота."""

    def __init__(self):
        # Токен бота от @BotFather
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "8676150074:AAFXKPfATw1cPrJVxiV4OP4vbmgdlHaEKN0")

        # ID канала (например, @flowers_shop или -1001234567890)
        self.channel_id = os.getenv("TELEGRAM_CHANNEL_ID", "")

        # ID владельца (чат для уведомлений о заказах)
        try:
            self.owner_id = int(os.getenv("TELEGRAM_OWNER_ID", "0") or "0")
        except ValueError:
            self.owner_id = 0

        # URL API: тот же процесс; на Render обязателен PORT (см. get_internal_api_base_url)
        self.api_url = get_internal_api_base_url()

        # API ключ для авторизации бота в API
        self.api_secret = os.getenv("TELEGRAM_API_SECRET", "telegram-bot-secret-key")


# Глобальный экземпляр настроек
settings = TelegramBotSettings()
