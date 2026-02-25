# 📦 Requirements Guide

Руководство по зависимостям UzFlower

---

## 📋 Файлы зависимостей

### 1. `requirements.txt` - Production

**Для запуска приложения:**

```bash
pip install -r requirements.txt
```

**Включает:**
- ✅ FastAPI (Web Framework)
- ✅ Uvicorn (Server)
- ✅ SQLAlchemy (Database)
- ✅ Jinja2 (Templates)
- ✅ Passlib (Security)
- ✅ Python-Jose (JWT)
- ✅ HTTPX (HTTP Client)
- ✅ Python-Multipart (Forms)

**Версии зафиксированы** для стабильности!

---

### 2. `requirements-dev.txt` - Development

**Для разработки и тестирования:**

```bash
pip install -r requirements-dev.txt
```

**Включает:**
- ✅ pytest (Testing framework)
- ✅ pytest-asyncio (Async tests)
- ✅ pytest-cov (Coverage reports)
- ✅ flake8 (Code style)
- ✅ black (Code formatting)
- ✅ pylint (Code quality)
- ✅ mypy (Type checking)
- ✅ httpx (HTTP testing)
- ✅ mkdocs (Documentation)

**Версии зафиксированы** для консистентности!

---

## 🎯 Использование

### Production (деплой):

```bash
# Только production зависимости
pip install -r requirements.txt

# Запуск приложения
uvicorn main:app --host 0.0.0.0 --port 8000
```

### Development (разработка):

```bash
# Всё сразу
pip install -r requirements.txt -r requirements-dev.txt

# Запуск с авто-релоадом
uvicorn main:app --reload

# Запуск тестов
pytest tests/ -v
```

### CI/CD:

```yaml
# GitHub Actions
- name: Install dependencies
  run: |
    pip install -r requirements.txt
    pip install -r requirements-dev.txt
```

### Docker:

```dockerfile
# Production image
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Development image (опционально)
COPY requirements-dev.txt .
RUN pip install --no-cache-dir -r requirements-dev.txt
```

---

## 🔄 Обновление зависимостей

### Проверить обновления:

```bash
pip install --upgrade pip
pip list --outdated
```

### Обновить конкретный пакет:

```bash
pip install --upgrade fastapi
```

### Обновить все:

```bash
pip install --upgrade -r requirements.txt
pip install --upgrade -r requirements-dev.txt
```

### Зафиксировать версии:

```bash
pip freeze > requirements.txt
pip freeze > requirements-dev.txt
```

---

## 🐛 Troubleshooting

### Конфликт зависимостей:

```bash
# Создайте чистый venv
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows

# Установите заново
pip install -r requirements.txt
```

### Пакет не устанавливается:

```bash
# Обновите pip
python -m pip install --upgrade pip

# Попробуйте без кэша
pip install --no-cache-dir -r requirements.txt
```

### Ошибка совместимости:

```bash
# Проверьте Python версию
python --version

# Требуется Python 3.12
# Если другая версия - обновите Python
```

---

## 📊 Зависимости по категориям

### Web Framework:
- fastapi==0.109.0
- uvicorn[standard]==0.27.0

### Database:
- sqlalchemy==2.0.25

### Templates:
- jinja2==3.1.3

### Security:
- passlib[bcrypt]==1.7.4
- python-jose[cryptography]==3.3.0

### Forms:
- python-multipart==0.0.6

### HTTP:
- httpx==0.26.0

### Testing:
- pytest==8.0.0
- pytest-asyncio==0.23.3
- pytest-cov==4.1.0

### Code Quality:
- flake8==7.0.0
- black==24.1.0
- pylint==3.0.3
- mypy==1.8.0

---

## ✅ Best Practices

1. **Фиксируйте версии** (`==` вместо `>=`)
2. **Разделяйте prod/dev** зависимости
3. **Регулярно обновляйте** (раз в месяц)
4. **Тестируйте после обновления**
5. **Используйте virtualenv**

---

## 🔗 Ссылки

- **PyPI**: https://pypi.org
- **Requirements Format**: https://pip.pypa.io/en/stable/reference/requirements-file-format/
- **Safety Check**: `pip install safety && safety check`

---

**Happy Coding! 🚀**
