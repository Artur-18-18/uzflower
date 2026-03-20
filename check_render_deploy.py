"""
Финальная проверка перед деплоем на Render.com
"""
import os
import sys
from dotenv import load_dotenv

load_dotenv()

print("=" * 60)
print("🔍 ПРОВЕРКА ПЕРЕД ДЕПЛОЕМ НА RENDER.COM")
print("=" * 60)

# Проверка переменных окружения
print("\n1. Проверка переменных окружения...")

checks = {
    "TELEGRAM_BOT_TOKEN": "Токен основного бота",
    "ADMIN_BOT_TOKEN": "Токен админ-бота",
    "ADMIN_USER_ID": "ID администратора",
    "TELEGRAM_API_URL": "URL API для ботов",
    "TELEGRAM_API_SECRET": "Секрет API",
    "ENABLE_TELEGRAM_BOTS": "Включение ботов"
}

all_ok = True
for key, desc in checks.items():
    value = os.getenv(key)
    if value:
        if "TOKEN" in key or "SECRET" in key:
            print(f"   ✅ {desc}: {key}={value[:10]}...")
        else:
            print(f"   ✅ {desc}: {key}={value}")
    else:
        print(f"   ❌ {desc}: {key} НЕ УСТАНОВЛЕН!")
        all_ok = False

# Проверка TELEGRAM_API_URL
api_url = os.getenv("TELEGRAM_API_URL", "")
if api_url == "http://localhost:8000":
    print(f"\n   ✅ TELEGRAM_API_URL настроен правильно для Render!")
else:
    print(f"\n   ⚠️ TELEGRAM_API_URL={api_url}")
    print(f"   Для Render.com должно быть: http://localhost:8000")

# Проверка ENABLE_TELEGRAM_BOTS
enable_bots = os.getenv("ENABLE_TELEGRAM_BOTS", "false").lower()
if enable_bots in ("true", "1", "yes"):
    print(f"   ✅ Боты включены (ENABLE_TELEGRAM_BOTS=true)")
else:
    print(f"   ⚠️ Боты выключены (ENABLE_TELEGRAM_BOTS={enable_bots})")
    print(f"   Для включения установите: ENABLE_TELEGRAM_BOTS=true")

# Проверка импорта модулей
print("\n2. Проверка импорта модулей...")

try:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from app.telegram_bot.config import settings as tg_settings
    print(f"   ✅ Telegram bot config: OK")
    print(f"      API URL: {tg_settings.api_url}")
except Exception as e:
    print(f"   ❌ Telegram bot config: {e}")
    all_ok = False

try:
    from app.admin_bot.config import settings as admin_settings
    print(f"   ✅ Admin bot config: OK")
    print(f"      API URL: {admin_settings.api_url}")
    print(f"      Admin IDs: {admin_settings.admin_ids}")
except Exception as e:
    print(f"   ❌ Admin bot config: {e}")
    all_ok = False

# Проверка токенов
print("\n3. Проверка токенов ботов...")

tg_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
if tg_token.startswith("8676150074:"):
    print(f"   ✅ Токен основного бота: верный формат")
else:
    print(f"   ⚠️ Токен основного бота: {tg_token[:20]}...")

admin_token = os.getenv("ADMIN_BOT_TOKEN", "")
if admin_token.startswith("8443193754:"):
    print(f"   ✅ Токен админ-бота: верный формат")
else:
    print(f"   ⚠️ Токен админ-бота: {admin_token[:20]}...")

admin_id = os.getenv("ADMIN_USER_ID", "0")
if admin_id != "0":
    print(f"   ✅ ADMIN_USER_ID установлен: {admin_id}")
else:
    print(f"   ⚠️ ADMIN_USER_ID не установлен (будет 0)")

# Итог
print("\n" + "=" * 60)
if all_ok:
    print("✅ ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ!")
    print("\nМожно деплоить на Render.com")
    print("Следуйте инструкции в RENDER_DEPLOY.md")
else:
    print("⚠️ ОБНАРУЖЕНЫ ПРОБЛЕМЫ!")
    print("\nУстраните проблемы перед деплоем")

print("=" * 60)

# Проверка файлов
print("\n4. Проверка важных файлов...")

files_to_check = [
    "main.py",
    "requirements.txt",
    "app/telegram_bot/bot.py",
    "app/admin_bot/bot.py",
    ".env.example",
    "RENDER_DEPLOY.md"
]

for file in files_to_check:
    if os.path.exists(file):
        print(f"   ✅ {file}")
    else:
        print(f"   ❌ {file} НЕ НАЙДЕН!")

print("\n" + "=" * 60)
print("🎉 ПРОВЕРКА ЗАВЕРШЕНА!")
print("=" * 60)
