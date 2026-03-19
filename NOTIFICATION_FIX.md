# 🔔 Исправление уведомлений покупателям

## Проблема

Уведомления покупателям о принятии/отмене заказа не приходили, потому что:

1. **Заказы создавались без `user_id`** (анонимные заказы)
2. **Telegram ID покупателя не сохранялся** в заказе
3. **Невозможно было найти покупателя** для отправки уведомления

## Решение

### 1. Сохранение Telegram ID при создании заказа

**Файлы:**
- `app/telegram_bot/handlers.py` - получение Telegram ID из сообщения
- `app/telegram_bot/services.py` - передача Telegram ID в API
- `main.py` - сохранение Telegram ID в поле `external_id`

**Изменения:**

```python
# handlers.py - Получаем Telegram ID пользователя
customer_telegram_id = message.from_user.id

# services.py - Передаём в API
await api.create_order(
    ...,
    customer_telegram_id=customer_telegram_id
)

# main.py - Сохраняем в external_id
order = Order(
    ...,
    external_id=str(order_data.customer_telegram_id) if order_data.customer_telegram_id else None
)
```

### 2. Возврат Telegram ID в API заказа

**Файл:** `main.py`

```python
@app.get("/api/admin/bot/orders/{order_id}")
async def admin_bot_get_order(...):
    # Получаем Telegram ID из external_id
    customer_telegram_id = None
    if order.external_id and order.external_id.isdigit():
        customer_telegram_id = int(order.external_id)
    
    return {
        ...,
        "customer_telegram_id": customer_telegram_id
    }
```

### 3. Упрощение получения Telegram ID в админ-боте

**Файл:** `app/admin_bot/handlers.py`

```python
# Было (сложный путь через user_id):
user_id_from_order = order.get("user_id")
if user_id_from_order:
    customer_telegram_id = await api.get_user_telegram_id(user_id_from_order)

# Стало (прямой путь из заказа):
customer_telegram_id = order.get("customer_telegram_id")
```

### 4. Добавлено подробное логирование

**Файлы:**
- `app/admin_bot/handlers.py` - логи каждого этапа
- `app/admin_bot/services.py` - логи отправки запроса
- `main.py` - логи получения запроса и отправки в Telegram

## Как это работает теперь

### Создание заказа

```
Пользователь отправляет заказ в Telegram-боте
       ↓
Бот получает Telegram ID из message.from_user.id
       ↓
Передаёт Telegram ID в API при создании заказа
       ↓
Сервер сохраняет Telegram ID в поле external_id
       ↓
Заказ создан с Telegram ID
```

### Уведомление покупателя

```
Админ нажимает "✅ Принять" в админ-боте
       ↓
Админ-бот получает заказ из API
       ↓
Получает customer_telegram_id напрямую из заказа
       ↓
Отправляет запрос на /api/admin/notify-customer-order-status
       ↓
Сервер отправляет сообщение покупателю через Telegram Bot API
       ↓
Покупатель получает уведомление
```

## Тестирование

### 1. Создайте новый заказ через Telegram-бота

```
1. Откройте @uzflowershop_bot
2. Оформите тестовый заказ
3. Отправьте чек
```

### 2. Проверьте логи сервера

```
INFO: 📦 Завершение заказа: product_id=X, name=Y, phone=Z, telegram_id=1186442364
INFO: 📤 Создание заказа: {..., 'customer_telegram_id': 1186442364}
INFO: ✅ Заказ создан через Telegram: ID=N
```

### 3. Примите заказ через админ-бота

```
1. Откройте @uzfloweradmin_bot
2. Найдите уведомление о заказе
3. Нажмите "✅ Принять"
```

### 4. Проверьте логи

**admin_bot.log:**
```
INFO: 🔔 Получен callback на принятие заказа #N
INFO:    Получен заказ: {..., 'customer_telegram_id': 1186442364}
INFO:    Telegram ID покупателя из заказа: 1186442364
INFO:    Статус заказа обновлён: True
INFO:    Отправка уведомления покупателю #1186442364
INFO:    Результат отправки уведомления: True
```

**server_debug.log:**
```
INFO: 📬 Получен запрос на уведомление покупателя: order_id=N, status=accepted, telegram_id=1186442364
INFO: 📤 Отправка сообщения в Telegram: chat_id=1186442364
INFO:    Ответ Telegram: {'ok': True, 'result': {'message_id': X}}
INFO: ✅ Покупатель #1186442364 уведомлён о статусе заказа #N: accepted
```

### 5. Проверьте Telegram

Откройте чат с @uzflowershop_bot - вы должны получить уведомление:
```
✅ Ваш заказ принят!

Уважаемый(ая) Тест,

Ваш заказ #N был принят нашим менеджером.
...
```

## Структура данных заказа

```json
{
  "id": 123,
  "customer_name": "Иван",
  "customer_telegram_id": 1186442364,
  "total_amount": 150000,
  "status": "accepted",
  "phone": "+998901234567",
  ...
}
```

## Логи для отладки

### Если уведомление не приходит

1. **Проверьте логи сервера:**
   ```
   server_debug.log - ищите "Получен запрос на уведомление покупателя"
   ```

2. **Проверьте логи админ-бота:**
   ```
   admin_bot.log - ищите "Telegram ID покупателя"
   ```

3. **Проверьте, что Telegram ID сохранён:**
   - Создайте новый заказ
   - Проверьте в логах: `telegram_id=XXXXXXXX`
   - Проверьте в API: `GET /api/admin/bot/orders/{id}` → `customer_telegram_id`

4. **Проверьте, что бот не заблокирован:**
   - Покупатель не должен блокировать @uzflowershop_bot

### Частые ошибки

| Ошибка | Причина | Решение |
|--------|---------|---------|
| "Telegram ID не найден" | Старый заказ без Telegram ID | Создайте новый заказ |
| "Bot token not configured" | Не настроен TELEGRAM_BOT_TOKEN | Проверьте .env файл |
| "Telegram error: Forbidden" | Бот заблокирован | Попросите покупателя разблокировать |
| "Bad Request: chat not found" | Неверный Telegram ID | Проверьте сохранение ID |

## Изменения в коде

### Файлы изменены:

1. **app/telegram_bot/handlers.py**
   - Получение `customer_telegram_id` из `message.from_user.id`
   - Передача `customer_telegram_id` в `create_order()`

2. **app/telegram_bot/services.py**
   - Добавлен параметр `customer_telegram_id` в метод `create_order()`
   - Передача Telegram ID в API

3. **main.py**
   - Добавлено поле `customer_telegram_id` в `TelegramOrderCreate`
   - Сохранение Telegram ID в `external_id`
   - Возврат `customer_telegram_id` в `admin_bot_get_order()`
   - Добавлено логирование в `admin_notify_customer_order_status()`

4. **app/admin_bot/handlers.py**
   - Упрощено получение Telegram ID (напрямую из заказа)
   - Добавлено подробное логирование

5. **app/admin_bot/services.py**
   - Добавлено логирование в `notify_customer_order_status()`

## Требования

- ✅ TELEGRAM_BOT_TOKEN должен быть настроен
- ✅ Покупатель не должен блокировать бота
- ✅ Новые заказы создаются с Telegram ID

## Будущие улучшения

- [ ] Перенос старых заказов с Telegram ID (из external_id)
- [ ] Добавление поля `customer_telegram_id` в таблицу orders
- [ ] Поддержка уведомлений для статусов "delivering" и "completed"
