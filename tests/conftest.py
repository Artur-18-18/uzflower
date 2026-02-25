import pytest
import os
import sys
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import Base, User, Product, Order, Category, Review, ReviewImage


def pytest_configure(config):
    config.addinivalue_line("markers", "unit: mark test as a unit test")
    config.addinivalue_line("markers", "integration: mark test as an integration test")
    config.addinivalue_line("markers", "slow: mark test as slow")


@pytest.fixture(scope="function")
def test_db_engine():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session(test_db_engine) -> Generator[Session, None, None]:
    connection = test_db_engine.connect()
    transaction = connection.begin()
    session = sessionmaker(autocommit=False, autoflush=False, bind=connection)()
    yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def sample_category(db_session: Session):
    category = Category(name="Букеты", slug="bukets")
    db_session.add(category)
    db_session.commit()
    return category


@pytest.fixture
def sample_product(db_session: Session, sample_category: Category):
    product = Product(
        name="Роза красная",
        price=50000.0,
        sale_price=40000.0,
        description="Букет из красных роз",
        composition="Роза красная - 7 шт",
        stock=20,
        is_sale=True,
        category_id=sample_category.id,
    )
    db_session.add(product)
    db_session.commit()
    return product


@pytest.fixture
def sample_user(db_session: Session):
    user = User(
        email="test@example.com",
        hashed_password="hashed_password",
        full_name="Test User",
        phone="+998901234567",
        is_admin=False,
        bonus_points=100,
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def sample_order(db_session: Session, sample_user: User, sample_product: Product):
    order = Order(
        user_id=sample_user.id,
        total_amount=50000.0,
        status="pending",
        delivery_address="Ташкент",
        phone="+998901234567",
    )
    db_session.add(order)
    db_session.commit()
    return order
