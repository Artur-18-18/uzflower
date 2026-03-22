# 🚀 Готово к Render.com!

## ✅ Сайт полностью готов к деплою

Все компоненты настроены для работы на Render.com:

### 📦 Что работает:

| Компонент | Статус | Примечание |
|-----------|--------|------------|
| **Сайт** | ✅ Готов | FastAPI + HTML/CSS/JS |
| **API** | ✅ Готов | REST API для товаров/заказов |
| **Telegram бот** | ✅ Готов | Webhook режим |
| **Admin бот** | ✅ Готов | Webhook режим |
| **Баннеры** | ✅ Исправлено | Видео + изображения |
| **Мобильная версия** | ✅ Исправлено | Модальное окно товара |
| **База данных** | ✅ Готово | SQLite / PostgreSQL |
| **Файлы** | ✅ Готово | Cloudinary / локально |

---

## 📋 Быстрый старт на Render

### 1️⃣ Закоммитьте изменения

```bash
cd c:\Users\matka\uzflower

git add .
git commit -m "Ready for Render deployment"
git push origin main
```

### 2️⃣ Создайте сервис на Render

1. Войдите на [render.com](https://render.com)
2. **New +** → **Web Service**
3. Подключите GitHub репозиторий
4. Выберите `uzflower`

### 3️⃣ Настройте сервис

**Basic Settings:**
```
Name: uzflower
Region: Frankfurt (Europe)
Branch: main
Root Directory: (оставьте пустым)
Runtime: Python 3
Build Command: pip install -r requirements.txt
Start Command: uvicorn main:app --host 0.0.0.0 --port $PORT
```

**Instance Type:**
- **Free** - для тестирования (засыпает через 15 мин)
- **Standard** - для продакшена ($7/мес)

### 4️⃣ Добавьте переменные окружения

В разделе **Environment** добавьте:

```bash
# Telegram Bot (ОБЯЗАТЕЛЬНО)
TELEGRAM_BOT_TOKEN=8676150074:AAFXKPfATw1cPrJVxiV4OP4vbmgdlHaEKN0
TELEGRAM_CHANNEL_ID=@uzflower_shop
TELEGRAM_OWNER_ID=0
ENABLE_TELEGRAM_BOTS=true
BOT_MODE=webhook

# Admin Bot (ОБЯЗАТЕЛЬНО)
ADMIN_BOT_TOKEN=8443193754:AAHWu7NqH9nE7UHshZW4Jb0M3TqqMdlRcSA
ADMIN_USER_ID=1186442364
ADMIN_IDS=1186442364

# API Settings (ВАЖНО!)
TELEGRAM_API_URL=http://localhost:8000
TELEGRAM_API_SECRET=telegram-bot-secret-key

# Database
DATABASE_URL=sqlite:///./uzflower.db
SECRET_KEY=uzflower-super-secret-key-production

# Cloudinary (опционально, для изображений)
# CLOUDINARY_CLOUD_NAME=your_cloud_name
# CLOUDINARY_API_KEY=your_api_key
# CLOUDINARY_API_SECRET=your_api_secret
```

### 5️⃣ Запустите деплой

1. Нажмите **Create Web Service**
2. Дождитесь завершения (5-10 минут)
3. Проверьте логи

---

## ✅ Проверка после деплоя

### 1. Сайт открывается

```
https://uzflower.onrender.com
```

### 2. API работает

```bash
curl https://uzflower.onrender.com/api/products
```

### 3. Боты работают

**Проверка webhook:**
```bash
# Основной бот
curl "https://api.telegram.org/bot8676150074:AAFXKPfATw1cPrJVxiV4OP4vbmgdlHaEKN0/getWebhookInfo"

# Админ-бот
curl "https://api.telegram.org/bot8443193754:AAHWu7NqH9nE7UHshZW4Jb0M3TqqMdlRcSA/getWebhookInfo"
```

**Ожидаемый ответ:**
```json
{
  "ok": true,
  "result": {
    "url": "https://uzflower.onrender.com/api/telegram/webhook",
    "has_custom_webhook": true,
    "pending_update_count": 0
  }
}
```

### 4. Тест заказа

1. Откройте сайт
2. Выберите товар
3. Нажмите **"Заказать в Telegram"**
4. Бот должен открыть товар

---

## 🔧 Настройка webhook

После деплоя установите webhook:

```bash
curl "https://uzflower.onrender.com/api/telegram/set-webhook?base_url=https://uzflower.onrender.com"
```

Или вручную через BotFather:
```
/setwebhook
URL: https://uzflower.onrender.com/api/telegram/webhook
```

---

## 🐛 Отладка проблем

### Боты не работают?

**Проверьте логи:**
```
Render Dashboard → Logs

Ищите:
✅ "Боты настроены в режиме webhook"
✅ "Webhook установлен для основного бота"
❌ "Ошибка при запуске бота"
```

**Проверьте переменные:**
```bash
# В Render Dashboard → Environment
TELEGRAM_BOT_TOKEN=✅
ADMIN_BOT_TOKEN=✅
ENABLE_TELEGRAM_BOTS=true
BOT_MODE=webhook
```

### Видео баннеров не работает?

**Проверьте формат:**
- ✅ MP4 (H.264)
- ✅ WebM
- ❌ MOV (может не работать)

**Проверьте логи:**
```
Console (F12) → "Видео загружено" или "Ошибка загрузки видео"
```

### Мобильное модальное окно не показывает фото?

**Проверьте консоль:**
```
Console (F12) → "Добавлено главное изображение"
```

**Проверьте товар:**
- Главное фото загружено?
- Дополнительные фото загружены?

---

## 📊 Мониторинг

### Логи

- **Render Dashboard → Logs** - все логи сервера
- **Console (F12)** - логи браузера

### Метрики

- **Render Dashboard → Metrics** - CPU/Memory
- **Render Dashboard → Deployments** - история деплоев

---

## 🔄 Обновление кода

### Автоматически (Auto-Deploy)

```bash
git add .
git commit -m "Fix: something"
git push origin main
```

Render автоматически задеплоит через 1-2 минуты.

### Вручную

1. Render → Deployments
2. **Manual Deploy** → **Deploy latest commit**

---

## 💡 Советы

### 1. Используйте Cloudinary

Для изображений и видео:
```bash
CLOUDINARY_CLOUD_NAME=your_name
CLOUDINARY_API_KEY=your_key
CLOUDINARY_API_SECRET=your_secret
```

### 2. PostgreSQL для продакшена

1. Создайте **Render PostgreSQL**
2. Скопируйте **External Database URL**
3. Замените `DATABASE_URL`

### 3. Стандартный тариф

Free тариф засыпает через 15 минут. Для продакшена:
- **Standard** ($7/мес) - не засыпает
- **Pro** ($25/мес) - больше ресурсов

### 4. Секретные ключи

Используйте **Generate Value** для:
- `SECRET_KEY`
- `TELEGRAM_API_SECRET`

---

## 📝 Чеклист

- [ ] Код закоммичен в git
- [ ] `.env` в `.gitignore`
- [ ] `render.yaml` создан
- [ ] Переменные окружения настроены
- [ ] `TELEGRAM_API_URL=http://localhost:8000`
- [ ] `BOT_MODE=webhook`
- [ ] Токены ботов правильные
- [ ] Бот добавлен в канал
- [ ] Webhook установлен

---

## 🎯 Полный тест

1. ✅ Сайт открывается
2. ✅ Товары отображаются
3. ✅ Фото товаров видны
4. ✅ Видео баннеров работает
5. ✅ Мобильная версия работает
6. ✅ Кнопка "Заказать в Telegram" работает
7. ✅ Бот открывает товар
8. ✅ Можно оформить заказ
9. ✅ Админ-бот получает уведомление

---

## 🔗 Ссылки

- **Render Dashboard:** https://dashboard.render.com
- **BotFather:** https://t.me/BotFather
- **Cloudinary:** https://cloudinary.com

---

## ✅ Готово!

Ваш сайт UzFlower готов к деплою на Render.com! 🎉

**Сайт:** `https://uzflower.onrender.com`
**Бот:** `@uzflowershop_bot`
**Админ-бот:** `@uzfloweradmin_bot`

**Удачи!** 🌸
