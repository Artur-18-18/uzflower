# UzFlower - Тесты

Полный набор тестов для интернет-магазина UzFlower.

## 📋 Структура

```
tests/
├── conftest.py              # Фикстуры и конфигурация pytest
├── unit/                    # Unit тесты
│   ├── test_user_crud.py    # Тесты User CRUD
│   └── test_product_crud.py # Тесты Product CRUD
├── integration/             # Integration тесты
│   ├── test_auth_api.py                 # Auth & Profile API
│   ├── test_products_orders_api.py      # Products & Orders API
│   └── test_reviews_notifications_api.py # Reviews & Notifications API
└── fixtures/                # Дополнительные фикстуры
```

## 🚀 Запуск тестов

### Все тесты:
```bash
cd c:\Users\matka\uzflower
c:\Users\matka\uzflower\.venv\Scripts\python.exe -m pytest
```

### Конкретная папка:
```bash
pytest tests/unit/
pytest tests/integration/
```

### Конкретный файл:
```bash
pytest tests/unit/test_user_crud.py -v
```

### Конкретный тест:
```bash
pytest tests/unit/test_user_crud.py::TestUserCreate::test_create_user_success -v
```

### С покрытием:
```bash
pytest --cov=main --cov-report=html
```

### С маркировкой:
```bash
pytest -m unit
pytest -m integration
pytest -m auth
```

## 📊 Отчёт о покрытии

После запуска с `--cov-report=html`, откройте:
```
htmlcov/index.html
```

## 🔧 Фикстуры

### Основные:
- `client` - TestClient с тестовой БД
- `db_session` - Сессия базы данных
- `test_engine` - Движок тестовой БД

### Тестовые данные:
- `test_user` - Обычный пользователь
- `test_admin` - Администратор
- `test_category` - Категория
- `test_product` - Товар
- `test_order` - Заказ
- `test_review` - Отзыв

### Аутентификация:
- `auth_token` - Токен пользователя
- `admin_token` - Токен админа
- `headers` - Заголовки с токеном
- `admin_headers` - Заголовки с токеном админа

### Фабрики:
- `create_test_user` - Создание пользователей
- `create_test_product` - Создание товаров

## 📝 Марки тестов

- `unit` - Unit тесты
- `integration` - Integration тесты
- `auth` - Аутентификация
- `user` - Пользователи
- `product` - Товары
- `order` - Заказы
- `review` - Отзывы
- `admin` - Админские эндпоинты

## 🎯 Покрытие

Тесты покрывают:

### Unit тесты:
- ✅ User CRUD операции
- ✅ Product CRUD операции
- ✅ Валидация данных
- ✅ Связи между моделями

### Integration тесты:
- ✅ Регистрация / Вход
- ✅ Профиль пользователя
- ✅ Адреса доставки
- ✅ Избранное
- ✅ Бонусы и промокоды
- ✅ Отзывы с фото
- ✅ Уведомления
- ✅ Напоминания
- ✅ Заказы (создание, статусы, повтор)
- ✅ Оплата (Click, Payme)
- ✅ Админ панель (товары, заказы, пользователи)
- ✅ Баннеры
- ✅ Поддержка

## 🐛 Отладка

### Запустить с выводом логов:
```bash
pytest -s -v
```

### Запустить до первой ошибки:
```bash
pytest -x
```

### Запустить с таймаутом:
```bash
pytest --timeout=300
```

## 📈 CI/CD

Для интеграции с CI/CD:
```bash
pytest --junitxml=test-results.xml --cov=main --cov-report=xml
```

## 🔑 Тестовые данные

### Пользователь:
- Email: `test@example.com`
- Пароль: `testpassword123`

### Админ:
- Email: `admin@example.com`
- Пароль: `adminpassword123`

## ⚠️ Важно

- Тесты используют отдельную БД `test_uzflower.db`
- БД удаляется после всех тестов
- Каждый тест работает с чистой БД
- Тесты независимы друг от друга
