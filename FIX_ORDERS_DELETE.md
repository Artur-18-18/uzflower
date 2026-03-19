# 🐛 Исправление: Ошибка при удалении заказов

## Проблема

При нажатии на кнопку **"Удалить все заказы"** в админке возникала ошибка:

```
Error: Internal Server Error
```

## Причина

При удалении всех заказов (`/api/admin/orders/all`) не удалялись сначала связанные записи:
- `OrderItem` — элементы заказов
- `Review` — отзывы, связанные с заказами

Это вызывало ошибку внешних ключей (Foreign Key constraint).

## Решение

Эндпоинт `/api/admin/orders/all` обновлён:

```python
@app.delete("/api/admin/orders/all")
async def clear_all_orders(...):
    # 1. Сначала удаляем отзывы о заказах
    db.query(Review).filter(Review.order_id.isnot(None)).delete()
    db.commit()
    
    # 2. Удаляем элементы заказов
    db.query(OrderItem).delete()
    db.commit()
    
    # 3. Теперь удаляем все заказы
    deleted_count = db.query(Order).delete()
    db.commit()
```

## ✅ Проверка

1. Запусти сайт:
   ```bash
   python main.py
   ```

2. Открой админку: `http://localhost:8000/admin`

3. Перейди в раздел **"Заказы"**

4. Нажми **"Удалить все заказы"**

5. Должно появиться сообщение:
   ```
   ✅ Удалено заказов: N
   ```

## 📝 Примечание

Если заказы не удаляются, проверь логи в `server_debug.log` — там будет подробная информация об ошибке.

---

**Исправлено в:** main.py (строка 2480)
