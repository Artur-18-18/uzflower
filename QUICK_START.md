# 🚀 Быстрый старт - Telegram боты UzFlower

## ✅ Проблема решена!

Теперь оба бота работают **независимо** через **webhook** режим.

---

## 📦 Что изменилось

### Новые файлы:
- `app/telegram_bot/runner.py` - универсальный запуск основного бота
- `app/admin_bot/runner.py` - универсальный запуск админ-бота
- `run_bots.py` - запуск обоих ботов вместе
- `BOT_SETUP.md` - полная документация

### Обновлённые файлы:
- `main.py` - добавлены webhook endpoints
- `run_bot.py` - поддержка polling/webhook
- `run_admin_bot.py` - поддержка polling/webhook
- `.env.example` - новые переменные `BOT_MODE`

---

## 🎯 Использование

### Для Render.com (Production)

**1. Настройте .env:**
```env
ENABLE_TELEGRAM_BOTS=true
BOT_MODE=webhook
TELEGRAM_API_SECRET=ваш-секретный-ключ
```

**2. После деплоя установите webhook:**
```bash
curl "https://your-app.onrender.com/api/telegram/set-webhook?base_url=https://your-app.onrender.com"
```

**Готово!** Оба бота работают независимо.

---

### Для локальной разработки (Polling)

**1. Настройте .env:**
```env
ENABLE_TELEGRAM_BOTS=true
BOT_MODE=polling
```

**2. Запустите сервер:**
```bash
python main.py
```

**3. В другом окне запустите ботов:**
```bash
# Оба бота вместе:
python run_bots.py --mode polling

# Или по отдельности:
python run_bot.py              # Основной бот
python run_admin_bot.py        # Админ-бот
```

---

## 🔍 Проверка работы

### Проверка webhook статуса:
```bash
# Основной бот
curl "https://api.telegram.org/bot<TELEGRAM_BOT_TOKEN>/getWebhookInfo"

# Админ-бот
curl "https://api.telegram.org/bot<ADMIN_BOT_TOKEN>/getWebhookInfo"
```

### Логи сервера:
```bash
# Windows PowerShell
Get-Content server_debug.log -Tail 50 -Wait

# Linux/Mac
tail -f server_debug.log
```

---

## 🛠️ Переменные окружения

| Переменная | Значение | Описание |
|------------|----------|----------|
| `ENABLE_TELEGRAM_BOTS` | `true`/`false` | Включить ботов |
| `BOT_MODE` | `webhook`/`polling` | Режим работы |
| `TELEGRAM_BOT_TOKEN` | токен | Токен основного бота |
| `ADMIN_BOT_TOKEN` | токен | Токен админ-бота |
| `TELEGRAM_API_SECRET` | секрет | Секретный ключ для webhook |
| `ADMIN_USER_ID` | ID | Telegram ID админа |

---

## ❓ Troubleshooting

### "Conflict: terminated by other getUpdates request"

**Причина:** Бот запущен в polling режиме в нескольких экземплярах.

**Решение:**
1. Завершите все процессы Python
2. На Render используйте `BOT_MODE=webhook`
3. Локально запускайте только один экземпляр бота

### Webhook не работает

1. Проверьте `BOT_MODE=webhook` в .env
2. Убедитесь, что webhook установлен:
   ```bash
   curl "https://your-app.onrender.com/api/telegram/set-webhook?base_url=https://your-app.onrender.com"
   ```
3. Проверьте логи сервера

---

## 📚 Полная документация

См. [`BOT_SETUP.md`](BOT_SETUP.md) для подробной информации.
