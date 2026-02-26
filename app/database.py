"""
Database configuration and models for UzFlower.
Вынесено в отдельный модуль для возможности тестирования.

В тестах устанавливайте переменную окружения DATABASE_URL=sqlite:///:memory:
перед импортом этого модуля.
"""
import os
from datetime import datetime
from typing import Generator, Optional, Any

from sqlalchemy import (
    Boolean, Column, DateTime, Float, ForeignKey, Integer,
    String, Text, create_engine, text, event
)
from sqlalchemy.engine import Engine
from sqlalchemy.orm import (
    DeclarativeBase, Session, relationship, sessionmaker
)


# ============================================================
# Database Configuration
# ============================================================

def get_database_url() -> str:
    """Получить URL базы данных из переменной окружения."""
    return os.getenv("DATABASE_URL", "sqlite:///./uzflower.db")


def create_db_engine() -> Engine:
    """Создать engine для подключения к БД."""
    database_url = get_database_url()
    
    # Для SQLite in-memory нужно использовать check_same_thread=False
    # и shared cache для работы в многопоточном режиме
    connect_args = {}
    if database_url.startswith("sqlite"):
        connect_args["check_same_thread"] = False
        # Включаем shared cache для in-memory БД
        if ":memory:" in database_url:
            # Добавляем cache=shared если ещё не добавлен
            if "?" not in database_url:
                database_url = database_url + "?cache=shared"
            elif "cache=" not in database_url:
                database_url = database_url + "&cache=shared"
    
    engine = create_engine(database_url, connect_args=connect_args)
    
    # Включаем FOREIGN KEY для SQLite
    if database_url.startswith("sqlite"):
        @event.listens_for(engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()
    
    return engine


# Создаём engine и SessionLocal
# В тестах DATABASE_URL переопределяется до импорта этого модуля
engine = create_db_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Базовый класс для всех моделей."""
    pass


# ============================================================
# SQLAlchemy Models
# ============================================================

class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    slug = Column(String, unique=True, index=True)

    products = relationship("Product", back_populates="category")


class Courier(Base):
    __tablename__ = "couriers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    phone = Column(String)
    status = Column(String, default="active")  # active, busy, off


class DeliveryZone(Base):
    __tablename__ = "delivery_zones"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True)
    price = Column(Float)


class Banner(Base):
    __tablename__ = "banners"

    id = Column(Integer, primary_key=True, index=True)
    image_url = Column(String, nullable=True)
    video_url = Column(String, nullable=True)
    media_type = Column(String, default="image")  # "image" или "video"
    link = Column(String, nullable=True)
    text = Column(String, nullable=True)  # Сезонный текст на баннере
    subtext = Column(String, nullable=True)  # Подзаголовок
    is_active = Column(Boolean, default=True)


class ProductImage(Base):
    __tablename__ = "product_images"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    url = Column(String)

    product = relationship("Product", back_populates="images")


class PromoCode(Base):
    __tablename__ = "promo_codes"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, index=True)
    discount_percent = Column(Integer)
    is_active = Column(Boolean, default=True)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    full_name = Column(String)
    phone = Column(String, nullable=True)
    is_admin = Column(Boolean, default=False)
    is_blocked = Column(Boolean, default=False)
    bonus_points = Column(Integer, default=0)
    image_url = Column(String, nullable=True)

    orders = relationship("Order", back_populates="owner")
    reviews = relationship("Review", back_populates="user", cascade="all, delete-orphan")
    addresses = relationship("UserAddress", back_populates="user", cascade="all, delete-orphan")
    favorites = relationship("Favorite", back_populates="user", cascade="all, delete-orphan")
    bonus_transactions = relationship("BonusTransaction", back_populates="user", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    reminders = relationship("Reminder", back_populates="user", cascade="all, delete-orphan")
    saved_cards = relationship("SavedCard", back_populates="user", cascade="all, delete-orphan")


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    price = Column(Float)
    sale_price = Column(Float, nullable=True)
    description = Column(Text, nullable=True)
    composition = Column(Text, nullable=True)
    image_url = Column(String, nullable=True)
    stock = Column(Integer, default=0)
    is_sale = Column(Boolean, default=False)
    is_featured = Column(Boolean, default=False)
    is_popular = Column(Boolean, default=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)

    # Size pricing
    price_s = Column(Float, nullable=True)
    price_m = Column(Float, nullable=True)
    price_l = Column(Float, nullable=True)

    width = Column(Float, nullable=True)
    height = Column(Float, nullable=True)

    category = relationship("Category", back_populates="products")
    images = relationship("ProductImage", back_populates="product")
    reviews = relationship("Review", back_populates="product", cascade="all, delete-orphan")
    favorites = relationship("Favorite", back_populates="product", cascade="all, delete-orphan")


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    total_amount = Column(Float)
    status = Column(String, default="pending")  # pending, processing, shipping, completed, cancelled
    is_paid = Column(Boolean, default=False)
    payment_method = Column(String, default="card")
    courier_id = Column(Integer, nullable=True)
    delivery_address = Column(String)
    phone = Column(String)
    items = Column(Text, nullable=True)

    delivery_date = Column(String, nullable=True)
    delivery_time = Column(String, nullable=True)
    postcard_text = Column(Text, nullable=True)
    comment = Column(Text, nullable=True)
    promo_code_used = Column(String, nullable=True)

    payment_status = Column(String, default="waiting")  # waiting, payed, error
    external_id = Column(String, nullable=True)  # ID транзакции в Click/Payme
    lat = Column(Float, nullable=True)
    lng = Column(Float, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    owner = relationship("User", back_populates="orders")
    reviews = relationship("Review", back_populates="order", cascade="all, delete-orphan")


class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    user_name = Column(String)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True)
    product_name = Column(String)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=True)
    text = Column(Text)
    rating = Column(Integer)
    is_approved = Column(Boolean, default=True)  # Модерация
    is_verified_purchase = Column(Boolean, default=False)  # Проверенная покупка
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="reviews")
    product = relationship("Product", back_populates="reviews")
    order = relationship("Order", back_populates="reviews")
    images = relationship("ReviewImage", back_populates="review")


class SupportMessage(Base):
    __tablename__ = "support_messages"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    message = Column(Text)
    is_admin = Column(Boolean, default=False)  # True if message is from admin
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class UserAddress(Base):
    __tablename__ = "user_addresses"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String, nullable=True)  # "Дом", "Работа", "Дача"
    address = Column(String)
    phone = Column(String)
    recipient_name = Column(String)
    lat = Column(Float, nullable=True)
    lng = Column(Float, nullable=True)
    is_default = Column(Boolean, default=False)

    user = relationship("User", back_populates="addresses")


class Favorite(Base):
    __tablename__ = "favorites"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="favorites")
    product = relationship("Product", back_populates="favorites")


class BonusTransaction(Base):
    __tablename__ = "bonus_transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    amount = Column(Integer)  # Положительный - начисление, отрицательный - списание
    description = Column(String)
    order_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="bonus_transactions")


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String)
    message = Column(Text)
    type = Column(String, default="info")  # info, order, promo, reminder
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="notifications")


class Reminder(Base):
    __tablename__ = "reminders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String)
    date = Column(String)  # YYYY-MM-DD
    recipient_name = Column(String)
    recipient_phone = Column(String, nullable=True)
    is_recurring = Column(Boolean, default=False)
    recurring_type = Column(String, nullable=True)  # yearly, monthly
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="reminders")


class SavedCard(Base):
    __tablename__ = "saved_cards"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    card_last_four = Column(String)
    card_type = Column(String)  # visa, mastercard, etc.
    is_default = Column(Boolean, default=False)

    user = relationship("User", back_populates="saved_cards")


class ReviewImage(Base):
    __tablename__ = "review_images"

    id = Column(Integer, primary_key=True, index=True)
    review_id = Column(Integer, ForeignKey("reviews.id"))
    url = Column(String)

    review = relationship("Review", back_populates="images")


# ============================================================
# Dependency Injection
# ============================================================

def get_db() -> Generator[Session, None, None]:
    """
    Dependency для получения сессии БД.
    Переопределяется в тестах через override_dependencies.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ============================================================
# Helper Functions
# ============================================================

def init_db_tables(engine_override=None):
    """
    Создать все таблицы в БД.
    Используется в тестах для инициализации in-memory БД.
    """
    target_engine = engine_override or engine
    Base.metadata.create_all(bind=target_engine)


def drop_db_tables(engine_override=None):
    """
    Удалить все таблицы из БД.
    Используется в тестах для очистки in-memory БД.
    """
    target_engine = engine_override or engine
    Base.metadata.drop_all(bind=target_engine)
