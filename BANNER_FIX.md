# 🎨 Исправление баннеров для Render.com

## ✅ Что было исправлено

### Проблема
На Render.com вместо видео отображался **чёрный фон** из-за:
1. Отсутствия обработки ошибок загрузки видео
2. Неправильных атрибутов для `<video>` элемента
3. Отсутствия `preload` и `poster` атрибутов

### Решение
Добавлена полная обработка ошибок и правильные атрибуты для видео:

#### Изменённые файлы:
1. **`static/js/app.js`** - главный баннер на homepage
2. **`templates/index.html`** - боковой баннер
3. **`templates/admin.html`** - превью баннеров в админке

---

## 🔧 Технические детали

### Правильный `<video>` элемент для Render

```html
<video 
    class="absolute inset-0 w-full h-full object-cover opacity-60" 
    autoplay 
    muted 
    loop 
    playsinline 
    preload="metadata" 
    poster=""
>
    <source src="${videoUrl}" type="video/mp4">
    Ваш браузер не поддерживает видео.
</video>
```

**Важные атрибуты:**
- `muted` - обязательно для autoplay в браузерах
- `playsinline` - для корректной работы на iOS
- `preload="metadata"` - загружает метаданные для ускорения старта
- `poster=""` - предотвращает чёрный экран до загрузки

### Обработка ошибок

```javascript
video.addEventListener('error', (e) => {
    console.error('Ошибка загрузки видео:', videoUrl, e);
    // Показываем заглушку если видео не загрузилось
    container.innerHTML = `
        <div class="absolute inset-0 bg-gradient-to-br from-rose-900 via-rose-800 to-black opacity-90"></div>
        <!-- Красивая заглушка -->
    `;
});

video.addEventListener('loadeddata', () => {
    console.log('Видео загружено:', videoUrl);
    video.play().catch(err => {
        console.warn('Автовоспроизведение заблокировано:', err);
    });
});
```

---

## 📋 Проверка работы

### 1. Проверьте загрузку видео

Откройте консоль браузера (F12) и проверьте логи:
```
Видео загружено: https://...
```

Если ошибка:
```
Ошибка загрузки видео: https://...
```

### 2. Проверьте URL видео

Видео должно быть доступно по прямому URL:
```bash
curl -I "https://your-app.onrender.com/static/uploads/banners/your-video.mp4"
```

**Ожидаемый ответ:**
```
HTTP/2 200 
content-type: video/mp4
content-length: 1234567
```

### 3. Форматы видео для Render

**Поддерживаемые форматы:**
- ✅ `.mp4` (H.264 + AAC) - **рекомендуется**
- ✅ `.webm` (VP8/VP9 + Vorbis)
- ⚠️ `.mov` - может не работать на всех устройствах

**Рекомендуемые настройки кодирования:**
```
- Кодек: H.264 (video) + AAC (audio)
- Разрешение: 1920x1080 или 1280x720
- Битрейт: 2-5 Mbps
- FPS: 24-30
- Размер файла: < 10 MB для быстрой загрузки
```

---

## 🎯 Как загрузить видео баннер

### Через админ-панель

1. Откройте **Админ-панель** → **Маркетинг** → **Баннеры**
2. Нажмите **"Добавить основной баннер"**
3. Выберите **"Видео"** тип
4. Загрузите видео файл или укажите URL
5. Заполните текст и subtext
6. Нажмите **"Сохранить"**

### Проверка после загрузки

1. Откройте главную страницу
2. Проверьте консоль (F12) на наличие ошибок
3. Если видео не загружается — проверьте права доступа к файлу

---

## 🐛 Troubleshooting

### Чёрный экран вместо видео

**Причины:**
1. Видео не загрузилось (ошибка URL)
2. Неподдерживаемый формат видео
3. Блокировка autoplay браузером

**Решение:**
1. Проверьте URL видео в консоли
2. Конвертируйте в MP4 (H.264)
3. Убедитесь, что есть атрибут `muted`

### Видео не воспроизводится автоматически

**Причина:** Браузер блокирует autoplay

**Решение:**
- Убедитесь, что есть `muted` и `playsinline`
- Добавьте `preload="metadata"`
- Проверьте логи на `Autoplay blocked`

### Видео загружается долго

**Решение:**
1. Сожмите видео (HandBrake, FFmpeg)
2. Уменьшите битрейт до 2-3 Mbps
3. Используйте WebM как fallback

---

## 📦 FFmpeg команды для оптимизации

### Конвертация в MP4 для web
```bash
ffmpeg -i input.mov -c:v libx264 -crf 23 -c:a aac -b:a 128k \
  -movflags +faststart -pix_fmt yuv420p output.mp4
```

### Создание WebM fallback
```bash
ffmpeg -i input.mp4 -c:v libvpx-vp9 -b:v 2M -c:a libopus output.webm
```

### Оптимизация существующего MP4
```bash
ffmpeg -i input.mp4 -c:v libx264 -crf 28 -c:a aac -b:a 96k \
  -movflags +faststart -vf "scale=1280:720" output-optimized.mp4
```

---

## ✅ Чеклист перед деплоем

- [ ] Видео конвертировано в MP4 (H.264)
- [ ] Размер файла < 10 MB
- [ ] Добавлены все атрибуты (`muted`, `playsinline`, `preload`)
- [ ] Обработка ошибок реализована
- [ ] Заглушка показывается при ошибке
- [ ] Логи в консоли чистые

---

## 📚 Дополнительные ресурсы

- [MDN: <video> element](https://developer.mozilla.org/en-US/docs/Web/HTML/Element/video)
- [Cloudinary: Video optimization](https://cloudinary.com/documentation/video_optimization)
- [Render: Static files](https://render.com/docs/static-sites)
