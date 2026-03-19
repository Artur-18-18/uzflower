#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Fix encoding using ftfy library"""

from ftfy import fix_text

# Read the file
with open(r'app\telegram_bot\handlers.py', 'r', encoding='utf-8') as f:
    content = f.read()

print("Original (first 500 chars):")
print(content[:500])
print("\n" + "="*50 + "\n")

# Try to fix the mojibake
fixed = fix_text(content)

print("Fixed (first 500 chars):")
print(fixed[:500])

# Save the fixed content
with open(r'app\telegram_bot\handlers.py', 'w', encoding='utf-8') as f:
    f.write(fixed)

print("\n✓ File saved successfully!")
