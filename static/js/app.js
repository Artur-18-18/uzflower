let currentUser = null;
let currentProfile = null;
let cart = JSON.parse(localStorage.getItem('cart') || '[]');
let favorites = JSON.parse(localStorage.getItem('favorites') || '[]');
let selectedCategory = null;
let appliedDiscount = 0;
let appliedPromoCode = null;
let allProductsList = [];
let selectedPaymentMethod = 'cash';
let isLoadingProducts = false;

// Telegram Bot Configuration
// Username берётся из window.TELEGRAM_BOT_USERNAME (задаётся в HTML) или используется по умолчанию
const TELEGRAM_BOT_USERNAME = window.TELEGRAM_BOT_USERNAME || 'uzflowershop_bot';

function formatPrice(price) {
    return Number(price).toLocaleString('ru-RU');
}

document.addEventListener('DOMContentLoaded', () => {
    lucide.createIcons();

    // Инициализация системы переводов
    if (window.i18n) {
        i18n.init();
    }

    loadUserFromStorage();
    loadCategories();
    loadBanners();
    loadProducts();
    loadReviews();  // Загружаем отзывы
    setupNavigation();
    setupHeaderScroll();
    // Инициализируем счётчики и кнопки избранного
    updateFavoriteButtons();
    const localCart = JSON.parse(localStorage.getItem('cart') || '[]');
    const totalCartItems = localCart.reduce((sum, item) => sum + item.quantity, 0);
    updateMobileCartCount(totalCartItems);
    // Сбрасываем radio button в мобильном меню
    const favRadio = document.getElementById('mobile-favorites');
    const cartRadio = document.getElementById('mobile-cart');
    if (favRadio) favRadio.checked = false;
    if (cartRadio) cartRadio.checked = false;
    // Избранное и корзина будут обновлены после загрузки товаров
});

function setupHeaderScroll() {
    const header = document.getElementById('main-header');
    if (!header) return;
    
    window.addEventListener('scroll', () => {
        if (window.scrollY > 50) {
            header.classList.add('rounded-b-3xl');
        } else {
            header.classList.remove('rounded-b-3xl');
        }
    });
}

// --- Auth ---

function loadUserFromStorage() {
    const savedUser = localStorage.getItem('user');
    const token = localStorage.getItem('token');
    
    if (savedUser && token) {
        currentUser = JSON.parse(savedUser);
        currentProfile = currentUser; // В нашей схеме они объединены
        console.log('✅ Пользователь загружен из хранилища:', currentUser.email);
    } else {
        console.log('ℹ️ Нет сохранённого пользователя или токена');
    }
    updateAuthUI();
}

function updateAuthUI() {
    const container = document.getElementById('auth-buttons');
    if (currentUser) {
        container.innerHTML = `
            <a href="/profile" class="flex items-center gap-2 px-3 py-2 hover:bg-gray-100 rounded-lg transition-colors">
                <div class="w-8 h-8 bg-rose-100 rounded-full flex items-center justify-center text-rose-600 font-bold">
                    ${currentUser.full_name?.[0] || 'U'}
                </div>
                <span class="hidden sm:block text-sm font-medium text-gray-700">${currentUser.full_name || 'Профиль'}</span>
            </a>
        `;
        renderCart();
    } else {
        container.innerHTML = `
            <a href="/login" class="px-4 py-2 bg-gradient-to-r from-rose-500 to-pink-600 text-white rounded-lg hover:from-rose-600 hover:to-pink-700 transition-all font-medium">
                Войти
            </a>
        `;
    }
}

function openAuthModal() {
    window.location.href = '/login';
}

function handleSignOut() {
    localStorage.removeItem('user');
    currentUser = null;
    window.location.href = '/';
}

// --- Products ---

function renderProducts(products, animate = false) {
    const container = document.getElementById('products-grid');
    if (!container) {
        console.error('❌ Контейнер products-grid не найден!');
        return;
    }

    console.log('📦 Рендер товаров:', products.length, 'штук');

    // Очищаем контейнер перед рендерингом
    container.innerHTML = '';

    container.innerHTML = products.map((product, index) => {
        const isFav = favorites.includes(product.id);
        const animationStyle = animate ? `opacity: 0; animation: fadeInUp 0.5s ease forwards; animation-delay: ${index * 50}ms;` : '';
        const productJson = JSON.stringify(product).replace(/"/g, '&quot;');
        
        // Для избранного используем SVG напрямую чтобы lucide не сбрасывал стили
        const heartIcon = isFav 
            ? `<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="rgb(225, 29, 72)" stroke="rgb(225, 29, 72)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-heart fill-rose-500 text-rose-500"><path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z"/></svg>`
            : `<i data-lucide="heart" class="w-5 h-5 text-gray-400"></i>`;
        
        return `
            <div class="card-3d scroll-reveal bg-white rounded-xl shadow-md overflow-hidden hover:shadow-xl transition-all duration-300 group cursor-pointer border border-gray-100" style="${animationStyle}" onclick="openProductDetail(${productJson})">
                <div class="relative aspect-square overflow-hidden bg-white">
                    <img src="${product.image_url || 'https://placehold.co/400'}" alt="${product.name}" class="w-full h-full object-contain p-2 hover:scale-105 transition-transform duration-500" loading="lazy">
                    ${product.stock === 0 ? '<div class="absolute inset-0 bg-black/50 flex items-center justify-center text-white font-bold">Нет в наличии</div>' : ''}
                    <button type="button" onclick="event.stopPropagation(); toggleFavorite(${product.id})" data-product-id="${product.id}" class="fav-heart-btn absolute top-3 right-3 flex items-center justify-center min-w-[44px] min-h-[44px] p-2 bg-white/90 backdrop-blur-sm rounded-full shadow-md hover:bg-white active:scale-95 transition-all z-10" aria-label="${isFav ? 'Убрать из избранного' : 'В избранное'}">
                        ${heartIcon}
                    </button>
                    ${product.is_sale ? '<div class="absolute top-3 left-3 bg-rose-500 text-white text-xs font-bold px-2 py-1 rounded">АКЦИЯ</div>' : ''}
                </div>
                <div class="p-4">
                    <h3 class="font-semibold text-lg text-gray-900 mb-2 line-clamp-2">${product.name}</h3>
                    <div class="flex items-center justify-between">
                        <div>
                            ${product.sale_price ? `
                                <span class="text-2xl font-bold text-rose-600">${formatPrice(product.sale_price)} сум</span>
                                <span class="text-sm text-gray-400 line-through ml-2">${formatPrice(product.price)} сум</span>
                            ` : `<span class="text-2xl font-bold text-gray-900">${formatPrice(product.price)} сум</span>`}
                        </div>
                        <div class="flex gap-2">
                             <button onclick="event.stopPropagation(); openProductDetail(${productJson})" class="p-2 border border-gray-200 text-gray-500 rounded-lg hover:border-rose-300 hover:text-rose-600 transition-all">
                                <i data-lucide="eye" class="w-5 h-5"></i>
                            </button>
                            <button onclick="event.stopPropagation(); addToCart(${productJson})" ${product.stock === 0 ? 'disabled' : ''} class="p-3 bg-rose-600 text-white rounded-lg hover:bg-rose-700 transition-all disabled:opacity-50">
                                <i data-lucide="shopping-cart" class="w-5 h-5"></i>
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }).join('');

    // Создаём иконки СРАЗУ после рендера, пропускаем fav-heart-btn
    if (window.lucide) {
        // Сначала применяем стили для избранного
        updateFavoriteButtons();
        // Затем создаём иконки для остальных элементов
        lucide.createIcons();
        console.log('✅ Иконки созданы после рендера товаров');
    }

    // Trigger scroll reveal after products are rendered
    setTimeout(() => {
        const reveals = document.querySelectorAll('.scroll-reveal');
        reveals.forEach((reveal) => {
            const elementTop = reveal.getBoundingClientRect().top;
            if (elementTop < window.innerHeight - 100) {
                reveal.classList.add('revealed');
            }
        });
    }, 100);
}

let activeProduct = null;
let currentImageIndex = 0;
let productImages = [];
let touchStartX = 0;
let touchEndX = 0;

/**
 * Преобразует URL Cloudinary для отдачи изображения в оригинальном качестве.
 * Добавляет параметры q_auto:best,f_auto если это Cloudinary URL.
 */
function getHighQualityImageUrl(url) {
    if (!url) return url;

    // Работа с Cloudinary
    if (url.includes('cloudinary.com') || url.includes('res.cloudinary.com')) {
        if (!url.includes('/upload/')) return url;
        
        // Просто заменяем /upload/ на /upload/q_auto:best,f_auto/ 
        // Но сначала удаляем любые существующие q_auto или f_auto для чистоты
        let cleanUrl = url.replace(/\/q_[^/]+/g, '').replace(/\/f_[^/]+/g, '');
        
        // Также удаляем любые другие трансформации типа w_500, h_500, c_fill и т.д.
        // Трансформации обычно идут сразу после /upload/ и не начинаются с 'v'
        const parts = cleanUrl.split('/upload/');
        const baseUrl = parts[0] + '/upload/';
        const secondPart = parts[1];
        
        const segments = secondPart.split('/');
        let dataStartIndex = 0;
        for (let i = 0; i < segments.length; i++) {
            // Если это не трансформация (обычно трансформации содержат '_', ',', или очень короткие)
            if (segments[i].startsWith('v') || segments[i].length > 10 || (!segments[i].includes('_') && !segments[i].includes(',') && segments[i].length > 4)) {
                dataStartIndex = i;
                break;
            }
        }
        
        const dataPath = segments.slice(dataStartIndex).join('/');
        return baseUrl + 'q_auto:best,f_auto/' + dataPath;
    }

    return url;
}

function openProductDetail(product) {
    activeProduct = product;
    currentImageIndex = 0;

    // Собираем все изображения товара в правильном порядке
    // Сначала главное изображение, затем дополнительные
    productImages = [];
    const seenUrls = new Set();

    console.log('🔍 Открытие товара:', product.name);
    console.log('📷 Главное изображение (image_url):', product.image_url);
    console.log('📷 Дополнительные изображения (images):', product.images);

    // Добавляем главное изображение первым
    if (product.image_url) {
        const highQualityUrl = getHighQualityImageUrl(product.image_url);
        productImages.push(highQualityUrl);
        seenUrls.add(product.image_url.split('?')[0]);
        console.log('✅ Добавлено главное изображение:', highQualityUrl);
    }

    // Добавляем дополнительные изображения (проверяем что это массив)
    if (product.images && Array.isArray(product.images) && product.images.length > 0) {
        product.images.forEach((url, idx) => {
            if (!url) return;

            // Проверяем на дубликаты (сравниваем без параметров)
            const urlBase = url.split('?')[0];
            if (!seenUrls.has(urlBase)) {
                seenUrls.add(urlBase);
                const highQualityUrl = getHighQualityImageUrl(url);
                productImages.push(highQualityUrl);
                console.log(`✅ Добавлено дополнительное изображение #${idx + 1}:`, highQualityUrl);
            } else {
                console.log(`⚠️ Пропущен дубликат:`, url);
            }
        });
    }

    console.log('📸 ВСЕГО изображений в галерее:', productImages.length);
    console.log('📸 Список URL:', productImages);

    const modal = document.getElementById('product-detail-modal');
    if (!modal) {
        console.error('❌ Модальное окно не найдено!');
        return;
    }

    // Блокируем прокрутку фона
    document.body.style.overflow = 'hidden';

    // Сбрасываем скролл в начало
    const scrollContainer = modal.querySelector('.overflow-y-auto');
    if (scrollContainer) {
        scrollContainer.scrollTop = 0;
    }

    document.getElementById('detail-name').innerText = product.name;
    document.getElementById('detail-desc').innerText = product.description || 'Описание отсутствует';
    document.getElementById('detail-composition').innerText = product.composition || 'Состав уточняйте у флориста';

    // Заполняем Swiper
    const swiperWrapper = document.getElementById('detail-swiper-wrapper');
    if (swiperWrapper) {
        // Если изображений нет, ставим placeholder
        const imagesToRender = productImages.length > 0 ? productImages : ['https://placehold.co/600'];
        swiperWrapper.innerHTML = imagesToRender.map((url, idx) => `
            <div class="swiper-slide" data-slide-index="${idx}">
                <img src="${url}" alt="Product image ${idx + 1}" style="width: 100%; height: auto;">
            </div>
        `).join('');

        console.log('🖼️ HTML для Swiper создан, слайдов:', imagesToRender.length);
    }

    // Удаляем старый инстанс Swiper если он был
    if (window.productSwiper && typeof window.productSwiper.destroy === 'function') {
        window.productSwiper.destroy(true, true);
        window.productSwiper = null;
        console.log('🔄 Старый Swiper уничтожен');
    }

    updateDetailPrice();
    modal.classList.remove('hidden');

    // Инициализируем Swiper после того, как модальное окно станет отображаться (remove 'hidden')
    setTimeout(() => {
        const swiperContainer = modal.querySelector('.swiper-container');
        if (!swiperContainer) {
            console.error('❌ Swiper container не найден!');
            return;
        }

        // Определяем количество изображений
        const hasMultipleImages = productImages.length > 1;
        const isMobile = window.innerWidth < 768;

        // Показываем/скрываем кнопки навигации в зависимости от количества фото
        const nextBtn = modal.querySelector('.swiper-button-next');
        const prevBtn = modal.querySelector('.swiper-button-prev');
        const pagination = modal.querySelector('.swiper-pagination');

        // На мобильных кнопки всегда видны если есть несколько изображений
        if (nextBtn) nextBtn.style.display = hasMultipleImages ? 'flex' : 'none';
        if (prevBtn) prevBtn.style.display = hasMultipleImages ? 'flex' : 'none';
        if (pagination) pagination.style.display = hasMultipleImages ? 'block' : 'none';

        window.productSwiper = new Swiper(swiperContainer, {
            loop: hasMultipleImages,
            allowSlidePrev: hasMultipleImages,
            allowSlideNext: hasMultipleImages,
            observer: true,
            observeParents: true,
            preloadImages: true,
            updateOnImagesReady: true,
            lazy: false,
            
            // Улучшенная навигация
            navigation: {
                nextEl: '.swiper-button-next',
                prevEl: '.swiper-button-prev',
            },
            
            // Пагинация
            pagination: {
                el: '.swiper-pagination',
                clickable: true,
                dynamicBullets: true,
                dynamicMainBullets: 5,
            },
            
            // Настройки для мобильных
            grabCursor: true,
            slidesPerView: 1,
            spaceBetween: 0,
            
            // Предотвращение случайных свайпов
            threshold: 10,
            touchRatio: 1,
            touchAngle: 45,
            
            // Автопрокрутка отключена
            autoplay: false,
            
            // Бесконечная прокрутка с эффектом
            rewind: false,
            
            // Эффект при переключении
            speed: 300,
            
            // Accessibility
            a11y: {
                prevSlideMessage: 'Предыдущее изображение',
                nextSlideMessage: 'Следующее изображение',
            },
            
            // События
            on: {
                init: function() {
                    console.log('✅ Swiper инициализирован');
                },
                slideChange: function() {
                    currentImageIndex = this.activeIndex;
                    console.log('📸 Слайд изменён:', currentImageIndex);
                },
                reachEnd: function() {
                    console.log('📸 Достигнут конец слайдера');
                },
                fromEdge: function() {
                    console.log('📸 Возврат от края');
                }
            }
        });
        
        console.log('✅ Swiper инициализирован, loop:', hasMultipleImages, 'mobile:', isMobile);
        console.log('✅ Текущий слайд:', window.productSwiper.activeIndex);
    }, 100);
}

function updateDetailPrice() {
    if (!activeProduct) return;
    // Use sale_price as base if it exists, otherwise use standard price
    let price = activeProduct.sale_price || activeProduct.price;

    document.getElementById('detail-price').innerText = formatPrice(price) + ' сум';
}

function addToCart(product) {
    // Clone product to avoid reference issues
    const cartItem = { ...product };

    // Use sale_price or base price
    cartItem.price = product.sale_price || product.price;

    const existing = cart.find(item => item.id === cartItem.id);
    if (existing) {
        existing.quantity += 1;
    } else {
        cart.push({ ...cartItem, quantity: 1 });
    }
    
    saveCart();
    updateCartCount();
    
    // Показываем toast уведомление
    showToast(`«${product.name}» добавлен в корзину`, 'success');
    
    // Открываем корзину
    toggleCart();
    
    // Закрываем модальное окно продукта если открыто
    if (document.getElementById('product-detail-modal')) {
        closeProductDetail();
    }
}

function closeProductDetail() {
    const modal = document.getElementById('product-detail-modal');
    modal.classList.add('hidden');
    // Восстанавливаем прокрутку body
    document.body.style.overflow = '';
    // Сбрасываем переменные
    currentImageIndex = 0;
    productImages = [];
}

async function loadCategories() {
    try {
        const res = await fetch('/api/categories');
        const categories = await res.json();

        // Render in Hero Grid
        const grid = document.getElementById('categories-grid');
        if (grid) {
            grid.innerHTML = categories.map(cat => `
                <button onclick="filterByCategory(${cat.id})" class="flex flex-col items-center group">
                    <div class="w-full aspect-square bg-gray-100 rounded-2xl flex items-center justify-center mb-3 group-hover:bg-rose-50 transition-all overflow-hidden border border-transparent group-hover:border-rose-200">
                        <img src="https://images.unsplash.com/photo-1526047932273-341f2a7631f9?w=300" alt="${cat.name}" class="w-full h-full object-cover opacity-80 group-hover:opacity-100 transition-opacity">
                    </div>
                    <span class="font-medium text-sm text-gray-700 group-hover:text-rose-600 transition-colors">${cat.name}</span>
                </button>
            `).join('');
        }

        // Render in Side Filter
        const filters = document.getElementById('category-filters');
        if (filters) {
            filters.innerHTML = `
                <button onclick="filterByCategory(null)" class="w-full text-left px-3 py-2 rounded-lg text-sm ${!selectedCategory ? 'bg-rose-50 text-rose-600 font-bold' : 'text-gray-600 hover:bg-gray-50'}">Все букеты</button>
                ${categories.map(cat => `
                    <button onclick="filterByCategory(${cat.id})" class="w-full text-left px-3 py-2 rounded-lg text-sm ${selectedCategory === cat.id ? 'bg-rose-50 text-rose-600 font-bold' : 'text-gray-600 hover:bg-gray-50'}">${cat.name}</button>
                `).join('')}
            `;
        }
    } catch (e) { console.error("Error loading categories:", e); }
}

function filterByCategory(id) {
    selectedCategory = id;
    loadCategories(); // Refresh buttons state

    // Плавная прокрутка к каталогу
    scrollToCatalog();

    loadProducts(true); // true = с анимацией
}

// Фильтрация по категории из мобильного поиска
function filterByCategoryFromSearch(id) {
    selectedCategory = id;
    
    // Закрываем мобильное меню если открыто
    const favRadio = document.getElementById('mobile-favorites');
    const cartRadio = document.getElementById('mobile-cart');
    if (favRadio) favRadio.checked = false;
    if (cartRadio) cartRadio.checked = false;
    
    // Плавная прокрутка к каталогу
    scrollToCatalog();
    
    loadProducts(true);
}

// Debounced search function (оптимизация поиска)
const handleSearch = debounce(function() {
    const query = document.getElementById('search-input')?.value?.toLowerCase().trim() || '';

    if (!query) {
        // Если поиск пустой, показываем все товары
        loadProducts(false);
        return;
    }

    // Фильтруем товары
    const filtered = allProductsList.filter(p =>
        p.name.toLowerCase().includes(query) ||
        (p.description && p.description.toLowerCase().includes(query))
    );

    // Прокрутка к каталогу
    scrollToCatalog();

    // Рендерим найденные товары
    const container = document.getElementById('products-grid');
    if (!container) return;

    if (filtered.length === 0) {
        container.innerHTML = `
            <div class="col-span-full text-center py-20">
                <i data-lucide="search-x" class="w-16 h-16 text-gray-300 mx-auto mb-4"></i>
                <p class="text-gray-500 text-lg">Букеты не найдены. Попробуйте изменить запрос.</p>
            </div>
        `;
        lucide.createIcons();
    } else {
        renderProducts(filtered, true);
        // Анимация прокрутки к первому товару
        setTimeout(() => {
            const firstProduct = container.querySelector('.bg-gray-100');
            if (firstProduct) {
                firstProduct.scrollIntoView({ behavior: 'smooth', block: 'center' });
                firstProduct.classList.add('ring-4', 'ring-rose-300');
                setTimeout(() => {
                    firstProduct.classList.remove('ring-4', 'ring-rose-300');
                }, 2000);
            }
        }, 300);
    }
}, 300); // Debounce 300ms

function scrollToTop(event) {
    if (event) event.preventDefault();
    
    // Если мы не на главной странице, переходим на неё
    if (window.location.pathname !== '/') {
        window.location.href = '/';
        return;
    }
    
    // Плавный скролл к баннеру (верх страницы)
    const heroBanner = document.getElementById('hero-banner');
    if (heroBanner) {
        heroBanner.scrollIntoView({ behavior: 'smooth', block: 'start' });
    } else {
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }
}

// Mobile menu navigation
function navigateToMobile(path) {
    if (path.startsWith('#')) {
        // Якорная ссылка
        const element = document.querySelector(path);
        if (element) {
            element.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    } else if (path === '/profile') {
        // Переход в профиль
        window.location.href = path;
    } else {
        // Главная страница
        window.location.href = '/';
    }
}

// Mobile search functions
let mobileSearchTimeout = null;

function openMobileSearch() {
    const modal = document.getElementById('mobile-search-modal');
    if (!modal) {
        console.error('Mobile search modal not found');
        return;
    }

    modal.classList.remove('hidden');

    setTimeout(() => {
        const input = document.getElementById('mobile-search-input');
        if (input) {
            input.focus();
            // Показываем популярные товары или подсказку при пустом поиске
            if (!input.value.trim()) {
                showEmptySearchState();
            }
        }
    }, 100);

    document.body.style.overflow = 'hidden';
}

function closeMobileSearch() {
    const modal = document.getElementById('mobile-search-modal');
    if (modal) {
        modal.classList.add('hidden');
        const input = document.getElementById('mobile-search-input');
        if (input) input.value = '';
        const results = document.getElementById('mobile-search-results');
        if (results) results.innerHTML = '';
    }
    // Очищаем таймер при закрытии
    if (mobileSearchTimeout) {
        clearTimeout(mobileSearchTimeout);
        mobileSearchTimeout = null;
    }
    document.body.style.overflow = '';
}

// Функция для показа начального состояния поиска (пустой запрос)
function showEmptySearchState() {
    const resultsContainer = document.getElementById('mobile-search-results');
    if (!resultsContainer) return;

    // Если товары ещё не загружены
    if (!allProductsList || allProductsList.length === 0) {
        resultsContainer.innerHTML = `
            <div class="flex flex-col items-center justify-center py-16">
                <div class="w-16 h-16 bg-gradient-to-br from-rose-100 to-pink-100 rounded-full flex items-center justify-center mb-4 animate-pulse">
                    <i data-lucide="loader" class="w-8 h-8 text-rose-500 animate-spin"></i>
                </div>
                <p class="text-gray-500 font-medium">Загрузка товаров...</p>
            </div>
        `;
        lucide.createIcons();
        return;
    }

    // Загружаем категории для отображения в поиске
    fetch('/api/categories')
        .then(res => res.json())
        .then(categories => {
            let categoriesHTML = '';
            
            if (categories && categories.length > 0) {
                categoriesHTML = `
                    <div class="mb-6">
                        <div class="search-section-header">
                            <div class="section-icon">
                                <i data-lucide="grid" class="w-4 h-4"></i>
                            </div>
                            <span class="section-title">Категории</span>
                        </div>
                        <div class="grid grid-cols-3 gap-2">
                            <button onclick="filterByCategoryFromSearch(null); closeMobileSearch();" 
                                class="search-category-card">
                                <span class="category-name">Все букеты</span>
                            </button>
                            ${categories.map(cat => `
                                <button onclick="filterByCategoryFromSearch(${cat.id}); closeMobileSearch();" 
                                    class="search-category-card">
                                    <span class="category-name">${cat.name}</span>
                                </button>
                            `).join('')}
                        </div>
                    </div>
                `;
            }

            // Показываем популярные товары (первые 12)
            const popularProducts = allProductsList.slice(0, 12);
            resultsContainer.innerHTML = `
                ${categoriesHTML}
                <div class="mb-6">
                    <div class="search-section-header">
                        <div class="section-icon">
                            <i data-lucide="flame" class="w-4 h-4"></i>
                        </div>
                        <span class="section-title">Популярные букеты</span>
                    </div>
                    <div class="grid grid-cols-3 gap-3">
                        ${popularProducts.map(product => `
                            <div class="search-product-card" onclick="selectProductFromSearch(${product.id})">
                                <img src="${product.image_url || 'https://placehold.co/200'}" alt="${product.name}" loading="lazy">
                                <p class="product-name line-clamp-2">${product.name}</p>
                                <p class="product-price">${formatPrice(product.price)} сум</p>
                            </div>
                        `).join('')}
                    </div>
                </div>
            `;
            lucide.createIcons();
        })
        .catch(err => {
            console.error('Ошибка загрузки категорий:', err);
            // Показываем только товары если категории не загрузились
            const popularProducts = allProductsList.slice(0, 12);
            resultsContainer.innerHTML = `
                <div class="mb-6">
                    <div class="search-section-header">
                        <div class="section-icon">
                            <i data-lucide="flame" class="w-4 h-4"></i>
                        </div>
                        <span class="section-title">Популярные букеты</span>
                    </div>
                    <div class="grid grid-cols-3 gap-3">
                        ${popularProducts.map(product => `
                            <div class="search-product-card" onclick="selectProductFromSearch(${product.id})">
                                <img src="${product.image_url || 'https://placehold.co/200'}" alt="${product.name}" loading="lazy">
                                <p class="product-name line-clamp-2">${product.name}</p>
                                <p class="product-price">${formatPrice(product.price)} сум</p>
                            </div>
                        `).join('')}
                    </div>
                </div>
            `;
            lucide.createIcons();
        });
}

// Debounced mobile search function
function handleMobileSearch() {
    if (mobileSearchTimeout) {
        clearTimeout(mobileSearchTimeout);
    }

    mobileSearchTimeout = setTimeout(() => {
        performMobileSearch();
    }, 300); // Debounce 300ms
}

function performMobileSearch() {
    const query = document.getElementById('mobile-search-input').value.toLowerCase().trim();
    const resultsContainer = document.getElementById('mobile-search-results');

    if (!resultsContainer) return;

    // Если товары ещё не загружены
    if (!allProductsList || allProductsList.length === 0) {
        resultsContainer.innerHTML = `
            <div class="flex flex-col items-center justify-center py-16">
                <div class="w-16 h-16 bg-gradient-to-br from-rose-100 to-pink-100 rounded-full flex items-center justify-center mb-4 animate-pulse">
                    <i data-lucide="loader" class="w-8 h-8 text-rose-500 animate-spin"></i>
                </div>
                <p class="text-gray-500 font-medium">Товары загружаются...</p>
            </div>
        `;
        lucide.createIcons();
        return;
    }

    if (!query) {
        showEmptySearchState();
        return;
    }

    // Фильтруем товары с улучшенным поиском
    const filtered = allProductsList.filter(p =>
        p.name.toLowerCase().includes(query) ||
        (p.description && p.description.toLowerCase().includes(query)) ||
        (p.composition && p.composition.toLowerCase().includes(query))
    );

    if (filtered.length === 0) {
        resultsContainer.innerHTML = `
            <div class="flex flex-col items-center justify-center py-16">
                <div class="w-20 h-20 bg-gradient-to-br from-gray-100 to-gray-200 rounded-full flex items-center justify-center mb-4">
                    <i data-lucide="search-x" class="w-10 h-10 text-gray-400"></i>
                </div>
                <p class="text-gray-600 font-semibold text-lg mb-1">Ничего не найдено</p>
                <p class="text-gray-400 text-sm">Попробуйте изменить запрос</p>
            </div>
        `;
    } else {
        resultsContainer.innerHTML = `
            <div class="mb-6">
                <div class="flex items-center justify-between mb-4 pb-3 border-b-2 border-gray-100">
                    <div class="flex items-center gap-2">
                        <div class="w-7 h-7 bg-gradient-to-br from-emerald-400 to-teal-500 rounded-lg flex items-center justify-center">
                            <i data-lucide="check" class="w-4 h-4 text-white"></i>
                        </div>
                        <span class="font-semibold text-gray-700">Результаты поиска</span>
                    </div>
                    <span class="text-xs font-medium bg-rose-100 text-rose-600 px-3 py-1 rounded-full">${filtered.length} тов.</span>
                </div>
                <div class="grid grid-cols-3 gap-3">
                    ${filtered.map(product => renderSearchProductCard(product)).join('')}
                </div>
            </div>
        `;
    }

    lucide.createIcons();
}

// Рендеринг карточки товара для поиска
function renderSearchProductCard(product) {
    return `
        <div class="search-product-card" onclick="selectProductFromSearch(${product.id})">
            <img src="${product.image_url || 'https://placehold.co/200'}" alt="${product.name}" loading="lazy">
            <p class="product-name line-clamp-2">${product.name}</p>
            <p class="product-price">${formatPrice(product.price)} сум</p>
        </div>
    `;
}

// Рендеринг элемента результата поиска с подсветкой совпадений
function renderSearchResultItem(product, query) {
    const highlightedName = highlightText(product.name, query);
    const highlightedDesc = product.description ? highlightText(product.description, query) : '';
    
    return `
        <div class="search-result-item bg-white p-3 rounded-xl mb-3 shadow-sm flex gap-3 items-center active:scale-[0.98] transition-transform cursor-pointer" 
             onclick="selectProductFromSearch(${product.id})">
            <img src="${product.image_url || 'https://placehold.co/60'}" alt="${product.name}" class="w-16 h-16 object-cover rounded-lg flex-shrink-0">
            <div class="flex-1 min-w-0">
                <p class="font-semibold text-gray-900 text-sm line-clamp-2">${highlightedName}</p>
                ${highlightedDesc ? `<p class="text-xs text-gray-500 mt-1 line-clamp-1">${highlightedDesc}</p>` : ''}
                <p class="text-rose-600 font-bold text-sm mt-1">${formatPrice(product.price)} сум</p>
            </div>
            <i data-lucide="chevron-right" class="w-5 h-5 text-gray-300 flex-shrink-0"></i>
        </div>
    `;
}

// Подсветка найденного текста
function highlightText(text, query) {
    if (!text || !query) return text;
    
    const regex = new RegExp(`(${escapeRegExp(query)})`, 'gi');
    return text.replace(regex, '<mark class="bg-yellow-200 text-gray-900 px-0.5 rounded">$1</mark>');
}

// Экранирование специальных символов для RegExp
function escapeRegExp(string) {
    return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

// Выбор товара из поиска
function selectProductFromSearch(productId) {
    const product = allProductsList.find(p => p.id === productId);
    
    if (!product) {
        console.error('Товар не найден по ID:', productId);
        return;
    }
    
    if (typeof openProductDetail !== 'function') {
        console.error('Функция openProductDetail не найдена');
        return;
    }
    
    closeMobileSearch();
    setTimeout(() => {
        openProductDetail(product);
    }, 300); // Небольшая задержка для плавного закрытия модалки
}

// Обработка нажатий клавиш в поиске
function handleMobileSearchKeydown(event) {
    if (event.key === 'Enter') {
        event.preventDefault();
        // Снимаем фокус с инпута, чтобы скрыть клавиатуру на мобильных
        event.target.blur();
    } else if (event.key === 'Escape') {
        closeMobileSearch();
    }
}

// Mobile favorites functions
function toggleMobileFavorites() {
    let sidebar = document.getElementById('mobile-favorites-sidebar');
    let overlay = document.getElementById('favorites-overlay');
    
    // Создаём overlay если нет
    if (!overlay) {
        overlay = document.createElement('div');
        overlay.id = 'favorites-overlay';
        overlay.className = 'fixed inset-0 bg-black/50 z-30 hidden transition-opacity duration-300 opacity-0';
        overlay.onclick = () => {
            closeMobileFavorites();
            closeMobileCart();
        };
        document.body.appendChild(overlay);
    }
    
    // Создаём sidebar если нет
    if (!sidebar) {
        sidebar = document.createElement('div');
        sidebar.id = 'mobile-favorites-sidebar';
        sidebar.className = 'fixed inset-x-0 bottom-[80px] z-40 bg-white rounded-t-3xl shadow-[0_-4px_20px_rgba(0,0,0,0.1)] transform transition-transform duration-300 translate-y-[110%] flex flex-col max-h-[80vh]';
        sidebar.innerHTML = `
            <div class="p-5 border-b border-gray-100 flex justify-between items-center bg-white rounded-t-3xl sticky top-0 z-10">
                <h2 class="text-xl font-bold text-gray-900">Избранное</h2>
                <button onclick="closeMobileFavorites()" class="p-2 bg-gray-100 rounded-full hover:bg-gray-200 transition-colors">
                    <i data-lucide="x" class="w-5 h-5 text-gray-500"></i>
                </button>
            </div>
            <div id="mobile-favorites-list" class="p-4 overflow-y-auto flex-1 pb-20"></div>
        `;
        document.body.appendChild(sidebar);
        lucide.createIcons();
    }
    
    if (sidebar.classList.contains('translate-y-0')) {
        closeMobileFavorites();
    } else {
        closeMobileCart(); // Закрываем корзину если открыта
        
        sidebar.classList.remove('translate-y-[110%]');
        sidebar.classList.add('translate-y-0');
        
        overlay.classList.remove('hidden');
        setTimeout(() => overlay.classList.remove('opacity-0'), 10);
        
        document.body.style.overflow = 'hidden';
        loadMobileFavorites();
    }
}

function closeMobileFavorites() {
    const sidebar = document.getElementById('mobile-favorites-sidebar');
    const overlay = document.getElementById('favorites-overlay');

    if (sidebar) {
        sidebar.classList.remove('translate-y-0');
        sidebar.classList.add('translate-y-[110%]');
    }

    if (overlay && !document.getElementById('mobile-cart-sidebar')?.classList.contains('translate-y-0')) {
        overlay.classList.add('opacity-0');
        setTimeout(() => overlay.classList.add('hidden'), 300);
    }

    document.body.style.overflow = '';
    
    // Сбрасываем radio button
    const favRadio = document.getElementById('mobile-favorites');
    if (favRadio) favRadio.checked = false;
}

// Mobile Cart Functions
function toggleMobileCart() {
    let sidebar = document.getElementById('mobile-cart-sidebar');
    let overlay = document.getElementById('favorites-overlay');

    if (!overlay) {
        overlay = document.createElement('div');
        overlay.id = 'favorites-overlay';
        overlay.className = 'fixed inset-0 bg-black/50 z-30 hidden transition-opacity duration-300 opacity-0';
        overlay.onclick = () => {
            closeMobileFavorites();
            closeMobileCart();
        };
        document.body.appendChild(overlay);
    }

    if (!sidebar) {
        sidebar = document.createElement('div');
        sidebar.id = 'mobile-cart-sidebar';
        sidebar.className = 'fixed inset-x-0 bottom-[80px] z-40 bg-white rounded-t-3xl shadow-[0_-4px_20px_rgba(0,0,0,0.1)] transform transition-transform duration-300 translate-y-[110%] flex flex-col max-h-[80vh]';
        sidebar.innerHTML = `
            <div class="p-5 border-b border-gray-100 flex justify-between items-center bg-white rounded-t-3xl sticky top-0 z-10">
                <h2 class="text-xl font-bold text-gray-900">Корзина</h2>
                <button onclick="closeMobileCart()" class="p-2 bg-gray-100 rounded-full hover:bg-gray-200 transition-colors">
                    <i data-lucide="x" class="w-5 h-5 text-gray-500"></i>
                </button>
            </div>
            <div id="mobile-cart-list" class="p-4 overflow-y-auto flex-1"></div>
            <div class="p-5 border-t border-gray-100 bg-white sticky bottom-0 z-10">
                <div class="flex justify-between items-center mb-4">
                    <span class="text-gray-500">Итого:</span>
                    <span id="mobile-cart-total" class="text-xl font-bold text-rose-600">0 сум</span>
                </div>
                <button onclick="handleCheckout()" class="w-full py-3 bg-rose-600 text-white rounded-xl font-bold hover:bg-rose-700 transition-all shadow-lg shadow-rose-200">
                    Оформить заказ
                </button>
            </div>
        `;
        document.body.appendChild(sidebar);
        lucide.createIcons();
    }

    if (sidebar.classList.contains('translate-y-0')) {
        closeMobileCart();
    } else {
        closeMobileFavorites(); // Закрываем избранное если открыто

        sidebar.classList.remove('translate-y-[110%]');
        sidebar.classList.add('translate-y-0');

        overlay.classList.remove('hidden');
        setTimeout(() => overlay.classList.remove('opacity-0'), 10);

        document.body.style.overflow = 'hidden';
        renderMobileCart();
    }
}

function closeMobileCart() {
    const sidebar = document.getElementById('mobile-cart-sidebar');
    const overlay = document.getElementById('favorites-overlay');

    if (sidebar) {
        sidebar.classList.remove('translate-y-0');
        sidebar.classList.add('translate-y-[110%]');
    }

    if (overlay && !document.getElementById('mobile-favorites-sidebar')?.classList.contains('translate-y-0')) {
        overlay.classList.add('opacity-0');
        setTimeout(() => overlay.classList.add('hidden'), 300);
    }

    document.body.style.overflow = '';
    
    // Сбрасываем radio button
    const cartRadio = document.getElementById('mobile-cart');
    if (cartRadio) cartRadio.checked = false;
}

function renderMobileCart() {
    const container = document.getElementById('mobile-cart-list');
    const totalElem = document.getElementById('mobile-cart-total');
    
    if (!container || !totalElem) return;
    
    if (cart.length === 0) {
        container.innerHTML = `
            <div class="flex flex-col items-center justify-center py-10 text-gray-400">
                <i data-lucide="shopping-bag" class="w-16 h-16 mb-4 opacity-20"></i>
                <p>Корзина пуста</p>
            </div>
        `;
        totalElem.innerText = '0 сум';
        lucide.createIcons();
        return;
    }
    
    container.innerHTML = cart.map(item => `
        <div class="flex gap-3 mb-4 bg-gray-50 p-3 rounded-xl">
            <img src="${item.image_url || 'https://placehold.co/80'}" class="w-20 h-20 object-cover rounded-lg">
            <div class="flex-1 min-w-0">
                <h4 class="font-bold text-sm text-gray-900 truncate">${item.name}</h4>
                <p class="text-rose-600 font-bold text-sm">${formatPrice(item.sale_price || item.price)} сум</p>

                <div class="flex items-center gap-3 mt-2">
                    <button onclick="updateQuantity(${item.id}, -1)" class="w-7 h-7 rounded-lg bg-white border border-gray-200 flex items-center justify-center">-</button>
                    <span class="text-sm font-bold">${item.quantity}</span>
                    <button onclick="updateQuantity(${item.id}, 1)" class="w-7 h-7 rounded-lg bg-white border border-gray-200 flex items-center justify-center">+</button>
                </div>
            </div>
            <button onclick="removeFromCart(${item.id})" class="self-start text-gray-300 hover:text-red-500">
                <i data-lucide="trash-2" class="w-5 h-5"></i>
            </button>
        </div>
    `).join('');
    
    const total = cart.reduce((sum, item) => sum + (item.sale_price || item.price) * item.quantity, 0);
    totalElem.innerText = formatPrice(total) + ' сум';
    
    lucide.createIcons();
}

function loadMobileFavorites() {
    const container = document.getElementById('mobile-favorites-list');
    const localFavorites = JSON.parse(localStorage.getItem('favorites') || '[]');

    // Обновляем счётчики везде
    updateFavoriteCounts();

    if (localFavorites.length === 0) {
        container.innerHTML = `
            <div class="favorites-empty-state py-8">
                <div class="icon-wrapper mb-4">
                    <i data-lucide="heart" class="w-10 h-10"></i>
                </div>
                <h3 class="text-lg font-bold text-gray-900 mb-2">Избранное пусто</h3>
                <p class="text-gray-500">Добавляйте товары через сердечко в каталоге</p>
            </div>
        `;
        if (window.lucide) lucide.createIcons();
        return;
    }

    // Фильтруем товары которые в избранном
    const favProducts = allProductsList.filter(p => localFavorites.includes(p.id));

    if (favProducts.length === 0) {
        container.innerHTML = '<p class="text-center text-gray-500 py-8">Товары больше недоступны</p>';
        return;
    }

    container.innerHTML = favProducts.map((product, index) => `
        <div class="fav-item flex gap-3 p-3 rounded-xl bg-white border border-gray-100 shadow-sm" style="animation-delay: ${index * 50}ms">
            <img src="${product.image_url || 'https://placehold.co/80'}" 
                alt="${product.name}" 
                class="w-20 h-20 object-cover rounded-lg flex-shrink-0">
            <div class="flex-1 min-w-0 flex flex-col justify-between py-1">
                <div>
                    <h4 class="font-semibold text-sm text-gray-900 truncate">${product.name}</h4>
                </div>
                <div class="flex items-center justify-between">
                    <p class="text-rose-600 font-bold text-sm">${formatPrice(product.sale_price || product.price)} сум</p>
                </div>
            </div>
            <div class="flex flex-col gap-2 justify-center">
                <button onclick="quickAddToCart(${product.id}); closeMobileFavorites();" 
                    class="p-2 bg-rose-50 text-rose-600 rounded-lg hover:bg-rose-100 transition-all"
                    title="В корзину">
                    <i data-lucide="shopping-cart" class="w-4 h-4"></i>
                </button>
                <button type="button" 
                    onclick="removeFromFavorites(${product.id}); closeMobileFavorites();" 
                    class="p-2 text-gray-400 hover:text-red-500 hover:bg-red-50 transition-all rounded-lg" 
                    title="Удалить">
                    <i data-lucide="trash-2" class="w-4 h-4"></i>
                </button>
            </div>
        </div>
    `).join('');

    if (window.lucide) lucide.createIcons();
}

/**
 * Обновить счетчик корзины в мобильном меню
 */
function updateMobileCartCount(count) {
    const badge = document.getElementById('mobile-cart-count');
    if (badge) {
        badge.textContent = count;
        badge.style.display = count > 0 ? 'flex' : 'none';
    }
}

function scrollToCatalog() {
    const catalogSection = document.getElementById('catalog');
    if (catalogSection) {
        catalogSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
}

async function loadBanners() {
    try {
        const res = await fetch('/api/banners');
        const banners = await res.json();

        const bannerContainer = document.getElementById('hero-banner');
        if (!bannerContainer || banners.length === 0) return;

        // Если только один баннер
        if (banners.length === 1) {
            renderSingleBanner(bannerContainer, banners[0]);
            return;
        }

        // Слайдер с несколькими баннерами
        let currentBannerIndex = 0;
        let bannerTimeout = null;

        // Очищаем предыдущий таймер при переключении
        const clearBannerTimeout = () => {
            if (bannerTimeout) {
                clearTimeout(bannerTimeout);
                bannerTimeout = null;
            }
        };

        const renderBanner = (banner, index) => {
            const bannerText = banner.text || 'Весенняя Коллекция';
            const bannerSubtext = banner.subtext || 'Создайте незабываемые моменты с нашими авторскими букетами';

            if (banner.media_type === 'video' && banner.video_url) {
                bannerContainer.innerHTML = `
                    <video id="hero-video" class="absolute inset-0 w-full h-full object-cover opacity-60" autoplay muted loop playsinline>
                        <source src="${banner.video_url}" type="video/mp4">
                        Ваш браузер не поддерживает видео.
                    </video>
                    <div class="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-full flex flex-col justify-center items-center text-center text-white pointer-events-none">
                        <h1 class="text-6xl md:text-8xl font-serif font-bold mb-6 drop-shadow-2xl animate-banner-text">${bannerText}</h1>
                        <p class="text-xl md:text-2xl mb-10 text-white/90 max-w-2xl drop-shadow-lg animate-banner-subtext">${bannerSubtext}</p>
                        <div class="flex gap-4 pointer-events-auto animate-banner-buttons">
                            <button onclick="scrollToCatalog()" class="px-10 py-4 bg-rose-600 text-white rounded-full font-bold hover:bg-rose-700 transition-all text-lg shadow-xl">Выбрать букет</button>
                            <button onclick="toggleCustomBouquet()" class="px-10 py-4 bg-white/20 backdrop-blur-md text-white border border-white/30 rounded-full font-bold hover:bg-white/30 transition-all text-lg">Собрать свой</button>
                        </div>
                    </div>
                `;

                // Обработка ошибок загрузки видео
                const video = document.getElementById('hero-video');
                if (video) {
                    video.addEventListener('error', () => {
                        console.error('Ошибка загрузки видео:', banner.video_url);
                        // Переключаем на следующий баннер если видео не загрузилось
                        clearBannerTimeout();
                        const nextIndex = (index + 1) % banners.length;
                        renderBanner(banners[nextIndex], nextIndex);
                    });

                    // Видео успешно загрузилось - переключаем через 15 секунд
                    video.addEventListener('loadeddata', () => {
                        console.log('✅ Видео загружено, показываем 15 сек');
                        clearBannerTimeout();
                        bannerTimeout = setTimeout(() => {
                            const nextIndex = (index + 1) % banners.length;
                            renderBanner(banners[nextIndex], nextIndex);
                        }, 15000);
                    });
                }

            } else if (banner.image_url) {
                bannerContainer.innerHTML = `
                    <div class="absolute inset-0 opacity-60">
                        <img src="${banner.image_url}" alt="Banner" class="w-full h-full object-cover">
                    </div>
                    <div class="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-full flex flex-col justify-center items-center text-center text-white pointer-events-none">
                        <h1 class="text-6xl md:text-8xl font-serif font-bold mb-6 drop-shadow-2xl animate-banner-text">${bannerText}</h1>
                        <p class="text-xl md:text-2xl mb-10 text-white/90 max-w-2xl drop-shadow-lg animate-banner-subtext">${bannerSubtext}</p>
                        <div class="flex gap-4 pointer-events-auto animate-banner-buttons">
                            <button onclick="scrollToCatalog()" class="px-10 py-4 bg-rose-600 text-white rounded-full font-bold hover:bg-rose-700 transition-all text-lg shadow-xl">Выбрать букет</button>
                            <button onclick="toggleCustomBouquet()" class="px-10 py-4 bg-white/20 backdrop-blur-md text-white border border-white/30 rounded-full font-bold hover:bg-white/30 transition-all text-lg">Собрать свой</button>
                        </div>
                    </div>
                `;

                // Для изображений — автопереключение через 5 секунд
                console.log(`🖼️ Показываем изображение #${index + 1}, переключение через 5 сек`);
                clearBannerTimeout();
                bannerTimeout = setTimeout(() => {
                    const nextIndex = (index + 1) % banners.length;
                    renderBanner(banners[nextIndex], nextIndex);
                }, 5000);
            }

            // Клик по баннеру с ссылкой
            if (banner.link) {
                bannerContainer.style.cursor = 'pointer';
                bannerContainer.onclick = (e) => {
                    // Если это кнопка - не переходим по ссылке баннера
                    if (e.target.tagName === 'BUTTON' || e.target.closest('button')) {
                        return;
                    }
                    window.location.href = banner.link;
                };
            }
        };

        // Запускаем первый баннер
        console.log(`🚀 Запуск слайдера, всего баннеров: ${banners.length}`);
        renderBanner(banners[currentBannerIndex], currentBannerIndex);

    } catch (e) {
        console.error("Error loading banners:", e);
    }
}

function renderSingleBanner(container, banner) {
    const bannerText = banner.text || 'Весенняя Коллекция';
    const bannerSubtext = banner.subtext || 'Создайте незабываемые моменты с нашими авторскими букетами';
    
    if (banner.media_type === 'video' && banner.video_url) {
        container.innerHTML = `
            <video class="absolute inset-0 w-full h-full object-cover opacity-60" autoplay muted loop playsinline src="${banner.video_url}">
                Ваш браузер не поддерживает видео.
            </video>
            <div class="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-full flex flex-col justify-center items-center text-center text-white">
                <h1 class="text-6xl md:text-8xl font-serif font-bold mb-6 drop-shadow-2xl animate-banner-text">${bannerText}</h1>
                <p class="text-xl md:text-2xl mb-10 text-white/90 max-w-2xl drop-shadow-lg animate-banner-subtext">${bannerSubtext}</p>
                <div class="flex gap-4 animate-banner-buttons">
                    <button onclick="scrollToCatalog()" class="px-10 py-4 bg-rose-600 text-white rounded-full font-bold hover:bg-rose-700 transition-all text-lg shadow-xl">Выбрать букет</button>
                    <button onclick="toggleCustomBouquet()" class="px-10 py-4 bg-white/20 backdrop-blur-md text-white border border-white/30 rounded-full font-bold hover:bg-white/30 transition-all text-lg">Собрать свой</button>
                </div>
            </div>
        `;
    } else if (banner.image_url) {
        container.innerHTML = `
            <div class="absolute inset-0 opacity-60">
                <img src="${banner.image_url}" alt="Banner" class="w-full h-full object-cover">
            </div>
            <div class="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-full flex flex-col justify-center items-center text-center text-white">
                <h1 class="text-6xl md:text-8xl font-serif font-bold mb-6 drop-shadow-2xl animate-banner-text">${bannerText}</h1>
                <p class="text-xl md:text-2xl mb-10 text-white/90 max-w-2xl drop-shadow-lg animate-banner-subtext">${bannerSubtext}</p>
                <div class="flex gap-4 animate-banner-buttons">
                    <button onclick="scrollToCatalog()" class="px-10 py-4 bg-rose-600 text-white rounded-full font-bold hover:bg-rose-700 transition-all text-lg shadow-xl">Выбрать букет</button>
                    <button onclick="toggleCustomBouquet()" class="px-10 py-4 bg-white/20 backdrop-blur-md text-white border border-white/30 rounded-full font-bold hover:bg-white/30 transition-all text-lg">Собрать свой</button>
                </div>
            </div>
        `;
    }

    if (banner.link) {
        container.style.cursor = 'pointer';
        container.onclick = () => window.location.href = banner.link;
    }
}

async function loadReviews() {
    try {
        const res = await fetch('/api/reviews?limit=6&approved_only=true');
        const reviews = await res.json();
        const container = document.getElementById('reviews-display');
        
        if (!container) return;
        
        if (reviews.length === 0) {
            container.innerHTML = `
                <div class="col-span-full text-center py-12 text-gray-500">
                    <i data-lucide="message-circle" class="w-16 h-16 mx-auto mb-4 text-gray-300"></i>
                    <p>Пока нет отзывов</p>
                </div>
            `;
            lucide.createIcons();
            return;
        }
        
        container.innerHTML = reviews.map(r => `
            <div class="bg-white p-6 rounded-xl shadow-sm hover:shadow-md transition-all">
                <div class="flex items-center gap-1 mb-3">
                    ${renderStars(r.rating)}
                    ${r.is_verified_purchase ? '<i data-lucide="check-circle" class="w-4 h-4 text-emerald-600 ml-2" title="Проверенная покупка"></i>' : ''}
                </div>
                <p class="text-gray-700 italic mb-4 line-clamp-4">"${r.text}"</p>
                <div class="flex items-center justify-between">
                    <div class="flex items-center gap-2">
                        <div class="w-8 h-8 bg-rose-100 rounded-full flex items-center justify-center text-rose-600 font-bold text-sm">
                            ${r.user_name?.[0] || 'U'}
                        </div>
                        <span class="font-medium text-gray-900 text-sm">${r.user_name}</span>
                    </div>
                    <span class="text-xs text-gray-400">${new Date(r.created_at).toLocaleDateString('ru-RU')}</span>
                </div>
                ${r.images && r.images.length > 0 ? `
                    <div class="flex gap-2 mt-4 overflow-x-auto pb-2">
                        ${r.images.slice(0, 3).map(img => `<img src="${img}" class="w-16 h-16 object-cover rounded-lg cursor-pointer hover:opacity-80 transition-opacity" onclick="window.open('${img}')">`).join('')}
                    </div>
                ` : ''}
            </div>
        `).join('');
        
        lucide.createIcons();
        
    } catch (error) {
        console.error("Error loading reviews:", error);
    }
}

function renderStars(rating) {
    let stars = '';
    for (let i = 1; i <= 5; i++) {
        stars += `<i data-lucide="star" class="w-4 h-4 ${i <= rating ? 'text-yellow-400 fill-yellow-400' : 'text-gray-300'}"></i>`;
    }
    return `<div class="flex">${stars}</div>`;
}

async function loadProducts(animate = false) {
    // Защита от повторных вызовов
    if (isLoadingProducts) return;

    const container = document.getElementById('products-grid');
    
    // Если контейнер ещё не готов, пробуем позже
    if (!container) {
        console.warn('⚠️ products-grid не найден, повторная попытка через 100мс...');
        setTimeout(() => loadProducts(animate), 100);
        return;
    }

    try {
        isLoadingProducts = true;
        const sort = document.getElementById('sort-filter')?.value || 'popular';
        const priceMax = document.getElementById('price-range')?.value || 2000000;

        const priceLabel = document.getElementById('price-label');
        if (priceLabel) priceLabel.innerText = formatPrice(priceMax);

        // Добавляем timestamp для обхода кэша
        let url = `/api/products?sort_by=${sort}&max_price=${priceMax}&_t=${Date.now()}`;
        if (selectedCategory) url += `&category_id=${selectedCategory}`;

        const res = await fetch(url, {
            headers: {
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache'
            }
        });
        const products = await res.json();
        allProductsList = products; // Keep for favorites side-filtering

        if (products.length === 0) {
            container.innerHTML = `
                <div class="col-span-full text-center py-20">
                    <i data-lucide="search-x" class="w-16 h-16 text-gray-300 mx-auto mb-4"></i>
                    <p class="text-gray-500 text-lg">Букеты не найдены. Попробуйте изменить фильтры.</p>
                </div>
            `;
            lucide.createIcons();
        } else {
            renderProducts(products, animate);
            // Обновляем кнопки избранного после рендера товаров
            setTimeout(() => updateFavoriteButtons(), 50);
        }

        // Обновляем счетчики и кнопки избранного
        updateFavoriteButtons();
    } catch (error) {
        console.error("Ошибка загрузки:", error);
    } finally {
        isLoadingProducts = false;
    }
}

// --- Favorites ---

/**
 * Показать toast уведомление
 * @param {string} message - Сообщение
 * @param {string} type - Тип: 'success', 'error', 'info'
 */
function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    
    const icons = {
        success: '<svg class="toast-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/></svg>',
        error: '<svg class="toast-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>',
        info: '<svg class="toast-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>'
    };

    toast.innerHTML = `
        ${icons[type] || icons.info}
        <span class="toast-message">${message}</span>
    `;

    container.appendChild(toast);

    // Удаляем через 3 секунды
    setTimeout(() => {
        toast.classList.add('removing');
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 300);
    }, 3000);
}

/**
 * Переключить статус избранного
 * @param {number} productId - ID товара
 */
function toggleFavorite(productId) {
    const index = favorites.indexOf(productId);
    const isAdding = index === -1;
    const product = allProductsList.find(p => p.id === productId);

    if (isAdding) {
        favorites.push(productId);
    } else {
        favorites.splice(index, 1);
    }
    localStorage.setItem('favorites', JSON.stringify(favorites));

    // Анимация кнопки
    animateFavoriteButton(productId, isAdding);

    // Обновляем счетчики и UI
    updateFavoriteCounts();
    updateFavoriteButtonVisual(productId, isAdding);

    // Показываем toast уведомление
    if (isAdding) {
        showToast(`«${product?.name || 'Товар'}» добавлен в избранное`, 'success');
    } else {
        showToast(`«${product?.name || 'Товар'}» удален из избранного`, 'info');
    }

    // Синхронизация с сервером если пользователь авторизован
    syncFavoriteWithServer(productId, isAdding);

    // Перерисовываем список избранного если он открыт
    const sidebar = document.getElementById('fav-sidebar');
    if (sidebar && !sidebar.classList.contains('hidden')) {
        renderFavorites();
    }
}

/**
 * Анимация кнопки избранного
 */
function animateFavoriteButton(productId, isAdding) {
    const buttons = document.querySelectorAll(`.fav-heart-btn[data-product-id="${productId}"]`);
    buttons.forEach(btn => {
        // Добавляем анимацию всегда (и при добавлении, и при удалении)
        btn.classList.remove('adding');
        // Форсируем перерисовку для перезапуска анимации
        void btn.offsetWidth;
        btn.classList.add('adding');
        setTimeout(() => {
            btn.classList.remove('adding');
        }, 400);
    });
}

/**
 * Обновить счетчики избранного
 */
function updateFavoriteCounts() {
    const countBadge = document.getElementById('fav-count');
    const mobileCountBadge = document.getElementById('mobile-fav-count');
    const sidebarCount = document.getElementById('fav-sidebar-count');

    const count = favorites.length;
    const displayCount = count > 0 ? count : '';

    if (countBadge) {
        countBadge.innerText = displayCount;
        countBadge.classList.toggle('hidden', count === 0);
    }

    if (mobileCountBadge) {
        mobileCountBadge.innerText = displayCount;
        mobileCountBadge.style.display = count === 0 ? 'none' : 'flex';
    }

    if (sidebarCount) {
        sidebarCount.innerText = count > 0 ? `(${count})` : '';
    }
}

/**
 * Синхронизация с сервером
 */
function syncFavoriteWithServer(productId, isAdding) {
    const token = localStorage.getItem('token');
    if (!token) return;

    if (isAdding) {
        fetch('/api/profile/favorites', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({ product_id: productId })
        })
        .then(response => {
            if (response.status === 401) {
                localStorage.removeItem('token');
                localStorage.removeItem('user');
            }
        })
        .catch(err => console.error('Ошибка добавления в избранное:', err));
    } else {
        fetch(`/api/profile/favorites/${productId}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        })
        .then(response => {
            if (response.status === 401) {
                localStorage.removeItem('token');
                localStorage.removeItem('user');
            }
        })
        .catch(err => console.error('Ошибка удаления из избранного:', err));
    }
}

/**
 * Обновить визуальное состояние кнопки избранного
 */
function updateFavoriteButtonVisual(productId, isFav) {
    const buttons = document.querySelectorAll(`.fav-heart-btn[data-product-id="${productId}"]`);

    buttons.forEach(btn => {
        const icon = btn.querySelector('i');
        if (!icon) return;
        if (icon.getAttribute('data-lucide') === 'trash-2') return;

        if (isFav) {
            // Добавляем в избранное - делаем красным с заливкой
            btn.classList.remove('text-gray-400');
            btn.classList.add('text-rose-500');
            icon.classList.remove('text-gray-400');
            icon.classList.add('fill-rose-500');
            icon.classList.remove('text-gray-400');
            icon.classList.add('text-rose-500');
            // Принудительно устанавливаем цвет через style с !important
            icon.setAttribute('style', 'color: rgb(225, 29, 72) !important; fill: rgb(225, 29, 72) !important;');
        } else {
            // Удаляем из избранного - делаем серым
            btn.classList.remove('text-rose-500');
            btn.classList.add('text-gray-400');
            icon.classList.remove('fill-rose-500', 'text-rose-500');
            icon.classList.add('text-gray-400');
            // Сбрасываем inline стили
            icon.removeAttribute('style');
        }
    });
}

/**
 * Обновить все кнопки избранного
 */
function updateFavoriteButtons() {
    updateFavoriteCounts();

    document.querySelectorAll('.fav-heart-btn').forEach(btn => {
        const productId = parseInt(btn.getAttribute('data-product-id'));
        if (!productId) return;

        const icon = btn.querySelector('i');
        if (!icon || icon.getAttribute('data-lucide') === 'trash-2') return;

        const isFav = favorites.includes(productId);

        if (isFav) {
            btn.classList.add('text-rose-500');
            btn.classList.remove('text-gray-400');
            icon.classList.add('fill-rose-500');
            icon.classList.remove('text-gray-400');
            icon.classList.add('text-rose-500');
            icon.setAttribute('style', 'color: rgb(225, 29, 72) !important; fill: rgb(225, 29, 72) !important;');
        } else {
            btn.classList.remove('text-rose-500');
            btn.classList.add('text-gray-400');
            icon.classList.remove('fill-rose-500', 'text-rose-500');
            icon.classList.add('text-gray-400');
            icon.removeAttribute('style');
        }
    });
}

/**
 * Открыть/закрыть sidebar избранного
 */
function toggleFavorites() {
    const sidebar = document.getElementById('fav-sidebar');
    const isOpening = sidebar.classList.contains('hidden');
    
    sidebar.classList.toggle('hidden');
    
    // Если открываем - рендерим содержимое
    if (isOpening) {
        setTimeout(() => {
            renderFavorites();
            if (window.lucide) {
                lucide.createIcons();
            }
        }, 10);
    }
}

/**
 * Отрендерить список избранного
 */
function renderFavorites() {
    const container = document.getElementById('fav-items');
    const footer = document.getElementById('fav-footer');
    if (!container) return;

    if (favorites.length === 0) {
        container.innerHTML = `
            <div class="favorites-empty-state">
                <div class="icon-wrapper">
                    <i data-lucide="heart" class="w-10 h-10"></i>
                </div>
                <h3 class="text-lg font-bold text-gray-900 mb-2">Нет избранных товаров</h3>
                <p class="text-gray-500 mb-6">Добавляйте товары в избранное, чтобы сохранить их на потом</p>
                <button onclick="toggleFavorites()"
                    class="px-6 py-3 bg-rose-600 text-white rounded-xl font-bold hover:bg-rose-700 transition-all shadow-lg shadow-rose-200">Смотреть каталог</button>
            </div>
        `;
        if (footer) footer.classList.add('hidden');
        return;
    }

    // Показываем футер
    if (footer) footer.classList.remove('hidden');

    // Если товары ещё не загружены, загружаем их
    if (!allProductsList || allProductsList.length === 0) {
        loadProducts().then(() => {
            renderFavoritesAfterLoad(container);
        });
        return;
    }

    renderFavoritesAfterLoad(container);
}

/**
 * Отрендерить список избранного после загрузки товаров
 */
function renderFavoritesAfterLoad(container) {
    const favProducts = allProductsList.filter(p => favorites.includes(p.id));

    if (favProducts.length === 0) {
        container.innerHTML = `
            <div class="favorites-empty-state">
                <div class="icon-wrapper">
                    <i data-lucide="heart" class="w-10 h-10"></i>
                </div>
                <h3 class="text-lg font-bold text-gray-900 mb-2">Товары больше недоступны</h3>
                <p class="text-gray-500 mb-6">Все товары из избранного были удалены из каталога</p>
                <button onclick="toggleFavorites()"
                    class="px-6 py-3 bg-rose-600 text-white rounded-xl font-bold hover:bg-rose-700 transition-all shadow-lg shadow-rose-200">Смотреть каталог</button>
            </div>
        `;
        const footer = document.getElementById('fav-footer');
        if (footer) footer.classList.add('hidden');
        return;
    }

    container.innerHTML = favProducts.map((product, index) => `
        <div class="fav-item flex gap-3 p-3 rounded-xl hover:bg-gray-50 transition-all border border-transparent hover:border-gray-100" style="animation-delay: ${index * 50}ms">
            <img src="${product.image_url || 'https://placehold.co/80'}" 
                alt="${product.name}" 
                class="w-20 h-20 object-cover rounded-lg flex-shrink-0 shadow-sm">
            <div class="flex-1 min-w-0 flex flex-col justify-between py-1">
                <div>
                    <h4 class="font-semibold text-sm text-gray-900 truncate">${product.name}</h4>
                    ${product.category ? `<p class="text-xs text-gray-500 mt-0.5">${product.category}</p>` : ''}
                </div>
                <div class="flex items-center justify-between">
                    <p class="text-rose-600 font-bold text-sm">${formatPrice(product.sale_price || product.price)} сум</p>
                </div>
            </div>
            <div class="flex flex-col gap-2 justify-center">
                <button onclick="quickAddToCart(${product.id});" 
                    class="p-2 bg-rose-50 text-rose-600 rounded-lg hover:bg-rose-100 active:scale-95 transition-all shadow-sm"
                    title="Добавить в корзину">
                    <i data-lucide="shopping-cart" class="w-4 h-4"></i>
                </button>
                <button type="button" 
                    onclick="removeFromFavorites(${product.id})" 
                    data-product-id="${product.id}" 
                    class="p-2 text-gray-400 hover:text-red-500 hover:bg-red-50 active:scale-95 transition-all rounded-lg" 
                    title="Удалить из избранного">
                    <i data-lucide="trash-2" class="w-4 h-4"></i>
                </button>
            </div>
        </div>
    `).join('');

    if (window.lucide) {
        lucide.createIcons();
    }
}

/**
 * Быстрое добавление в корзину из избранного
 */
function quickAddToCart(productId) {
    const product = allProductsList.find(p => p.id === productId);
    if (!product) return;

    addToCart(product);
    showToast(`«${product.name}» добавлен в корзину`, 'success');
}

/**
 * Удалить из избранного с анимацией
 */
function removeFromFavorites(productId) {
    const index = favorites.indexOf(productId);
    if (index === -1) return;

    const product = allProductsList.find(p => p.id === productId);
    
    // Находим элемент в DOM и добавляем класс анимации
    const buttons = document.querySelectorAll(`.fav-heart-btn[data-product-id="${productId}"]`);
    buttons.forEach(btn => {
        const item = btn.closest('.fav-item');
        if (item) {
            item.classList.add('removing');
            setTimeout(() => {
                // После анимации удаляем из массива
                const idx = favorites.indexOf(productId);
                if (idx > -1) {
                    favorites.splice(idx, 1);
                    localStorage.setItem('favorites', JSON.stringify(favorites));
                    
                    updateFavoriteCounts();
                    updateFavoriteButtonVisual(productId, false);
                    syncFavoriteWithServer(productId, false);
                    
                    // Перерисовываем
                    renderFavorites();
                }
            }, 300);
        }
    });

    // Если элемент не найден, просто удаляем
    if (buttons.length === 0) {
        favorites.splice(index, 1);
        localStorage.setItem('favorites', JSON.stringify(favorites));
        updateFavoriteCounts();
        updateFavoriteButtonVisual(productId, false);
        syncFavoriteWithServer(productId, false);
        renderFavorites();
    }

    showToast(`«${product?.name || 'Товар'}» удален из избранного`, 'info');
}

// --- Cart ---

function toggleCart() {
    const sidebar = document.getElementById('cart-sidebar');
    if (sidebar) sidebar.classList.toggle('hidden');
}


function updateQuantity(productId, delta) {
    const item = cart.find(i => i.id === productId);
    if (item) {
        item.quantity += delta;
        if (item.quantity <= 0) {
            removeFromCart(productId);
        } else {
            localStorage.setItem('cart', JSON.stringify(cart));
            renderCart();
            updateCartCount();
        }
    }
}

/**
 * Обновить счетчики корзины
 */
function updateCartCount() {
    const totalQuantity = cart.reduce((sum, item) => sum + item.quantity, 0);
    
    const countElem = document.getElementById('cart-count');
    if (countElem) {
        countElem.innerText = totalQuantity;
        countElem.classList.toggle('hidden', totalQuantity === 0);
    }

    const mobileCartCount = document.getElementById('mobile-cart-count');
    if (mobileCartCount) {
        mobileCartCount.innerText = totalQuantity;
        mobileCartCount.style.display = totalQuantity > 0 ? 'flex' : 'none';
    }
}

function renderCart() {
    const container = document.getElementById('cart-items');
    const totalElem = document.getElementById('cart-total');
    const countElem = document.getElementById('cart-count');

    if (!container || !totalElem || !countElem) return;

    const totalQuantity = cart.reduce((sum, item) => sum + item.quantity, 0);
    countElem.innerText = totalQuantity;
    countElem.classList.toggle('hidden', totalQuantity === 0);

    // Обновляем бейдж в нижнем мобильном меню
    const mobileCartCount = document.getElementById('mobile-cart-count');
    if (mobileCartCount) {
        mobileCartCount.innerText = totalQuantity;
        mobileCartCount.style.display = totalQuantity > 0 ? 'flex' : 'none';
    }

    if (cart.length === 0) {
        container.innerHTML = `
            <div class="h-full flex flex-col items-center justify-center text-gray-400 py-20">
                <i data-lucide="shopping-bag" class="w-16 h-16 mb-4 opacity-20"></i>
                <p>Ваша корзина пуста</p>
            </div>
        `;
        totalElem.innerText = '0 сум';
        lucide.createIcons();
        return;
    }

    container.innerHTML = cart.map((item, index) => `
        <div class="flex gap-4 p-4 bg-gray-50 rounded-2xl group relative">
            <div class="w-16 h-16 rounded-xl overflow-hidden flex-shrink-0">
                <img src="${item.image_url || 'https://placehold.co/100'}" class="w-full h-full object-cover">
            </div>
            <div class="flex-1 min-w-0">
                <h4 class="font-bold text-sm text-gray-900 truncate pr-6">${item.name}</h4>
                <p class="text-rose-600 font-bold text-sm mt-1">${formatPrice(item.sale_price || item.price)} сум</p>

                <div class="flex items-center gap-3 mt-3">
                    <button onclick="updateQuantity(${item.id}, -1)" class="w-6 h-6 rounded-lg bg-white border border-gray-200 flex items-center justify-center hover:border-rose-300 hover:text-rose-600 transition-all">-</button>
                    <span class="text-sm font-bold">${item.quantity}</span>
                    <button onclick="updateQuantity(${item.id}, 1)" class="w-6 h-6 rounded-lg bg-white border border-gray-200 flex items-center justify-center hover:border-rose-300 hover:text-rose-600 transition-all">+</button>
                </div>
            </div>
            <button onclick="removeFromCart(${item.id})" class="absolute top-4 right-4 text-gray-300 hover:text-red-500 transition-colors">
                <i data-lucide="trash-2" class="w-4 h-4"></i>
            </button>
        </div>
    `).join('');

    const total = cart.reduce((sum, item) => sum + (item.sale_price || item.price) * item.quantity, 0);
    totalElem.innerText = formatPrice(total) + ' сум';

    lucide.createIcons();

    // Обновляем мобильную корзину
    renderMobileCart();
}

function removeFromCart(productId) {
    cart = cart.filter(item => item.id !== productId);
    saveCart();
    renderCart();
    updateCartCount();
}

async function handleCheckout() {
    if (!currentUser) {
        alert("Пожалуйста, войдите в аккаунт для оформления заказа");
        openAuthModal();
        return;
    }

    const checkoutSection = document.getElementById('checkout-section');
    const checkoutBtn = document.getElementById('checkout-btn');

    if (checkoutSection.classList.contains('hidden')) {
        checkoutSection.classList.remove('hidden');
        checkoutBtn.innerText = 'Подтвердить заказ';
        return;
    }

    const phone = document.getElementById('order-phone').value;
    const name = document.getElementById('order-name').value;
    const total = parseFloat(document.getElementById('cart-total').innerText.replace(' сум', '').replace(/\s/g, ''));

    if (!phone || !name) {
        alert("Пожалуйста, заполните номер телефона и имя");
        return;
    }

    const token = localStorage.getItem('token');
    try {
        const res = await fetch('/api/orders', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
                total_amount: total,
                delivery_address: '',
                phone: phone,
                name: name,
                items: JSON.stringify(cart)  // ✅ Передаём товары в заказе
            })
        });

        if (res.ok) {
            alert("Заказ успешно создан! Мы свяжемся с вами в ближайшее время.");
            cart = [];
            localStorage.setItem('cart', JSON.stringify(cart));
            renderCart();
            toggleCart();
        } else {
            const err = await res.json();
            alert("Ошибка: " + (err.detail || "Не удалось оформить заказ"));
        }
    } catch (e) {
        alert("Ошибка сети при оформлении заказа");
    }
}

// Твоя логика форматирования карты (адаптированная)
document.addEventListener('input', (e) => {
    if (e.target.id === 'card-number') {
        let val = e.target.value.replace(/\D/g, '');
        let newval = '';
        for (let i = 0; i < val.length; i++) {
            if (i > 0 && i % 4 === 0) newval += ' ';
            newval += val[i];
        }
        e.target.value = newval;

        // Brand Detection Logic
        const brandElement = document.getElementById('card-brand');
        if (brandElement) {
            if (val.startsWith('8600')) {
                brandElement.innerHTML = '<span class="text-blue-400 font-bold">UZCARD</span>';
            } else if (val.startsWith('9860')) {
                brandElement.innerHTML = '<span class="text-orange-400 font-bold">HUMO</span>';
            } else if (val.startsWith('4')) {
                brandElement.innerHTML = '<span class="text-white font-bold">VISA</span>';
            } else if (/^5[1-5]/.test(val)) {
                brandElement.innerHTML = '<span class="text-red-400 font-bold">MASTERCARD</span>';
            } else {
                brandElement.innerHTML = '<i data-lucide="credit-card" class="w-6 h-6 inline mr-2"></i>CARD';
            }
            lucide.createIcons();
        }
    }

    if (e.target.id === 'card-exp') {
        let val = e.target.value.replace(/\D/g, '');
        if (val.length >= 2) {
            e.target.value = val.slice(0, 2) + '/' + val.slice(2, 4);
        } else {
            e.target.value = val;
        }
    }

    if (e.target.id === 'card-cvv') {
        let val = e.target.value.replace(/\D/g, '');
        e.target.value = val.slice(0, 3);
    }
});

// Вспомогательная функция для сохранения корзины
function saveCart() {
    localStorage.setItem('cart', JSON.stringify(cart));
}

// Функция отправки
async function applyPromoCode() {
    const code = document.getElementById('promo-code')?.value.trim().toUpperCase();
    const messageElem = document.getElementById('promo-message');
    if (!code) return;

    try {
        const res = await fetch(`/api/promo-codes/${code}`);
        if (!res.ok) throw new Error("Промокод не найден");

        const data = await res.json();
        appliedPromoCode = data.code;
        appliedDiscount = data.discount_percent;

        messageElem.innerText = `✓ Применен промокод ${data.code}: -${data.discount_percent}%`;
        messageElem.className = "text-sm mt-2 text-emerald-600 font-medium";
        messageElem.classList.remove('hidden');

        // Update totals
        updateCheckoutTotals();
    } catch (e) {
        appliedPromoCode = null;
        appliedDiscount = 0;
        messageElem.innerText = '✗ ' + e.message;
        messageElem.className = "text-sm mt-2 text-red-600 font-medium";
        messageElem.classList.remove('hidden');
    }
}

function selectPaymentMethod(method) {
    selectedPaymentMethod = method;
    
    // Update UI - remove active state from all buttons
    document.querySelectorAll('.payment-method-btn').forEach(btn => {
        btn.classList.remove('active');
        const checkIcon = btn.querySelector('.check-icon');
        if (checkIcon) checkIcon.classList.add('hidden');
    });

    // Add active state to selected button
    const activeBtn = document.getElementById(`pay-${method}`);
    if (activeBtn) {
        activeBtn.classList.add('active');
        const checkIcon = activeBtn.querySelector('.check-icon');
        if (checkIcon) checkIcon.classList.remove('hidden');
    }

    // Toggle card input wrapper with animation
    const cardWrapper = document.getElementById('card-input-wrapper');
    const cardNumberInput = document.getElementById('card-number');
    const cardExpInput = document.getElementById('card-exp');
    const cardCvvInput = document.getElementById('card-cvv');
    const cardBrand = document.getElementById('card-brand');
    
    if (cardWrapper) {
        if (method === 'cash') {
            cardWrapper.classList.add('hidden');
        } else {
            cardWrapper.classList.remove('hidden');
            
            // Update card brand
            if (cardBrand) {
                if (method === 'click') {
                    cardBrand.innerHTML = '<img src="/static/images/click-logo.svg" class="h-6 object-contain" alt="Click"> Click';
                } else if (method === 'payme') {
                    cardBrand.innerHTML = '<img src="https://cdn.payme.uz/logo/payme_color.svg" class="h-5 object-contain" alt="Payme"> Payme';
                }
            }
            
            // Focus on card number after animation
            setTimeout(() => {
                if (cardNumberInput) cardNumberInput.focus();
            }, 300);
        }
    }
}

async function processFinalPayment() {
    if (!currentUser) {
        alert("Пожалуйста, войдите в аккаунт");
        openAuthModal();
        return;
    }

    const phone = document.getElementById('order-phone')?.value.trim();
    const name = document.getElementById('order-name')?.value.trim();
    const postcard = document.getElementById('order-postcard')?.value.trim();
    const comment = document.getElementById('order-comment')?.value.trim();

    if (!phone || !name) {
        alert("Заполните все обязательные поля (телефон, имя)!");
        return;
    }

    const subtotal = cart.reduce((sum, item) => sum + (item.sale_price || item.price) * item.quantity, 0);
    const total = appliedDiscount ? subtotal * (1 - appliedDiscount / 100) : subtotal;

    const lat = document.getElementById('order-lat')?.value;
    const lng = document.getElementById('order-lng')?.value;

    const token = localStorage.getItem('token');
    try {
        // Сначала создаём заказ
        const orderRes = await fetch('/api/order', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
                name: name,
                phone: phone,
                delivery_address: '',
                comment: comment,
                delivery_date: '',
                delivery_time: '',
                postcard_text: postcard
            })
        });

        const orderData = await orderRes.json();
        if (!orderRes.ok || !orderData.success) {
            throw new Error(orderData.detail || 'Ошибка при создании заказа');
        }

        const orderId = orderData.order_id;

        // Добавляем товары в заказ
        for (const item of cart) {
            await fetch(`/api/order/${orderId}/add-item`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    product_id: item.id,
                    quantity: item.quantity,
                    comment: item.comment || null
                })
            });
        }

        if (selectedPaymentMethod === 'cash') {
            alert(`Заказ #${orderId} успешно оформлен! Мы свяжемся с вами в ближайшее время.`);
            cart = [];
            appliedPromoCode = null;
            appliedDiscount = 0;
            saveCart();
            hideCheckout();
            window.location.href = "/";
        } else {
            // Fetch payment link for Click/Payme
            try {
                const payRes = await fetch(`/api/payment/create-link/${orderId}?method=${selectedPaymentMethod}`);
                const payData = await payRes.json();
                if (payData.url) {
                    alert(`Заказ #${orderId} создан. Перенаправляем на оплату через ${selectedPaymentMethod}...`);
                    cart = [];
                    saveCart();
                    hideCheckout();
                    window.location.href = payData.url;
                } else {
                    throw new Error("Не удалось получить ссылку на оплату");
                }
            } catch (payErr) {
                alert(`Ошибка при создании ссылки на оплату, но заказ #${orderId} сохранен. Мы свяжемся с вами.`);
                window.location.href = "/";
            }
        }
    } catch (error) {
        console.error('Ошибка при оформлении заказа:', error);
        alert('Ошибка: ' + (error.message || 'Не удалось оформить заказ'));
    }
}

// --- Checkout Page Logic ---

function showCheckout() {
    openCheckout();
}

function openCheckout() {
    // Проверка авторизации
    if (!currentUser) {
        alert('Пожалуйста, войдите в аккаунт для оформления заказа');
        window.location.href = '/login';
        return;
    }

    // 1. Прячем корзину (если она открыта)
    const sidebar = document.getElementById('cart-sidebar');
    if (sidebar) sidebar.classList.add('hidden');

    // 2. Показываем с����раницу оформления
    const checkoutPage = document.getElementById('page-checkout');
    if (checkoutPage) checkoutPage.classList.remove('hidden');

    // Блокируем скролл основной страницы
    document.body.style.overflow = 'hidden';

    // Обновляем иконки Lucide внутри новой страницы
    lucide.createIcons();

    // 3. Отображаем товары в checkout
    renderCheckoutItems();
}

function renderCheckoutItems() {
    const container = document.getElementById('checkout-items');
    if (!container) return;

    if (cart.length === 0) {
        container.innerHTML = '<p class="text-gray-500 text-center py-4">Корзина пуста</p>';
        updateCheckoutTotals();
        return;
    }

    container.innerHTML = cart.map(item => `
        <div class="flex items-center gap-3 p-3 bg-gray-50 rounded-xl">
            <img src="${item.image_url || 'https://placehold.co/60'}"
                 class="w-14 h-14 object-cover rounded-lg flex-shrink-0">
            <div class="flex-1 min-w-0">
                <p class="font-medium text-gray-900 truncate text-sm">${item.name}</p>
                <p class="text-xs text-gray-500">
                    ${item.quantity} шт
                </p>
            </div>
            <p class="font-bold text-rose-600 text-sm whitespace-nowrap">
                ${formatPrice(item.price * item.quantity)}
            </p>
        </div>
    `).join('');

    updateCheckoutTotals();
}

function updateCheckoutTotals() {
    const subtotal = cart.reduce((sum, item) => sum + (item.price * item.quantity), 0);
    const discount = appliedDiscount || 0;
    const total = subtotal - discount;

    const subtotalEl = document.getElementById('checkout-subtotal');
    const discountEl = document.getElementById('checkout-discount');
    const totalEl = document.getElementById('checkout-total');

    if (subtotalEl) subtotalEl.textContent = formatPrice(subtotal) + ' сум';
    if (discountEl) {
        discountEl.textContent = '-' + formatPrice(discount) + ' сум';
        discountEl.parentElement.classList.toggle('hidden', discount === 0);
    }
    if (totalEl) totalEl.textContent = formatPrice(total) + ' сум';
}

function hideCheckout() {
    const checkoutPage = document.getElementById('page-checkout');
    if (checkoutPage) checkoutPage.classList.add('hidden');
    document.body.style.overflow = 'auto';
}

// --- Navigation ---

function setupNavigation() {
    const path = window.location.pathname;
    showPage(path);
}

function navigate(e, path) {
    e.preventDefault();
    
    // Redirect to new profile page
    if (path === '/profile') {
        window.location.href = '/profile';
        return;
    }
    
    window.history.pushState({}, '', path);
    showPage(path);
}

function showPage(path) {
    const pageHome = document.getElementById('page-home');
    const pageProfile = document.getElementById('page-profile');

    if (!pageHome || !pageProfile) return;

    pageHome.classList.add('hidden');
    pageProfile.classList.add('hidden');

    if (path === '/profile') {
        if (!currentUser) {
            openAuthModal();
            pageHome.classList.remove('hidden');
            return;
        }
        pageProfile.classList.remove('hidden');
        loadProfileData();
    } else {
        pageHome.classList.remove('hidden');
    }
    
    // Пересоздаем обработчики якорных ссылок
    setupAnchorHandlers();
}

function setupAnchorHandlers() {
    // Обработка якорных ссылок (например, #footer)
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        // Удаляем старые обработчики (клонированием)
        const newAnchor = anchor.cloneNode(true);
        anchor.parentNode.replaceChild(newAnchor, anchor);
        
        newAnchor.addEventListener('click', function(e) {
            const targetId = this.getAttribute('href').substring(1);
            const targetElement = document.getElementById(targetId);
            
            if (targetElement) {
                e.preventDefault();
                
                // Плавная прокрутка к секции
                targetElement.scrollIntoView({ 
                    behavior: 'smooth', 
                    block: 'start' 
                });
                
                // Ищем заголовок, который соответствует тексту ссылки
                const linkText = this.textContent.trim();
                const title = Array.from(targetElement.querySelectorAll('h1, h2, h3'))
                    .find(h => h.textContent.trim() === linkText);
                
                if (title) {
                    // Удаляем класс анимации и добавляем снова
                    title.classList.remove('animate-bounce-title');
                    // force reflow для перезапуска анимации
                    void title.offsetWidth;
                    title.classList.add('animate-bounce-title');
                }
            }
        });
    });
}

async function loadProfileData() {
    if (!currentUser) return;
    document.getElementById('profile-name').innerText = currentUser.full_name;
    document.getElementById('profile-email').innerText = currentUser.email;

    // Bonus points display
    const bonusElem = document.getElementById('profile-bonus');
    if (bonusElem) bonusElem.innerText = `Бонусные баллы: ${currentUser.bonus_points || 0}`;

    const adminLink = document.getElementById('admin-link-container');
    if (currentUser.is_admin) {
        adminLink.innerHTML = `<a href="/admin" class="px-4 py-2 bg-white text-rose-600 rounded-lg font-bold hover:bg-gray-100 transition-colors">В админку</a>`;
    } else {
        adminLink.innerHTML = '';
    }

    loadOrders();
}

async function loadOrders() {
    if (!currentUser) return;
    const container = document.getElementById('orders-list');

    try {
        const token = localStorage.getItem('token');
        const res = await fetch('/api/profile/orders', {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (!res.ok) {
            const container = document.getElementById('orders-list');
            container.innerHTML = '<p class="text-gray-500 text-center py-10">Для просмотра заказов войдите в аккаунт</p>';
            return;
        }
        
        const data = await res.json();

        if (!data || data.length === 0) {
            container.innerHTML = '<p class="text-gray-500 text-center py-10">У вас пока нет заказов</p>';
            return;
        }

        container.innerHTML = data.map(order => `
            <div class="border border-gray-100 rounded-2xl p-6 bg-gray-50/50">
                <div class="flex flex-wrap justify-between items-start gap-4 mb-4">
                    <div>
                        <div class="text-xs font-bold text-gray-400 uppercase tracking-wider mb-1">Заказ #${order.id}</div>
                        <div class="text-sm font-medium text-gray-500">${new Date(order.created_at).toLocaleDateString()}</div>
                    </div>
                    <span class="px-3 py-1 bg-rose-50 text-rose-600 rounded-full text-xs font-bold">${order.status}</span>
                </div>
                <div class="flex justify-between items-end">
                    <div class="text-xl font-bold text-gray-900">${formatPrice(order.total_amount)} сум</div>
                    <button onclick='repeatOrder(${JSON.stringify(order).replace(/'/g, "&apos;")})' class="px-4 py-2 bg-white border border-gray-200 rounded-xl text-sm font-bold hover:border-rose-300 hover:text-rose-600 transition-all">Повторить</button>
                </div>
            </div>
        `).join('');
    } catch (e) {
        container.innerHTML = 'Ошибка при загрузке заказов';
    }
}

function repeatOrder(order) {
    try {
        const items = JSON.parse(order.items);
        if (Array.isArray(items)) {
            cart = items;
            saveCart();
            toggleCart();
        }
    } catch (e) {
        alert("Не удалось повторить заказ");
    }
}

// --- Support Chat Logic ---
let supportPolling = null;

function toggleChat() {
    const chat = document.getElementById('chat-window');
    chat.classList.toggle('hidden');
    if (!chat.classList.contains('hidden')) {
        document.getElementById('chat-input').focus();
        loadSupportMessages();
        if (!supportPolling) {
            supportPolling = setInterval(loadSupportMessages, 3000);
        }
    } else {
        if (supportPolling) {
            clearInterval(supportPolling);
            supportPolling = null;
        }
    }
}

async function loadSupportMessages() {
    if (!currentUser || !currentUser.id) return;
    const token = localStorage.getItem('token');
    try {
        const res = await fetch(`/api/support/messages?user_id=${currentUser.id}`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        if (!res.ok) return;
        const messages = await res.json();
        if (Array.isArray(messages)) {
            renderSupportMessages(messages);
        }
    } catch (e) {
        console.error("Error loading messages:", e);
    }
}

function renderSupportMessages(messages) {
    if (!Array.isArray(messages)) return;
    const container = document.getElementById('chat-messages');
    const isAtBottom = container.scrollHeight - container.scrollTop <= container.clientHeight + 100;

    container.innerHTML = messages.map(m => `
        <div class="${m.is_admin ? 'bg-rose-100 rounded-tl-none self-start text-rose-900 border border-rose-100' : 'bg-gray-200 rounded-tr-none self-end text-gray-800 ml-auto'} p-3 rounded-2xl max-w-[80%] shadow-sm mb-2">
            ${m.message}
            <div class="text-[8px] opacity-50 mt-1 ${m.is_admin ? 'text-left' : 'text-right'}">
                ${new Date(m.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
            </div>
        </div>
    `).join('') || `
        <div class="bg-rose-100 p-3 rounded-2xl rounded-tl-none self-start max-w-[80%] text-rose-900 shadow-sm">
            Здравствуйте! Напишите нам, и мы ответим вам в ближайшее время.
        </div>
    `;

    if (isAtBottom) {
        container.scrollTop = container.scrollHeight;
    }
}

async function sendChatMessage() {
    if (!currentUser) {
        alert("Пожалуйста, войдите, чтобы написать в поддержку");
        openAuthModal();
        return;
    }
    const input = document.getElementById('chat-input');
    const message = input.value.trim();

    if (!message) return;

    const token = localStorage.getItem('token');

    try {
        const res = await fetch('/api/support/send', {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({ user_id: currentUser.id, message })
        });
        
        if (!res.ok) throw new Error('Failed to send message');
        
        input.value = '';
        loadSupportMessages();
    } catch (e) {
        alert("Ошибка при отправке сообщения");
    }
}

window.onpopstate = () => showPage(window.location.pathname);
window.onload = () => {
    lucide.createIcons();
    setupNavigation();
    setupAnchorHandlers();
    checkBackButton();
};

function checkBackButton() {
    const backBtn = document.getElementById('back-to-admin');
    if (!backBtn) return;
    
    // Проверяем, не нажали ли уже кнопку "Назад"
    const cameBackFromAdmin = sessionStorage.getItem('cameBackFromAdmin');
    if (cameBackFromAdmin === 'true') {
        sessionStorage.removeItem('cameBackFromAdmin');
        return;
    }
    
    // Показываем кнопку только если пользователь пришёл из админки
    const referrer = document.referrer;
    if (referrer.includes('/admin')) {
        backBtn.classList.remove('hidden');
        backBtn.classList.add('flex');
        lucide.createIcons();
    }
}

function goBackToAdmin() {
    // Закрываем текущую вкладку (которая была открыта из админки)
    window.close();
}

// Заказ через Telegram - прямое перенаправление в Telegram
function openTelegramOrderModal() {
    if (cart.length === 0) {
        alert('Корзина пуста');
        return;
    }

    // Формируем сообщение для Telegram
    let message = '🌸 Новый заказ\n\n';
    message += '📦 Товары:\n';

    cart.forEach((item, index) => {
        message += `${index + 1}. ${item.name} — ${item.quantity} шт. × ${formatPrice(item.price)} сум\n`;
    });

    const total = cart.reduce((sum, item) => sum + (item.price * item.quantity), 0);
    message += `\n💰 Итого: ${formatPrice(total)} сум`;

    // Копируем сообщение в буфер обмена
    navigator.clipboard.writeText(message).then(() => {
        alert('✅ Детали заказа скопированы в буфер обмена.\n\nСейчас откроется Telegram — просто вставьте сообщение в чат.');

        // Очищаем корзину
        cart = [];
        saveCart();
        toggleCart();

        // Открываем Telegram
        const isMobile = /iPhone|iPad|iPod|Android/i.test(navigator.userAgent);
        if (isMobile) {
            window.location.href = 'https://t.me/uzflower';
        } else {
            window.open('https://t.me/uzflower', '_blank');
        }
    }).catch(() => {
        alert('✅ Сейчас откроется Telegram.');

        cart = [];
        saveCart();
        toggleCart();

        const isMobile = /iPhone|iPad|iPod|Android/i.test(navigator.userAgent);
        if (isMobile) {
            window.location.href = 'https://t.me/uzflower';
        } else {
            window.open('https://t.me/uzflower', '_blank');
        }
    });
}

function closeTelegramOrderModal() {
    // Функция больше не используется
}

async function submitTelegramOrder() {
    // Функция больше не используется - заказ оформляется напрямую через Telegram
}

// Старая функция orderViaTelegram (для совместимости)
async function orderViaTelegram() {
    openTelegramOrderModal();
}

// Открыть модальное окно Telegram заказа из карточки товара
function openTelegramOrderModalFromProduct() {
    if (!activeProduct) {
        alert('Товар не выбран');
        return;
    }

    // Генерируем ссылку на Telegram бота с deep-link
    // Формат: https://t.me/your_bot?start=product_ID
    const productId = activeProduct.id;
    const telegramLink = `https://t.me/${TELEGRAM_BOT_USERNAME}?start=product_${productId}`;

    // Открываем Telegram
    window.open(telegramLink, '_blank');

    // Закрываем модальное окно товара
    closeProductDetail();
}
