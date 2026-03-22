"""
Конфигурация Admin Telegram-бота.
"""

import logging
import os
from dotenv import load_dotenv

from app.internal_api_url import get_internal_api_base_url

# Загружаем переменные из .env файла
load_dotenv()

logger = logging.getLogger(__name__)


def _parse_int_env(key: str, default: int = 0) -> int:
    raw = os.getenv(key)
    if raw is None or str(raw).strip() == "":
        return default
    try:
        return int(str(raw).strip())
    except ValueError:
        return default


class AdminBotSettings:
    """Настройки Admin Telegram-бота."""

    def __init__(self):
        # Токен админ-бота от @BotFather
        self.bot_token = os.getenv("ADMIN_BOT_TOKEN", "8443193754:AAHWu7NqH9nE7UHshZW4Jb0M3TqqMdlRcSA")

        # Основной админ; если не задан — пробуем TELEGRAM_OWNER_ID (часто тот же человек)
        admin_user_id = _parse_int_env("ADMIN_USER_ID")
        owner_id = _parse_int_env("TELEGRAM_OWNER_ID")
        if admin_user_id == 0 and owner_id:
            admin_user_id = owner_id

        admin_ids: list[int] = []
        admin_ids_str = (os.getenv("ADMIN_IDS") or "").strip()
        if admin_ids_str:
            for part in admin_ids_str.split(","):
                part = part.strip()
                if not part:
                    continue
                try:
                    admin_ids.append(int(part))
                except ValueError:
                    continue

        if admin_user_id and admin_user_id not in admin_ids:
            admin_ids.append(admin_user_id)

        self.admin_user_id = admin_user_id
        self.admin_ids = admin_ids if admin_ids else ([admin_user_id] if admin_user_id else [])

        if not self.admin_ids:
            logger.warning(
                "ADMIN_USER_ID, ADMIN_IDS и TELEGRAM_OWNER_ID пусты — "
                "админ-бот будет отвечать «нет доступа». Задайте ADMIN_USER_ID в Render."
            )

        self.api_url = get_internal_api_base_url()

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
        try:
            uid = int(user_id)
        except (TypeError, ValueError):
            return False
        return uid in self.admin_ids


# Глобальный экземпляр настроек
settings = AdminBotSettings()
