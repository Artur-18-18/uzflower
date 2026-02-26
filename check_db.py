#!/usr/bin/env python3
"""Проверка базы данных UzFlower"""

from app.database import SessionLocal, User, engine, Base
from sqlalchemy import inspect

db = SessionLocal()
inspector = inspect(engine)

print("=== Таблицы в БД ===")
tables = inspector.get_table_names()
for table in tables:
    print(f"  ✓ {table}")

print("\n=== Структура таблицы users ===")
try:
    columns = inspector.get_columns("users")
    for col in columns:
        print(f"  {col['name']}: {col['type']}")
except Exception as e:
    print(f"  ✗ Ошибка: {e}")

print("\n=== Количество записей ===")
print(f"  Пользователей: {db.query(User).count()}")

db.close()
