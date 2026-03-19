# PostgreSQL BOOLEAN Default Value Fix

## ❌ Ошибка

```
sqlalchemy.exc.ProgrammingError: (psycopg2.errors.DatatypeMismatch) 
column "delivery_option" is of type boolean but default expression is of type integer
HINT: You will need to rewrite or cast the expression.
[SQL: ALTER TABLE orders ADD COLUMN delivery_option BOOLEAN DEFAULT 1]
```

## 🔍 Причина

PostgreSQL требует использования `TRUE`/`FALSE` для BOOLEAN полей, а не `1`/`0` как в SQLite.

## ✅ Решение

Изменены все миграции с BOOLEAN полями:

### Было (SQLite стиль):
```python
db.execute(text("ALTER TABLE orders ADD COLUMN delivery_option BOOLEAN DEFAULT 1"))
db.execute(text("ALTER TABLE users ADD COLUMN is_blocked BOOLEAN DEFAULT 0"))
```

### Стало (PostgreSQL совместимо):
```python
if 'postgresql' in DATABASE_URL:
    db.execute(text("ALTER TABLE orders ADD COLUMN delivery_option BOOLEAN DEFAULT true"))
else:
    db.execute(text("ALTER TABLE orders ADD COLUMN delivery_option BOOLEAN DEFAULT 1"))
```

## 📋 Изменённые поля

| Таблица | Поле | Старое значение | Новое значение (PostgreSQL) |
|---------|------|----------------|----------------------------|
| users | is_blocked | DEFAULT 0 | DEFAULT false |
| products | is_popular | DEFAULT 0 | DEFAULT false |
| orders | is_paid | DEFAULT 0 | DEFAULT false |
| orders | delivery_option | DEFAULT 1 | DEFAULT true |
| reviews | is_approved | DEFAULT 1 | DEFAULT true |
| reviews | is_verified_purchase | DEFAULT 0 | DEFAULT false |

## 🚀 Деплой

Изменения закоммичены и запушены в commit `6d801e5`.

Render.com автоматически задеплоит новую версию.

## ✅ Проверка

После деплоя проверьте логи на Render.com:
1. Откройте проект на https://render.com
2. Перейдите в Logs
3. Убедитесь что приложение запустилось без ошибок

## 📝 Примечание

Это изменение обратно совместимо:
- SQLite продолжает работать с `DEFAULT 0/1`
- PostgreSQL использует `DEFAULT true/false`
- Определение типа БД происходит автоматически по `DATABASE_URL`
