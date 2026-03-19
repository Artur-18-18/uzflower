// ============================================================
// ФУНКЦИИ ОФОРМЛЕНИЯ ЗАКАЗА (Checkout)
// Закомментированы для будущего использования
// Когда понадобится - раскомментировать и подключить в app.js
// ============================================================

/*
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

// ============================================
// ДЛЯ ПОДКЛЮЧЕНИЯ ДОБАВИТЬ В app.js:
// ============================================
// 1. Раскомментировать этот файл
// 2. Добавить <script src="/static/js/checkout.js"></script> в index.html
// 3. Раскомментировать кнопку в cart-sidebar (index.html)
// 4. Проверить что page-checkout существует в index.html
// ============================================
*/
