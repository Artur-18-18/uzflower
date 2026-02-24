# 🚀 Quick Deploy - Railway & Render

Самый быстрый способ задеплоить UzFlower!

---

## ⚡ 2 минуты до запуска

### Вариант 1: Railway (Рекомендуется)

```bash
# 1. Откройте Railway.app
https://railway.app

# 2. New Project → Deploy from GitHub
# 3. Выберите репозиторий uzflower
# 4. Добавьте переменные:
DATABASE_URL=sqlite:///./uzflower.db
SECRET_KEY=change-this-to-random-string
ENVIRONMENT=production

# 5. Готово! ✅
```

**Время:** ~2 минуты  
**Цена:** $5/месяц (или бесплатно с $5 кредитами)

---

### Вариант 2: Render

```bash
# 1. Откройте Render.com
https://render.com

# 2. New + → Web Service
# 3. Connect repository → uzflower
# 4. Настройте:
Build Command: pip install -r requirements.txt
Start Command: uvicorn main:app --host 0.0.0.0 --port $PORT

# 5. Готово! ✅
```

**Время:** ~3 минуты  
**Цена:** Бесплатно (но sleep mode) или $7/месяц

---

## 📊 Какую платформу выбрать?

| Критерий | Railway | Render |
|----------|---------|--------|
| **Скорость** | ⚡ 2 мин | ⚡ 3 мин |
| **Простота** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Цена** | $5/мес | $0 или $7/мес |
| **RAM** | 1GB | 512MB |
| **Sleep** | ❌ Нет | ⚠️ 15 мин |
| **Рекомендация** | 🏆 Лучший | 💰 Бесплатно |

### Мой выбор: **Railway** 🏆

Почему:
- ✅ Проще настройка
- ✅ Больше RAM (1GB)
- ✅ Нет sleep mode
- ✅ $5 кредитов бесплатно

---

## 🎯 Пошаговые инструкции

### Railway:

1. **Создайте аккаунт** → https://railway.app
2. **Login через GitHub**
3. **New Project**
4. **Deploy from GitHub repo**
5. **Выберите `uzflower`**
6. **Add Variables:**
   ```
   DATABASE_URL=sqlite:///./uzflower.db
   SECRET_KEY=your-secret-key-change-this
   ENVIRONMENT=production
   ```
7. **Deploy**
8. **Получите URL** → `https://uzflower-production.up.railway.app`

**Полная инструкция:** [`DEPLOY_RAILWAY.md`](DEPLOY_RAILWAY.md)

---

### Render:

1. **Создайте аккаунт** → https://render.com
2. **Login через GitHub**
3. **New + → Web Service**
4. **Connect repository**
5. **Выберите `uzflower`**
6. **Configure:**
   ```
   Name: uzflower
   Build Command: pip install -r requirements.txt
   Start Command: uvicorn main:app --host 0.0.0.0 --port $PORT
   ```
7. **Advanced:**
   ```
   Auto-Deploy: ✅ Enabled
   Health Check: /health
   ```
8. **Create Web Service**
9. **Получите URL** → `https://uzflower.onrender.com`

**Полная инструкция:** [`DEPLOY_RENDER.md`](DEPLOY_RENDER.md)

---

## 🔧 Переменные окружения

### Обязательно настройте:

```bash
DATABASE_URL=sqlite:///./uzflower.db
SECRET_KEY=change-this-to-random-string-xyz123
ENVIRONMENT=production
PYTHON_VERSION=3.13
```

### Опционально:

```bash
CLICK_SERVICE_ID=your-click-id
CLICK_MERCHANT_ID=your-click-merchant
PAYME_MERCHANT_ID=your-payme-id
```

### Для разработки (локально):

```bash
# Production зависимости
pip install -r requirements.txt

# Development зависимости (для тестов)
pip install -r requirements-dev.txt
```

---

## ✅ Проверка после деплоя

```bash
# 1. Откройте сайт
https://your-project.up.railway.app

# 2. Проверьте API
curl https://your-project.up.railway.app/api/products

# 3. Проверьте health
curl https://your-project.up.railway.app/health

# 4. Проверьте админку
https://your-project.up.railway.app/admin
```

---

## 🐛 Troubleshooting

### "Build failed"

```bash
# Проверьте логи в панели управления
# Частые проблемы:
# - Нет requirements.txt
# - Ошибки в pip install
```

### "Service crashed"

```bash
# Проверьте переменные окружения
# Особенно SECRET_KEY и DATABASE_URL
```

### "Database not found"

```bash
# Railway: New → Database → Add PostgreSQL
# Render: New → PostgreSQL
# Обновите DATABASE_URL
```

---

## 📈 Следующие шаги

1. ✅ Настройте домен (опционально)
2. ✅ Включите HTTPS (автоматически)
3. ✅ Настройте бэкапы
4. ✅ Добавьте мониторинг
5. ✅ Настройте alerts

---

## 📚 Документация

- **Railway:** [`DEPLOY_RAILWAY.md`](DEPLOY_RAILWAY.md)
- **Render:** [`DEPLOY_RENDER.md`](DEPLOY_RENDER.md)
- **Сравнение:** [`PLATFORM_COMPARISON.md`](PLATFORM_COMPARISON.md)
- **Полная:** [`DEPLOYMENT.md`](DEPLOYMENT.md)

---

## 💰 Стоимость

### Railway:

```
Hobby: $5/месяц
- 500 часов
- 1GB RAM
- $5 кредитов включено
```

### Render:

```
Free: $0/месяц
- 750 часов
- 512MB RAM
- ⚠️ Sleep после 15 мин

Starter: $7/месяц
- Unlimited hours
- 512MB RAM
- ✅ No sleep
```

---

**Choose your platform and deploy! 🚀**
