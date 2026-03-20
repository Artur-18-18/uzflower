"""
Конфигурация Admin Telegram-бота.
"""

import os
from dotenv import load_dotenv

# Загружаем переменные из .env файла
load_dotenv()


class AdminBotSettings:
    """Настройки Admin Telegram-бота."""

    def __init__(self):
        # Токен админ-бота от @BotFather
        self.bot_token = os.getenv("ADMIN_BOT_TOKEN", "8443193754:AAHWu7NqH9nE7UHshZW4Jb0M3TqqMdlRcSA")

        # ID администратора/владельца (основной админ)
        try:
            self.admin_user_id = int(os.getenv("ADMIN_USER_ID", "0") or "0")
        except ValueError:
            self.admin_user_id = 0

        # Список ID администраторов (для поддержки нескольких админов)
        admin_ids_str = os.getenv("ADMIN_IDS", "")
        if admin_ids_str:
            try:
                self.admin_ids = [int(x.strip()) for x in admin_ids_str.split(",")]
            except ValueError:
                self.admin_ids = []
        else:
            # Если ADMIN_IDS не указан, используем ADMIN_USER_ID
            self.admin_ids = [self.admin_user_id] if self.admin_user_id else []

        # URL API сайта (для получения информации о заказах)
        # На Render.com используется localhost, так как боты работают в том же контейнере
        self.api_url = os.getenv("TELEGRAM_API_URL", "http://localhost:8000")

        # API ключ для авторизации бота в API
        self.api_secret = os.getenv("TELEGRAM_API_SECRET", "telegram-bot-secret-key")

        # ID канала для мониторинга (откуда брать товары)
        self.channel_id = os.getenv("TELEGRAM_CHANNEL_ID", "")

    def is_admin(self, user_id: int) -> bool:
        """
        Проверить, является ли пользователь администратором.

        Args:
            user_id: Telegram ID пользователя

        Returns:
            True если пользователь администратор
        """
        return user_id in self.admin_ids or (self.admin_user_id and user_id == self.admin_user_id)


# Глобальный экземпляр настроек
settings = AdminBotSettings()
