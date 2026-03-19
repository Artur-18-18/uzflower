"""
Тест для проверки отправки уведомления в админ-бот при получении чека.
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


async def test_full_flow():
    """Тест полного пути отправки уведомления."""
    from app.telegram_bot.services import UzFlowerAPI
    from app.telegram_bot.config import settings as bot_settings
    
    print("=" * 60)
    print("🧪 Тест отправки уведомления в админ-бот")
    print("=" * 60)
    print()
    
    # Проверяем конфигурацию
    print("📋 Конфигурация:")
    print(f"   API URL: {bot_settings.api_url}")
    print(f"   API Secret: {bot_settings.api_secret[:10]}...")
    print(f"   ADMIN_BOT_TOKEN: {os.getenv('ADMIN_BOT_TOKEN', 'НЕ НАСТРОЕН')[:10]}...")
    print(f"   ADMIN_USER_ID: {os.getenv('ADMIN_USER_ID', 'НЕ НАСТРОЕН')}")
    print()
    
    api = UzFlowerAPI()
    
    # Тестовые данные
    test_data = {
        "order_id": 99999,
        "product_name": "Тестовый букет роз",
        "product_price": 150000,
        "customer_name": "Иван Тестов",
        "customer_phone": "+998901234567",
        "delivery_address": "ул. Тестовая, 1",
        "delivery_date": "2026-03-16 14:00",
        "total_amount": 170000,
        "delivery_option": True,
        "payment_proof_url": "https://example.com/test.jpg",
        "card_number": "4000 0000 0000 0000"
    }
    
    print("📤 Отправка уведомления...")
    print(f"   Заказ #: {test_data['order_id']}")
    print(f"   Товар: {test_data['product_name']}")
    print(f"   Сумма: {test_data['total_amount']:,} сум")
    print(f"   Чек: {'загружен' if test_data['payment_proof_url'] else 'нет'}")
    print()
    
    result = await api.send_order_to_admin_bot(**test_data)
    
    print()
    print("=" * 60)
    if result:
        print("✅ Тест пройден! Уведомление отправлено.")
    else:
        print("❌ Тест не пройден. Проверьте логи выше.")
    print("=" * 60)
    
    return result


if __name__ == "__main__":
    asyncio.run(test_full_flow())
