// ============================================
// PROFILE PAGE JAVASCRIPT
// ============================================

let currentUser = null;
let currentTab = 'profile';
let selectedOrder = null;
let currentRating = 5;

// --- Initialization ---
document.addEventListener('DOMContentLoaded', () => {
    lucide.createIcons();
    checkAuth();
    loadProfile();
    syncFavoritesFromStorage(); // Синхронизация избранного из localStorage
});

// --- Authentication ---
function checkAuth() {
    const savedUser = localStorage.getItem('user');
    if (!savedUser) {
        window.location.href = '/login';
        return;
    }
    currentUser = JSON.parse(savedUser);
}

function handleSignOut() {
    localStorage.removeItem('user');
    localStorage.removeItem('token');
    window.location.href = '/';
}

// --- Tab Navigation ---
function switchTab(tabName) {
    // Hide all tabs
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.add('hidden');
    });
    
    // Remove active class from all buttons
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('tab-active');
    });
    
    // Show selected tab
    document.getElementById(`tab-${tabName}`).classList.remove('hidden');
    
    // Add active class to selected button
    document.querySelector(`[data-tab="${tabName}"]`).classList.add('tab-active');
    
    currentTab = tabName;
    
    // Load data for selected tab
    loadTabData(tabName);
}

function loadTabData(tabName) {
    switch(tabName) {
        case 'profile':
            loadProfile();
            break;
        case 'orders':
            loadOrders();
            break;
        case 'favorites':
            loadFavorites();
            break;
        case 'addresses':
            loadAddresses();
            break;
        case 'bonuses':
            loadBonuses();
            break;
        case 'reminders':
            loadReminders();
            break;
        case 'notifications':
            loadNotifications();
            break;
        case 'reviews':
            loadMyReviews();
            break;
    }
}

// --- Profile Functions ---
async function loadProfile() {
    try {
        const token = localStorage.getItem('token');
        const res = await fetch('/api/profile/me', {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (!res.ok) throw new Error('Failed to load profile');
        
        const data = await res.json();
        currentUser = data;
        
        // Update sidebar
        document.getElementById('sidebar-name').textContent = data.full_name || 'Пользователь';
        document.getElementById('sidebar-email').textContent = data.email;
        document.getElementById('sidebar-bonuses').textContent = `${data.bonus_points || 0} бонусов`;
        document.getElementById('sidebar-avatar').src = data.image_url || 'https://placehold.co/80';
        
        // Update form
        document.getElementById('profile-fullname').value = data.full_name || '';
        document.getElementById('profile-email-input').value = data.email;
        document.getElementById('profile-phone').value = data.phone || '';
        
        // Update badges
        document.getElementById('sidebar-bonuses').textContent = `${data.bonus_points || 0} бонусов`;
        
    } catch (error) {
        console.error('Error loading profile:', error);
    }
}

async function updateProfile(event) {
    event.preventDefault();
    
    const token = localStorage.getItem('token');
    const data = {
        full_name: document.getElementById('profile-fullname').value,
        email: document.getElementById('profile-email-input').value,
        phone: document.getElementById('profile-phone').value
    };
    
    try {
        const res = await fetch('/api/profile/me', {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify(data)
        });
        
        if (!res.ok) throw new Error('Failed to update profile');
        
        const result = await res.json();
        
        // Update localStorage
        localStorage.setItem('user', JSON.stringify(result));
        
        alert('Профиль успешно обновлен!');
        loadProfile();
        
    } catch (error) {
        console.error('Error updating profile:', error);
        alert('Ошибка при обновлении профиля');
    }
}

async function changePassword(event) {
    event.preventDefault();
    
    const token = localStorage.getItem('token');
    const data = {
        current_password: document.getElementById('current-password').value,
        new_password: document.getElementById('new-password').value
    };
    
    try {
        const res = await fetch('/api/profile/change-password', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify(data)
        });
        
        if (!res.ok) {
            const error = await res.json();
            throw new Error(error.detail || 'Failed to change password');
        }
        
        alert('Пароль успешно изменен!');
        document.getElementById('current-password').value = '';
        document.getElementById('new-password').value = '';
        
    } catch (error) {
        console.error('Error changing password:', error);
        alert(error.message || 'Ошибка при изменении пароля');
    }
}

async function uploadAvatar(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    const token = localStorage.getItem('token');
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        const res = await fetch('/api/profile/upload-avatar', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`
            },
            body: formData
        });
        
        if (!res.ok) throw new Error('Failed to upload avatar');
        
        const result = await res.json();
        
        // Update avatar
        document.getElementById('sidebar-avatar').src = result.url + '?t=' + Date.now();
        
        alert('Аватар успешно загружен!');
        
    } catch (error) {
        console.error('Error uploading avatar:', error);
        alert('Ошибка при загрузке аватара');
    }
}

// --- Orders Functions ---
async function loadOrders() {
    const token = localStorage.getItem('token');
    
    try {
        const res = await fetch('/api/profile/orders', {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (!res.ok) throw new Error('Failed to load orders');
        
        const orders = await res.json();
        
        const container = document.getElementById('orders-list');
        
        if (orders.length === 0) {
            container.innerHTML = `
                <div class="text-center py-12 text-gray-500">
                    <i data-lucide="shopping-bag" class="w-16 h-16 mx-auto mb-4 text-gray-300"></i>
                    <p>У вас пока нет заказов</p>
                </div>
            `;
            lucide.createIcons();
            return;
        }
        
        // Update badge
        const activeOrders = orders.filter(o => o.status !== 'completed' && o.status !== 'cancelled').length;
        const badge = document.getElementById('orders-badge');
        badge.textContent = activeOrders;
        badge.classList.toggle('hidden', activeOrders === 0);
        
        container.innerHTML = orders.map(order => `
            <div class="border border-gray-200 rounded-xl p-4 hover:shadow-md transition-shadow cursor-pointer" onclick="showOrderDetail(${order.id})">
                <div class="flex justify-between items-start mb-3">
                    <div>
                        <p class="font-bold text-gray-900">Заказ #${order.id}</p>
                        <p class="text-sm text-gray-500">${new Date(order.created_at).toLocaleDateString('ru-RU')}</p>
                    </div>
                    <span class="status-${order.status} px-3 py-1 rounded-full text-sm font-medium">
                        ${getStatusText(order.status)}
                    </span>
                </div>
                <div class="flex justify-between items-center">
                    <div class="text-sm text-gray-600">
                        <p>${order.items ? JSON.parse(order.items).length : 0} товаров</p>
                        <p>${order.delivery_address}</p>
                    </div>
                    <p class="text-lg font-bold text-rose-600">${formatPrice(order.total_amount)} сум</p>
                </div>
                ${order.courier ? `
                    <div class="mt-3 pt-3 border-t flex items-center gap-2 text-sm text-gray-600">
                        <i data-lucide="truck" class="w-4 h-4"></i>
                        <span>Курьер: ${order.courier.name} (${order.courier.phone})</span>
                    </div>
                ` : ''}
            </div>
        `).join('');
        
        lucide.createIcons();
        
    } catch (error) {
        console.error('Error loading orders:', error);
    }
}

function getStatusText(status) {
    const statusMap = {
        'pending': 'В обработке',
        'processing': 'Собирается',
        'shipping': 'Доставляется',
        'completed': 'Выполнен',
        'cancelled': 'Отменен'
    };
    return statusMap[status] || status;
}

function showOrderDetail(orderId) {
    selectedOrder = orderId;
    document.getElementById('order-detail-modal').classList.remove('hidden');
    document.body.style.overflow = 'hidden';
    loadOrderDetail(orderId);
}

async function loadOrderDetail(orderId) {
    const token = localStorage.getItem('token');
    
    try {
        const res = await fetch(`/api/profile/orders/${orderId}`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (!res.ok) throw new Error('Failed to load order detail');
        
        const order = await res.json();
        
        document.getElementById('detail-order-id').textContent = order.id;
        
        let itemsHtml = '';
        if (order.items) {
            try {
                const items = JSON.parse(order.items);
                itemsHtml = items.map(item => `
                    <div class="flex items-center gap-4 py-2 border-b">
                        <img src="${item.image_url || 'https://placehold.co/60'}" class="w-16 h-16 object-cover rounded-lg">
                        <div class="flex-1">
                            <p class="font-medium">${item.name}</p>
                            <p class="text-sm text-gray-500">Размер: ${item.size || 'M'}</p>
                        </div>
                        <p class="font-bold">${formatPrice(item.price)} сум</p>
                    </div>
                `).join('');
            } catch (e) {
                itemsHtml = `<p class="text-gray-500">${order.items}</p>`;
            }
        }
        
        document.getElementById('order-detail-content').innerHTML = `
            <div class="grid grid-cols-2 gap-4 mb-6">
                <div>
                    <p class="text-sm text-gray-500">Статус</p>
                    <span class="status-${order.status} px-3 py-1 rounded-full text-sm font-medium inline-block mt-1">
                        ${getStatusText(order.status)}
                    </span>
                </div>
                <div>
                    <p class="text-sm text-gray-500">Оплата</p>
                    <p class="font-medium">${order.is_paid ? 'Оплачен' : 'Не оплачен'}</p>
                </div>
                <div>
                    <p class="text-sm text-gray-500">Дата доставки</p>
                    <p class="font-medium">${order.delivery_date || 'Не указана'}</p>
                </div>
                <div>
                    <p class="text-sm text-gray-500">Время доставки</p>
                    <p class="font-medium">${order.delivery_time || 'Не указано'}</p>
                </div>
            </div>
            
            <div class="mb-6">
                <p class="text-sm text-gray-500 mb-2">Адрес доставки</p>
                <p class="font-medium">${order.delivery_address}</p>
            </div>
            
            <div class="mb-6">
                <p class="text-sm text-gray-500 mb-2">Телефон</p>
                <p class="font-medium">${order.phone}</p>
            </div>
            
            ${order.comment ? `
                <div class="mb-6">
                    <p class="text-sm text-gray-500 mb-2">Комментарий</p>
                    <p class="font-medium">${order.comment}</p>
                </div>
            ` : ''}
            
            <div class="mb-6">
                <p class="text-sm text-gray-500 mb-2">Товары</p>
                <div class="border rounded-lg p-3">
                    ${itemsHtml || 'Нет товаров'}
                </div>
            </div>
            
            <div class="flex justify-between items-center pt-4 border-t">
                <p class="text-lg font-medium">Итого</p>
                <p class="text-2xl font-bold text-rose-600">${formatPrice(order.total_amount)} сум</p>
            </div>
            
            ${order.courier ? `
                <div class="mt-4 p-4 bg-gray-50 rounded-lg">
                    <p class="font-medium mb-2">Информация о курьере</p>
                    <div class="flex items-center gap-3">
                        <div class="w-10 h-10 bg-rose-100 rounded-full flex items-center justify-center">
                            <i data-lucide="user" class="w-5 h-5 text-rose-600"></i>
                        </div>
                        <div>
                            <p class="font-medium">${order.courier.name}</p>
                            <a href="tel:${order.courier.phone}" class="text-sm text-rose-600">${order.courier.phone}</a>
                        </div>
                    </div>
                </div>
            ` : ''}
        `;
        
        lucide.createIcons();
        
    } catch (error) {
        console.error('Error loading order detail:', error);
    }
}

function hideOrderDetail() {
    document.getElementById('order-detail-modal').classList.add('hidden');
    document.body.style.overflow = '';
    selectedOrder = null;
}

async function repeatOrder() {
    if (!selectedOrder) return;
    
    const token = localStorage.getItem('token');
    
    try {
        const res = await fetch(`/api/profile/orders/${selectedOrder}/repeat`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (!res.ok) throw new Error('Failed to repeat order');
        
        const result = await res.json();
        
        alert(`Заказ повторен! Новый заказ #${result.id}`);
        hideOrderDetail();
        loadOrders();
        
    } catch (error) {
        console.error('Error repeating order:', error);
        alert('Ошибка при повторе заказа');
    }
}

async function downloadReceipt() {
    if (!selectedOrder) return;
    
    const token = localStorage.getItem('token');
    
    try {
        const res = await fetch(`/api/profile/orders/${selectedOrder}/receipt`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (!res.ok) throw new Error('Failed to get receipt');
        
        const receipt = await res.json();
        
        // Create printable receipt
        const printWindow = window.open('', '_blank');
        printWindow.document.write(`
            <html>
                <head>
                    <title>Чек заказа #${receipt.order_id}</title>
                    <style>
                        body { font-family: Arial, sans-serif; padding: 20px; }
                        .header { text-align: center; margin-bottom: 30px; }
                        .title { font-size: 24px; font-weight: bold; }
                        .info { margin-bottom: 20px; }
                        .row { display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #eee; }
                        .total { font-size: 20px; font-weight: bold; margin-top: 20px; }
                    </style>
                </head>
                <body>
                    <div class="header">
                        <div class="title">UzFlower</div>
                        <p>Чек заказа #${receipt.order_id}</p>
                        <p>${receipt.created_at}</p>
                    </div>
                    <div class="info">
                        <div class="row"><span>Адрес доставки:</span><span>${receipt.delivery_address}</span></div>
                        <div class="row"><span>Способ оплаты:</span><span>${receipt.payment_method}</span></div>
                        <div class="row"><span>Статус оплаты:</span><span>${receipt.is_paid ? 'Оплачено' : 'Не оплачено'}</span></div>
                    </div>
                    <div class="total">
                        Итого: ${formatPrice(receipt.total_amount)} сум
                    </div>
                    <script>
                        window.onload = function() { window.print(); }
                    </script>
                </body>
            </html>
        `);
        printWindow.document.close();
        
    } catch (error) {
        console.error('Error downloading receipt:', error);
        alert('Ошибка при получении чека');
    }
}

// --- Favorites Functions ---

// Синхронизация избранного из localStorage в базу данных
async function syncFavoritesFromStorage() {
    const token = localStorage.getItem('token');
    const localFavorites = JSON.parse(localStorage.getItem('favorites') || '[]');
    
    if (!token || !currentUser || localFavorites.length === 0) return;
    
    try {
        // Получаем текущие избранные товары с сервера
        const res = await fetch('/api/profile/favorites', {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (!res.ok) return;
        
        const serverFavorites = await res.json();
        const serverProductIds = serverFavorites.map(f => f.product.id);
        
        // Добавляем товары которые есть в localStorage но нет на сервере
        for (const productId of localFavorites) {
            if (!serverProductIds.includes(productId)) {
                await fetch('/api/profile/favorites', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${token}`
                    },
                    body: JSON.stringify({ product_id: productId })
                });
            }
        }
    } catch (error) {
        console.error('Error syncing favorites:', error);
    }
}

async function loadFavorites() {
    const token = localStorage.getItem('token');
    
    try {
        const res = await fetch('/api/profile/favorites', {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (!res.ok) throw new Error('Failed to load favorites');
        
        const favorites = await res.json();
        
        const container = document.getElementById('favorites-list');
        
        if (favorites.length === 0) {
            container.innerHTML = `
                <div class="text-center py-12 col-span-full text-gray-500">
                    <i data-lucide="heart" class="w-16 h-16 mx-auto mb-4 text-gray-300"></i>
                    <p>Список избранного пуст</p>
                </div>
            `;
            lucide.createIcons();
            return;
        }
        
        // Update badge
        const badge = document.getElementById('favorites-badge');
        badge.textContent = favorites.length;
        badge.classList.remove('hidden');
        
        container.innerHTML = favorites.map(fav => `
            <div class="border border-gray-200 rounded-xl overflow-hidden hover:shadow-md transition-shadow">
                <img src="${fav.product.image_url || 'https://placehold.co/300'}" class="w-full h-48 object-cover">
                <div class="p-4">
                    <h4 class="font-bold text-gray-900 mb-2">${fav.product.name}</h4>
                    <div class="flex justify-between items-center">
                        <div>
                            ${fav.product.sale_price ? `
                                <span class="text-lg font-bold text-rose-600">${formatPrice(fav.product.sale_price)}</span>
                                <span class="text-sm text-gray-400 line-through ml-2">${formatPrice(fav.product.price)}</span>
                            ` : `<span class="text-lg font-bold text-gray-900">${formatPrice(fav.product.price)}</span>`}
                        </div>
                        <button onclick="removeFromFavorites(${fav.product.id})" class="p-2 text-red-500 hover:bg-red-50 rounded-lg transition-colors">
                            <i data-lucide="trash-2" class="w-5 h-5"></i>
                        </button>
                    </div>
                    <button onclick="addToCartFromFavorite(${fav.product.id})" ${fav.product.stock === 0 ? 'disabled' : ''} class="mt-3 w-full py-2 bg-rose-600 text-white rounded-lg hover:bg-rose-700 transition-all disabled:opacity-50">
                        ${fav.product.stock === 0 ? 'Нет в наличии' : 'В корзину'}
                    </button>
                </div>
            </div>
        `).join('');
        
        lucide.createIcons();
        
    } catch (error) {
        console.error('Error loading favorites:', error);
    }
}

async function removeFromFavorites(productId) {
    const token = localStorage.getItem('token');
    
    try {
        const res = await fetch(`/api/profile/favorites/${productId}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (!res.ok) throw new Error('Failed to remove from favorites');
        
        loadFavorites();
        
    } catch (error) {
        console.error('Error removing from favorites:', error);
    }
}

function addToCartFromFavorite(productId) {
    // TODO: Implement add to cart logic
    alert('Товар добавлен в корзину (функционал в разработке)');
}

// --- Addresses Functions ---
async function loadAddresses() {
    const token = localStorage.getItem('token');
    
    try {
        const res = await fetch('/api/profile/addresses', {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (!res.ok) throw new Error('Failed to load addresses');
        
        const addresses = await res.json();
        
        const container = document.getElementById('addresses-list');
        
        if (addresses.length === 0) {
            container.innerHTML = `
                <div class="text-center py-12 text-gray-500">
                    <i data-lucide="map-pin" class="w-16 h-16 mx-auto mb-4 text-gray-300"></i>
                    <p>У вас пока нет адресов</p>
                </div>
            `;
            lucide.createIcons();
            return;
        }
        
        container.innerHTML = addresses.map(addr => `
            <div class="border border-gray-200 rounded-xl p-4 relative ${addr.is_default ? 'ring-2 ring-rose-500' : ''}">
                ${addr.is_default ? '<span class="absolute top-2 right-2 bg-rose-500 text-white text-xs px-2 py-1 rounded">По умолчанию</span>' : ''}
                <div class="flex items-start gap-3">
                    <i data-lucide="map-pin" class="w-5 h-5 text-rose-600 mt-1"></i>
                    <div class="flex-1">
                        ${addr.title ? `<p class="font-bold text-gray-900 mb-1">${addr.title}</p>` : ''}
                        <p class="text-gray-700">${addr.address}</p>
                        <p class="text-sm text-gray-500 mt-2">
                            <span class="font-medium">${addr.recipient_name}</span>
                            <span class="mx-2">•</span>
                            <a href="tel:${addr.phone}" class="text-rose-600">${addr.phone}</a>
                        </p>
                    </div>
                </div>
                <div class="flex gap-2 mt-4 pt-4 border-t">
                    <button onclick="editAddress(${addr.id})" class="flex-1 py-2 text-sm border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">
                        Редактировать
                    </button>
                    <button onclick="deleteAddress(${addr.id})" class="flex-1 py-2 text-sm border border-red-300 text-red-600 rounded-lg hover:bg-red-50 transition-colors">
                        Удалить
                    </button>
                </div>
            </div>
        `).join('');
        
        lucide.createIcons();
        
    } catch (error) {
        console.error('Error loading addresses:', error);
    }
}

function showAddAddressModal() {
    document.getElementById('add-address-modal').classList.remove('hidden');
    document.getElementById('address-title').value = '';
    document.getElementById('address-full').value = '';
    document.getElementById('address-phone').value = '';
    document.getElementById('address-recipient').value = '';
    document.getElementById('address-default').checked = false;
}

function hideAddAddressModal() {
    document.getElementById('add-address-modal').classList.add('hidden');
}

async function addAddress(event) {
    event.preventDefault();
    
    const token = localStorage.getItem('token');
    const data = {
        title: document.getElementById('address-title').value || null,
        address: document.getElementById('address-full').value,
        phone: document.getElementById('address-phone').value,
        recipient_name: document.getElementById('address-recipient').value,
        is_default: document.getElementById('address-default').checked
    };
    
    try {
        const res = await fetch('/api/profile/addresses', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify(data)
        });
        
        if (!res.ok) throw new Error('Failed to add address');
        
        hideAddAddressModal();
        loadAddresses();
        
        alert('Адрес успешно добавлен!');
        
    } catch (error) {
        console.error('Error adding address:', error);
        alert('Ошибка при добавлении адреса');
    }
}

async function deleteAddress(addressId) {
    if (!confirm('Вы уверены, что хотите удалить этот адрес?')) return;
    
    const token = localStorage.getItem('token');
    
    try {
        const res = await fetch(`/api/profile/addresses/${addressId}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (!res.ok) throw new Error('Failed to delete address');
        
        loadAddresses();
        
    } catch (error) {
        console.error('Error deleting address:', error);
    }
}

function editAddress(addressId) {
    // TODO: Implement edit address modal
    alert('Функционал редактирования в разработке');
}

// --- Bonuses Functions ---
async function loadBonuses() {
    const token = localStorage.getItem('token');
    
    try {
        // Load balance and history
        const res = await fetch('/api/profile/bonuses', {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (!res.ok) throw new Error('Failed to load bonuses');
        
        const data = await res.json();
        
        document.getElementById('bonus-balance').textContent = data.balance;
        
        const historyContainer = document.getElementById('bonus-history');
        
        if (data.transactions.length === 0) {
            historyContainer.innerHTML = `
                <div class="text-center py-8 text-gray-500">
                    <p>История пуста</p>
                </div>
            `;
        } else {
            historyContainer.innerHTML = data.transactions.map(t => `
                <div class="flex justify-between items-center py-3 border-b">
                    <div>
                        <p class="font-medium">${t.description}</p>
                        ${t.order_id ? `<p class="text-sm text-gray-500">Заказ #${t.order_id}</p>` : ''}
                    </div>
                    <span class="${t.amount > 0 ? 'text-green-600' : 'text-red-600'} font-bold">
                        ${t.amount > 0 ? '+' : ''}${t.amount}
                    </span>
                </div>
            `).join('');
        }
        
        // Load promo codes
        const promoRes = await fetch('/api/profile/promocodes', {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (promoRes.ok) {
            const promocodes = await promoRes.json();
            
            const promoContainer = document.getElementById('promo-codes-list');
            
            if (promocodes.length === 0) {
                promoContainer.innerHTML = `
                    <div class="text-center py-8 text-gray-500 col-span-full">
                        <p>Нет доступных промокодов</p>
                    </div>
                `;
            } else {
                promoContainer.innerHTML = promocodes.map(p => `
                    <div class="border-2 border-dashed border-rose-300 rounded-xl p-4 bg-rose-50">
                        <div class="flex justify-between items-center">
                            <div>
                                <p class="font-bold text-gray-900">Скидка ${p.discount_percent}%</p>
                                <p class="text-sm text-gray-500">Промокод</p>
                            </div>
                            <code class="text-lg font-bold text-rose-600 bg-white px-3 py-1 rounded">${p.code}</code>
                        </div>
                    </div>
                `).join('');
            }
        }
        
    } catch (error) {
        console.error('Error loading bonuses:', error);
    }
}

// --- Reminders Functions ---
async function loadReminders() {
    const token = localStorage.getItem('token');
    
    try {
        const res = await fetch('/api/profile/reminders', {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (!res.ok) throw new Error('Failed to load reminders');
        
        const reminders = await res.json();
        
        const container = document.getElementById('reminders-list');
        
        if (reminders.length === 0) {
            container.innerHTML = `
                <div class="text-center py-12 text-gray-500">
                    <i data-lucide="bell" class="w-16 h-16 mx-auto mb-4 text-gray-300"></i>
                    <p>У вас пока нет напоминаний</p>
                </div>
            `;
            lucide.createIcons();
            return;
        }
        
        container.innerHTML = reminders.map(r => `
            <div class="border border-gray-200 rounded-xl p-4 flex justify-between items-center">
                <div class="flex items-start gap-3">
                    <div class="w-12 h-12 bg-rose-100 rounded-full flex items-center justify-center flex-shrink-0">
                        <i data-lucide="calendar" class="w-6 h-6 text-rose-600"></i>
                    </div>
                    <div>
                        <p class="font-bold text-gray-900">${r.title}</p>
                        <p class="text-sm text-gray-500">${r.recipient_name}</p>
                        <div class="flex items-center gap-3 mt-1 text-sm">
                            <span class="text-rose-600 font-medium">${formatDate(r.date)}</span>
                            ${r.is_recurring ? `<span class="text-gray-400">• ${r.recurring_type === 'yearly' ? 'Ежегодно' : 'Ежемесячно'}</span>` : ''}
                        </div>
                    </div>
                </div>
                <button onclick="deleteReminder(${r.id})" class="p-2 text-gray-400 hover:text-red-600 transition-colors">
                    <i data-lucide="trash-2" class="w-5 h-5"></i>
                </button>
            </div>
        `).join('');
        
        lucide.createIcons();
        
    } catch (error) {
        console.error('Error loading reminders:', error);
    }
}

function showAddReminderModal() {
    document.getElementById('add-reminder-modal').classList.remove('hidden');
    document.getElementById('reminder-title').value = '';
    document.getElementById('reminder-date').value = '';
    document.getElementById('reminder-recipient').value = '';
    document.getElementById('reminder-phone').value = '';
    document.getElementById('reminder-recurring').checked = false;
    document.getElementById('reminder-recurring-type').value = 'yearly';
    document.getElementById('recurring-type-container').classList.add('hidden');
}

function hideAddReminderModal() {
    document.getElementById('add-reminder-modal').classList.add('hidden');
}

function toggleRecurringType() {
    const isRecurring = document.getElementById('reminder-recurring').checked;
    document.getElementById('recurring-type-container').classList.toggle('hidden', !isRecurring);
}

async function addReminder(event) {
    event.preventDefault();
    
    const token = localStorage.getItem('token');
    const data = {
        title: document.getElementById('reminder-title').value,
        date: document.getElementById('reminder-date').value,
        recipient_name: document.getElementById('reminder-recipient').value,
        recipient_phone: document.getElementById('reminder-phone').value || null,
        is_recurring: document.getElementById('reminder-recurring').checked,
        recurring_type: document.getElementById('reminder-recurring').checked ? document.getElementById('reminder-recurring-type').value : null
    };
    
    try {
        const res = await fetch('/api/profile/reminders', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify(data)
        });
        
        if (!res.ok) throw new Error('Failed to add reminder');
        
        hideAddReminderModal();
        loadReminders();
        
        alert('Напоминание успешно добавлено!');
        
    } catch (error) {
        console.error('Error adding reminder:', error);
        alert('Ошибка при добавлении напоминания');
    }
}

async function deleteReminder(reminderId) {
    if (!confirm('Вы уверены, что хотите удалить это напоминание?')) return;
    
    const token = localStorage.getItem('token');
    
    try {
        const res = await fetch(`/api/profile/reminders/${reminderId}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (!res.ok) throw new Error('Failed to delete reminder');
        
        loadReminders();
        
    } catch (error) {
        console.error('Error deleting reminder:', error);
    }
}

// --- Notifications Functions ---
async function loadNotifications() {
    const token = localStorage.getItem('token');
    
    try {
        const res = await fetch('/api/profile/notifications', {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (!res.ok) throw new Error('Failed to load notifications');
        
        const data = await res.json();
        
        // Update badge
        const badge = document.getElementById('notifications-badge');
        badge.textContent = data.unread_count;
        badge.classList.toggle('hidden', data.unread_count === 0);
        
        const container = document.getElementById('notifications-list');
        
        if (data.notifications.length === 0) {
            container.innerHTML = `
                <div class="text-center py-12 text-gray-500">
                    <i data-lucide="message-square" class="w-16 h-16 mx-auto mb-4 text-gray-300"></i>
                    <p>Нет уведомлений</p>
                </div>
            `;
            lucide.createIcons();
            return;
        }
        
        container.innerHTML = data.notifications.map(n => `
            <div class="p-4 rounded-xl border ${!n.is_read ? 'notification-unread' : 'border-gray-200'} cursor-pointer" onclick="markNotificationRead(${n.id})">
                <div class="flex items-start gap-3">
                    <div class="w-10 h-10 bg-rose-100 rounded-full flex items-center justify-center flex-shrink-0">
                        ${getNotificationIcon(n.type)}
                    </div>
                    <div class="flex-1">
                        <p class="font-bold text-gray-900">${n.title}</p>
                        <p class="text-sm text-gray-600 mt-1">${n.message}</p>
                        <p class="text-xs text-gray-400 mt-2">${formatDateTime(n.created_at)}</p>
                    </div>
                    ${!n.is_read ? '<div class="w-2 h-2 bg-red-500 rounded-full"></div>' : ''}
                </div>
            </div>
        `).join('');
        
        lucide.createIcons();
        
    } catch (error) {
        console.error('Error loading notifications:', error);
    }
}

function getNotificationIcon(type) {
    const icons = {
        'info': '<i data-lucide="info" class="w-5 h-5 text-rose-600"></i>',
        'order': '<i data-lucide="shopping-bag" class="w-5 h-5 text-rose-600"></i>',
        'promo': '<i data-lucide="percent" class="w-5 h-5 text-rose-600"></i>',
        'reminder': '<i data-lucide="bell" class="w-5 h-5 text-rose-600"></i>',
        'bonus': '<i data-lucide="gift" class="w-5 h-5 text-rose-600"></i>'
    };
    return icons[type] || icons['info'];
}

async function markNotificationRead(notificationId) {
    const token = localStorage.getItem('token');
    
    try {
        await fetch(`/api/profile/notifications/${notificationId}/read`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        loadNotifications();
        
    } catch (error) {
        console.error('Error marking notification as read:', error);
    }
}

async function markAllNotificationsRead() {
    const token = localStorage.getItem('token');

    try {
        await fetch('/api/profile/notifications/read-all', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        loadNotifications();

    } catch (error) {
        console.error('Error marking all notifications as read:', error);
    }
}

async function clearAllNotifications() {
    const token = localStorage.getItem('token');

    if (!confirm('Вы уверены что хотите удалить все уведомления? Это действие нельзя отменить.')) {
        return;
    }

    try {
        const res = await fetch('/api/profile/notifications/all', {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (!res.ok) throw new Error('Failed to clear notifications');

        const result = await res.json();
        
        // Обновляем badge
        const badge = document.getElementById('notifications-badge');
        if (badge) {
            badge.textContent = '0';
            badge.classList.add('hidden');
        }

        // Перезагружаем список
        loadNotifications();

        // Показываем уведомление
        alert(`✅ Удалено ${result.count} уведомлений`);

    } catch (error) {
        console.error('Error clearing notifications:', error);
        alert('Ошибка при удалении уведомлений');
    }
}

// --- Reviews Functions ---

let selectedPhotos = [];

async function loadMyReviews() {
    const token = localStorage.getItem('token');
    const container = document.getElementById('my-reviews-list');
    
    try {
        const res = await fetch('/api/profile/reviews', {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (!res.ok) throw new Error('Failed to load reviews');
        
        const reviews = await res.json();
        
        if (reviews.length === 0) {
            container.innerHTML = `
                <div class="text-center py-12 text-gray-500">
                    <i data-lucide="star" class="w-16 h-16 mx-auto mb-4 text-gray-300"></i>
                    <p>У вас пока нет отзывов</p>
                    <button onclick="showReviewModal()" class="mt-4 px-4 py-2 bg-rose-600 text-white rounded-lg hover:bg-rose-700 transition-all">
                        Оставить первый отзыв
                    </button>
                </div>
            `;
            lucide.createIcons();
            return;
        }
        
        container.innerHTML = reviews.map(r => `
            <div class="border border-gray-200 rounded-xl p-4 hover:shadow-md transition-all">
                <div class="flex items-start justify-between mb-3">
                    <div class="flex items-center gap-3">
                        ${r.product_image ? `<img src="${r.product_image}" class="w-16 h-16 object-cover rounded-lg">` : ''}
                        <div>
                            <p class="font-bold text-gray-900">${r.product_name}</p>
                            <div class="flex items-center gap-2 mt-1">
                                ${renderStars(r.rating)}
                                ${r.is_verified_purchase ? '<span class="verified-badge"><i data-lucide="check-circle" class="w-3 h-3"></i>Проверенная покупка</span>' : ''}
                            </div>
                        </div>
                    </div>
                    <div class="flex items-center gap-2">
                        ${!r.is_approved ? '<span class="text-xs bg-yellow-100 text-yellow-800 px-2 py-1 rounded">На модерации</span>' : ''}
                        <button onclick="deleteReview(${r.id})" class="p-2 text-gray-400 hover:text-red-600 transition-colors">
                            <i data-lucide="trash-2" class="w-5 h-5"></i>
                        </button>
                    </div>
                </div>
                <p class="text-gray-700 mb-3">${r.text}</p>
                ${r.images && r.images.length > 0 ? `
                    <div class="flex gap-2 overflow-x-auto pb-2">
                        ${r.images.map(img => `<img src="${img}" class="w-20 h-20 object-cover rounded-lg cursor-pointer" onclick="window.open('${img}')">`).join('')}
                    </div>
                ` : ''}
                <p class="text-xs text-gray-400 mt-3">${new Date(r.created_at).toLocaleDateString('ru-RU')}</p>
            </div>
        `).join('');
        
        lucide.createIcons();
        
    } catch (error) {
        console.error('Error loading reviews:', error);
        container.innerHTML = '<p class="text-center text-red-500 py-12">Ошибка при загрузке отзывов</p>';
    }
}

function renderStars(rating) {
    let stars = '';
    for (let i = 1; i <= 5; i++) {
        stars += `<i data-lucide="star" class="w-4 h-4 ${i <= rating ? 'text-yellow-400 fill-yellow-400' : 'text-gray-300'}"></i>`;
    }
    return `<div class="flex">${stars}</div>`;
}

async function loadProductsForReview() {
    const select = document.getElementById('review-product-id');
    
    if (!select) {
        console.error('Select element not found');
        return;
    }
    
    // Показываем индикатор загрузки
    select.innerHTML = '<option value="">Загрузка товаров...</option>';
    select.disabled = true;
    
    try {
        const res = await fetch('/api/products');
        if (!res.ok) throw new Error('Failed to load products');
        
        const products = await res.json();
        
        if (products.length === 0) {
            select.innerHTML = '<option value="">Нет доступных товаров</option>';
            return;
        }
        
        select.innerHTML = '<option value="">-- Выберите букет --</option>' +
            products
                .filter(p => p.id && p.name)  // Фильтруем товары с id и name
                .sort((a, b) => a.name.localeCompare(b.name))  // Сортируем по названию
                .map(p => `<option value="${p.id}" data-name="${p.name}">${p.name} - ${formatPrice(p.price)} сум</option>`)
                .join('');
        
        select.disabled = false;
        
    } catch (error) {
        console.error('Error loading products:', error);
        select.innerHTML = '<option value="">Ошибка загрузки</option>';
        select.disabled = false;
    }
}

function showReviewModal() {
    document.getElementById('review-modal').classList.remove('hidden');
    document.body.style.overflow = 'hidden';
    setRating(5);
    selectedPhotos = [];
    document.getElementById('review-photo-preview').innerHTML = '';
    document.getElementById('review-photos').value = '';
}

function hideReviewModal() {
    document.getElementById('review-modal').classList.add('hidden');
    document.body.style.overflow = '';
}

function setRating(rating) {
    currentRating = rating;
    document.getElementById('review-rating').value = rating;
    
    const ratingTexts = ['Ужасно', 'Плохо', 'Нормально', 'Хорошо', 'Отлично!'];
    document.getElementById('rating-text').textContent = ratingTexts[rating - 1];
    
    document.querySelectorAll('.star-btn').forEach(btn => {
        const starRating = parseInt(btn.dataset.rating);
        const icon = btn.querySelector('i');
        if (starRating <= rating) {
            icon.classList.remove('text-gray-300');
            icon.classList.add('text-yellow-400', 'fill-yellow-400');
            btn.classList.add('active');
        } else {
            icon.classList.add('text-gray-300');
            icon.classList.remove('text-yellow-400', 'fill-yellow-400');
            btn.classList.remove('active');
        }
    });
}

function previewReviewPhotos() {
    const input = document.getElementById('review-photos');
    const preview = document.getElementById('review-photo-preview');
    
    if (input.files) {
        Array.from(input.files).forEach(file => {
            if (file.size > 5 * 1024 * 1024) {
                alert(`Файл ${file.name} слишком большой (макс. 5MB)`);
                return;
            }
            
            const reader = new FileReader();
            reader.onload = function(e) {
                selectedPhotos.push(file);
                preview.innerHTML += `
                    <div class="relative group">
                        <img src="${e.target.result}" class="w-full h-20 object-cover rounded-lg">
                        <button type="button" onclick="removePhoto(this, ${selectedPhotos.length - 1})" class="absolute top-1 right-1 p-1 bg-red-500 text-white rounded-full opacity-0 group-hover:opacity-100 transition-opacity">
                            <i data-lucide="x" class="w-3 h-3"></i>
                        </button>
                    </div>
                `;
                lucide.createIcons();
            };
            reader.readAsDataURL(file);
        });
    }
}

function removePhoto(button, index) {
    selectedPhotos.splice(index, 1);
    button.parentElement.remove();
}

async function submitReviewWithPhotos(event) {
    event.preventDefault();

    const token = localStorage.getItem('token');
    const rating = parseInt(document.getElementById('review-rating').value);
    const text = document.getElementById('review-text').value;

    if (rating < 1 || rating > 5) {
        alert('⚠️ Выберите оценку от 1 до 5 звёзд');
        return;
    }

    if (!text || text.trim().length === 0) {
        alert('⚠️ Введите текст отзыва');
        return;
    }

    const formData = new FormData();
    formData.append('product_name', 'Заказ через сайт');
    formData.append('rating', rating.toString());
    formData.append('text', text);
    formData.append('user_name', currentUser.full_name || 'Пользователь');

    selectedPhotos.forEach(photo => {
        formData.append('files', photo);
    });

    try {
        const res = await fetch('/api/profile/reviews', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`
            },
            body: formData
        });

        // Проверяем что вернулся JSON
        const contentType = res.headers.get('content-type');
        if (!contentType || !contentType.includes('application/json')) {
            const text = await res.text();
            console.error('Server returned non-JSON:', text.substring(0, 500));
            throw new Error('Сервер вернул ошибку (не JSON). Проверьте консоль сервера.');
        }

        if (!res.ok) {
            const error = await res.json();
            throw new Error(error.detail || error.message || 'Failed to create review');
        }

        const result = await res.json();
        console.log('✅ Review created:', result);

        alert('✅ Отзыв успешно отправлен!');
        hideReviewModal();
        loadMyReviews();

    } catch (error) {
        console.error('❌ Error submitting review:', error);
        alert('❌ Ошибка: ' + error.message);
    }
}

async function deleteReview(reviewId) {
    if (!confirm('Вы уверены что хотите удалить этот отзыв?')) return;
    
    const token = localStorage.getItem('token');
    
    try {
        const res = await fetch(`/api/profile/reviews/${reviewId}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (!res.ok) throw new Error('Failed to delete review');
        
        loadMyReviews();
        
    } catch (error) {
        console.error('Error deleting review:', error);
        alert('Ошибка при удалении отзыва');
    }
}

// --- Utilities ---
function formatPrice(price) {
    return Number(price).toLocaleString('ru-RU');
}

function formatDate(dateStr) {
    const date = new Date(dateStr);
    return date.toLocaleDateString('ru-RU', { day: 'numeric', month: 'long', year: 'numeric' });
}

function formatDateTime(dateTimeStr) {
    const date = new Date(dateTimeStr);
    return date.toLocaleDateString('ru-RU', {
        day: 'numeric',
        month: 'short',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}
