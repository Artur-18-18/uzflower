# 🤖 Telegram Bot Setup для UzFlower

## 📋 Обзор

Проект использует **два Telegram-бота**:
1. **Основной бот** (@uzflower_bot) - для взаимодействия с клиентами
2. **Админ-бот** (@uzfloweradmin_bot) - для обработки заказов администратором

## 🚀 Режимы работы

### 1. Webhook (Production - Render.com)

**Рекомендуемый режим для production!**

Преимущества:
- ✅ Нет конфликта `getUpdates` (оба бота работают одновременно)
- ✅ Мгновенная доставка обновлений
- ✅ Эффективное использование ресурсов
- ✅ Стабильная работа на Render.com

**Настройка .env:**
```env
ENABLE_TELEGRAM_BOTS=true
BOT_MODE=webhook
TELEGRAM_API_SECRET=your-secret-key-here
```

**Установка webhook:**
```bash
# После деплоя на Render вызовите:
GET https://your-app.onrender.com/api/telegram/set-webhook?base_url=https://your-app.onrender.com
```

Или вручную через BotFather:
```
/setwebhook
URL: https://your-app.onrender.com/api/telegram/webhook (для основного бота)
URL: https://your-app.onrender.com/api/admin-telegram/webhook (для админ-бота)
```

### 2. Polling (Локальная разработка)

**Только для локальной разработки!**

```env
ENABLE_TELEGRAM_BOTS=true
BOT_MODE=polling
```

**Запуск:**
```bash
# Запустить обоих ботов
python run_bots.py --mode polling

# Или по отдельности:
python run_bot.py              # Основной бот
python run_admin_bot.py        # Админ-бот
```

⚠️ **ВАЖНО:** При использовании polling:
- Не запускайте ботов на одном токене в нескольких процессах
- Для тестирования используйте разных ботов

## 📁 Структура файлов

```
uzflower/
├── run_bot.py                 # Запуск основного бота
├── run_admin_bot.py           # Запуск админ-бота
├── run_bots.py                # Запуск обоих ботов
├── main.py                    # FastAPI приложение + webhook endpoints
├── app/
│   ├── telegram_bot/
│   │   ├── bot.py             # Инициализация бота
│   │   ├── config.py          # Настройки
│   │   ├── handlers.py        # Обработчики команд
│   │   └── runner.py          # Универсальный runner (polling/webhook)
│   └── admin_bot/
│       ├── bot.py             # Инициализация админ-бота
│       ├── config.py          # Настройки
│       ├── handlers.py        # Обработчики команд
│       └── runner.py          # Универсальный runner (polling/webhook)
└── .env                       # Переменные окружения
```

## 🔧 Webhook Endpoints

| Endpoint | Описание |
|----------|----------|
| `POST /api/telegram/webhook` | Webhook для основного бота |
| `POST /api/admin-telegram/webhook` | Webhook для админ-бота |
| `GET /api/telegram/set-webhook?base_url=...` | Установка webhook |

## 🎯 Инструкции для Render.com

### 1. Переменные окружения

Добавьте в Render Dashboard → Environment:

```env
# Bot settings
ENABLE_TELEGRAM_BOTS=true
BOT_MODE=webhook

# Tokens
TELEGRAM_BOT_TOKEN=your-main-bot-token
ADMIN_BOT_TOKEN=your-admin-bot-token

# Admin
ADMIN_USER_ID=your-telegram-id
ADMIN_IDS=your-telegram-id

# API
TELEGRAM_API_SECRET=your-secret-key-here
TELEGRAM_API_URL=http://localhost:8000
```

### 2. После деплоя

Вызовите endpoint для установки webhook:
```bash
curl "https://your-app.onrender.com/api/telegram/set-webhook?base_url=https://your-app.onrender.com"
```

### 3. Проверка

Проверьте статус webhook:
```bash
# Основной бот
curl "https://api.telegram.org/bot<TELEGRAM_BOT_TOKEN>/getWebhookInfo"

# Админ-бот
curl "https://api.telegram.org/bot<ADMIN_BOT_TOKEN>/getWebhookInfo"
```

## 🧪 Локальная разработка

### Вариант 1: Polling (проще)

```bash
# Терминал 1 - запустить сервер
python main.py

# Терминал 2 - запустить ботов
python run_bots.py --mode polling
```

### Вариант 2: Webhook (как на production)

```bash
# Используем ngrok для туннеля
ngrok http 8000

# Копируем URL (например, https://abc123.ngrok.io)
# Вызываем установку webhook
curl "http://localhost:8000/api/telegram/set-webhook?base_url=https://abc123.ngrok.io"

# Запускаем сервер с webhook режимом
python main.py
```

## 🔐 Безопасность

1. **Смените TELEGRAM_API_SECRET** на уникальное значение
2. **Не коммитьте .env** в git
3. **Используйте Render Environment Variables** для секретов
4. **Проверяйте secret_token** в webhook requests

## 🐛 Troubleshooting

### Conflict: terminated by other getUpdates request

**Причина:** Бот запущен в нескольких экземплярах.

**Решение:**
1. Остановите все процессы с ботом
2. Используйте webhook режим для production
3. Для локальной разработки убедитесь, что только один процесс использует polling

### Webhook не работает

1. Проверьте, что BOT_MODE=webhook
2. Проверьте URL webhook (должен быть HTTPS)
3. Проверьте secret_token
4. Посмотрите логи: `GET https://api.telegram.org/bot<token>/getWebhookInfo`

### Бот не отвечает

1. Проверьте логи приложения
2. Убедитесь, что ENABLE_TELEGRAM_BOTS=true
3. Проверьте, что webhook установлен правильно
