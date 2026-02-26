"""
Test database configuration.
Импортируется ПЕРЕД app.database для установки переменной окружения.
"""
import os
import tempfile

# Создаём временный файл для тестовой БД
# Это надёжнее чем in-memory SQLite
test_db_fd, test_db_path = tempfile.mkstemp(suffix=".db")
os.close(test_db_fd)  # Закрываем fd, файл будет удалён после тестов

TEST_DATABASE_URL = f"sqlite:///{test_db_path}"
os.environ["DATABASE_URL"] = TEST_DATABASE_URL
