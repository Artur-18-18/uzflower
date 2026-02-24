# 🚀 Deploy to Render.com

Полное руководство по деплою UzFlower на Render.com

---

## 📋 Почему Render?

- ✅ **Бесплатный тариф** (Web Services)
- ✅ **Автоматический HTTPS**
- ✅ **PostgreSQL включён**
- ✅ **Auto-deploy из GitHub**
- ✅ **DDoS защита**

---

## 🎯 Пошаговая инструкция

### Шаг 1: Подготовка

1. **Создайте аккаунт на [Render.com](https://render.com)**
2. **Push проект на GitHub**:
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/yourusername/uzflower.git
   git push -u origin main
   ```

### Шаг 2: Создание Web Service

1. **Войдите на Render.com**
2. **Нажмите "New +" → "Web Service"**
3. **Выберите "Connect a repository"**
4. **Выберите репозиторий `uzflower`**

### Шаг 3: Настройка

#### 3.1 Basic Settings:

```
Name: uzflower
Region: Frankfurt (Germany) / London
Branch: main
Root Directory: (оставьте пустым)
```

#### 3.2 Runtime:

```
Runtime: Python 3
Build Command: pip install -r requirements.txt
Start Command: uvicorn main:app --host 0.0.0.0 --port $PORT
```

#### 3.3 Environment Variables:

```bash
Add Environment Variable:

DATABASE_URL: sqlite:///./uzflower.db
SECRET_KEY: your-super-secret-key-change-this
ENVIRONMENT: production
PYTHON_VERSION: 3.13.1
```

#### 3.4 Instance Type:

```
Free Tier:
- CPU: Shared
- Memory: 512MB
- Storage: Persistent

(Для production выберите Starter $7/месяц)
```

### Шаг 4: Advanced Settings

#### Auto-Deploy:

```
✅ Enabled (автоматический деплой при push)
```

#### Health Check Path:

```
/health
```

#### Docker:

```
❌ Disabled (используем Python runtime)
```

### Шаг 5: Деплой

1. **Нажмите "Create Web Service"**
2. **Ждите ~3-5 минут**
3. **Получите URL** вида: `https://uzflower.onrender.com`

### Шаг 6: Проверка

```bash
# Откройте в браузере
https://uzflower.onrender.com

# Проверьте API
curl https://uzflower.onrender.com/api/products

# Проверьте health
curl https://uzflower.onrender.com/health
```

---

## 🗄️ Добавление PostgreSQL

Render предоставляет бесплатную PostgreSQL:

### 1. Создайте базу:

```bash
New → PostgreSQL → Create Database

Name: uzflower-db
Database Name: uzflower
Region: Frankfurt (Germany)
```

### 2. Скопируйте Internal Database URL:

```bash
PostgreSQL → Connect → Internal Database URL
postgresql://uzflower:password@database-123:5432/uzflower
```

### 3. Обновите переменную:

```bash
Web Service → Environment → Add Variable

DATABASE_URL: postgresql://uzflower:password@database-123:5432/uzflower
```

### 4. Пересоберите:

```bash
Manual Deploy → Deploy
```

---

## 📊 Мониторинг

### Логи:

```bash
Web Service → Logs

# Real-time логи
# Фильтры по уровню
# Поиск
```

### Метрики:

```bash
Web Service → Metrics

- CPU Usage
- Memory Usage
- Request Count
- Response Time
```

### Alerts:

```bash
Settings → Alerts → Add Alert

- CPU > 80%
- Memory > 80%
- Downtime detected
```

---

## 💰 Тарифы

### Free:
- ✅ 750 часов в месяц
- ✅ 512MB RAM
- ✅ Shared CPU
- ⚠️ Засыпает через 15 мин бездействия

### Starter ($7/месяц):
- ✅ 512MB RAM
- ✅ 0.5 CPU
- ✅ Не засыпает
- ✅ 100GB bandwidth

### Standard ($14/месяц):
- ✅ 2GB RAM
- ✅ 1 CPU
- ✅ 400GB bandwidth

---

## 🔄 Автоматический деплой

Render автоматически деплоит при push в main ветку!

```bash
git push origin main
# → Render автоматически задеплоит через 2-4 минуты
```

### Manual Deploy:

```bash
Web Service → Manual Deploy → Deploy
```

### Rollback:

```bash
Deployments → Выберите предыдущий → Deploy
```

---

## 🐛 Troubleshooting

### Ошибка: "Build failed"

```bash
# Проверьте логи
Web Service → Logs

# Частые проблемы:
# 1. Нет requirements.txt
# 2. Ошибки в pip install
# 3. Неправильный Start Command
```

### Ошибка: "Service crashed"

```bash
# Проверьте логи
Web Service → Logs → Filter: ERROR

# Проверьте переменные
Web Service → Environment
```

### Ошибка: "Database connection failed"

```bash
# Создайте PostgreSQL
New → PostgreSQL

# Обновите DATABASE_URL
Web Service → Environment → DATABASE_URL
```

### Ошибка: "Service sleeping"

```bash
# Free тариф засыпает через 15 мин
# Для пробуждения просто откройте сайт

# Или upgrade до Starter ($7/месяц)
```

---

## 🔒 SSL/HTTPS

Render автоматически предоставляет SSL!

```
✅ HTTPS автоматически
✅ Let's Encrypt
✅ Auto-renewal
```

URL будет: `https://uzflower.onrender.com`

---

## 📧 Поддержка

- **Документация**: https://render.com/docs
- **Status**: https://status.render.com
- **Support**: support@render.com

---

## 🎯 Production Checklist

- [ ] Переменные окружения настроены
- [ ] PostgreSQL подключён
- [ ] Health check работает
- [ ] Логи собираются
- [ ] Alerts настроены
- [ ] Backup базы настроен
- [ ] DOMAIN подключён (опционально)

---

## 🌐 Custom Domain (опционально)

### 1. Добавьте домен:

```bash
Settings → Custom Domain → Add Custom Domain

Domain: uzflower.com
```

### 2. Настройте DNS:

```bash
У вашего регистратора доменов:

Type: CNAME
Name: www
Value: uzflower.onrender.com
```

### 3. SSL автоматически:

```bash
Render автоматически выпустит SSL сертификат
```

---

**Ready to deploy on Render! 🚀**
