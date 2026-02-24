# 🚀 Deploy to Railway.app

Полное руководство по деплою UzFlower на Railway.app

---

## 📋 Почему Railway?

- ✅ **Бесплатный тариф** ($5 кредитов в месяц)
- ✅ **Автоматический деплой** из GitHub
- ✅ **PostgreSQL включён**
- ✅ **SSL автоматически**
- ✅ **Простая настройка**

---

## 🎯 Пошаговая инструкция

### Шаг 1: Подготовка

1. **Создайте аккаунт на [Railway.app](https://railway.app)**
2. **Push проект на GitHub** (если ещё не сделали):
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/yourusername/uzflower.git
   git push -u origin main
   ```

### Шаг 2: Создание проекта

1. **Войдите на Railway.app**
2. **Нажмите "New Project"**
3. **Выберите "Deploy from GitHub repo"**
4. **Выберите репозиторий `uzflower`**

### Шаг 3: Настройка

#### 3.1 Добавьте переменные окружения:

```bash
Settings → Variables → Add Variable

DATABASE_URL: sqlite:///./uzflower.db
SECRET_KEY: your-super-secret-key-change-this
ENVIRONMENT: production
PYTHON_VERSION: 3.13
```

#### 3.2 Настройте Build:

```bash
Settings → Build

Root Directory: (оставьте пустым)
Build Command: pip install -r requirements.txt
Start Command: uvicorn main:app --host 0.0.0.0 --port $PORT
```

#### 3.3 Настройте Port:

```bash
Settings → Networking

Port: 8000 (или используйте $PORT)
```

### Шаг 4: Деплой

1. **Нажмите "Deploy"**
2. **Ждите ~2-3 минуты**
3. **Получите URL** вида: `https://uzflower-production.up.railway.app`

### Шаг 5: Проверка

```bash
# Откройте в браузере
https://your-project.up.railway.app

# Проверьте API
curl https://your-project.up.railway.app/api/products

# Проверьте health
curl https://your-project.up.railway.app/health
```

---

## 🗄️ Добавление PostgreSQL (опционально)

Railway предоставляет бесплатную PostgreSQL:

### 1. Добавьте базу:

```bash
New → Database → Add PostgreSQL
```

### 2. Скопируйте DATABASE_URL:

```bash
PostgreSQL → Connect → COPY URL
```

### 3. Обновите переменную:

```bash
Settings → Variables → DATABASE_URL
Вставьте новый URL
```

### 4. Пересоберите:

```bash
Deployments → Redeploy
```

---

## 📊 Мониторинг

### Логи:

```bash
Deployments → Выберите деплой → View Logs
```

### Метрики:

```bash
Settings → Metrics
- CPU Usage
- Memory Usage
- Network Traffic
```

### Health Checks:

```bash
Settings → Healthchecks → Add Healthcheck

Path: /health
Interval: 30s
Timeout: 10s
```

---

## 💰 Тарифы

### Hobby (Бесплатно):
- ✅ $5 кредитов в месяц
- ✅ 500 часов работы
- ✅ 1GB RAM
- ✅ 1 CPU

### Pro ($5/месяц):
- ✅ $20 кредитов в месяц
- ✅ Неограниченные часы
- ✅ 2GB RAM
- ✅ 2 CPU

---

## 🐛 Troubleshooting

### Ошибка: "Build failed"

```bash
# Проверьте логи
Deployments → View Logs

# Частые проблемы:
# 1. Нет requirements.txt
# 2. Неправильный Start Command
# 3. Ошибки в main.py
```

### Ошибка: "Container exited"

```bash
# Проверьте переменные окружения
Settings → Variables

# Убедитесь что PORT настроен
# Railway использует случайный порт
```

### Ошибка: "Database not found"

```bash
# Добавьте PostgreSQL
New → Database → Add PostgreSQL

# Обновите DATABASE_URL
```

---

## 🔄 Автоматический деплой

Railway автоматически деплоит при push в main ветку!

```bash
git push origin main
# → Railway автоматически задеплоит через 1-2 минуты
```

---

## 📧 Поддержка

- **Документация**: https://docs.railway.app
- **Discord**: https://discord.gg/railway
- **Status**: https://status.railway.app

---

**Ready to deploy on Railway! 🚀**
