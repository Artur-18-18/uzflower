"""
Тест подключения к API для Telegram-бота.
"""
import asyncio
import httpx
import os
from dotenv import load_dotenv

load_dotenv()

API_URL = os.getenv("TELEGRAM_API_URL", "http://localhost:8000")
API_SECRET = os.getenv("TELEGRAM_API_SECRET", "telegram-bot-secret-key")

async def test_api():
    """Проверить подключение к API."""
    print(f"🔍 Тестирование подключения к API: {API_URL}")
    print("=" * 50)
    
    # Тест 1: Проверка доступности сервера
    print("\n1. Проверка доступности сервера...")
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{API_URL}/")
            print(f"   ✅ Сервер доступен: статус {response.status_code}")
    except Exception as e:
        print(f"   ❌ Сервер недоступен: {e}")
        return
    
    # Тест 2: Получение списка товаров
    print("\n2. Получение списка товаров...")
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{API_URL}/api/products")
            print(f"   ✅ Статус: {response.status_code}")
            products = response.json()
            print(f"   📦 Найдено товаров: {len(products) if isinstance(products, list) else 'N/A'}")
            
            if isinstance(products, list) and len(products) > 0:
                first_product = products[0]
                print(f"   🌸 Первый товар: ID={first_product.get('id')}, name={first_product.get('name', 'N/A')}")
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
    
    # Тест 3: Получение конкретного товара (ID=1)
    print("\n3. Получение товара ID=1...")
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{API_URL}/api/products/1")
            print(f"   ✅ Статус: {response.status_code}")
            print(f"   📥 Ответ: {response.text[:200]}")
            
            if response.status_code == 200:
                product = response.json()
                print(f"   🌸 Товар: {product.get('name', 'N/A')}")
            else:
                print(f"   ⚠️ Ошибка: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
    
    # Тест 4: Проверка авторизации бота
    print("\n4. Проверка авторизации бота...")
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{API_URL}/api/products",
                headers={"Authorization": f"Bearer {API_SECRET}"}
            )
            print(f"   ✅ Статус с авторизацией: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
    
    print("\n" + "=" * 50)
    print("Тестирование завершено!")

if __name__ == "__main__":
    asyncio.run(test_api())
