#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Fix encoding of handlers.py"""

# Читаем байты
with open(r'app\telegram_bot\handlers.py', 'rb') as f:
    data = f.read()

# Пробуем разные кодировки
print("=== Raw bytes (first 100) ===")
print(data[:100])

print("\n=== Try UTF-8 ===")
try:
    text = data.decode('utf-8')
    print("UTF-8 OK!")
    print(text[:200])
except Exception as e:
    print(f"UTF-8 Error: {e}")

print("\n=== Try CP1251 ===")
try:
    text = data.decode('cp1251')
    print("CP1251 OK!")
    print(text[:200])
except Exception as e:
    print(f"CP1251 Error: {e}")

print("\n=== Try CP1252 ===")
try:
    text = data.decode('cp1252')
    print("CP1252 OK!")
    print(text[:200])
except Exception as e:
    print(f"CP1252 Error: {e}")

print("\n=== Try latin-1 ===")
try:
    text = data.decode('latin-1')
    print("latin-1 OK!")
    print(text[:200])
except Exception as e:
    print(f"latin-1 Error: {e}")
