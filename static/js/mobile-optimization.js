/**
 * Mobile Optimization Module
 * Оптимизация мобильной версии: жесты, свайпы, оптимизация
 */

// ============================================================
// 1. SWIPE GESTURES - Свайп жесты для навигации
// ============================================================

// Используем глобальные переменные из app.js если они есть
// Если нет - создаём локальные
if (typeof window.touchStartX === 'undefined') {
    window.touchStartX = 0;
    window.touchEndX = 0;
    window.touchStartY = 0;
    window.touchEndY = 0;
}

function initSwipeGestures() {
    document.addEventListener('touchstart', handleTouchStart, { passive: true });
    document.addEventListener('touchend', handleTouchEnd, { passive: true });
}

function handleTouchStart(event) {
    window.touchStartX = event.touches[0].clientX;
    window.touchStartY = event.touches[0].clientY;
}

function handleTouchEnd(event) {
    window.touchEndX = event.changedTouches[0].clientX;
    window.touchEndY = event.changedTouches[0].clientY;
    
    const deltaX = window.touchEndX - window.touchStartX;
    const deltaY = window.touchEndY - window.touchStartY;
    
    // Определяем, было ли движение горизонтальным
    if (Math.abs(deltaX) > Math.abs(deltaY) && Math.abs(deltaX) > 50) {
        // Горизонтальный свайп
        if (deltaX > 0) {
            // Свайп вправо - назад
            handleSwipeRight();
        } else {
            // Свайп влево - вперёд (можно использовать для истории)
            handleSwipeLeft();
        }
    }
    
    // Pull-to-refresh (свайп вниз для обновления)
    if (deltaY > 100 && window.scrollY < 50) {
        handlePullToRefresh();
    }
}

function handleSwipeRight() {
    // Закрытие модальных окон свайпом вправо
    const modals = [
        'product-detail-modal',
        'mobile-search-modal',
        'cart-sidebar',
        'fav-sidebar'
    ];
    
    for (const modalId of modals) {
        const modal = document.getElementById(modalId);
        if (modal && !modal.classList.contains('hidden')) {
            if (modalId === 'cart-sidebar' || modalId === 'fav-sidebar') {
                // Для боковых панелей
                modal.classList.add('hidden');
                document.body.style.overflow = '';
            } else {
                // Для полноэкранных модалок
                if (typeof window[getCloseFunction(modalId)] === 'function') {
                    window[getCloseFunction(modalId)]();
                }
            }
            break;
        }
    }
}

function handleSwipeLeft() {
    // Можно использовать для навигации вперёд (например, следующая страница каталога)
    console.log('Swipe left detected');
}

function handlePullToRefresh() {
    // Pull-to-refresh для обновления страницы
    if (window.location.pathname === '/' || window.location.pathname === '/index.html') {
        showRefreshIndicator();
        location.reload();
    }
}

function getCloseFunction(modalId) {
    const closeFunctions = {
        'product-detail-modal': 'closeProductDetail',
        'mobile-search-modal': 'closeMobileSearch',
        'cart-sidebar': 'toggleCart',
        'fav-sidebar': 'toggleFavorites'
    };
    return closeFunctions[modalId] || '';
}

// ============================================================
// 2. PULL-TO-REFRESH INDICATOR - Индикатор обновления
// ============================================================

function showRefreshIndicator() {
    const indicator = document.createElement('div');
    indicator.id = 'refresh-indicator';
    indicator.innerHTML = `
        <div class="fixed top-20 left-1/2 transform -translate-x-1/2 z-50">
            <div class="animate-spin rounded-full h-10 w-10 border-b-2 border-rose-600"></div>
        </div>
    `;
    document.body.appendChild(indicator);
    
    setTimeout(() => {
        indicator.remove();
    }, 2000);
}

// ============================================================
// 3. IMAGE OPTIMIZATION - Оптимизация изображений
// ============================================================

function initImageOptimization() {
    // Lazy loading для всех изображений
    document.querySelectorAll('img').forEach(img => {
        if (!img.hasAttribute('loading')) {
            img.setAttribute('loading', 'lazy');
        }
        
        // Добавляем placeholder
        if (!img.hasAttribute('data-placeholder')) {
            img.setAttribute('data-placeholder', 'true');
            img.style.background = 'linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%)';
            img.style.backgroundSize = '200% 100%';
            img.style.animation = 'loading 1.5s infinite';
            
            img.addEventListener('load', () => {
                img.style.background = '';
                img.style.animation = '';
            });
        }
    });
}

// ============================================================
// 4. SMOOTH SCROLL - Плавная прокрутка
// ============================================================

function initSmoothScroll() {
    // Плавная прокрутка для всех якорных ссылок
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            const href = this.getAttribute('href');
            if (href !== '#' && href !== 'javascript:void(0)') {
                e.preventDefault();
                const target = document.querySelector(href);
                if (target) {
                    target.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            }
        });
    });
}

// ============================================================
// 5. TOUCH FEEDBACK - Тактильная отдача
// ============================================================

function initTouchFeedback() {
    // Добавляем эффект нажатия для кнопок
    document.querySelectorAll('button, a, [role="button"]').forEach(element => {
        element.addEventListener('touchstart', function() {
            this.style.transform = 'scale(0.97)';
            this.style.transition = 'transform 0.1s ease';
        }, { passive: true });
        
        element.addEventListener('touchend', function() {
            this.style.transform = 'scale(1)';
        }, { passive: true });
    });
}

// ============================================================
// 6. MOBILE MENU OPTIMIZATION - Оптимизация мобильного меню
// ============================================================

function initMobileMenu() {
    // Автоматическое закрытие меню при клике на элемент
    document.querySelectorAll('.mobile-bottom-menu input[type="checkbox"]').forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            if (this.checked) {
                // Закрываем другие чекбоксы
                document.querySelectorAll('.mobile-bottom-menu input[type="checkbox"]').forEach(cb => {
                    if (cb !== this) {
                        cb.checked = false;
                    }
                });
            }
        });
    });
}

// ============================================================
// 7. PERFORMANCE OPTIMIZATION - Оптимизация производительности
// ============================================================

function initPerformanceOptimization() {
    // Debounce для скролла
    let scrollTimeout;
    window.addEventListener('scroll', () => {
        clearTimeout(scrollTimeout);
        scrollTimeout = setTimeout(() => {
            // Оптимизированный обработчик скролла
            handleOptimizedScroll();
        }, 10);
    }, { passive: true });
    
    // Throttle для resize
    let resizeTimeout;
    window.addEventListener('resize', () => {
        clearTimeout(resizeTimeout);
        resizeTimeout = setTimeout(() => {
            handleOptimizedResize();
        }, 200);
    });
}

function handleOptimizedScroll() {
    // Здесь можно добавить оптимизированные обработчики скролла
    // Например, показ/скрытие хедера
}

function handleOptimizedResize() {
    // Обработчик изменения размера окна
}

// ============================================================
// 8. SAFE AREA HANDLING - Обработка safe area (iPhone X+)
// ============================================================

function initSafeArea() {
    // Добавляем класс для элементов с safe area padding
    document.querySelectorAll('.safe-area-top').forEach(el => {
        el.style.paddingTop = 'max(1rem, env(safe-area-inset-top))';
    });
    
    document.querySelectorAll('.safe-area-bottom').forEach(el => {
        el.style.paddingBottom = 'max(1rem, env(safe-area-inset-bottom))';
    });
}

// ============================================================
// 9. GESTURE NAVIGATION - Жестовая навигация
// ============================================================

function initGestureNavigation() {
    // Навигация свайпом от края экрана (как в мобильных приложениях)
    let edgeSwipeStart = 0;
    
    document.addEventListener('touchstart', (e) => {
        // Проверяем, начинается ли свайп от левого края
        if (e.touches[0].clientX < 20) {
            edgeSwipeStart = e.touches[0].clientX;
        }
    }, { passive: true });
    
    document.addEventListener('touchmove', (e) => {
        if (edgeSwipeStart > 0 && e.touches[0].clientX > 100) {
            // Свайп от левого края - навигация назад
            history.back();
            edgeSwipeStart = 0;
        }
    }, { passive: true });
}

// ============================================================
// 10. MOBILE CART OPTIMIZATION - Оптимизация корзины
// ============================================================

function initMobileCart() {
    // Улучшенная прокрутка в корзине
    const cartItems = document.getElementById('cart-items');
    if (cartItems) {
        cartItems.style.webkitOverflowScrolling = 'touch';
    }
}

// ============================================================
// 11. PRODUCT CARD OPTIMIZATION - Оптимизация карточек товаров
// ============================================================

function initProductCards() {
    // Добавляем быстрое добавление в корзину по долгому тапу
    document.querySelectorAll('.card-3d').forEach(card => {
        let longPressTimer;
        
        card.addEventListener('touchstart', (e) => {
            longPressTimer = setTimeout(() => {
                // Долгий тап - быстрое добавление
                const addToCartBtn = card.querySelector('button[onclick*="addToCart"]');
                if (addToCartBtn) {
                    addToCartBtn.click();
                    
                    // Вибрация (если поддерживается)
                    if (navigator.vibrate) {
                        navigator.vibrate(50);
                    }
                }
            }, 500);
        }, { passive: true });
        
        card.addEventListener('touchend', () => {
            clearTimeout(longPressTimer);
        });
        
        card.addEventListener('touchmove', () => {
            clearTimeout(longPressTimer);
        });
    });
}

// ============================================================
// INITIALIZATION - Инициализация
// ============================================================

function initMobileOptimization() {
    // Проверяем, мобильное ли устройство
    const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent) ||
                     window.innerWidth <= 1024;
    
    if (isMobile) {
        console.log('📱 Mobile optimization initialized');
        
        // Инициализируем все модули
        initSwipeGestures();
        initImageOptimization();
        initSmoothScroll();
        initTouchFeedback();
        initMobileMenu();
        initPerformanceOptimization();
        initSafeArea();
        initGestureNavigation();
        initMobileCart();
        
        // Инициализируем карточки товаров после загрузки контента
        setTimeout(initProductCards, 1000);
    }
}

// Запускаем после загрузки DOM
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initMobileOptimization);
} else {
    initMobileOptimization();
}

// Экспорт функций для глобального доступа
window.mobileOptimization = {
    initSwipeGestures,
    initImageOptimization,
    initSmoothScroll,
    initTouchFeedback,
    initMobileMenu,
    initPerformanceOptimization,
    initSafeArea,
    initGestureNavigation,
    initMobileCart,
    initProductCards
};
