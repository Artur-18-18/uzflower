# 🚀 Развёртывание UzFlower на Render.com с Telegram ботами

## ✅ Готово к деплою!

Все настройки обновлены для работы на Render.com. Telegram боты будут работать автоматически вместе с сервером.

---

## 📋 Шаг 1: Подготовка GitHub репозитория

### 1.1 Закоммитьте все изменения

```bash
cd c:\Users\matka\uzflower

git add .
git commit -m "Fix: Telegram bots working on Render.com"
git push origin main
```

### 1.2 Проверьте .gitignore

Убедитесь, что следующие файлы НЕ в git:
- `.env` ❌
- `uzflower.db` ❌
- `__pycache__/` ❌
- `static/uploads/` ❌

---

## 📋 Шаг 2: Настройка Render.com

### 2.1 Создайте новый сервис (или обновите существующий)

1. Войдите на [render.com](https://render.com)
2. Нажмите **New +** → **Web Service**
3. Подключите ваш GitHub репозиторий
4. Выберите репозиторий `uzflower`

### 2.2 Настройте сервис

**Basic Settings:**
- **Name:** `uzflower` (или ваше название)
- **Region:** Выберите ближайший к вам
- **Branch:** `main`
- **Root Directory:** (оставьте пустым)
- **Runtime:** `Python 3`
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`

**Instance Type:**
- **Free** (для тестирования)
- **Standard** (для продакшена)

### 2.3 Добавьте переменные окружения

В разделе **Environment** добавьте:

```bash
# ============================================
# Telegram Bot Settings (ОБЯЗАТЕЛЬНО)
# ============================================
TELEGRAM_BOT_TOKEN=8676150074:AAFXKPfATw1cPrJVxiV4OP4vbmgdlHaEKN0
TELEGRAM_CHANNEL_ID=@uzflower_shop
TELEGRAM_OWNER_ID=0
ENABLE_TELEGRAM_BOTS=true

# ============================================
# Admin Bot Settings (ОБЯЗАТЕЛЬНО)
# ============================================
ADMIN_BOT_TOKEN=8443193754:AAHWu7NqH9nE7UHshZW4Jb0M3TqqMdlRcSA
ADMIN_USER_ID=1186442364
ADMIN_IDS=1186442364

# ============================================
# API Settings (ВАЖНО: localhost для Render!)
# ============================================
TELEGRAM_API_URL=http://localhost:8000
TELEGRAM_API_SECRET=telegram-bot-secret-key

# ============================================
# Database Settings
# ============================================
DATABASE_URL=sqlite:///./uzflower.db
SECRET_KEY=uzflower-super-secret-key-production

# ============================================
# Cloudinary (опционально, для изображений)
# ============================================
# CLOUDINARY_CLOUD_NAME=your_cloud_name
# CLOUDINARY_API_KEY=your_api_key
# CLOUDINARY_API_SECRET=your_api_secret
```

### 2.4 Настройте базу данных (опционально)

Для продакшена рекомендуется PostgreSQL:

1. Создайте **Render PostgreSQL** в том же регионе
2. Скопируйте **External Database URL**
3. Замените `DATABASE_URL` в настройках сервиса

---

## 📋 Шаг 3: Деплой

### 3.1 Запустите деплой

1. Перейдите в **Deployments**
2. Нажмите **Manual Deploy** → **Deploy latest commit**
3. Дождитесь завершения (5-10 минут)

### 3.2 Проверьте логи

В разделе **Logs** должны быть сообщения:

```
✅ Кэширование инициализировано
🤖 Запуск Telegram ботов...
✅ Telegram боты запущены в фоне
```

---

## 📋 Шаг 4: Проверка работы

### 4.1 Проверка сайта

Откройте ваш сайт:
```
https://uzflower.onrender.com
```

### 4.2 Проверка API

```bash
curl https://uzflower.onrender.com/api/products
```

### 4.3 Проверка Telegram ботов

1. Откройте `@uzflowershop_bot` в Telegram
2. Отправьте `/start`
3. Бот должен ответить приветствием

### 4.4 Проверка админ-бота

1. Откройте `@uzfloweradmin_bot` в Telegram
2. Отправьте `/start`
3. Бот должен показать меню администратора

---

## 🔧 Настройка Telegram ботов

### Добавление бота в канал

1. Откройте ваш Telegram канал
2. Настройки → Администраторы → Добавить
3. Найдите `@uzflowershop_bot`
4. Дайте права на **чтение сообщений**

### Проверка deep-link для товаров

1. Откройте сайт на Render
2. Откройте любой товар
3. Нажмите **"Заказать в Telegram"**
4. Должен открыться бот с товаром

---

## 🛠 Отладка проблем

### Боты не запускаются?

#### Проверьте логи Render:

```
В панели Render → Logs ищите:
- "Запуск Telegram ботов"
- "Ошибка при запуске бота"
- "Telegram боты запущены в фоне"
```

#### Проверьте переменные окружения:

Убедитесь, что установлены:
- `TELEGRAM_BOT_TOKEN`
- `ADMIN_BOT_TOKEN`
- `ADMIN_USER_ID`
- `ENABLE_TELEGRAM_BOTS=true`

### Боты работают, но не видят товары?

#### Проверьте TELEGRAM_API_URL:

**ВАЖНО:** На Render должно быть:
```bash
TELEGRAM_API_URL=http://localhost:8000
```

НЕ используйте внешний URL типа `https://uzflower.onrender.com`!

#### Проверьте TELEGRAM_API_SECRET:

Должен совпадать с секретом в main.py:
```bash
TELEGRAM_API_SECRET=telegram-bot-secret-key
```

### Ошибка "Token is invalid"?

1. Проверьте токены в @BotFather
2. Убедитесь, что нет лишних пробелов
3. Перезапустите бот на Render (Restart)

### Товары не создаются из канала?

1. Убедитесь, что бот добавлен в канал
2. Проверьте `TELEGRAM_CHANNEL_ID`
3. Убедитесь, что бот имеет права на чтение

---

## 📊 Мониторинг

### Логи

- **Server Logs:** Render → Logs
- **Bot Logs:** Ищите сообщения с "🤖" и "✅"

### Метрики

- **CPU/Memory:** Render → Metrics
- **Requests:** Render → Metrics

---

## 🔄 Обновление кода

### Автоматический деплой

При пуше в `main`:
```bash
git push origin main
```

Render автоматически задеплоит изменения.

### Ручной деплой

1. Render → Deployments
2. Manual Deploy → Deploy latest commit

---

## 💡 Советы для Render

### 1. Используйте бесплатный тариф с умом

- Бесплатный тариф "засыпает" через 15 минут бездействия
- Первый запрос после "сна" может занимать 30-50 секунд
- Для продакшена используйте Standard тариф ($7/мес)

### 2. Оптимизируйте базу данных

- Для продакшена используйте PostgreSQL
- SQLite подходит только для тестирования

### 3. Настройте Cloudinary

- Для хранения изображений используйте Cloudinary
- Это быстрее и надёжнее локального хранения

### 4. Мониторьте логи

- Проверяйте логи после каждого деплоя
- Настройте алерты на ошибки

---

## 📝 Чеклист перед деплоем

- [ ] Все изменения закоммичены в git
- [ ] `.env` не в git (добавлен в `.gitignore`)
- [ ] Переменные окружения настроены на Render
- [ ] `TELEGRAM_API_URL=http://localhost:8000`
- [ ] `ENABLE_TELEGRAM_BOTS=true`
- [ ] Токены ботов правильные
- [ ] Бот добавлен в канал
- [ ] `ADMIN_USER_ID` указан правильно

---

## 🎯 Проверка после деплоя

### Полный тест заказа:

1. ✅ Сайт открывается
2. ✅ Товары отображаются
3. ✅ Кнопка "Заказать в Telegram" работает
4. ✅ Бот открывает товар
5. ✅ Можно оформить заказ
6. ✅ Админ-бот получает уведомление

---

## 🔗 Полезные ссылки

- [Render Docs](https://render.com/docs)
- [FastAPI на Render](https://render.com/deploy/fastapi)
- [Telegram Bot API](https://core.telegram.org/bots/api)

---

## ✅ Готово!

Ваш сайт UzFlower с Telegram ботами работает на Render.com! 🎉

**Сайт:** `https://uzflower.onrender.com`
**Бот:** `@uzflowershop_bot`
**Админ-бот:** `@uzfloweradmin_bot`

---

## 🆘 Нужна помощь?

Если что-то не работает:

1. Проверьте логи на Render
2. Проверьте переменные окружения
3. Убедитесь, что все токены правильные
4. Попробуйте перезапустить сервис (Restart)

**Удачи!** 🌸
