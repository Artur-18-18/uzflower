let currentUser = null;
let currentProfile = null;
let cart = JSON.parse(localStorage.getItem('cart') || '[]');
let favorites = JSON.parse(localStorage.getItem('favorites') || '[]');
let selectedCategory = null;
let appliedDiscount = 0;
let appliedPromoCode = null;
let allProductsList = [];
let selectedPaymentMethod = 'cash';

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
    loadPopularProducts();
    loadProducts();
    loadReviews();  // Загружаем отзывы
    setupNavigation();
    setupHeaderScroll();
    // Инициализируем счётчик избранного
    const localFavorites = JSON.parse(localStorage.getItem('favorites') || '[]');
    updateMobileFavCount(localFavorites.length);
    // Избранное будет обновлено после загрузки товаров в loadProducts()
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
    if (savedUser) {
        currentUser = JSON.parse(savedUser);
        currentProfile = currentUser; // В нашей схеме они объединены
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
    if (!container) return;

    container.innerHTML = products.map((product, index) => {
        const isFav = favorites.includes(product.id);
        const animationStyle = animate ? `opacity: 0; animation: fadeInUp 0.5s ease forwards; animation-delay: ${index * 50}ms;` : '';
        const productJson = JSON.stringify(product).replace(/"/g, '&quot;');
        return `
            <div class="bg-gray-100 rounded-xl shadow-md overflow-hidden hover:shadow-xl transition-all duration-300 group cursor-pointer" style="${animationStyle}" onclick="openProductDetail(${productJson})">
                <div class="relative aspect-square overflow-hidden bg-gray-200">
                    <img src="${product.image_url || 'https://placehold.co/400'}" alt="${product.name}" class="w-full h-full object-cover">
                    ${product.stock === 0 ? '<div class="absolute inset-0 bg-black/50 flex items-center justify-center text-white font-bold">Нет в наличии</div>' : ''}
                    <button type="button" onclick="event.stopPropagation(); toggleFavorite(${product.id})" class="fav-heart-btn absolute top-3 right-3 flex items-center justify-center min-w-[44px] min-h-[44px] p-2 bg-white/90 backdrop-blur-sm rounded-full shadow-md hover:bg-white active:scale-95 transition-all z-10" aria-label="${isFav ? 'Убрать из избранного' : 'В избранное'}">
                        <i data-lucide="heart" class="w-5 h-5 ${isFav ? 'fill-rose-500 text-rose-500' : 'text-gray-400'}"></i>
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
    lucide.createIcons();
}

let activeProduct = null;
let selectedSize = 'M';

function openProductDetail(product) {
    activeProduct = product;
    selectedSize = 'M';
    const modal = document.getElementById('product-detail-modal');
    if (!modal) return;

    document.getElementById('detail-image').src = product.image_url || 'https://placehold.co/600';
    document.getElementById('detail-name').innerText = product.name;
    document.getElementById('detail-desc').innerText = product.description || 'Описание отсутствует';
    document.getElementById('detail-composition').innerText = product.composition || 'Состав уточняйте у флориста';

    updateDetailPrice();
    modal.classList.remove('hidden');
    document.body.style.overflow = 'hidden';
}

function updateDetailPrice() {
    if (!activeProduct) return;
    // Use sale_price as base if it exists, otherwise use standard price
    let basePrice = activeProduct.sale_price || activeProduct.price;
    let price = basePrice;

    if (selectedSize === 'S' && activeProduct.price_s) price = activeProduct.price_s;
    if (selectedSize === 'L' && activeProduct.price_l) price = activeProduct.price_l;
    if (selectedSize === 'M' && activeProduct.price_m) price = activeProduct.price_m;

    document.getElementById('detail-price').innerText = formatPrice(price) + ' сум';

    // Update active state of buttons
    document.querySelectorAll('.size-btn').forEach(btn => {
        const isSelected = btn.dataset.size === selectedSize;
        btn.classList.toggle('border-rose-600', isSelected);
        btn.classList.toggle('bg-rose-50', isSelected);
        btn.classList.toggle('text-rose-600', isSelected);
    });
}

function selectSize(size) {
    selectedSize = size;
    updateDetailPrice();
}

function addToCart(product) {
    // Проверка авторизации (опционально, можно требовать вход только при оформлении)
    // if (!currentUser) {
    //     alert('Пожалуйста, войдите в аккаунт для добавления в корзину');
    //     window.location.href = '/login';
    //     return;
    // }
    
    // Clone product to avoid reference issues
    const cartItem = { ...product };

    // If it's the active product from modal, apply size selection
    if (activeProduct && activeProduct.id === product.id) {
        cartItem.size = selectedSize;
        let basePrice = product.sale_price || product.price;
        let finalPrice = basePrice;

        if (selectedSize === 'S' && product.price_s) finalPrice = product.price_s;
        if (selectedSize === 'L' && product.price_l) finalPrice = product.price_l;
        if (selectedSize === 'M' && product.price_m) finalPrice = product.price_m;

        cartItem.price = finalPrice;
        // Clear sale_price for cart items with specific sizes to avoid confusion
        delete cartItem.sale_price;
    }

    const existing = cart.find(item => item.id === cartItem.id && item.size === cartItem.size);
    if (existing) {
        existing.quantity += 1;
    } else {
        cart.push({ ...cartItem, quantity: 1 });
    }
    saveCart();
    toggleCart();
    if (document.getElementById('product-detail-modal')) closeProductDetail();
}

function closeProductDetail() {
    document.getElementById('product-detail-modal').classList.add('hidden');
    document.body.style.overflow = '';
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

function handleSearch() {
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
}

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
function openMobileSearch() {
    document.getElementById('mobile-search-modal').classList.add('active');
    setTimeout(() => {
        document.getElementById('mobile-search-input').focus();
    }, 100);
    document.body.style.overflow = 'hidden';
    lucide.createIcons();
    
    // Если товары ещё не загружены, показываем сообщение
    if (allProductsList.length === 0) {
        document.getElementById('mobile-search-results').innerHTML = 
            '<p class="text-center text-gray-500 py-8">Загрузка товаров...</p>';
    }
}

function closeMobileSearch() {
    document.getElementById('mobile-search-modal').classList.remove('active');
    document.getElementById('mobile-search-input').value = '';
    document.getElementById('mobile-search-results').innerHTML = '';
    document.body.style.overflow = '';
}

function handleMobileSearch() {
    const query = document.getElementById('mobile-search-input').value.toLowerCase().trim();
    const resultsContainer = document.getElementById('mobile-search-results');

    // Если товары ещё не загружены
    if (allProductsList.length === 0) {
        resultsContainer.innerHTML = '<p class="text-center text-gray-500 py-8">Товары загружаются...</p>';
        return;
    }

    if (!query) {
        resultsContainer.innerHTML = '';
        return;
    }

    // Фильтруем товары
    const filtered = allProductsList.filter(p =>
        p.name.toLowerCase().includes(query) ||
        (p.description && p.description.toLowerCase().includes(query))
    );

    if (filtered.length === 0) {
        resultsContainer.innerHTML = '<p class="text-center text-gray-500 py-8">Ничего не найдено</p>';
    } else {
        resultsContainer.innerHTML = filtered.map(product => `
            <div class="search-result-item" onclick="openProductDetail(${JSON.stringify(product).replace(/"/g, '&quot;')}); closeMobileSearch();">
                <img src="${product.image_url || 'https://placehold.co/60'}" alt="${product.name}">
                <div class="flex-1">
                    <p class="font-semibold">${product.name}</p>
                    <p class="text-rose-600 font-bold">${formatPrice(product.price)} сум</p>
                </div>
            </div>
        `).join('');
    }

    lucide.createIcons();
}

// Mobile favorites functions
function toggleMobileFavorites() {
    const sidebar = document.getElementById('mobile-favorites-sidebar');
    const overlay = document.getElementById('favorites-overlay');
    
    // Создаём overlay если нет
    if (!overlay) {
        const newOverlay = document.createElement('div');
        newOverlay.id = 'favorites-overlay';
        newOverlay.className = 'favorites-overlay';
        newOverlay.onclick = closeMobileFavorites;
        document.body.appendChild(newOverlay);
    }
    
    sidebar.classList.toggle('active');
    document.getElementById('favorites-overlay').classList.toggle('active');
    document.body.style.overflow = 'hidden';
    
    // Загружаем избранное
    loadMobileFavorites();
}

function closeMobileFavorites() {
    document.getElementById('mobile-favorites-sidebar').classList.remove('active');
    document.getElementById('favorites-overlay').classList.remove('active');
    document.body.style.overflow = '';
}

function loadMobileFavorites() {
    const container = document.getElementById('mobile-favorites-list');
    const localFavorites = JSON.parse(localStorage.getItem('favorites') || '[]');
    
    // Обновляем счётчик
    updateMobileFavCount(localFavorites.length);
    
    if (localFavorites.length === 0) {
        container.innerHTML = '<p class="text-center text-gray-500 py-8">Избранное пусто</p>';
        return;
    }
    
    // Фильтруем товары которые в избранном
    const favProducts = allProductsList.filter(p => localFavorites.includes(p.id));
    
    if (favProducts.length === 0) {
        container.innerHTML = '<p class="text-center text-gray-500 py-8">Товары больше недоступны</p>';
        return;
    }
    
    container.innerHTML = favProducts.map(product => `
        <div class="favorites-item">
            <img src="${product.image_url || 'https://placehold.co/80'}" alt="${product.name}">
            <div class="flex-1">
                <p class="font-semibold">${product.name}</p>
                <p class="text-rose-600 font-bold">${formatPrice(product.price)} сум</p>
                <button onclick="addToCart(${JSON.stringify(product).replace(/"/g, '&quot;')}); closeMobileFavorites();" 
                    class="mt-2 px-4 py-2 bg-rose-600 text-white text-sm rounded-lg">
                    В корзину
                </button>
            </div>
        </div>
    `).join('');
    
    lucide.createIcons();
}

function updateMobileFavCount(count) {
    const badge = document.getElementById('mobile-fav-count');
    if (badge) {
        badge.textContent = count;
        badge.style.display = count > 0 ? 'block' : 'none';
    }
}

// Обновляем счётчик при изменении избранного
const originalToggleFavorite = toggleFavorite;
toggleFavorite = function(productId) {
    originalToggleFavorite(productId);
    
    // Обновляем счётчик через небольшую задержку
    setTimeout(() => {
        const localFavorites = JSON.parse(localStorage.getItem('favorites') || '[]');
        updateMobileFavCount(localFavorites.length);
    }, 100);
};

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

        const renderBanner = (banner) => {
            const bannerText = banner.text || 'Весенняя Коллекция';
            const bannerSubtext = banner.subtext || 'Создайте незабываемые моменты с нашими авторскими букетами';
            
            if (banner.media_type === 'video' && banner.video_url) {
                bannerContainer.innerHTML = `
                    <video id="hero-video" class="absolute inset-0 w-full h-full object-cover opacity-60" autoplay muted playsinline>
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

                // Переключение после окончания видео
                const video = document.getElementById('hero-video');
                video.onended = () => {
                    currentBannerIndex = (currentBannerIndex + 1) % banners.length;
                    renderBanner(banners[currentBannerIndex]);
                };

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
                setTimeout(() => {
                    currentBannerIndex = (currentBannerIndex + 1) % banners.length;
                    renderBanner(banners[currentBannerIndex]);
                }, 5000);
            }

            // Клик по баннеру с ссылкой
            if (banner.link) {
                bannerContainer.style.cursor = 'pointer';
                bannerContainer.onclick = () => window.location.href = banner.link;
            }
        };

        renderBanner(banners[currentBannerIndex]);

    } catch (e) {
        console.error("Error loading banners:", e);
    }
}

function renderSingleBanner(container, banner) {
    const bannerText = banner.text || 'Весенняя Коллекция';
    const bannerSubtext = banner.subtext || 'Создайте незабываемые моменты с нашими авторскими букетами';
    
    if (banner.media_type === 'video' && banner.video_url) {
        container.innerHTML = `
            <video class="absolute inset-0 w-full h-full object-cover opacity-60" autoplay muted loop playsinline>
                <source src="${banner.video_url}" type="video/mp4">
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

async function loadPopularProducts() {
    try {
        const res = await fetch('/api/products?sort_by=popular');
        const products = await res.json();
        const container = document.getElementById('popular-products');
        if (container) {
            container.innerHTML = products.slice(0, 6).map(product => `
                <div class="w-72 flex-shrink-0 bg-gray-100 rounded-2xl shadow-sm border border-gray-200 overflow-hidden group">
                    <div class="relative h-64 overflow-hidden bg-gray-200">
                        <img src="${product.image_url || 'https://placehold.co/400'}" alt="${product.name}" class="w-full h-full object-cover group-hover:scale-110 transition-transform duration-500">
                        <button type="button" onclick="event.stopPropagation(); toggleFavorite(${product.id})" class="fav-heart-btn absolute top-3 right-3 flex items-center justify-center min-w-[44px] min-h-[44px] p-2 bg-white/90 backdrop-blur-sm rounded-full shadow-md hover:bg-white active:scale-95 transition-all z-10" aria-label="Избранное">
                            <i data-lucide="heart" class="w-5 h-5 ${favorites.includes(product.id) ? 'fill-rose-500 text-rose-500' : 'text-gray-400'}"></i>
                        </button>
                    </div>
                    <div class="p-4">
                        <h3 class="font-bold text-gray-900 mb-1 truncate">${product.name}</h3>
                        <p class="text-rose-600 font-bold">${formatPrice(product.price)} сум</p>
                    </div>
                </div>
            `).join('');
            lucide.createIcons();
        }
    } catch (e) { console.error("Error loading popular products:", e); }
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
    try {
        const sort = document.getElementById('sort-filter')?.value || 'popular';
        const priceMax = document.getElementById('price-range')?.value || 2000000;

        const priceLabel = document.getElementById('price-label');
        if (priceLabel) priceLabel.innerText = formatPrice(priceMax);

        let url = `/api/products?sort_by=${sort}&max_price=${priceMax}`;
        if (selectedCategory) url += `&category_id=${selectedCategory}`;

        const res = await fetch(url);
        const products = await res.json();
        allProductsList = products; // Keep for favorites side-filtering

        const container = document.getElementById('products-grid');
        if (!container) return;

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
        }
        
        // Обновляем избранное после загрузки товаров
        renderFavorites();
    } catch (error) {
        console.error("Ошибка загрузки:", error);
    }
}

// --- Favorites ---

function toggleFavorite(productId) {
    const index = favorites.indexOf(productId);
    const isAdding = index === -1;
    
    if (isAdding) {
        favorites.push(productId);
    } else {
        favorites.splice(index, 1);
    }
    localStorage.setItem('favorites', JSON.stringify(favorites));

    // Синхронизация с сервером если пользователь авторизован
    const token = localStorage.getItem('token');
    if (token && currentUser) {
        if (isAdding) {
            // Добавляем в избранное на сервере
            fetch('/api/profile/favorites', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({ product_id: productId })
            }).catch(err => console.error('Error adding to favorites:', err));
        } else {
            // Удаляем из избранного на сервере
            fetch(`/api/profile/favorites/${productId}`, {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            }).catch(err => console.error('Error removing from favorites:', err));
        }
    }

    // Перерисовываем товары и избранное
    const container = document.getElementById('products-grid');
    if (container && container.innerHTML !== '') {
        renderProducts(allProductsList, false);
    }
    renderFavorites();
}

function toggleFavorites() {
    const sidebar = document.getElementById('fav-sidebar');
    sidebar.classList.toggle('hidden');
}

function renderFavorites() {
    const container = document.getElementById('fav-items');
    const countBadge = document.getElementById('fav-count');

    if (!countBadge || !container) return;

    countBadge.innerText = favorites.length;
    countBadge.classList.toggle('hidden', favorites.length === 0);

    if (favorites.length === 0) {
        container.innerHTML = '<p class="text-center text-gray-500 mt-10">Список избранного пуст</p>';
        return;
    }

    // Если товары ещё не загружены, загружаем их
    if (!allProductsList || allProductsList.length === 0) {
        loadProducts().then(() => {
            renderFavoritesAfterLoad(container);
        });
        return;
    }

    renderFavoritesAfterLoad(container);
}

function renderFavoritesAfterLoad(container) {
    const favProducts = allProductsList.filter(p => favorites.includes(p.id));
    
    if (favProducts.length === 0) {
        container.innerHTML = '<p class="text-center text-gray-500 mt-10">Товары в избранном больше недоступны</p>';
        return;
    }
    
    container.innerHTML = favProducts.map(product => `
        <div class="flex gap-3 border-b pb-4 items-center">
            <img src="${product.image_url || 'https://placehold.co/80'}" class="w-20 h-20 object-cover rounded-lg">
            <div class="flex-1">
                <h4 class="font-semibold text-sm">${product.name}</h4>
                <p class="text-rose-600 font-bold">${formatPrice(product.sale_price || product.price)} сум</p>
            </div>
            <div class="flex flex-col gap-2">
                <button onclick="addToCart(${JSON.stringify(product).replace(/"/g, '&quot;')})" class="p-2 bg-rose-50 text-rose-600 rounded hover:bg-rose-100 transition-all">
                    <i data-lucide="shopping-cart" class="w-4 h-4"></i>
                </button>
                <button type="button" onclick="toggleFavorite(${product.id})" class="fav-heart-btn min-w-[44px] min-h-[44px] flex items-center justify-center p-2 text-gray-400 hover:text-rose-500 active:scale-95 transition-all rounded-lg" aria-label="Удалить из избранного">
                    <i data-lucide="trash-2" class="w-5 h-5"></i>
                </button>
            </div>
        </div>
    `).join('');

    lucide.createIcons();
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
        }
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
                <h4 class="font-bold text-sm text-gray-900 truncate pr-6">${item.name} ${item.size ? `(${item.size})` : ''}</h4>
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
}

function updateQuantity(productId, delta) {
    const item = cart.find(i => i.id === productId);
    if (item) {
        item.quantity += delta;
        if (item.quantity <= 0) {
            cart = cart.filter(i => i.id !== productId);
        }
        saveCart();
    }
}

function removeFromCart(productId) {
    cart = cart.filter(item => item.id !== productId);
    saveCart();
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

    const address = document.getElementById('order-address').value;
    const phone = document.getElementById('order-phone').value;
    const total = parseFloat(document.getElementById('cart-total').innerText.replace(' сум', '').replace(/\s/g, ''));

    if (!address || !phone) {
        alert("Пожалуйста, заполните адрес и номер телефона");
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
                delivery_address: address,
                phone: phone
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
    renderCart();
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

    const address = document.getElementById('order-address')?.value.trim();
    const phone = document.getElementById('order-phone')?.value.trim();
    const date = document.getElementById('order-date')?.value;
    const time = document.getElementById('order-time')?.value;
    const postcard = document.getElementById('order-postcard')?.value.trim();
    const cardNumber = document.getElementById('card-number')?.value.trim();

    if (!address || !phone || !date || !time || (selectedPaymentMethod !== 'cash' && cardNumber.length < 19)) {
        alert("Заполните все обязательные поля (адрес, телефон, дата, время и номер карты)!");
        return;
    }

    const subtotal = cart.reduce((sum, item) => sum + (item.sale_price || item.price) * item.quantity, 0);
    const total = appliedDiscount ? subtotal * (1 - appliedDiscount / 100) : subtotal;

    const lat = document.getElementById('order-lat')?.value;
    const lng = document.getElementById('order-lng')?.value;

    const orderData = {
        delivery_address: address,
        phone: phone,
        delivery_date: date,
        delivery_time: time,
        postcard_text: postcard,
        comment: document.getElementById('order-comment')?.value || "",
        promo_code_used: appliedPromoCode,
        items: JSON.stringify(cart),
        total_amount: total,
        lat: lat ? parseFloat(lat) : null,
        lng: lng ? parseFloat(lng) : null
    };

    const token = localStorage.getItem('token');
    try {
        const response = await fetch('/api/orders', {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify(orderData)
        });

        if (response.ok) {
            const data = await response.json();
            const orderId = data.id;

            if (selectedPaymentMethod === 'cash') {
                alert("Заказ успешно оформлен! Мы свяжемся с вами в ближайшее время.");
                cart = [];
                appliedPromoCode = null;
                appliedDiscount = 0;
                saveCart();
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
                        window.location.href = payData.url;
                    } else {
                        throw new Error("Не удалось получить ссылку на оплату");
                    }
                } catch (payErr) {
                    alert("Ошибка при создании ссылки на оплату, но заказ сохранен. Мы свяжемся с вами.");
                    window.location.href = "/";
                }
            }
        } else {
            const error = await response.json();
            alert("Ошибка: " + (error.detail || "Не удалось оформить заказ"));
        }
    } catch (err) {
        console.error("Ошибка при отправке:", err);
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

    // 2. Показываем страницу оформления
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
                    ${item.size ? `Размер: ${item.size} • ` : ''}
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
    try {
        const res = await fetch(`/api/support/messages?user_id=${currentUser.id}`);
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

    try {
        await fetch('/api/support/send', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: currentUser.id, message })
        });
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

function initAutocomplete() {
    const input = document.getElementById('order-address');
    if (!input) return;

    const autocomplete = new google.maps.places.Autocomplete(input, {
        componentRestrictions: { country: "uz" },
        fields: ["address_components", "geometry"],
        types: ["address"],
    });

    autocomplete.addListener("place_changed", () => {
        const place = autocomplete.getPlace();
        if (!place.geometry || !place.geometry.location) {
            console.log("No location data for this place");
            return;
        }

        document.getElementById('order-lat').value = place.geometry.location.lat();
        document.getElementById('order-lng').value = place.geometry.location.lng();
    });
}
