"""
Integration тесты API - Продукты и Заказы
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from main import User, Product, Order, Category


class TestProductsAPI:
    """Тесты API продуктов"""
    
    def test_get_products(self, client: TestClient, test_product: Product):
        """Получение списка продуктов"""
        response = client.get("/api/products")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
    
    def test_get_products_filtered(self, client: TestClient, test_category: Category):
        """Получение продуктов с фильтрацией"""
        p1 = Product(name="Cheap", price=50000, category_id=test_category.id)
        p2 = Product(name="Expensive", price=500000, category_id=test_category.id)
        client.app.dependency_overrides[client.app.dependency_overrides.get(list(client.app.dependency_overrides.keys())[0]) if client.app.dependency_overrides else lambda: None] if client.app.dependency_overrides else None
        from main import get_db
        def override_get_db():
            yield client.app.state.db_session if hasattr(client.app.state, 'db_session') else None
        
        response = client.get("/api/products?max_price=100000")
        
        assert response.status_code == 200
    
    def test_get_products_by_category(self, client: TestClient, test_category: Category, test_product: Product):
        """Получение продуктов по категории"""
        response = client.get(f"/api/products?category_id={test_category.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
    
    def test_get_products_sorted(self, client: TestClient, test_category: Category):
        """Получение продуктов с сортировкой"""
        p1 = Product(name="A", price=100000, category_id=test_category.id)
        p2 = Product(name="B", price=50000, category_id=test_category.id)
        
        response = client.get("/api/products?sort_by=price_asc")
        
        assert response.status_code == 200


class TestAdminProductsAPI:
    """Тесты API админа для продуктов"""
    
    def test_admin_get_products(self, client: TestClient, admin_headers: dict, test_product: Product):
        """Админ получает все продукты"""
        response = client.get("/api/admin/products", headers=admin_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
    
    def test_admin_add_product(self, client: TestClient, admin_headers: dict, test_category: Category):
        """Админ добавляет продукт"""
        response = client.post("/api/products", headers=admin_headers, json={
            "name": "New Product",
            "price": 150000,
            "description": "Test description",
            "category_id": test_category.id,
            "stock": 10
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "New Product"
    
    def test_admin_update_product(self, client: TestClient, admin_headers: dict, test_product: Product):
        """Админ обновляет продукт"""
        response = client.put(f"/api/products/{test_product.id}", headers=admin_headers, json={
            "name": test_product.name,
            "price": 200000,
            "description": test_product.description,
            "category_id": test_product.category_id,
            "stock": test_product.stock
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["price"] == 200000
    
    def test_admin_delete_product(self, client: TestClient, admin_headers: dict, test_category: Category):
        """Админ удаляет продукт"""
        # Создаем продукт
        product = Product(name="ToDelete", price=100000, category_id=test_category.id)
        
        response = client.delete(f"/api/products/{product.id}", headers=admin_headers)
        
        assert response.status_code == 200
    
    def test_admin_add_product_unauthorized(self, client: TestClient, test_product: Product, headers: dict):
        """Пользователь не может добавить продукт"""
        response = client.post("/api/products", headers=headers, json={
            "name": "Unauthorized",
            "price": 100000
        })
        
        assert response.status_code == 403


class TestOrdersAPI:
    """Тесты API заказов"""
    
    def test_create_order(self, client: TestClient, test_user: User, headers: dict):
        """Создание заказа"""
        response = client.post("/api/orders", headers=headers, json={
            "total_amount": 100000,
            "delivery_address": "Test Address",
            "phone": "+998901234567",
            "delivery_date": "2024-03-08",
            "delivery_time": "12:00-15:00"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_amount"] == 100000
        assert data["status"] == "pending"
    
    def test_create_order_unauthorized(self, client: TestClient):
        """Создание заказа без авторизации"""
        response = client.post("/api/orders", json={
            "total_amount": 100000,
            "delivery_address": "Test Address",
            "phone": "+998901234567"
        })
        
        assert response.status_code == 401
    
    def test_get_my_orders(self, client: TestClient, test_user: User, test_order: Order, headers: dict):
        """Получение своих заказов"""
        response = client.get("/api/profile/orders", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
    
    def test_get_order_detail(self, client: TestClient, test_user: User, test_order: Order, headers: dict):
        """Получение деталей заказа"""
        response = client.get(f"/api/profile/orders/{test_order.id}", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_order.id
    
    def test_repeat_order(self, client: TestClient, test_user: User, test_order: Order, headers: dict):
        """Повтор заказа"""
        response = client.post(f"/api/profile/orders/{test_order.id}/repeat", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
    
    def test_get_order_receipt(self, client: TestClient, test_user: User, test_order: Order, headers: dict):
        """Получение чека"""
        response = client.get(f"/api/profile/orders/{test_order.id}/receipt", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "order_id" in data


class TestAdminOrdersAPI:
    """Тесты API админа для заказов"""
    
    def test_admin_get_all_orders(self, client: TestClient, admin_headers: dict, test_order: Order):
        """Админ получает все заказы"""
        response = client.get("/api/orders", headers=admin_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
    
    def test_admin_update_order_status(self, client: TestClient, admin_headers: dict, test_order: Order):
        """Админ обновляет статус заказа"""
        response = client.put(f"/api/orders/{test_order.id}/status", headers=admin_headers, json={
            "status": "processing"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "processing"
    
    def test_admin_update_order_paid(self, client: TestClient, admin_headers: dict, test_order: Order):
        """Админ обновляет оплату заказа"""
        response = client.put(f"/api/orders/{test_order.id}/status", headers=admin_headers, json={
            "is_paid": True
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["is_paid"] is True


class TestPaymentAPI:
    """Тесты API оплаты"""
    
    def test_create_click_payment_link(self, client: TestClient, test_user: User, test_order: Order, headers: dict):
        """Создание ссылки на оплату Click"""
        response = client.get(f"/api/payment/create-link/{test_order.id}?method=click", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "url" in data
    
    def test_create_payme_payment_link(self, client: TestClient, test_user: User, test_order: Order, headers: dict):
        """Создание ссылки на оплату Payme"""
        response = client.get(f"/api/payment/create-link/{test_order.id}?method=payme", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "url" in data


class TestCategoriesAPI:
    """Тесты API категорий"""
    
    def test_get_categories(self, client: TestClient, test_category: Category):
        """Получение категорий"""
        response = client.get("/api/categories")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
    
    def test_admin_add_category(self, client: TestClient, admin_headers: dict):
        """Админ добавляет категорию"""
        response = client.post("/api/categories", headers=admin_headers, json={
            "name": "New Category",
            "slug": "new-category"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "New Category"
    
    def test_admin_delete_category(self, client: TestClient, admin_headers: dict, test_category: Category):
        """Админ удаляет категорию"""
        response = client.delete(f"/api/categories/{test_category.id}", headers=admin_headers)
        
        assert response.status_code == 200


class TestPromoCodesAPI:
    """Тесты API промокодов"""
    
    def test_admin_add_promocode(self, client: TestClient, admin_headers: dict):
        """Админ добавляет промокод"""
        response = client.post("/api/promo-codes", headers=admin_headers, json={
            "code": "SALE20",
            "discount_percent": 20,
            "is_active": True
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == "SALE20"
    
    def test_get_promocode(self, client: TestClient, admin_headers: dict):
        """Получение промокода"""
        # Сначала создадим
        client.post("/api/promo-codes", headers=admin_headers, json={
            "code": "TEST10",
            "discount_percent": 10,
            "is_active": True
        })
        
        response = client.get("/api/promo-codes/TEST10")
        
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == "TEST10"
    
    def test_admin_delete_promocode(self, client: TestClient, admin_headers: dict):
        """Админ удаляет промокод"""
        # Создаём
        create_response = client.post("/api/promo-codes", headers=admin_headers, json={
            "code": "DELETE5",
            "discount_percent": 5,
            "is_active": True
        })
        promocode_id = create_response.json()["id"]
        
        # Удаляем
        response = client.delete(f"/api/promo-codes/{promocode_id}", headers=admin_headers)
        
        assert response.status_code == 200
