"""
Pytest configuration and fixtures for UzFlower tests.

Использует SQLite in-memory базу для изоляции тестов.
Каждый тест работает с чистой БД.

Запуск:
    pytest --cov=app

GitHub Actions:
    DATABASE_URL=sqlite:///:memory: pytest --cov=app
"""
# Импортируем test_config ПЕРВЫМ для установки DATABASE_URL
from tests.test_config import TEST_DATABASE_URL

import os
from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, Session

# Теперь импортируем модели из app.database (он использует DATABASE_URL)
from app.database import (
    Base,
    get_db,
    User,
    Category,
    Product,
    Order,
    Review,
    Banner,
    PromoCode,
    Favorite,
    Notification,
    Reminder,
    BonusTransaction,
    UserAddress,
    SavedCard,
    DeliveryZone,
    Courier,
    SupportMessage,
    ProductImage,
    ReviewImage,
)

# Импортируем модуль database для переопределения
import app.database as db_module


# ============================================================
# Create test engine and session factory
# ============================================================

# Создаём тестовый engine
test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False
)

# SessionFactory для тестовой БД
TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=test_engine,
    class_=Session
)

# ============================================================
# Создаём таблицы один раз при загрузке модуля
# ============================================================
Base.metadata.create_all(bind=test_engine)


def _clean_test_database():
    """Очистка тестовой БД."""
    db = TestingSessionLocal()
    try:
        # Включаем FOREIGN KEY constraints для этой сессии
        db.execute(text("PRAGMA foreign_keys=ON"))
        
        from sqlalchemy import inspect
        inspector = inspect(test_engine)
        try:
            inspector.get_columns("users")
        except Exception:
            # Таблицы ещё не созданы
            return

        # Очищаем все таблицы
        tables_to_clean = [
            "review_images", "reviews", "bonus_transactions", "favorites",
            "user_addresses", "saved_cards", "notifications", "reminders",
            "support_messages", "orders", "product_images", "products",
            "promo_codes", "banners", "delivery_zones", "couriers",
            "categories", "users",
        ]

        db.execute(text("PRAGMA foreign_keys=OFF"))
        for table in tables_to_clean:
            try:
                db.execute(text(f"DELETE FROM {table}"))
            except Exception:
                pass
        db.execute(text("PRAGMA foreign_keys=ON"))
        db.commit()
    finally:
        db.close()


# ============================================================
# Pytest Fixtures
# ============================================================


@pytest.fixture(autouse=True)
def _clean_db_before_test():
    """
    Автоматическая очистка БД перед КАЖДЫМ тестом.
    Гарантирует изоляцию тестов.
    """
    _clean_test_database()
    yield


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    """
    Фикстура для прямого доступа к сессии БД в тестах.
    Используется для unit-тестов моделей.
    """
    db = TestingSessionLocal()
    try:
        # Включаем FOREIGN KEY constraints
        db.execute(text("PRAGMA foreign_keys=ON"))
        yield db
    finally:
        db.close()


# Глобальные переменные для хранения оригинальных значений
_original_session_local = None
_original_engine = None

@pytest.fixture(scope="function")
def client():
    """
    TestClient для HTTP-тестов API.
    
    Использование:
        def test_create_user(client: TestClient):
            response = client.post("/api/auth/register", json={...})
            assert response.status_code == 200
    """
    global _original_session_local, _original_engine
    
    # Переопределяем зависимости ДО импорта main
    _original_session_local = db_module.SessionLocal
    _original_engine = db_module.engine
    db_module.SessionLocal = TestingSessionLocal
    db_module.engine = test_engine

    from main import app
    
    def override_get_db() -> Generator[Session, None, None]:
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()
    
    app.dependency_overrides[get_db] = override_get_db
    
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        # Сбрасываем переопределение
        app.dependency_overrides.clear()
        db_module.SessionLocal = _original_session_local
        db_module.engine = _original_engine


# ============================================================
# Helper Fixtures for Test Data
# ============================================================

@pytest.fixture
def test_user_data() -> dict:
    """Базовые данные тестового пользователя."""
    return {
        "email": "test@example.com",
        "password": "testpassword123",
        "full_name": "Test User"
    }


@pytest.fixture
def test_category_data() -> dict:
    """Базовые данные тестовой категории."""
    return {
        "name": "Тестовые цветы",
        "slug": "test-flowers"
    }


@pytest.fixture
def test_product_data() -> dict:
    """Базовые данные тестового продукта."""
    return {
        "name": "Тестовый букет",
        "price": 100000,
        "description": "Описание тестового букета",
        "composition": "Розы, упаковка",
        "stock": 10
    }


@pytest.fixture
def test_order_data() -> dict:
    """Базовые данные тестового заказа."""
    return {
        "total_amount": 100000,
        "delivery_address": "г. Ташкент, ул. Тестовая, 1",
        "phone": "+998901234567",
        "delivery_date": "2026-03-01",
        "delivery_time": "14:00-18:00"
    }


@pytest.fixture
def created_user(db_session: Session, test_user_data: dict) -> User:
    """Созданный тестовый пользователь в БД."""
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    user = User(
        email=test_user_data["email"],
        hashed_password=pwd_context.hash(test_user_data["password"]),
        full_name=test_user_data["full_name"]
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def created_category(db_session: Session, test_category_data: dict) -> Category:
    """Созданная тестовая категория в БД."""
    category = Category(
        name=test_category_data["name"],
        slug=test_category_data["slug"]
    )
    db_session.add(category)
    db_session.commit()
    db_session.refresh(category)
    return category


@pytest.fixture
def created_product(
    db_session: Session,
    test_product_data: dict,
    created_category: Category
) -> Product:
    """Созданный тестовый продукт в БД."""
    product = Product(
        name=test_product_data["name"],
        price=test_product_data["price"],
        description=test_product_data["description"],
        composition=test_product_data["composition"],
        stock=test_product_data["stock"],
        category_id=created_category.id
    )
    db_session.add(product)
    db_session.commit()
    db_session.refresh(product)
    return product


@pytest.fixture
def created_order(
    db_session: Session,
    test_order_data: dict,
    created_user: User
) -> Order:
    """Созданный тестовый заказ в БД."""
    order = Order(
        user_id=created_user.id,
        total_amount=test_order_data["total_amount"],
        delivery_address=test_order_data["delivery_address"],
        phone=test_order_data["phone"],
        delivery_date=test_order_data["delivery_date"],
        delivery_time=test_order_data["delivery_time"],
        items='[{"product_id": 1, "quantity": 1}]'
    )
    db_session.add(order)
    db_session.commit()
    db_session.refresh(order)
    return order
