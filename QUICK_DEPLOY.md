# 🚀 Quick Deploy - UzFlower

## ⚡ Быстрый старт за 5 минут

### 1️⃣ Установка Docker

```bash
# Windows/Mac: Скачайте Docker Desktop
# https://www.docker.com/products/docker-desktop

# Linux:
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
```

### 2️⃣ Запуск приложения

```bash
# Клонирование (если ещё не склонировали)
cd c:\Users\matka\uzflower

# Запуск
docker-compose up -d --build

# Готово! Откройте http://localhost:8000
```

### 3️⃣ Проверка

```bash
# Статус
docker-compose ps

# Логи
docker-compose logs -f

# Health check
curl http://localhost:8000/health
```

---

## 🔄 CI/CD Pipeline

Автоматический pipeline при push в GitHub:

```yaml
Push → Lint → Test → Build → Deploy
```

### Настройка GitHub Actions:

1. **Push в репозиторий**
2. **Actions запустится автоматически**
3. **Следите за статусом** в GitHub Actions tab

### Переменные окружения (GitHub Secrets):

```bash
Settings → Secrets and variables → Actions

Добавьте:
- DEPLOY_TOKEN (для деплоя)
- SECRET_KEY (для приложения)
```

---

## 📦 Docker команды

```bash
# Запуск
docker-compose up -d

# Остановка
docker-compose down

# Пересборка
docker-compose up -d --build --force-recreate

# Логи
docker-compose logs -f uzflower

# Вход в контейнер
docker-compose exec uzflower bash

# Очистка
docker-compose down -v  # удалит volumes
```

---

## 🌐 Production с Nginx + HTTPS

### 1. Получите SSL сертификаты:

```bash
# Let's Encrypt (бесплатно)
sudo certbot certonly --standalone -d yourdomain.com
```

### 2. Скопируйте сертификаты:

```bash
sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem nginx/ssl/
sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem nginx/ssl/
```

### 3. Запустите с Nginx:

```bash
docker-compose --profile with-nginx up -d
```

### 4. Проверьте:

```bash
curl https://yourdomain.com/health
```

---

## 🐛 Troubleshooting

### Порт 8000 занят:

```bash
# Измените в docker-compose.yml
ports:
  - "8001:8000"  # используйте 8001
```

### Ошибка базы данных:

```bash
# Удалите старую БД и пересоздайте
rm uzflower.db
docker-compose down
docker-compose up -d
```

### Контейнер падает:

```bash
# Проверьте логи
docker-compose logs uzflower

# Пересоберите
docker-compose up -d --build --force-recreate
```

---

## 📊 Мониторинг

```bash
# Статус контейнеров
docker-compose ps

# Использование ресурсов
docker stats

# Логи приложения
docker-compose logs -f uzflower

# Health check
curl http://localhost:8000/health
```

---

## 🎯 Следующие шаги

1. ✅ Настройте GitHub Actions
2. ✅ Добавьте SSL сертификаты
3. ✅ Настройте бэкапы базы данных
4. ✅ Включите мониторинг
5. ✅ Настройте логирование

---

**Ready to deploy! 🚀**
