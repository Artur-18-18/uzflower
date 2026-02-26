/**
 * i18n - Система переводов UzFlower
 * Поддерживает русский и узбекский языки
 */

const i18n = {
    currentLang: 'ru',
    translations: {},

    // Доступные языки
    languages: {
        ru: { name: 'Русский', flag: '🇷🇺' },
        uz: { name: "O'zbek", flag: '🇺🇿' }
    },

    // Инициализация
    async init() {
        // Загружаем сохранённый язык из localStorage
        const savedLang = localStorage.getItem('uzflower_lang');
        if (savedLang && this.languages[savedLang]) {
            this.currentLang = savedLang;
        }

        // Загружаем переводы
        await this.loadTranslations();

        // Применяем переводы
        this.translatePage();

        // Обновляем переключатель языка
        this.updateLangSwitcher();
    },

    // Загрузка переводов
    async loadTranslations() {
        try {
            const response = await fetch(`/static/js/i18n/${this.currentLang}.json`);
            if (!response.ok) throw new Error('Failed to load translations');
            this.translations = await response.json();
        } catch (error) {
            console.error('Error loading translations:', error);
            // Загружаем переводы по умолчанию (русский)
            if (this.currentLang !== 'ru') {
                this.currentLang = 'ru';
                await this.loadTranslations();
            }
        }
    },

    // Получение перевода по ключу
    t(key, params = {}) {
        const keys = key.split('.');
        let value = this.translations;

        for (const k of keys) {
            if (value && typeof value === 'object' && k in value) {
                value = value[k];
            } else {
                return key; // Возвращаем ключ если перевод не найден
            }
        }

        // Подстановка параметров
        if (typeof value === 'string' && Object.keys(params).length > 0) {
            for (const [param, val] of Object.entries(params)) {
                value = value.replace(new RegExp(`\\{${param}\\}`, 'g'), val);
            }
        }

        return value;
    },

    // Перевод всей страницы
    translatePage() {
        // Перевод элементов с data-i18n атрибутом
        document.querySelectorAll('[data-i18n]').forEach(el => {
            const key = el.getAttribute('data-i18n');
            const translation = this.t(key);
            
            if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA') {
                if (el.getAttribute('placeholder')) {
                    el.placeholder = translation;
                } else {
                    el.value = translation;
                }
            } else if (el.tagName === 'IMG') {
                el.alt = translation;
            } else {
                el.textContent = translation;
            }
        });

        // Перевод элементов с data-i18n-placeholder
        document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
            const key = el.getAttribute('data-i18n-placeholder');
            el.placeholder = this.t(key);
        });

        // Перевод элементов с data-i18n-title
        document.querySelectorAll('[data-i18n-title]').forEach(el => {
            const key = el.getAttribute('data-i18n-title');
            el.title = this.t(key);
        });

        // Сохраняем язык в localStorage
        localStorage.setItem('uzflower_lang', this.currentLang);

        // Обновляем направление текста
        document.documentElement.lang = this.currentLang;
        document.documentElement.dir = this.translations.meta?.direction || 'ltr';

        // Генерируем событие изменения языка
        window.dispatchEvent(new CustomEvent('languageChanged', { 
            detail: { lang: this.currentLang } 
        }));
    },

    // Переключение языка
    setLang(lang) {
        if (this.languages[lang]) {
            this.currentLang = lang;
            this.loadTranslations().then(() => {
                this.translatePage();
                this.updateLangSwitcher();
            });
        }
    },

    // Обновление переключателя языка
    updateLangSwitcher() {
        document.querySelectorAll('.lang-switcher').forEach(el => {
            el.innerHTML = this.renderLangSwitcher();
        });

        // Обновляем активный класс на кнопках
        document.querySelectorAll('.lang-btn').forEach(btn => {
            const btnLang = btn.getAttribute('data-lang');
            btn.classList.toggle('active', btnLang === this.currentLang);
        });
    },

    // Рендер переключателя языка
    renderLangSwitcher() {
        return `
            <div class="lang-buttons">
                ${Object.entries(this.languages).map(([code, { name, flag }]) => `
                    <button 
                        class="lang-btn ${code === this.currentLang ? 'active' : ''}" 
                        data-lang="${code}"
                        onclick="i18n.setLang('${code}')"
                        title="${name}"
                    >
                        ${flag}
                    </button>
                `).join('')}
            </div>
        `;
    },

    // Получение текущего направления текста
    getDirection() {
        return this.translations.meta?.direction || 'ltr';
    },

    // Проверка RTL направления
    isRTL() {
        return this.getDirection() === 'rtl';
    }
};

// Автоинициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
    i18n.init();
});

// Экспортируем глобально
window.i18n = i18n;
