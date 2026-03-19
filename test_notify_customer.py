"""
Тест для проверки уведомления покупателя о статусе заказа.
"""

import asyncio
import logging
import os
from dotenv import load_dotenv

load_dotenv()

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

logger = logging.getLogger(__name__)


async def test_notify_customer():
    """Тест уведомления покупателя."""
    from app.admin_bot.services import UzFlowerAPI
    
    print("=" * 60)
    print("🧪 Тест уведомления покупателя о статусе заказа")
    print("=" * 60)
    print()
    
    # Проверяем конфигурацию
    print("📋 Конфигурация:")
    print(f"   TELEGRAM_API_URL: {os.getenv('TELEGRAM_API_URL')}")
    print(f"   TELEGRAM_API_SECRET: {os.getenv('TELEGRAM_API_SECRET', 'NOT SET')}")
    print()
    
    api = UzFlowerAPI()
    
    # Тестовые данные - ЗАМЕНИТЕ НА РЕАЛЬНЫЕ!
    test_data = {
        "order_id": 1,  # Номер заказа
        "status": "accepted",  # или "cancelled"
        "customer_telegram_id": 1186442364,  # Ваш Telegram ID для теста
        "customer_name": "Тест"
    }
    
    print("📤 Отправка уведомления...")
    print(f"   Заказ #: {test_data['order_id']}")
    print(f"   Статус: {test_data['status']}")
    print(f"   Telegram ID: {test_data['customer_telegram_id']}")
    print(f"   Имя: {test_data['customer_name']}")
    print()
    
    result = await api.notify_customer_order_status(**test_data)
    
    print()
    print("=" * 60)
    if result:
        print("✅ Тест пройден! Уведомление отправлено.")
        print("   Проверьте Telegram - вы должны получить сообщение.")
    else:
        print("❌ Тест не пройден. Проверьте логи выше.")
    print("=" * 60)
    
    return result


if __name__ == "__main__":
    asyncio.run(test_notify_customer())
