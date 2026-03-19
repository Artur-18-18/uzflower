#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Fix encoding of handlers.py - convert double-encoded UTF-8 back to proper UTF-8"""

# Читаем байты
with open(r'app\telegram_bot\handlers.py', 'rb') as f:
    data = f.read()

# Пробуем разные подходы
print("=== Approach 1: UTF-8 -> CP437 -> UTF-8 ===")
try:
    text = data.decode('utf-8')
    original_bytes = text.encode('cp437')
    correct_text = original_bytes.decode('utf-8')
    print("Success!")
    print(correct_text[:500])
    with open(r'app\telegram_bot\handlers.py', 'w', encoding='utf-8') as f:
        f.write(correct_text)
    print("\nFile saved successfully!")
except Exception as e:
    print(f"Error: {e}")
    
print("\n=== Approach 2: UTF-8 -> CP850 -> UTF-8 ===")
try:
    text = data.decode('utf-8')
    original_bytes = text.encode('cp850')
    correct_text = original_bytes.decode('utf-8')
    print("Success!")
    print(correct_text[:500])
    with open(r'app\telegram_bot\handlers.py', 'w', encoding='utf-8') as f:
        f.write(correct_text)
    print("\nFile saved successfully!")
except Exception as e:
    print(f"Error: {e}")

print("\n=== Approach 3: UTF-8 raw re-encode ===")
try:
    # Это для случаев когда UTF-8 был прочитан как последовательность байт
    text = data.decode('utf-8')
    # Символы вида Đx - это UTF-8 байты прочитанные как отдельные символы
    # Пробуем исправить через replace
    fixed = text.replace('Đ', '').replace('Â', '').replace('Å', '').replace('Ã', '')
    print(fixed[:500])
except Exception as e:
    print(f"Error: {e}")
