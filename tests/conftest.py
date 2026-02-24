"""
Конфигурация pytest и общие фикстуры для тестирования UzFlower
"""
import pytest
import os
from typing import Generator, Dict, Any
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from passlib.context import CryptContext

# Импортируем приложение и модели
from main import app, Base, get_db, User, Product, Order, Category, Review
from main import pwd_context, create_access_token

# ============================================================
# Конфигурация тестовой базы данных
# ============================================================

TEST_DATABASE_URL = "sqlite:///./test_uzflower.db"

@pytest.fixture(scope="session")
def test_engine():
    """Создать тестовый движок базы данных"""
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()
    # Удаляем тестовую БД после всех тестов
    if os.path.exists("test_uzflower.db"):
        os.remove("test_uzflower.db")


@pytest.fixture(scope="function")
def db_session(test_engine) -> Generator[Session, None, None]:
    """Создать сессию базы данных для каждого теста"""
    SessionTesting = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = SessionTesting()
    
    # Создаём таблицы перед каждым тестом
    Base.metadata.create_all(bind=test_engine)
    
    try:
        yield session
    finally:
        session.close()
        # Очищаем базу после каждого теста
        Base.metadata.drop_all(bind=test_engine)
        Base.metadata.create_all(bind=test_engine)


@pytest.fixture(scope="function")
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """Создать тестовый клиент с тестовой базой данных"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


# ============================================================
# Фикстуры для тестовых данных
# ============================================================

@pytest.fixture
def test_user(db_session: Session) -> User:
    """Создать тестового пользователя"""
    user = User(
        email="test@example.com",
        hashed_password=pwd_context.hash("testpassword123"),
        full_name="Test User",
        phone="+998901234567",
        is_admin=False,
        bonus_points=100
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_admin(db_session: Session) -> User:
    """Создать тестового админа"""
    admin = User(
        email="admin@example.com",
        hashed_password=pwd_context.hash("adminpassword123"),
        full_name="Admin User",
        phone="+998901234568",
        is_admin=True,
        bonus_points=500
    )
    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)
    return admin


@pytest.fixture
def test_category(db_session: Session) -> Category:
    """Создать тестовую категорию"""
    category = Category(
        name="Test Category",
        slug="test-category"
    )
    db_session.add(category)
    db_session.commit()
    db_session.refresh(category)
    return category


@pytest.fixture
def test_product(db_session: Session, test_category: Category) -> Product:
    """Создать тестовый товар"""
    product = Product(
        name="Test Product",
        price=100000,
        sale_price=80000,
        description="Test product description",
        composition="Roses, ribbon",
        image_url="https://via.placeholder.com/400",
        stock=10,
        is_sale=True,
        is_featured=False,
        is_popular=True,
        category_id=test_category.id,
        price_s=90000,
        price_m=100000,
        price_l=120000
    )
    db_session.add(product)
    db_session.commit()
    db_session.refresh(product)
    return product


@pytest.fixture
def test_order(db_session: Session, test_user: User, test_product: Product) -> Order:
    """Создать тестовый заказ"""
    order = Order(
        user_id=test_user.id,
        total_amount=100000,
        status="pending",
        is_paid=False,
        payment_method="card",
        delivery_address="Test Address, Tashkent",
        phone="+998901234567",
        items='[{"id": 1, "name": "Test Product", "price": 100000, "quantity": 1}]',
        delivery_date="2024-03-08",
        delivery_time="12:00-15:00"
    )
    db_session.add(order)
    db_session.commit()
    db_session.refresh(order)
    return order


@pytest.fixture
def test_review(db_session: Session, test_user: User, test_product: Product) -> Review:
    """Создать тестовый отзыв"""
    review = Review(
        user_id=test_user.id,
        user_name=test_user.full_name,
        product_id=test_product.id,
        product_name=test_product.name,
        text="Great product!",
        rating=5,
        is_approved=True,
        is_verified_purchase=False
    )
    db_session.add(review)
    db_session.commit()
    db_session.refresh(review)
    return review


# ============================================================
# Фикстуры для аутентификации
# ============================================================

@pytest.fixture
def auth_token(test_user: User) -> str:
    """Создать токен авторизации для тестового пользователя"""
    return create_access_token({"sub": test_user.email})


@pytest.fixture
def admin_token(test_admin: User) -> str:
    """Создать токен авторизации для тестового админа"""
    return create_access_token({"sub": test_admin.email})


@pytest.fixture
def headers(auth_token: str) -> Dict[str, str]:
    """Заголовки с токеном авторизации"""
    return {"Authorization": f"Bearer {auth_token}"}


@pytest.fixture
def admin_headers(admin_token: str) -> Dict[str, str]:
    """Заголовки с токеном авторизации админа"""
    return {"Authorization": f"Bearer {admin_token}"}


# ============================================================
# Вспомогательные функции
# ============================================================

@pytest.fixture
def create_test_user(db_session: Session):
    """Фабрика для создания тестовых пользователей"""
    def _create_user(email: str, password: str = "password123", **kwargs) -> User:
        user = User(
            email=email,
            hashed_password=pwd_context.hash(password),
            full_name=kwargs.get("full_name", "Test User"),
            phone=kwargs.get("phone", "+998901234567"),
            is_admin=kwargs.get("is_admin", False),
            bonus_points=kwargs.get("bonus_points", 0)
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        return user
    return _create_user


@pytest.fixture
def create_test_product(db_session: Session, test_category: Category):
    """Фабрика для создания тестовых товаров"""
    def _create_product(name: str, price: float = 100000, **kwargs) -> Product:
        product = Product(
            name=name,
            price=price,
            sale_price=kwargs.get("sale_price"),
            description=kwargs.get("description", "Test description"),
            image_url=kwargs.get("image_url", "https://via.placeholder.com/400"),
            stock=kwargs.get("stock", 10),
            is_sale=kwargs.get("is_sale", False),
            is_featured=kwargs.get("is_featured", False),
            is_popular=kwargs.get("is_popular", False),
            category_id=test_category.id,
            price_s=kwargs.get("price_s", price * 0.9),
            price_m=kwargs.get("price_m", price),
            price_l=kwargs.get("price_l", price * 1.2)
        )
        db_session.add(product)
        db_session.commit()
        db_session.refresh(product)
        return product
    return _create_product
