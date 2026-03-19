"""
Admin Telegram Bot for UzFlower.
Бот для администраторов магазина для обработки заказов.
"""

from .bot import bot, dp, start_admin_bot
from .handlers import router
from .services import UzFlowerAPI

__all__ = ["bot", "dp", "start_admin_bot", "router", "UzFlowerAPI"]
