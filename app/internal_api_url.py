"""
Базовый URL API для HTTP-запросов из ботов в том же процессе, что и uvicorn.

На Render переменная PORT задаёт реальный порт; фиксированный :8000 даёт отказ соединения.
"""

import os


def get_internal_api_base_url() -> str:
    explicit = (os.getenv("TELEGRAM_API_URL") or "").strip()
    if explicit:
        return explicit.rstrip("/")
    port = (os.getenv("PORT") or "8000").strip()
    return f"http://127.0.0.1:{port}"
