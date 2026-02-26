# 🚀 Инструкция по деплою UzFlower

## Проблема с регистрацией
Если при регистрации возникает "Ошибка подключения к серверу", выполните следующие шаги:

## 1. Проверка на сервере

### Остановить текущий контейнер
```bash
cd /path/to/uzflower
docker-compose down
```

### Пересобрать образ с исправлениями
```bash
docker-compose build --no-cache
```

### Запустить
```bash
docker-compose up -d
```

### Проверить логи
```bash
docker-compose logs -f uzflower
```

## 2. Проверка базы данных

### Выполнить скрипт проверки
```bash
docker exec uzflower-app python check_db.py
```

Или вручную:
```bash
docker exec -it uzflower-app python
```

```python
from app.database import SessionLocal, User, engine
from sqlalchemy import inspect

db = SessionLocal()
inspector = inspect(engine)

# Проверка таблиц
print("Таблицы:", inspector.get_table_names())

# Проверка пользователей
print("Пользователей:", db.query(User).count())

db.close()
```

## 3. Проверка CORS

Откройте консоль браузера (F12) и проверьте:
- Вкладка **Network**: статус запроса на `/api/auth/register`
- Вкладка **Console**: ошибки CORS

## 4. Проверка nginx (если используется)

```bash
docker-compose logs -f nginx
```

Проверьте, что nginx проксирует запросы на `/api/` correctly.

## 5. Тестирование API вручную

```bash
# Тест регистрации
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"test123","full_name":"Test"}'

# Тест входа
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"test123"}'
```

## 6. Возможные ошибки и решения

| Ошибка | Решение |
|--------|---------|
| `404 Not Found` | Проверьте nginx.conf, location /api/ |
| `502 Bad Gateway` | Бэкенд не запущен: `docker-compose logs uzflower` |
| `CORS policy` | Уже исправлено в main.py |
| `table users does not exist` | Пересоберите образ, таблицы создаются в lifespan |
| `connection refused` | Порт 80/443 не открыт в фаерволе |

## 7. Финальная проверка

После деплоя:
1. Откройте `https://your-domain.com/login`
2. Попробуйте зарегистрироваться
3. Проверьте консоль браузера (F12)
