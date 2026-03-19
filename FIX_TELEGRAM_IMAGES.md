# 📸 Исправление проблемы: "Одно и то же изображение при свайпе"

## ❌ Проблема

При добавлении товаров через Telegram-канал:
- Свайп работает, но показывает **одно и то же изображение**
- Меняется только качество (размер) картинки
- В базе данных все изображения имеют одинаковый URL

### Причина

Telegram-бот использовал временные URL вида:
```
https://api.telegram.org/file/bot{token}/{file_path}
```

Эти ссылки:
1. **Временные** - перестают работать через несколько часов
2. **Одинаковые** для всех версий одного фото
3. **Не сохраняются** на сервере

---

## ✅ Решение

### 1. Скачивание фото с Telegram

Теперь каждое фото:
1. Скачивается с Telegram (`bot.download_file()`)
2. Сохраняется на сервере с **уникальным именем**
3. Получает постоянный URL

### 2. Уникальные имена файлов

Используется UUID для генерации уникальных имён:
```python
import uuid

filename = f"{uuid.uuid4().hex}.{ext}"
# Пример: "a1b2c3d4e5f6.jpg"
```

### 3. Загрузка на сервер

Новый endpoint `/api/telegram/upload-photo`:
- Принимает фото как `multipart/form-data`
- Сохраняет в `/static/uploads/products/` или Cloudinary
- Возвращает постоянный URL

---

## 🔧 Изменения в коде

### main.py

Добавлен новый endpoint:
```python
@app.post("/api/telegram/upload-photo")
async def telegram_upload_photo(
    file: UploadFile = File(...),
    api_secret: str = Form(...),
):
    """Загрузить фото из Telegram-бота."""
    # Генерируем уникальное имя файла
    import uuid
    unique_filename = f"{uuid.uuid4().hex}{ext}"
    
    url = upload_file_to_storage(file_bytes, unique_filename, folder="uzflower/products")
    return {"url": url}
```

### app/telegram_bot/services.py

Добавлен метод для загрузки фото:
```python
async def upload_photo_from_telegram(
    self,
    file_bytes: bytes,
    filename: str
) -> Optional[str]:
    """Загрузить фото из Telegram на сервер."""
    files = {'file': (filename, file_bytes, 'image/jpeg')}
    data = {'api_secret': self.api_secret}
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(upload_url, files=files, data=data)
        result = response.json()
        return result.get('url')
```

### app/telegram_bot/handlers.py

Обновлена обработка постов:
```python
# Скачиваем и загружаем каждое фото на сервер
for i, photo in enumerate(unique_photos):
    # Скачиваем фото
    file = await bot.get_file(photo.file_id)
    photo_bytes = (await bot.download_file(file.file_path)).read()
    
    # Генерируем уникальное имя файла
    import uuid
    ext = file.file_path.split('.')[-1] if '.' in file.file_path else 'jpg'
    filename = f"{uuid.uuid4().hex}.{ext}"
    
    # Загружаем на сервер
    image_url = await api.upload_photo_from_telegram(photo_bytes, filename)
    
    if image_url:
        photo_urls.append(image_url)
```

---

## 📊 Результат

### До исправления:
```
product_images:
id | product_id | image_url
1  | 15         | https://api.telegram.org/file/bot.../photo.jpg
2  | 15         | https://api.telegram.org/file/bot.../photo.jpg  ← То же самое!
3  | 15         | https://api.telegram.org/file/bot.../photo.jpg  ← То же самое!
```

### После исправления:
```
product_images:
id | product_id | image_url
1  | 15         | /static/uploads/products/a1b2c3d4e5f6.jpg
2  | 15         | /static/uploads/products/f6e5d4c3b2a1.jpg  ← Уникальное!
3  | 15         | /static/uploads/products/1a2b3c4d5e6f.jpg  ← Уникальное!
```

---

## 🧪 Тестирование

### 1. Проверка новых товаров

1. Опубликуйте пост в Telegram-канале с **2-3 фото**
2. Проверьте логи бота:
   ```
   ✅ Фото 1/3 загружено: /static/uploads/products/abc123.jpg
   ✅ Фото 2/3 загружено: /static/uploads/products/def456.jpg
   ✅ Фото 3/3 загружено: /static/uploads/products/ghi789.jpg
   ```
3. Откройте сайт → найдите товар
4. Кликните на товар → проверьте свайп

### 2. Проверка базы данных

```bash
python check_images.py
```

Ожидаемый результат:
- У каждого товара уникальные URL изображений
- `product_id` не NULL

### 3. Проверка в браузере

Откройте консоль (F12) → ищите:
```
🖼️ Product images initialized: 3 images
✅ Swiper initialized, loop: true
```

---

## ⚠️ Важно

### Старые товары

Товары, созданные **до исправления**, могут иметь:
- Одинаковые URL изображений
- Временные ссылки Telegram

**Решение:**
1. Удалите старые товары
2. Создайте заново через Telegram
3. Или обновите вручную через админ-панель

### Логи

Смотрите логи для отладки:
```bash
tail -f server_debug.log | grep "Telegram"
```

Ищите:
- `📸 В сообщении N фото`
- `✅ Фото N/3 загружено`
- `✅ Добавлено N дополнительных фото`

---

## 📚 Структура хранения

### Локальное хранилище:
```
static/
  uploads/
    products/
      a1b2c3d4e5f6.jpg  ← Уникальное имя
      f6e5d4c3b2a1.jpg
      1a2b3c4d5e6f.jpg
```

### Cloudinary (если настроен):
```
https://res.cloudinary.com/{cloud}/image/upload/
  q_auto:best,f_auto/
  uzflower/products/a1b2c3d4e5f6.jpg
```

---

## ✅ Чек-лист исправления

- [ ] Endpoint `/api/telegram/upload-photo` добавлен
- [ ] Метод `upload_photo_from_telegram` в services.py
- [ ] Обработка фото в handlers.py обновлена
- [ ] Фото сохраняются с уникальными именами
- [ ] Свайп показывает разные изображения
- [ ] Логи подтверждают загрузку

---

**Дата исправления:** 14 марта 2026 г.  
**Проблема:** Одно и то же изображение при свайпе  
**Решение:** Уникальные имена файлов + загрузка на сервер
