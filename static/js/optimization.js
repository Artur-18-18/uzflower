// ============================================================
// OPTIMIZATION UTILITIES
// Быстрые утилиты для оптимизации производительности
// ============================================================

// === Debounce Function ===
// Ограничивает частоту вызова функции
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// === Throttle Function ===
// Ограничивает выполнение функции до одного раза в указанный промежуток времени
function throttle(func, limit) {
    let inThrottle;
    return function(...args) {
        if (!inThrottle) {
            func.apply(this, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

// === Lazy Load Images ===
// Ленивая загрузка изображений
function initLazyLoading() {
    if ('IntersectionObserver' in window) {
        const imageObserver = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    if (img.dataset.src) {
                        img.src = img.dataset.src;
                        img.removeAttribute('data-src');
                        img.classList.add('loaded');
                    }
                    observer.unobserve(img);
                }
            });
        }, {
            rootMargin: '50px 0px',
            threshold: 0.01
        });

        document.querySelectorAll('img[data-src]').forEach(img => {
            imageObserver.observe(img);
        });
    } else {
        // Fallback для старых браузеров
        document.querySelectorAll('img[data-src]').forEach(img => {
            img.src = img.dataset.src;
            img.removeAttribute('data-src');
        });
    }
}

// === Cache API Responses ===
// Кэширование API запросов в localStorage
const apiCache = {
    cache: new Map(),
    
    async get(key, fetcher, ttl = 60000) {
        const cached = this.cache.get(key);
        if (cached && Date.now() - cached.timestamp < ttl) {
            return cached.data;
        }
        
        const data = await fetcher();
        this.cache.set(key, {
            data,
            timestamp: Date.now()
        });
        return data;
    },
    
    clear() {
        this.cache.clear();
    },
    
    delete(key) {
        this.cache.delete(key);
    }
};

// === Optimize Images for Web ===
// Конвертация URL изображений в WebP формат (если поддерживается)
function optimizeImageUrl(url, quality = 80) {
    if (!url) return url;
    
    // Проверяем поддержку WebP
    const supportsWebP = document.createElement('canvas').toDataURL('image/webp').includes('webp');
    
    if (supportsWebP && url.includes('cloudinary.com')) {
        // Для Cloudinary добавляем формат WebP
        return url.replace('/upload/', '/upload/f_auto,q_auto:best/');
    }
    
    return url;
}

// === Preload Critical Resources ===
// Предзагрузка критических ресурсов
function preloadResource(url, type = 'image') {
    if (type === 'image') {
        const link = document.createElement('link');
        link.rel = 'preload';
        link.as = 'image';
        link.href = url;
        document.head.appendChild(link);
    } else if (type === 'script') {
        const link = document.createElement('link');
        link.rel = 'preload';
        link.as = 'script';
        link.href = url;
        document.head.appendChild(link);
    }
}

// === Request Animation Frame ===
// Оптимизация анимаций через requestAnimationFrame
function optimizeAnimation(callback) {
    let running = false;
    return function(...args) {
        if (!running) {
            running = true;
            requestAnimationFrame(() => {
                callback.apply(this, args);
                running = false;
            });
        }
    };
}

// === Memory Management ===
// Очистка слушателей событий
function cleanupEventListeners(element, events = []) {
    events.forEach(event => {
        element.removeEventListener(event, element[`_${event}Handler`]);
        delete element[`_${event}Handler`];
    });
}

// ============================================================
// EXPORT FOR USE IN OTHER FILES
// ============================================================
if (typeof window !== 'undefined') {
    window.debounce = debounce;
    window.throttle = throttle;
    window.initLazyLoading = initLazyLoading;
    window.apiCache = apiCache;
    window.optimizeImageUrl = optimizeImageUrl;
    window.preloadResource = preloadResource;
    window.optimizeAnimation = optimizeAnimation;
}
