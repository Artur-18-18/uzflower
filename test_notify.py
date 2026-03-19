"""
Тестовый скрипт для проверки отправки уведомления в админ-бот.
"""

import asyncio
import httpx
import os
from dotenv import load_dotenv

load_dotenv()

API_URL = os.getenv("TELEGRAM_API_URL", "http://localhost:8000")
API_SECRET = os.getenv("TELEGRAM_API_SECRET", "telegram-bot-secret-key")


async def test_notify_admin():
    """Тест отправки уведомления в админ-бот."""
    print(f"🔍 Тест отправки уведомления в админ-бот")
    print(f"   API URL: {API_URL}")
    print(f"   API Secret: {API_SECRET}")
    print()

    async with httpx.AsyncClient(timeout=30.0) as client:
        payload = {
            "order_id": 99999,  # Тестовый ID
            "product_name": "Тестовый букет",
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

        headers = {
            "Authorization": f"Bearer {API_SECRET}",
            "Content-Type": "application/json"
        }

        endpoint = f"{API_URL}/api/telegram/orders/notify-admin"
        print(f"📤 Отправка POST запроса на: {endpoint}")
        print(f"   Payload: {payload}")
        print()

        try:
            response = await client.post(endpoint, json=payload, headers=headers)
            print(f"📥 Ответ сервера:")
            print(f"   Статус: {response.status_code}")
            print(f"   Тело: {response.text}")
            print()

            if response.status_code == 200:
                print("✅ Уведомление успешно отправлено!")
            elif response.status_code == 401:
                print("❌ Ошибка авторизации (401): Проверьте TELEGRAM_API_SECRET")
            elif response.status_code == 403:
                print("❌ Ошибка авторизации (403): Неправильный токен")
            else:
                print(f"❌ Ошибка сервера: {response.status_code}")

        except httpx.ConnectError as e:
            print(f"❌ Ошибка подключения: {e}")
            print("   Убедитесь, что сервер запущен на {API_URL}")
        except Exception as e:
            print(f"❌ Ошибка: {e}")


if __name__ == "__main__":
    asyncio.run(test_notify_admin())
