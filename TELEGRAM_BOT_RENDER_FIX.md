# 🚀 Telegram Bot Fix для Render.com

## ❌ Проблема

После деплоя на Render.com Telegram боты не работали, потому что:
1. Боты используют **polling режим** (отдельный процесс)
2. На Render запущен **только uvicorn** (FastAPI сервер)
3. Боты не запускались автоматически

---

## ✅ Решение

Боты теперь запускаются **внутри lifespan контекста** FastAPI приложения.

### Что изменилось:

1. **main.py обновлён** - боты запускаются при старте сервера
2. **Новая переменная окружения** `ENABLE_TELEGRAM_BOTS` для управления
3. **Автоматическая остановка** ботов при shutdown сервера

---

## 📋 Инструкция по деплою на Render.com

### Шаг 1: Обновите код на GitHub

```bash
git add .
git commit -m "Fix: Запуск Telegram ботов через lifespan (для Render)"
git push origin main
```

### Шаг 2: Добавьте переменные окружения в Render

В панели Render.com перейдите в ваш проект → **Environment** и добавьте:

```bash
# Telegram Bot Settings
TELEGRAM_BOT_TOKEN=8676150074:AAFXKPfATw1cPrJVxiV4OP4vbmgdlHaEKN0
TELEGRAM_CHANNEL_ID=@uzflower_shop
TELEGRAM_OWNER_ID=0

# Admin Bot Settings
ADMIN_BOT_TOKEN=8443193754:AAHWu7NqH9nE7UHshZW4Jb0M3TqqMdlRcSA
ADMIN_USER_ID=1186442364
ADMIN_IDS=1186442364

# API Settings
TELEGRAM_API_URL=https://your-project.onrender.com
TELEGRAM_API_SECRET=telegram-bot-secret-key

# Включение ботов
ENABLE_TELEGRAM_BOTS=true

# Database (если используете PostgreSQL)
DATABASE_URL=postgresql://user:password@host:5432/dbname

# Secret Key
SECRET_KEY=your-super-secret-key-change-this
```

### Шаг 3: Проверьте Start Command

В настройках Render (**Settings → Build & Deploy**) убедитесь:

**Start Command:**
```bash
uvicorn main:app --host 0.0.0.0 --port $PORT
```

### Шаг 4: Перезапустите деплой

1. Перейдите в **Deployments**
2. Нажмите **Manual Deploy → Deploy latest commit**
3. Дождитесь завершения

---

## 🔍 Проверка работы

### 1. Проверьте логи сервера

В панели Render → **Logs** должны быть сообщения:

```
🤖 Запуск Telegram ботов...
✅ Telegram боты запущены в фоне
```

### 2. Проверьте ботов

- Отправьте `/start` основному боту: `@uzflowershop_bot`
- Отправьте `/start` админ-боту: `@uzfloweradmin_bot`

### 3. Проверьте API

```bash
curl https://your-project.onrender.com/api/products
```

---

## 🛠 Отладка

### Боты не запускаются?

#### Проверьте логи:

```bash
# В панели Render → Logs ищите:
"Запуск Telegram ботов"
"Ошибка при запуске бота"
```

#### Проверьте переменные окружения:

Убедитесь, что все токены установлены правильно:

```bash
# В Render → Environment должны быть:
TELEGRAM_BOT_TOKEN=...
ADMIN_BOT_TOKEN=...
ADMIN_USER_ID=...
ENABLE_TELEGRAM_BOTS=true
```

### Ошибка "Token is invalid"?

1. Проверьте токены в @BotFather
2. Убедитесь, что нет лишних пробелов в .env

### Боты работают, но не отвечают?

Проверьте webhook/polling:

```python
# Боты используют polling - это правильно для Render
# Webhook не нужен!
```

---

## 📊 Альтернативные варианты

### Вариант 1: Отключить ботов на сервере

Если хотите запускать ботов отдельно (например, на локальном сервере):

```bash
# В Render → Environment установите:
ENABLE_TELEGRAM_BOTS=false
```

Тогда на Render будет работать только API, а ботов можно запустить локально:

```bash
python run_bot.py
python run_admin_bot.py
```

### Вариант 2: Запуск ботов на отдельном сервисе

Создайте второй сервис на Render для ботов:

**Start Command для бота:**
```bash
python run_bot.py
```

**Start Command для админ-бота:**
```bash
python run_admin_bot.py
```

---

## 🎯 Проверка после деплоя

### Чеклист:

- [ ] Сайт открывается: `https://your-project.onrender.com`
- [ ] API работает: `https://your-project.onrender.com/api/products`
- [ ] Бот отвечает на `/start`: `@uzflowershop_bot`
- [ ] Админ-бот отвечает на `/start`: `@uzfloweradmin_bot`
- [ ] В логах есть: "✅ Telegram боты запущены в фоне"

---

## 📝 Технические детали

### Как это работает:

1. **lifespan контекст** FastAPI запускается при старте сервера
2. **asyncio.create_task()** создаёт фоновые задачи для ботов
3. Боты работают в **polling режиме** (`dp.start_polling`)
4. При shutdown сервера задачи **корректно отменяются**

### Структура:

```
main.py (FastAPI сервер)
├── lifespan()
│   ├── запуск сервера
│   ├── 🤖 start_telegram_bot() ← polling
│   └── 🤖 start_admin_bot() ← polling
└── API endpoints
```

---

## 🔗 Полезные ссылки

- [Render.com Docs](https://render.com/docs)
- [FastAPI Lifespan](https://fastapi.tiangolo.com/advanced/events/)
- [Aiogram Polling](https://docs.aiogram.dev/en/latest/dispatcher/polling.html)

---

## ✅ Status

- [x] Обновлён main.py (lifespan с ботами)
- [x] Обновлён .env.example (ENABLE_TELEGRAM_BOTS)
- [x] Проверен синтаксис
- [ ] **Закоммитить изменения**
- [ ] **Запушить на GitHub**
- [ ] **Деплой на Render.com**
- [ ] **Проверить работу ботов**

---

**После деплоя Telegram боты будут работать автоматически!** 🎉
