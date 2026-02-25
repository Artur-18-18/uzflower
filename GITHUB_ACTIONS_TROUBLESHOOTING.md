# 🔧 GitHub Actions Troubleshooting

Решение проблем с CI/CD pipeline

---

## ❌ Тесты упали (красный крестик)

### Проблема 1: "ModuleNotFoundError"

**Ошибка:**
```
ModuleNotFoundError: No module named 'pytest'
```

**Решение:**
```yaml
- name: Install dependencies
  run: |
    pip install -r requirements.txt
    pip install -r requirements-dev.txt
```

---

### Проблема 2: "tests/ directory not found"

**Ошибка:**
```
ERROR: file or directory not found: tests/
```

**Решение:**
```yaml
# Проверьте что папка tests существует
# Проверьте что в tests есть __init__.py
# Проверьте что файлы называются test_*.py
```

---

### Проблема 3: "SyntaxError"

**Ошибка:**
```
SyntaxError: invalid syntax
```

**Решение:**
```bash
# Проверьте локально
python -m py_compile main.py

# Исправьте синтаксические ошибки
# Закоммитьте и запушьте
```

---

### Проблема 4: Тесты проходят локально но не в CI

**Причина:**
- Разные версии Python
- Нет переменных окружения
- Нет базы данных

**Решение:**
```yaml
- name: Set up Python
  uses: actions/setup-python@v5
  with:
    python-version: '3.12'

- name: Set environment variables
  run: |
    echo "DATABASE_URL=sqlite:///./test.db" >> $GITHUB_ENV
    echo "SECRET_KEY=test-secret-key" >> $GITHUB_ENV
```

---

### Проблема 5: "ImportError"

**Ошибка:**
```
ImportError: cannot import name 'User' from 'main'
```

**Решение:**
```python
# Проверьте импорты в тестах
from main import User, Product  # Должно быть в main.py
```

---

## 📊 Просмотр логов

### GitHub Actions:

1. **Откройте репозиторий на GitHub**
2. **Actions tab**
3. **Выберите failed run**
4. **Кликните на job "test"**
5. **Разверните шаг "Run Tests"**

### Локальное тестирование:

```bash
# Запустите тесты локально
pytest tests/ -v --tb=short

# С покрытием
pytest tests/ --cov=main --cov-report=html

# Один тест
pytest tests/unit/test_user_crud.py::TestUserCreate::test_create_user_success -v
```

---

## ✅ Чек-лист перед push

- [ ] Тесты проходят локально
- [ ] Все импорты работают
- [ ] Переменные окружения настроены
- [ ] requirements.txt актуален
- [ ] Python версия совпадает (3.13)

---

## 🔧 Быстрое исправление

### 1. Обновите workflow:

```yaml
# .github/workflows/test.yml

- name: Install dependencies
  run: |
    pip install -r requirements.txt
    pip install -r requirements-dev.txt
```

### 2. Закоммитьте изменения:

```bash
git add .
git commit -m "Fix CI/CD workflow"
git push origin main
```

### 3. Проверьте Actions:

```
GitHub → Actions → Tests → Latest run
```

---

## 📚 Документация

- **GitHub Actions Docs**: https://docs.github.com/en/actions
- **Pytest Docs**: https://docs.pytest.org
- **Python Setup**: https://github.com/actions/setup-python

---

**Fix your CI/CD! 🚀**
