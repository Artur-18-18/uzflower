# 🚀 UzFlower CI/CD & Deployment Guide

Полное руководство по развёртыванию UzFlower.

---

## 📋 Содержание

1. [CI/CD Pipeline](#cicd-pipeline)
2. [🎯 Выбор платформы](#-выбор-платформы)
3. [🚀 Railway.app (Рекомендуется)](#-railwayapp-рекомендуется)
4. [🚀 Render.com](#-rendercom)
5. [Docker деплой](#docker-деплой)
6. [Production деплой](#production-деплой)
7. [Мониторинг](#мониторинг)

---

## 🎯 Выбор платформы

### Быстрое сравнение:

| Платформа | Free | Paid | Sleep | RAM |
|-----------|------|------|-------|-----|
| **Railway** | $5 кредиты | $5/мес | ❌ Нет | 1GB |
| **Render** | 750 часов | $7/мес | ⚠️ 15мин | 512MB |

### Рекомендации:

- **🏆 Railway** - Лучший выбор для production ($5/мес)
- **💰 Render** - Лучший бесплатный тариф (но sleep mode)
- **🐳 Docker** - Для своего VPS

### Полное сравнение:

Смотрите [`PLATFORM_COMPARISON.md`](PLATFORM_COMPARISON.md)

---

## 🚀 Railway.app (Рекомендуется)

### Быстрый старт:

1. **Войдите на [Railway.app](https://railway.app)**
2. **New Project → Deploy from GitHub**
3. **Выберите репозиторий `uzflower`**
4. **Настройте переменные:**
   ```
   DATABASE_URL=sqlite:///./uzflower.db
   SECRET_KEY=your-super-secret-key
   ENVIRONMENT=production
   ```
5. **Deploy!**

### Полная инструкция:

Смотрите [`DEPLOY_RAILWAY.md`](DEPLOY_RAILWAY.md)

---

## 🚀 Render.com

### Быстрый старт:

1. **Войдите на [Render.com](https://render.com)**
2. **New + → Web Service**
3. **Connect repository → `uzflower`**
4. **Настройте:**
   ```
   Build Command: pip install -r requirements.txt
   Start Command: uvicorn main:app --host 0.0.0.0 --port $PORT
   ```
5. **Deploy!**

### Полная инструкция:

Смотрите [`DEPLOY_RENDER.md`](DEPLOY_RENDER.md)

---

## 🔄 CI/CD Pipeline

### Этапы:

```
┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
│  LINT   │ -> │  TEST   │ -> │  BUILD  │ -> │ DEPLOY  │
│  🔍     │    │  🧪     │    │  🔨     │    │  🚀     │
└─────────┘    └─────────┘    └─────────┘    └─────────┘
```

### 1. 🔍 LINT
- **Flake8** - проверка стиля кода
- **Black** - форматирование
- **Pylint** - анализ качества
- **MyPy** - проверка типов

### 2. 🧪 TEST
- **Unit тесты** - `tests/unit/`
- **Integration тесты** - `tests/integration/`
- **Покрытие** - Codecov

### 3. 🔨 BUILD
- Проверка синтаксиса Python
- Сборка Docker образа
- Сохранение артефакта

### 4. 🚀 DEPLOY
- Развёртывание на production
- Только для `main`/`master` ветки

---

## 💻 Локальная разработка

### Установка зависимостей:

```bash
# Python
python -m pip install -r requirements.txt

# Тесты
pip install pytest pytest-asyncio pytest-cov
```

### Запуск тестов:

```bash
# Все тесты
pytest

# Unit тесты
pytest tests/unit/ -v

# Integration тесты
pytest tests/integration/ -v

# С покрытием
pytest --cov=main --cov-report=html
```

### Запуск приложения:

```bash
# Development
python -m uvicorn main:app --reload

# Production
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

---

## 🐳 Docker деплой

### Быстрый старт:

```bash
# Сборка и запуск
docker-compose up -d --build

# Просмотр логов
docker-compose logs -f

# Остановка
docker-compose down
```

### Режимы работы:

```bash
# Только приложение
docker-compose up -d

# С Nginx (HTTPS)
docker-compose --profile with-nginx up -d

# С PostgreSQL
docker-compose --profile with-postgres up -d

# Все сервисы
docker-compose --profile with-nginx --profile with-postgres up -d
```

### Переменные окружения:

Создайте `.env` файл:

```bash
# .env
SECRET_KEY=your-super-secret-key-here
POSTGRES_USER=uzflower
POSTGRES_PASSWORD=secure-password-here
```

---

## 🌐 Production деплой

### Вариант 1: Docker Compose (Рекомендуется)

```bash
# 1. Клонируйте репозиторий
git clone https://github.com/yourusername/uzflower.git
cd uzflower

# 2. Настройте переменные
cp .env.example .env
nano .env

# 3. Запустите
docker-compose --profile with-nginx up -d --build

# 4. Проверьте
docker-compose ps
curl http://localhost/health
```

### Вариант 2: VPS (Ubuntu/Debian)

```bash
# 1. Установите Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# 2. Установите Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 3. Клонируйте проект
git clone https://github.com/yourusername/uzflower.git
cd uzflower

# 4. Настройте
cp .env.example .env
nano .env

# 5. Запустите
docker-compose up -d --build

# 6. Настройте Nginx (опционально)
sudo ln -s /path/to/uzflower/nginx/uzflower.conf /etc/nginx/sites-available/
sudo nginx -t
sudo systemctl reload nginx
```

### Вариант 3: Cloud Platforms

#### Heroku:

```bash
# heroku.yml уже настроен
heroku create uzflower
heroku config:set SECRET_KEY=your-key
git push heroku main
```

#### Railway:

1. Подключите GitHub репозиторий
2. Добавьте переменные окружения
3. Deploy автоматически

#### Vercel:

```bash
npm i -g vercel
vercel --prod
```

---

## 🔒 SSL/HTTPS настройка

### Let's Encrypt (бесплатно):

```bash
# Установите Certbot
sudo apt install certbot python3-certbot-nginx

# Получите сертификат
sudo certbot --nginx -d yourdomain.com

# Автообновление
sudo certbot renew --dry-run
```

### Обновите `nginx/ssl/`:
- `fullchain.pem` - полный сертификат
- `privkey.pem` - приватный ключ

---

## 📊 Мониторинг

### Проверка статуса:

```bash
# Docker контейнеры
docker-compose ps

# Логи
docker-compose logs -f uzflower

# Использование ресурсов
docker stats

# Health check
curl http://localhost/health
```

### Логи приложения:

```bash
# Просмотр
docker-compose logs -f

# Экспорт
docker-compose logs > logs.txt
```

### Метрики:

- **Uptime**: `/health` endpoint
- **Requests**: Nginx access logs
- **Errors**: Nginx error logs
- **Performance**: Application logs

---

## 🐛 Troubleshooting

### Проблема: Контейнер не запускается

```bash
# Проверьте логи
docker-compose logs uzflower

# Пересоберите
docker-compose up -d --build --force-recreate
```

### Проблема: База данных не сохраняется

```bash
# Проверьте volumes в docker-compose.yml
# Убедитесь что путь правильный
docker volume ls
```

### Проблема: Nginx не проксирует

```bash
# Проверьте конфиг
docker-compose exec nginx nginx -t

# Перезагрузите
docker-compose restart nginx
```

---

## 📈 Performance Optimization

### Кэширование:

```bash
# Включите Redis профиль
docker-compose --profile with-redis up -d
```

### База данных:

```bash
# Используйте PostgreSQL для production
docker-compose --profile with-postgres up -d
```

### CDN для статики:

Настройте Cloudflare или другой CDN для `/static/`

---

## 🎯 Checklist перед деплоем

- [ ] Все тесты проходят
- [ ] Покрытие тестов > 70%
- [ ] SECRET_KEY изменён на уникальный
- [ ] База данных настроена
- [ ] SSL сертификаты установлены
- [ ] Бэкапы настроены
- [ ] Мониторинг включён
- [ ] Логи собираются

---

## 📞 Support

- **Issues**: GitHub Issues
- **Email**: support@uzflower.com
- **Docs**: `/docs` folder

---

**Happy Deploying! 🚀**
