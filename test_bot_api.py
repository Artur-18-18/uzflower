"""
Тест получения товара через API бота.
"""
import asyncio
import sys
sys.path.insert(0, 'c:\\Users\\matka\\uzflower')

from app.telegram_bot.services import UzFlowerAPI

async def test_get_product():
    """Проверить получение товара."""
    api = UzFlowerAPI()
    
    # Тест с существующим товаром (ID=2)
    print("Тест 1: Получение товара ID=2 (Roza)")
    product = await api.get_product(2)
    if product:
        print(f"  ✅ Товар получен: {product.get('name')}")
        print(f"     Цена: {product.get('price')}")
        print(f"     Описание: {product.get('description', 'Нет описания')[:50]}")
    else:
        print("  ❌ Товар не найден")
    
    print()
    
    # Тест с несуществующим товаром (ID=1)
    print("Тест 2: Получение товара ID=1 (удалён)")
    product = await api.get_product(1)
    if product:
        print(f"  ✅ Товар получен: {product.get('name')}")
    else:
        print("  ❌ Товар не найден (ожидаемо)")
    
    print()
    
    # Тест с другим существующим товаром (ID=16)
    print("Тест 3: Получение товара ID=16 (роза)")
    product = await api.get_product(16)
    if product:
        print(f"  ✅ Товар получен: {product.get('name')}")
    else:
        print("  ❌ Товар не найден")

if __name__ == "__main__":
    asyncio.run(test_get_product())
