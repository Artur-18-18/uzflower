# Система переводов UzFlower (i18n)

## Обзор

Проект поддерживает два языка:
- 🇷🇺 **Русский** (ru) - язык по умолчанию
- 🇺🇿 **O'zbek** (uz) - узбекский язык

## Структура файлов

```
uzflower/
├── locales/                    # Исходные файлы переводов
│   ├── ru.json                # Русские переводы
│   └── uz.json                # Узбекские переводы
├── static/
│   └── js/
│       ├── i18n/              # Копии переводов для клиента
│       │   ├── ru.json
│       │   └── uz.json
│       └── i18n.js            # Клиентская библиотека переводов
└── templates/
    └── index.html             # Шаблон с data-i18n атрибутами
```

## Использование на фронтенде

### 1. Автоматический перевод элементов

Добавьте атрибут `data-i18n` к любому HTML элементу:

```html
<h1 data-i18n="hero.title">Весенняя Коллекция</h1>
<p data-i18n="hero.subtitle">Создайте незабываемые моменты</p>
<button data-i18n="products.add_to_cart">В корзину</button>
```

### 2. Перевод placeholder

```html
<input type="text" data-i18n-placeholder="header.search_placeholder" placeholder="Поиск...">
```

### 3. Перевод в JavaScript

```javascript
// Получить перевод
const title = i18n.t('hero.title');

// Перевод с параметрами
const message = i18n.t('validation.min_value', { min: 100 });

// Перевести всю страницу
i18n.translatePage();

// Переключить язык
i18n.setLang('uz');

// Получить текущий язык
console.log(i18n.currentLang); // 'ru' или 'uz'
```

### 4. Переключатель языка

Переключатель автоматически добавляется в header:

```html
<div class="lang-switcher hidden sm:flex"></div>
```

Кнопки переключения:
- 🇷🇺 для русского
- 🇺🇿 для узбекского

## Добавление новых переводов

### 1. Откройте файл переводов

Откройте `locales/ru.json` или `locales/uz.json`

### 2. Добавьте новый ключ

```json
{
  "my_new_section": {
    "title": "Заголовок",
    "description": "Описание",
    "button": "Кнопка"
  }
}
```

### 3. Используйте в HTML

```html
<h2 data-i18n="my_new_section.title">Заголовок</h2>
```

### 4. Синхронизируйте файлы

После изменения `locales/*.json` скопируйте файлы:

```bash
copy locales\ru.json static\js\i18n\ru.json
copy locales\uz.json static\js\i18n\uz.json
```

## Структура ключей переводов

| Ключ | Описание |
|------|----------|
| `common.*` | Общие элементы (кнопки, сообщения) |
| `header.*` | Шапка сайта |
| `hero.*` | Главный баннер |
| `categories.*` | Категории товаров |
| `products.*` | Карточки товаров |
| `advantages.*` | Преимущества |
| `filters.*` | Фильтры и сортировка |
| `reviews.*` | Отзывы |
| `cart.*` | Корзина |
| `checkout.*` | Оформление заказа |
| `profile.*` | Профиль пользователя |
| `orders.*` | Заказы |
| `favorites.*` | Избранное |
| `auth.*` | Авторизация и регистрация |
| `footer.*` | Подвал сайта |
| `notifications.*` | Уведомления |
| `validation.*` | Сообщения валидации |
| `custom_bouquet.*` | Конструктор букетов |
| `delivery.*` | Доставка |

## Хранение выбора языка

Выбранный язык сохраняется в `localStorage`:
```javascript
localStorage.setItem('uzflower_lang', 'uz');
```

При следующей загрузке страницы язык восстановится автоматически.

## События изменения языка

Можно подписаться на событие смены языка:

```javascript
window.addEventListener('languageChanged', (event) => {
    console.log('Новый язык:', event.detail.lang);
    // Обновить динамический контент
});
```

## RTL поддержка

Система поддерживает RTL языки (арабский, иврит и др.):

```json
{
  "meta": {
    "direction": "rtl"
  }
}
```

Для проверки направления:
```javascript
if (i18n.isRTL()) {
    // Применить RTL стили
}
```

## Добавление нового языка

1. Создайте файл `locales/<code>.json`
2. Скопируйте структуру из `ru.json`
3. Переведите все строки
4. Добавьте язык в `i18n.js`:
```javascript
languages: {
    ru: { name: 'Русский', flag: '🇷🇺' },
    uz: { name: "O'zbek", flag: '🇺🇿' },
    en: { name: 'English', flag: '🇬🇧' }  // Новый язык
}
```
5. Скопируйте файл в `static/js/i18n/`

## Примеры использования

### В приложении корзины

```javascript
function addToCart(product) {
    cart.push(product);
    
    // Показываем уведомление на текущем языке
    showToast(i18n.t('notifications.added_to_cart'));
}
```

### В форме оформления заказа

```javascript
function validateOrder(order) {
    if (!order.phone) {
        return { valid: false, message: i18n.t('validation.required') };
    }
    
    if (order.total < 10000) {
        return { 
            valid: false, 
            message: i18n.t('validation.min_value', { min: 10000 })
        };
    }
    
    return { valid: true };
}
```

### Динамическое обновление контента

```javascript
// Подписка на смену языка
window.addEventListener('languageChanged', () => {
    // Обновить заголовки модальных окон
    document.getElementById('modal-title').textContent = 
        i18n.t('custom_bouquet.title');
    
    // Обновить кнопки
    document.querySelectorAll('.btn-submit').forEach(btn => {
        btn.textContent = i18n.t('common.confirm');
    });
});
```

## Тестирование

1. Откройте сайт
2. Нажмите на флаг 🇺🇿 в header
3. Проверьте что все тексты перевелись
4. Обновите страницу - язык должен сохраниться
5. Нажмите 🇷🇺 чтобы вернуть русский

## Примечания

- Все переводы хранятся в JSON формате
- Ключи используют точечную нотацию (`section.key`)
- Поддерживается интерполяция параметров (`{param}`)
- Язык по умолчанию - русский (ru)
- Переключение работает без перезагрузки страницы
