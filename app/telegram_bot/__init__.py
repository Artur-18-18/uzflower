"""
Telegram Bot для UzFlower.

Функционал:
1. Получение постов из канала и создание товаров на сайте
2. Обработка заказов через deep-link (start=product_X)
3. Отправка заказов владельцу
"""

from .bot import bot, dp, start_bot
from .handlers import router
from .services import UzFlowerAPI

__all__ = ["bot", "dp", "start_bot", "router", "UzFlowerAPI"]
