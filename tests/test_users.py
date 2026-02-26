"""
Unit tests for User model and User API endpoints.

Тесты покрывают:
- Создание пользователя
- Валидацию данных
- Уникальность email
- Связи с другими моделями
"""
import pytest
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient
from passlib.context import CryptContext

from app.database import User, Order, Review, Favorite, UserAddress, Product


# ============================================================
# Unit Tests: User Model
# ============================================================

class TestUserModel:
    """Тесты модели User на уровне БД."""

    def test_create_user(self, db_session: Session, test_user_data: dict):
        """Тест: создание пользователя с корректными данными."""
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        
        user = User(
            email=test_user_data["email"],
            hashed_password=pwd_context.hash(test_user_data["password"]),
            full_name=test_user_data["full_name"]
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        assert user.id is not None
        assert user.email == test_user_data["email"]
        assert user.full_name == test_user_data["full_name"]
        assert user.bonus_points == 0
        assert user.is_admin is False
        assert user.is_blocked is False

    def test_user_unique_email(self, db_session: Session, test_user_data: dict):
        """Тест: попытка создания пользователя с существующим email."""
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        
        # Создаём первого пользователя
        user1 = User(
            email=test_user_data["email"],
            hashed_password=pwd_context.hash(test_user_data["password"]),
            full_name=test_user_data["full_name"]
        )
        db_session.add(user1)
        db_session.commit()
        
        # Пытаемся создать второго с тем же email
        user2 = User(
            email=test_user_data["email"],
            hashed_password=pwd_context.hash("anotherpassword"),
            full_name="Another User"
        )
        db_session.add(user2)
        
        with pytest.raises(Exception):  # IntegrityError
            db_session.commit()

    def test_user_default_values(self, db_session: Session, test_user_data: dict):
        """Тест: значения по умолчанию для полей пользователя."""
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        
        user = User(
            email=test_user_data["email"],
            hashed_password=pwd_context.hash(test_user_data["password"]),
            full_name=test_user_data["full_name"]
        )
        db_session.add(user)
        db_session.commit()
        
        assert user.phone is None
        assert user.image_url is None
        assert user.bonus_points == 0
        assert user.is_admin is False
        assert user.is_blocked is False

    def test_user_password_hashing(self, db_session: Session, test_user_data: dict):
        """Тест: хеширование пароля."""
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        
        password = "my_secure_password"
        user = User(
            email=test_user_data["email"],
            hashed_password=pwd_context.hash(password),
            full_name=test_user_data["full_name"]
        )
        db_session.add(user)
        db_session.commit()
        
        # Пароль должен быть захеширован
        assert user.hashed_password != password
        assert pwd_context.verify(password, user.hashed_password)
        assert not pwd_context.verify("wrong_password", user.hashed_password)


# ============================================================
# Integration Tests: User API
# ============================================================

class TestUserAPI:
    """Тесты API пользователей."""

    def test_register_user(self, client: TestClient, test_user_data: dict):
        """Тест: регистрация нового пользователя."""
        response = client.post("/api/auth/register", json=test_user_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_user_data["email"]
        assert data["full_name"] == test_user_data["full_name"]
        assert "id" in data

    def test_register_duplicate_email(self, client: TestClient, test_user_data: dict):
        """Тест: регистрация с существующим email."""
        # Регистрируем первого пользователя
        client.post("/api/auth/register", json=test_user_data)
        
        # Пытаемся зарегистрировать второго с тем же email
        response = client.post("/api/auth/register", json=test_user_data)
        
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"]

    def test_login_success(self, client: TestClient, test_user_data: dict):
        """Тест: успешный вход пользователя."""
        # Сначала регистрируемся
        client.post("/api/auth/register", json=test_user_data)
        
        # Теперь входим
        login_data = {
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        }
        response = client.post("/api/auth/login", json=login_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["email"] == test_user_data["email"]

    def test_login_wrong_password(self, client: TestClient, test_user_data: dict):
        """Тест: вход с неправильным паролем."""
        # Регистрируемся
        client.post("/api/auth/register", json=test_user_data)
        
        # Пытаемся войти с неправильным паролем
        login_data = {
            "email": test_user_data["email"],
            "password": "wrong_password"
        }
        response = client.post("/api/auth/login", json=login_data)
        
        assert response.status_code == 400
        assert "Invalid" in response.json()["detail"]

    def test_login_nonexistent_user(self, client: TestClient):
        """Тест: вход несуществующего пользователя."""
        login_data = {
            "email": "nonexistent@example.com",
            "password": "anypassword"
        }
        response = client.post("/api/auth/login", json=login_data)
        
        assert response.status_code == 400

    def test_get_profile_authenticated(self, client: TestClient, test_user_data: dict):
        """Тест: получение профиля авторизованным пользователем."""
        # Регистрируемся и получаем токен
        client.post("/api/auth/register", json=test_user_data)
        login_response = client.post("/api/auth/login", json={
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        })
        token = login_response.json()["access_token"]
        
        # Получаем профиль
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/profile/me", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_user_data["email"]
        assert data["full_name"] == test_user_data["full_name"]

    def test_get_profile_unauthenticated(self, client: TestClient):
        """Тест: получение профиля без авторизации."""
        response = client.get("/api/profile/me")
        
        assert response.status_code == 401


# ============================================================
# Tests: User Relationships
# ============================================================

class TestUserRelationships:
    """Тесты связей пользователя с другими моделями."""

    def test_user_orders_relationship(self, db_session: Session, created_user: User):
        """Тест: связь пользователя с заказами."""
        order = Order(
            user_id=created_user.id,
            total_amount=50000,
            delivery_address="Test Address",
            phone="+998901234567"
        )
        db_session.add(order)
        db_session.commit()
        
        # Проверяем связь через relationship
        db_session.refresh(created_user)
        assert len(created_user.orders) == 1
        assert created_user.orders[0].id == order.id

    def test_user_favorites_relationship(self, db_session: Session, created_user: User, created_product: Product):
        """Тест: связь пользователя с избранным."""
        favorite = Favorite(
            user_id=created_user.id,
            product_id=created_product.id
        )
        db_session.add(favorite)
        db_session.commit()
        
        db_session.refresh(created_user)
        assert len(created_user.favorites) == 1
        assert created_user.favorites[0].product_id == created_product.id

    def test_user_addresses_relationship(self, db_session: Session, created_user: User):
        """Тест: связь пользователя с адресами."""
        address = UserAddress(
            user_id=created_user.id,
            title="Дом",
            address="г. Ташкент, ул. Тестовая, 1",
            phone="+998901234567",
            recipient_name="Test User"
        )
        db_session.add(address)
        db_session.commit()
        
        db_session.refresh(created_user)
        assert len(created_user.addresses) == 1
        assert created_user.addresses[0].title == "Дом"

    def test_user_reviews_relationship(self, db_session: Session, created_user: User, created_product: Product):
        """Тест: связь пользователя с отзывами."""
        review = Review(
            user_id=created_user.id,
            user_name=created_user.full_name,
            product_id=created_product.id,
            product_name=created_product.name,
            text="Отличный продукт!",
            rating=5
        )
        db_session.add(review)
        db_session.commit()
        
        db_session.refresh(created_user)
        assert len(created_user.reviews) == 1
        assert created_user.reviews[0].text == "Отличный продукт!"
