import base64
import hashlib
import json
import logging
import os
import shutil
from contextlib import asynccontextmanager
from datetime import datetime
from typing import List, Optional

from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.security import OAuth2PasswordBearer
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from sqlalchemy.orm import Session

# ============================================================
# Настройка логгера — все события пишутся в server_debug.log
# и одновременно выводятся в консоль
# ============================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("server_debug.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# --- Database Setup ---
# Импортируем модели и зависимости из app.database
# Для тестов DATABASE_URL переопределяется через переменную окружения
from app.database import (
    Base,
    BonusTransaction,
    Banner,
    Category,
    Courier,
    DeliveryZone,
    Favorite,
    Notification,
    Order,
    Product,
    ProductImage,
    PromoCode,
    Reminder,
    Review,
    ReviewImage,
    SavedCard,
    SessionLocal,
    SupportMessage,
    User,
    UserAddress,
    engine,
    get_db,
    init_db_tables,
)

# ============================================================
# Helper Functions
# ============================================================

def create_notification(db: Session, user_id: int, title: str, message: str, notification_type: str = "info"):
    """Создать уведомление для пользователя"""
    try:
        notification = Notification(
            user_id=user_id,
            title=title,
            message=message,
            type=notification_type
        )
        db.add(notification)
        db.commit()
        logger.info("🔔 Уведомление создано для пользователя #%s: %s", user_id, title)
    except Exception as e:
        logger.error("Ошибка при создании уведомления: %s", e)
        db.rollback()

def add_bonus_points(db: Session, user_id: int, amount: int, description: str, order_id: Optional[int] = None):
    """Начислить бонусы пользователю с созданием уведомления"""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return

        # Начисляем бонусы
        user.bonus_points += amount

        # Создаем запись о транзакции
        transaction = BonusTransaction(
            user_id=user_id,
            amount=amount,
            description=description,
            order_id=order_id
        )
        db.add(transaction)

        # Создаем уведомление
        create_notification(
            db=db,
            user_id=user_id,
            title="🎁 Бонусы начислены",
            message=f"{description}. Вам начислено {amount} бонусов",
            notification_type="bonus"
        )

        db.commit()
        logger.info("⭐ Начислено %s бонусов пользователю #%s", amount, user_id)
    except Exception as e:
        logger.error("Ошибка при начислении бонусов: %s", e)
        db.rollback()

# --- Security ---
# Silence passlib warnings about bcrypt version
logging.getLogger("passlib").setLevel(logging.ERROR)

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__truncate_error=True
)

SECRET_KEY = "uzflower-super-secret-key-2026" # В проде менять на переменную окружения
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 43200 # 30 дней

# --- Payment Settings (Замените на реальные в продакшене) ---
CLICK_SERVICE_ID = "YOUR_CLICK_SERVICE_ID"
CLICK_MERCHANT_ID = "YOUR_CLICK_MERCHANT_ID"
CLICK_SECRET_KEY = "YOUR_CLICK_SECRET_KEY"

PAYME_MERCHANT_ID = "YOUR_PAYME_MERCHANT_ID"
PAYME_SECRET_KEY = "YOUR_PAYME_SECRET_KEY"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login", auto_error=False)

def create_access_token(data: dict):
    to_encode = data.copy()
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(token: Optional[str] = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    if not token:
        return None  # Анонимный пользователь
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            return None
    except JWTError:
        return None
    user = db.query(User).filter(User.email == email).first()
    return user

async def get_current_admin(current_user: Optional[User] = Depends(get_current_user)):
    if not current_user or not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not an admin")
    return current_user

# --- Schemas ---
class UserCreate(BaseModel):
    email: str
    password: str
    full_name: str

class UserLogin(BaseModel):
    email: str
    password: str

class CategoryBase(BaseModel):
    name: str
    slug: str

class PromoCodeBase(BaseModel):
    code: str
    discount_percent: float
    is_active: bool = True

class ProductBase(BaseModel):
    name: str
    price: float
    sale_price: Optional[float] = None
    description: Optional[str] = None
    composition: Optional[str] = None
    image_url: Optional[str] = None
    stock: int = 0
    is_sale: bool = False
    is_featured: bool = False
    is_popular: bool = False
    category_id: Optional[int] = None
    price_s: Optional[float] = None
    price_m: Optional[float] = None
    price_l: Optional[float] = None
    width: Optional[float] = None
    height: Optional[float] = None

class OrderCreate(BaseModel):
    total_amount: float
    delivery_address: str
    phone: str
    items: Optional[str] = None
    delivery_date: Optional[str] = None
    delivery_time: Optional[str] = None
    postcard_text: Optional[str] = None
    comment: Optional[str] = None
    promo_code_used: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None

class SupportMessageCreate(BaseModel):
    user_id: int
    message: str

class SupportReply(BaseModel):
    user_id: int
    message: str

# --- Profile Schemas ---
class UserProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None

class PasswordChange(BaseModel):
    current_password: str
    new_password: str

class UserAddressCreate(BaseModel):
    title: Optional[str] = None
    address: str
    phone: str
    recipient_name: str
    lat: Optional[float] = None
    lng: Optional[float] = None
    is_default: bool = False

class UserAddressUpdate(BaseModel):
    title: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    recipient_name: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    is_default: Optional[bool] = None

class FavoriteCreate(BaseModel):
    product_id: int

class BonusTransactionCreate(BaseModel):
    amount: int
    description: str
    order_id: Optional[int] = None

class NotificationCreate(BaseModel):
    title: str
    message: str
    type: str = "info"

class ReminderCreate(BaseModel):
    title: str
    date: str
    recipient_name: str
    recipient_phone: Optional[str] = None
    is_recurring: bool = False
    recurring_type: Optional[str] = None

class ReminderUpdate(BaseModel):
    title: Optional[str] = None
    date: Optional[str] = None
    recipient_name: Optional[str] = None
    recipient_phone: Optional[str] = None
    is_recurring: Optional[bool] = None
    recurring_type: Optional[str] = None
    is_active: Optional[bool] = None

class ReviewCreate(BaseModel):
    user_name: str
    product_name: str
    text: str
    rating: int
    image_urls: Optional[List[str]] = None

class SavedCardCreate(BaseModel):
    card_last_four: str
    card_type: str
    is_default: bool = False

# --- Lifespan ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    # Используем db_module для поддержки переопределения в тестах
    import app.database as db_module

    db = db_module.SessionLocal()

    # --- Migrations: Add new columns if missing ---
    from sqlalchemy import inspect, text
    from sqlalchemy.exc import NoSuchTableError
    
    inspector = inspect(db_module.engine)

    # Проверяем существует ли таблица users
    try:
        inspector.get_columns("users")
    except NoSuchTableError:
        # Таблицы не существуют - создаём их
        # Это происходит в тестах где таблицы создаются через conftest
        db.close()
        yield
        return

    # Users table
    user_cols = [c['name'] for c in inspector.get_columns("users")]
    if 'bonus_points' not in user_cols:
        db.execute(text("ALTER TABLE users ADD COLUMN bonus_points INTEGER DEFAULT 0"))
    if 'is_blocked' not in user_cols:
        db.execute(text("ALTER TABLE users ADD COLUMN is_blocked BOOLEAN DEFAULT 0"))
    if 'phone' not in user_cols:
        db.execute(text("ALTER TABLE users ADD COLUMN phone TEXT"))
    if 'image_url' not in user_cols:
        db.execute(text("ALTER TABLE users ADD COLUMN image_url TEXT"))
    db.commit()

    # Products table
    prod_cols = [c['name'] for c in inspector.get_columns("products")]
    if 'is_popular' not in prod_cols:
        db.execute(text("ALTER TABLE products ADD COLUMN is_popular BOOLEAN DEFAULT 0"))
    if 'category_id' not in prod_cols:
        db.execute(text("ALTER TABLE products ADD COLUMN category_id INTEGER REFERENCES categories(id)"))
    if 'price_s' not in prod_cols:
        db.execute(text("ALTER TABLE products ADD COLUMN price_s FLOAT"))
    if 'price_m' not in prod_cols:
        db.execute(text("ALTER TABLE products ADD COLUMN price_m FLOAT"))
    if 'price_l' not in prod_cols:
        db.execute(text("ALTER TABLE products ADD COLUMN price_l FLOAT"))
    db.commit()

    # Orders table
    order_cols = [c['name'] for c in inspector.get_columns("orders")]
    if 'delivery_date' not in order_cols:
        db.execute(text("ALTER TABLE orders ADD COLUMN delivery_date TEXT"))
    if 'delivery_time' not in order_cols:
        db.execute(text("ALTER TABLE orders ADD COLUMN delivery_time TEXT"))
    if 'postcard_text' not in order_cols:
        db.execute(text("ALTER TABLE orders ADD COLUMN postcard_text TEXT"))
    if 'is_paid' not in order_cols:
        db.execute(text("ALTER TABLE orders ADD COLUMN is_paid BOOLEAN DEFAULT 0"))
    if 'payment_method' not in order_cols:
        db.execute(text("ALTER TABLE orders ADD COLUMN payment_method TEXT DEFAULT 'card'"))
    if 'courier_id' not in order_cols:
        db.execute(text("ALTER TABLE orders ADD COLUMN courier_id INTEGER"))
    if 'payment_status' not in order_cols:
        db.execute(text("ALTER TABLE orders ADD COLUMN payment_status TEXT DEFAULT 'waiting'"))
    if 'lat' not in order_cols:
        db.execute(text("ALTER TABLE orders ADD COLUMN lat FLOAT"))
    if 'lng' not in order_cols:
        db.execute(text("ALTER TABLE orders ADD COLUMN lng FLOAT"))
    if 'external_id' not in order_cols:
        db.execute(text("ALTER TABLE orders ADD COLUMN external_id TEXT"))
    db.commit()

    if 'comment' not in order_cols:
        db.execute(text("ALTER TABLE orders ADD COLUMN comment TEXT"))
    if 'promo_code_used' not in order_cols:
        db.execute(text("ALTER TABLE orders ADD COLUMN promo_code_used TEXT"))
    db.commit()

    # Banners table
    banner_cols = [c['name'] for c in inspector.get_columns("banners")]
    if 'video_url' not in banner_cols:
        db.execute(text("ALTER TABLE banners ADD COLUMN video_url TEXT"))
    if 'media_type' not in banner_cols:
        db.execute(text("ALTER TABLE banners ADD COLUMN media_type TEXT DEFAULT 'image'"))
    if 'text' not in banner_cols:
        db.execute(text("ALTER TABLE banners ADD COLUMN text TEXT"))
    if 'subtext' not in banner_cols:
        db.execute(text("ALTER TABLE banners ADD COLUMN subtext TEXT"))
    db.commit()

    # --- Seed Logic ---
    if db.query(User).count() == 0:
        admin = User(
            email="admin@test.com",
            hashed_password=pwd_context.hash("admin123"),
            full_name="Администратор",
            is_admin=True
        )
        db.add(admin)
        db.commit()

    # --- Seed Categories ---
    if db.query(Category).count() == 0:
        cats = [
            Category(name="8 Марта", slug="8-march"),
            Category(name="День рождения", slug="birthday"),
            Category(name="Романтика", slug="romance"),
            Category(name="Свадьба", slug="wedding"),
            Category(name="Корпоративные", slug="corporate"),
            Category(name="Цветы в коробке", slug="box-flowers"),
        ]
        db.add_all(cats)
        db.commit()

    if db.query(Product).count() == 0:
        cat_romance = db.query(Category).filter_by(slug="romance").first()
        p1 = Product(
            name="Букет из клубники",
            price=350000,
            price_s=250000,
            price_m=350000,
            price_l=500000,
            image_url="https://images.unsplash.com/photo-1591017403986-ed8184539f16?w=500",
            description="Свежая клубника в шоколаде",
            composition="Клубника 25 шт, шоколад молочный, посыпка",
            is_sale=False,
            is_featured=True,
            is_popular=True,
            category_id=cat_romance.id if cat_romance else None,
            stock=10
        )
        p2 = Product(
            name="Красные розы",
            price=250000,
            price_s=150000,
            price_m=250000,
            price_l=400000,
            image_url="https://images.unsplash.com/photo-1548610762-65603758ee75?w=500",
            description="Прекрасный букет алых роз",
            composition="Розы красные 25 шт, лента",
            is_sale=True,
            sale_price=190000,
            is_featured=True,
            category_id=cat_romance.id if cat_romance else None,
            stock=5
        )
        db.add(p1)
        db.add(p2)
        db.commit()

    # --- Migrations for Profile Extended Tables ---
    # Create new tables if not exist
    try:
        # Check if tables exist by querying them
        db.execute(text("SELECT 1 FROM user_addresses LIMIT 1"))
    except Exception:
        # Tables don't exist - create them
        Base.metadata.create_all(bind=db_module.engine)
        db.commit()

    # --- Migrations for Reviews ---
    review_cols = [c['name'] for c in inspector.get_columns("reviews")]
    if 'user_id' not in review_cols:
        db.execute(text("ALTER TABLE reviews ADD COLUMN user_id INTEGER REFERENCES users(id)"))
    if 'product_id' not in review_cols:
        db.execute(text("ALTER TABLE reviews ADD COLUMN product_id INTEGER REFERENCES products(id)"))
    if 'order_id' not in review_cols:
        db.execute(text("ALTER TABLE reviews ADD COLUMN order_id INTEGER REFERENCES orders(id)"))
    if 'is_approved' not in review_cols:
        db.execute(text("ALTER TABLE reviews ADD COLUMN is_approved BOOLEAN DEFAULT 1"))
    if 'is_verified_purchase' not in review_cols:
        db.execute(text("ALTER TABLE reviews ADD COLUMN is_verified_purchase BOOLEAN DEFAULT 0"))
    db.commit()

    db.close()
    yield
    # Shutdown logic if needed

# --- FastAPI App ---
app = FastAPI(lifespan=lifespan)

if not os.path.exists("static/uploads"):
    os.makedirs("static/uploads")

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# ============================================================
# CORS Middleware - разрешаем запросы с любых доменов
# ============================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене лучше указать конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Auth API ---
@app.post("/api/auth/register")
async def register(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_password = pwd_context.hash(user.password)
    new_user = User(email=user.email, hashed_password=hashed_password, full_name=user.full_name)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"id": new_user.id, "email": new_user.email, "full_name": new_user.full_name}

@app.post("/api/auth/login")
async def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if not db_user or not pwd_context.verify(user.password, db_user.hashed_password):
        raise HTTPException(status_code=400, detail="Invalid email or password")

    token = create_access_token({"sub": db_user.email})
    logger.info("🔐 Вход: %s (admin=%s)", db_user.email, db_user.is_admin)

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": db_user.id,
            "email": db_user.email,
            "full_name": db_user.full_name,
            "is_admin": db_user.is_admin,
            "bonus_points": db_user.bonus_points
        }
    }

# ============================================
# --- PROFILE API ---
# ============================================

@app.get("/api/profile/me")
async def get_profile(current_user: User = Depends(get_current_user)):
    """Получить данные текущего пользователя"""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return {
        "id": current_user.id,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "phone": current_user.phone,
        "bonus_points": current_user.bonus_points,
        "is_admin": current_user.is_admin,
        "addresses": [
            {
                "id": a.id,
                "title": a.title,
                "address": a.address,
                "phone": a.phone,
                "recipient_name": a.recipient_name,
                "lat": a.lat,
                "lng": a.lng,
                "is_default": a.is_default
            } for a in current_user.addresses
        ],
        "saved_cards": [
            {
                "id": c.id,
                "card_last_four": c.card_last_four,
                "card_type": c.card_type,
                "is_default": c.is_default
            } for c in current_user.saved_cards
        ]
    }

@app.put("/api/profile/me")
async def update_profile(
    profile_data: UserProfileUpdate,
    current_user: User = Depends(get_current_user)
):
    """Обновить данные профиля"""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    db = SessionLocal()
    try:
        # Merge the object into this session
        current_user = db.merge(current_user)

        update_data = profile_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(current_user, key, value)

        db.commit()
        db.refresh(current_user)

        logger.info("👤 Профиль обновлен: %s", current_user.email)
        return {
            "id": current_user.id,
            "email": current_user.email,
            "full_name": current_user.full_name,
            "phone": current_user.phone,
            "bonus_points": current_user.bonus_points
        }
    finally:
        db.close()

@app.post("/api/profile/change-password")
async def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_user)
):
    """Изменить пароль"""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    if not pwd_context.verify(password_data.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Current password is incorrect")

    db = SessionLocal()
    try:
        current_user = db.merge(current_user)
        current_user.hashed_password = pwd_context.hash(password_data.new_password)
        db.commit()

        logger.info("🔑 Пароль изменен для: %s", current_user.email)
        return {"detail": "Password changed successfully"}
    finally:
        db.close()

@app.post("/api/profile/upload-avatar")
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """Загрузить фото профиля"""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    # Проверка типа файла
    allowed_extensions = [".jpg", ".jpeg", ".png", ".webp"]
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in allowed_extensions:
        raise HTTPException(status_code=400, detail="Неподдерживаемый тип файла")

    # Генерируем уникальное имя файла
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_filename = f"avatar_{current_user.id}_{timestamp}{ext}"

    file_path = f"static/uploads/avatars/{unique_filename}"
    os.makedirs("static/uploads/avatars", exist_ok=True)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Сохраняем путь к аватару в поле image_url (добавим если нет)
    db = SessionLocal()
    try:
        current_user = db.merge(current_user)
        current_user.image_url = f"/static/uploads/avatars/{unique_filename}"
        db.commit()

        logger.info("📷 Аватар загружен для: %s", current_user.email)
        return {"url": f"/static/uploads/avatars/{unique_filename}"}
    finally:
        db.close()

# --- User Addresses API ---
@app.get("/api/profile/addresses")
async def get_addresses(current_user: User = Depends(get_current_user)):
    """Получить все адреса пользователя"""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    return [
        {
            "id": a.id,
            "title": a.title,
            "address": a.address,
            "phone": a.phone,
            "recipient_name": a.recipient_name,
            "lat": a.lat,
            "lng": a.lng,
            "is_default": a.is_default
        } for a in current_user.addresses
    ]

@app.post("/api/profile/addresses")
async def add_address(
    address_data: UserAddressCreate,
    current_user: User = Depends(get_current_user)
):
    """Добавить новый адрес"""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    db = SessionLocal()

    # Если адрес по умолчанию, сбросим у остальных
    if address_data.is_default:
        db.query(UserAddress).filter(
            UserAddress.user_id == current_user.id,
            UserAddress.is_default.is_(True)
        ).update({"is_default": False})

    new_address = UserAddress(
        user_id=current_user.id,
        **address_data.model_dump()
    )
    db.add(new_address)
    db.commit()
    db.refresh(new_address)

    logger.info("📍 Адрес добавлен: %s", address_data.address)
    return {
        "id": new_address.id,
        "title": new_address.title,
        "address": new_address.address,
        "phone": new_address.phone,
        "recipient_name": new_address.recipient_name,
        "is_default": new_address.is_default
    }

@app.put("/api/profile/addresses/{address_id}")
async def update_address(
    address_id: int,
    address_data: UserAddressUpdate,
    current_user: User = Depends(get_current_user)
):
    """Обновить адрес"""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    db = SessionLocal()
    address = db.query(UserAddress).filter(
        UserAddress.id == address_id,
        UserAddress.user_id == current_user.id
    ).first()

    if not address:
        raise HTTPException(status_code=404, detail="Address not found")

    update_dict = address_data.model_dump(exclude_unset=True)

    # Если устанавливаем is_default, сбросим у остальных
    if update_dict.get("is_default"):
        db.query(UserAddress).filter(
            UserAddress.user_id == current_user.id,
            UserAddress.is_default.is_(True),
            UserAddress.id != address_id
        ).update({"is_default": False})

    for key, value in update_dict.items():
        setattr(address, key, value)

    db.commit()
    db.refresh(address)

    return {
        "id": address.id,
        "title": address.title,
        "address": address.address,
        "phone": address.phone,
        "recipient_name": address.recipient_name,
        "is_default": address.is_default
    }

@app.delete("/api/profile/addresses/{address_id}")
async def delete_address(
    address_id: int,
    current_user: User = Depends(get_current_user)
):
    """Удалить адрес"""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    db = SessionLocal()
    address = db.query(UserAddress).filter(
        UserAddress.id == address_id,
        UserAddress.user_id == current_user.id
    ).first()

    if not address:
        raise HTTPException(status_code=404, detail="Address not found")

    db.delete(address)
    db.commit()

    logger.info("🗑️ Адрес #%s удален", address_id)
    return {"detail": "Address deleted"}

# --- Favorites API ---
@app.get("/api/profile/favorites")
async def get_favorites(current_user: User = Depends(get_current_user)):
    """Получить избранные товары"""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    db = SessionLocal()
    try:
        favorites = db.query(Favorite).filter(Favorite.user_id == current_user.id).all()

        result = []
        for fav in favorites:
            product = db.query(Product).filter(Product.id == fav.product_id).first()
            if product:
                result.append({
                    "id": fav.id,
                    "favorite_id": fav.id,
                    "product": {
                        "id": product.id,
                        "name": product.name,
                        "price": product.price,
                        "sale_price": product.sale_price,
                        "image_url": product.image_url,
                        "stock": product.stock,
                        "is_sale": product.is_sale
                    }
                })

        return result
    finally:
        db.close()

@app.post("/api/profile/favorites")
async def add_favorite(
    fav_data: FavoriteCreate,
    current_user: User = Depends(get_current_user)
):
    """Добавить товар в избранное"""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    db = SessionLocal()
    try:
        # Проверка на дубликат
        existing = db.query(Favorite).filter(
            Favorite.user_id == current_user.id,
            Favorite.product_id == fav_data.product_id
        ).first()

        if existing:
            return {"detail": "Already in favorites", "id": existing.id}

        new_favorite = Favorite(
            user_id=current_user.id,
            product_id=fav_data.product_id
        )
        db.add(new_favorite)
        db.commit()
        db.refresh(new_favorite)

        return {"id": new_favorite.id, "product_id": new_favorite.product_id}
    finally:
        db.close()

@app.delete("/api/profile/favorites/{product_id}")
async def remove_favorite(
    product_id: int,
    current_user: User = Depends(get_current_user)
):
    """Удалить товар из избранного"""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    db = SessionLocal()
    try:
        favorite = db.query(Favorite).filter(
            Favorite.user_id == current_user.id,
            Favorite.product_id == product_id
        ).first()

        if not favorite:
            raise HTTPException(status_code=404, detail="Favorite not found")

        db.delete(favorite)
        db.commit()

        return {"detail": "Removed from favorites"}
    finally:
        db.close()

# --- Orders API (Extended for Profile) ---
@app.get("/api/profile/orders")
async def get_my_orders(current_user: User = Depends(get_current_user)):
    """Получить мои заказы"""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    db = SessionLocal()
    orders = db.query(Order).filter(Order.user_id == current_user.id).order_by(Order.created_at.desc()).all()

    result = []
    for o in orders:
        courier = None
        if o.courier_id:
            courier = db.query(Courier).filter(Courier.id == o.courier_id).first()

        result.append({
            "id": o.id,
            "total_amount": o.total_amount,
            "status": o.status,
            "is_paid": o.is_paid,
            "payment_method": o.payment_method,
            "delivery_address": o.delivery_address,
            "phone": o.phone,
            "delivery_date": o.delivery_date,
            "delivery_time": o.delivery_time,
            "items": o.items,
            "created_at": o.created_at.isoformat(),
            "courier": {
                "name": courier.name,
                "phone": courier.phone
            } if courier else None
        })

    return result

@app.get("/api/profile/orders/{order_id}")
async def get_order_detail(
    order_id: int,
    current_user: User = Depends(get_current_user)
):
    """Получить детали заказа"""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    db = SessionLocal()
    order = db.query(Order).filter(
        Order.id == order_id,
        Order.user_id == current_user.id
    ).first()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    courier = None
    if order.courier_id:
        courier = db.query(Courier).filter(Courier.id == order.courier_id).first()

    return {
        "id": order.id,
        "total_amount": order.total_amount,
        "status": order.status,
        "is_paid": order.is_paid,
        "payment_method": order.payment_method,
        "delivery_address": order.delivery_address,
        "phone": order.phone,
        "delivery_date": order.delivery_date,
        "delivery_time": order.delivery_time,
        "items": order.items,
        "comment": order.comment,
        "promo_code_used": order.promo_code_used,
        "created_at": order.created_at.isoformat(),
        "courier": {
            "name": courier.name,
            "phone": courier.phone
        } if courier else None
    }

@app.post("/api/profile/orders/{order_id}/repeat")
async def repeat_order(
    order_id: int,
    current_user: User = Depends(get_current_user)
):
    """Повторить заказ"""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    db = SessionLocal()
    order = db.query(Order).filter(
        Order.id == order_id,
        Order.user_id == current_user.id
    ).first()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # Создаем новый заказ с теми же данными
    new_order = Order(
        user_id=current_user.id,
        total_amount=order.total_amount,
        status="pending",
        is_paid=False,
        payment_method=order.payment_method,
        delivery_address=order.delivery_address,
        phone=order.phone,
        items=order.items,
        delivery_date=order.delivery_date,
        delivery_time=order.delivery_time,
        comment=order.comment
    )

    db.add(new_order)
    db.commit()
    db.refresh(new_order)

    logger.info("🔄 Заказ #%s повторен как #%s", order_id, new_order.id)
    return {"id": new_order.id, "detail": "Order repeated"}

@app.get("/api/profile/orders/{order_id}/receipt")
async def get_order_receipt(
    order_id: int,
    current_user: User = Depends(get_current_user)
):
    """Получить чек заказа (для печати)"""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    db = SessionLocal()
    order = db.query(Order).filter(
        Order.id == order_id,
        Order.user_id == current_user.id
    ).first()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # Возвращаем данные для чека
    return {
        "order_id": order.id,
        "created_at": order.created_at.strftime("%d.%m.%Y %H:%M"),
        "items": order.items,
        "total_amount": order.total_amount,
        "payment_method": order.payment_method,
        "is_paid": order.is_paid,
        "delivery_address": order.delivery_address
    }

# --- Bonus Points API ---
@app.get("/api/profile/bonuses")
async def get_bonus_balance(current_user: User = Depends(get_current_user)):
    """Получить баланс бонусов и историю"""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    db = SessionLocal()
    transactions = db.query(BonusTransaction).filter(
        BonusTransaction.user_id == current_user.id
    ).order_by(BonusTransaction.created_at.desc()).all()

    return {
        "balance": current_user.bonus_points,
        "transactions": [
            {
                "id": t.id,
                "amount": t.amount,
                "description": t.description,
                "order_id": t.order_id,
                "created_at": t.created_at.isoformat()
            } for t in transactions
        ]
    }

@app.get("/api/profile/promocodes")
async def get_my_promocodes(current_user: User = Depends(get_current_user)):
    """Получить персональные промокоды"""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    db = SessionLocal()
    # Персональные промокоды можно хранить в отдельной таблице
    # Пока вернем все активные промокоды
    promocodes = db.query(PromoCode).filter(PromoCode.is_active.is_(True)).all()

    return [
        {
            "id": p.id,
            "code": p.code,
            "discount_percent": p.discount_percent,
            "is_active": p.is_active
        } for p in promocodes
    ]

# --- Notifications API ---
@app.get("/api/profile/notifications")
async def get_notifications(current_user: User = Depends(get_current_user)):
    """Получить уведомления"""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    db = SessionLocal()
    notifications = db.query(Notification).filter(
        Notification.user_id == current_user.id
    ).order_by(Notification.created_at.desc()).limit(50).all()

    unread_count = db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.is_read.is_(False)
    ).count()

    return {
        "unread_count": unread_count,
        "notifications": [
            {
                "id": n.id,
                "title": n.title,
                "message": n.message,
                "type": n.type,
                "is_read": n.is_read,
                "created_at": n.created_at.isoformat()
            } for n in notifications
        ]
    }

@app.post("/api/profile/notifications/{notification_id}/read")
async def mark_notification_read(
    notification_id: int,
    current_user: User = Depends(get_current_user)
):
    """Отметить уведомление как прочитанное"""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    db = SessionLocal()
    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == current_user.id
    ).first()

    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")

    notification.is_read = True
    db.commit()

    return {"detail": "Notification marked as read"}

@app.post("/api/profile/notifications/read-all")
async def mark_all_notifications_read(
    current_user: User = Depends(get_current_user)
):
    """Отметить все уведомления как прочитанные"""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    db = SessionLocal()
    db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.is_read.is_(False)
    ).update({"is_read": True})
    db.commit()

    return {"detail": "All notifications marked as read"}

@app.delete("/api/profile/notifications/all")
async def clear_all_notifications(
    current_user: User = Depends(get_current_user)
):
    """Удалить все уведомления пользователя"""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    db = SessionLocal()
    deleted_count = db.query(Notification).filter(
        Notification.user_id == current_user.id
    ).delete()
    db.commit()

    logger.info("🗑️ Удалено %s уведомлений для пользователя #%s", deleted_count, current_user.id)
    return {"detail": f"Deleted {deleted_count} notifications", "count": deleted_count}

# --- Reminders API ---
@app.get("/api/profile/reminders")
async def get_reminders(current_user: User = Depends(get_current_user)):
    """Получить напоминания"""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    db = SessionLocal()
    reminders = db.query(Reminder).filter(
        Reminder.user_id == current_user.id,
        Reminder.is_active.is_(True)
    ).order_by(Reminder.date.asc()).all()

    return [
        {
            "id": r.id,
            "title": r.title,
            "date": r.date,
            "recipient_name": r.recipient_name,
            "recipient_phone": r.recipient_phone,
            "is_recurring": r.is_recurring,
            "recurring_type": r.recurring_type
        } for r in reminders
    ]

@app.post("/api/profile/reminders")
async def add_reminder(
    reminder_data: ReminderCreate,
    current_user: User = Depends(get_current_user)
):
    """Добавить напоминание"""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    db = SessionLocal()
    new_reminder = Reminder(
        user_id=current_user.id,
        **reminder_data.model_dump()
    )
    db.add(new_reminder)
    db.commit()
    db.refresh(new_reminder)

    logger.info("⏰ Напоминание добавлено: %s", reminder_data.title)
    return {
        "id": new_reminder.id,
        "title": new_reminder.title,
        "date": new_reminder.date,
        "recipient_name": new_reminder.recipient_name
    }

@app.put("/api/profile/reminders/{reminder_id}")
async def update_reminder(
    reminder_id: int,
    reminder_data: ReminderUpdate,
    current_user: User = Depends(get_current_user)
):
    """Обновить напоминание"""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    db = SessionLocal()
    reminder = db.query(Reminder).filter(
        Reminder.id == reminder_id,
        Reminder.user_id == current_user.id
    ).first()

    if not reminder:
        raise HTTPException(status_code=404, detail="Reminder not found")

    update_dict = reminder_data.model_dump(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(reminder, key, value)

    db.commit()
    db.refresh(reminder)

    return {
        "id": reminder.id,
        "title": reminder.title,
        "date": reminder.date,
        "is_active": reminder.is_active
    }

@app.delete("/api/profile/reminders/{reminder_id}")
async def delete_reminder(
    reminder_id: int,
    current_user: User = Depends(get_current_user)
):
    """Удалить напоминание"""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    db = SessionLocal()
    reminder = db.query(Reminder).filter(
        Reminder.id == reminder_id,
        Reminder.user_id == current_user.id
    ).first()

    if not reminder:
        raise HTTPException(status_code=404, detail="Reminder not found")

    db.delete(reminder)
    db.commit()

    logger.info("🗑️ Напоминание #%s удалено", reminder_id)
    return {"detail": "Reminder deleted"}

# --- Reviews API ---

# --- Saved Cards API ---
@app.get("/api/profile/cards")
async def get_saved_cards(current_user: User = Depends(get_current_user)):
    """Получить сохраненные карты"""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    return [
        {
            "id": c.id,
            "card_last_four": c.card_last_four,
            "card_type": c.card_type,
            "is_default": c.is_default
        } for c in current_user.saved_cards
    ]

@app.post("/api/profile/cards")
async def add_saved_card(
    card_data: SavedCardCreate,
    current_user: User = Depends(get_current_user)
):
    """Сохранить карту"""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    db = SessionLocal()

    # Если карта по умолчанию, сбросим у остальных
    if card_data.is_default:
        db.query(SavedCard).filter(
            SavedCard.user_id == current_user.id,
            SavedCard.is_default.is_(True)
        ).update({"is_default": False})

    new_card = SavedCard(
        user_id=current_user.id,
        **card_data.model_dump()
    )
    db.add(new_card)
    db.commit()
    db.refresh(new_card)

    return {
        "id": new_card.id,
        "card_last_four": new_card.card_last_four,
        "card_type": new_card.card_type
    }

@app.delete("/api/profile/cards/{card_id}")
async def delete_saved_card(
    card_id: int,
    current_user: User = Depends(get_current_user)
):
    """Удалить сохраненную карту"""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    db = SessionLocal()
    card = db.query(SavedCard).filter(
        SavedCard.id == card_id,
        SavedCard.user_id == current_user.id
    ).first()

    if not card:
        raise HTTPException(status_code=404, detail="Card not found")

    db.delete(card)
    db.commit()

    return {"detail": "Card deleted"}

# ============================================
# --- Categories API ---
@app.get("/api/categories")
async def get_categories(db: Session = Depends(get_db)):
    return db.query(Category).all()

@app.post("/api/categories")
async def add_category(category: CategoryBase, db: Session = Depends(get_db), admin: User = Depends(get_current_admin)):
    new_cat = Category(**category.dict())
    db.add(new_cat)
    db.commit()
    db.refresh(new_cat)
    return new_cat

@app.delete("/api/categories/{cat_id}")
async def delete_category(cat_id: int, db: Session = Depends(get_db), admin: User = Depends(get_current_admin)):
    db_cat = db.query(Category).filter(Category.id == cat_id).first()
    if not db_cat:
        raise HTTPException(status_code=404, detail="Category not found")
    db.delete(db_cat)
    db.commit()
    return {"detail": "Category deleted"}

# --- Promo API ---
@app.get("/api/promo-codes/{code}")
async def get_promo_code(code: str, db: Session = Depends(get_db)):
    promo = db.query(PromoCode).filter(PromoCode.code == code, PromoCode.is_active.is_(True)).first()
    if not promo:
        raise HTTPException(status_code=404, detail="Promo code not found or inactive")
    return promo

@app.get("/api/promo-codes")
async def list_promo_codes(db: Session = Depends(get_db), admin: User = Depends(get_current_admin)):
    return db.query(PromoCode).all()

@app.post("/api/promo-codes")
async def add_promo_code(promo: PromoCodeBase, db: Session = Depends(get_db), admin: User = Depends(get_current_admin)):
    new_promo = PromoCode(**promo.dict())
    db.add(new_promo)
    db.commit()
    db.refresh(new_promo)
    return new_promo

@app.delete("/api/promo-codes/{promo_id}")
async def delete_promo_code(promo_id: int, db: Session = Depends(get_db), admin: User = Depends(get_current_admin)):
    db_promo = db.query(PromoCode).filter(PromoCode.id == promo_id).first()
    if not db_promo:
        raise HTTPException(status_code=404, detail="Promo code not found")
    db.delete(db_promo)
    db.commit()
    return {"detail": "Promo code deleted"}

# --- Products API ---
@app.get("/api/products")
async def get_products(
    category_id: Optional[int] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    sort_by: Optional[str] = None, # price_asc, price_desc, popular
    db: Session = Depends(get_db)
):
    try:
        query = db.query(Product)
        if category_id:
            query = query.filter(Product.category_id == category_id)
        if min_price is not None:
            query = query.filter(Product.price >= min_price)
        if max_price is not None:
            query = query.filter(Product.price <= max_price)

        if sort_by == "price_asc":
            query = query.order_by(Product.price.asc())
        elif sort_by == "price_desc":
            query = query.order_by(Product.price.desc())
        elif sort_by == "popular":
            query = query.order_by(Product.is_popular.desc())

        return query.all()
    except Exception as e:
        logger.error("Ошибка при загрузке товаров: %s", e)
        raise

@app.get("/api/admin/products")
async def get_all_products(db: Session = Depends(get_db), admin: User = Depends(get_current_admin)):
    """Получить все товары для админки"""
    products = db.query(Product).all()
    # Преобразуем SQLAlchemy модели в словари
    return [
        {
            "id": p.id,
            "name": p.name,
            "price": p.price,
            "sale_price": p.sale_price,
            "description": p.description,
            "composition": p.composition,
            "image_url": p.image_url,
            "stock": p.stock,
            "is_sale": p.is_sale,
            "is_featured": p.is_featured,
            "is_popular": p.is_popular,
            "category_id": p.category_id,
            "price_s": p.price_s,
            "price_m": p.price_m,
            "price_l": p.price_l,
            "width": p.width,
            "height": p.height
        } for p in products
    ]

@app.post("/api/products")
async def add_product(product: ProductBase, db: Session = Depends(get_db), admin: User = Depends(get_current_admin)):
    new_product = Product(**product.dict())
    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    return new_product

@app.put("/api/products/{product_id}")
async def update_product(product_id: int, product: ProductBase, db: Session = Depends(get_db), admin: User = Depends(get_current_admin)):
    db_product = db.query(Product).filter(Product.id == product_id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")
    for key, value in product.dict().items():
        setattr(db_product, key, value)
    db.commit()
    return db_product

@app.delete("/api/products/{product_id}")
async def delete_product(product_id: int, db: Session = Depends(get_db), admin: User = Depends(get_current_admin)):
    db_product = db.query(Product).filter(Product.id == product_id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")
    db.delete(db_product)
    db.commit()
    return {"detail": "Product deleted"}

# --- Customers API ---
@app.get("/api/customers")
async def get_customers(db: Session = Depends(get_db), admin: User = Depends(get_current_admin)):
    return db.query(User).all()

# ============================================
# --- REVIEWS API ---
# ============================================

@app.get("/api/reviews")
async def get_reviews(
    limit: int = 50,
    approved_only: bool = True,
    db: Session = Depends(get_db)
):
    """Получить отзывы (для главной страницы)"""
    query = db.query(Review)
    if approved_only:
        query = query.filter(Review.is_approved.is_(True))
    return query.order_by(Review.created_at.desc()).limit(limit).all()

@app.get("/api/profile/reviews")
async def get_my_reviews(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Получить мои отзывы"""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    reviews = db.query(Review).filter(Review.user_id == current_user.id).order_by(Review.created_at.desc()).all()

    result = []
    for r in reviews:
        product = db.query(Product).filter(Product.id == r.product_id).first()
        result.append({
            "id": r.id,
            "product_id": r.product_id,
            "product_name": r.product_name,
            "product_image": product.image_url if product else None,
            "rating": r.rating,
            "text": r.text,
            "is_approved": r.is_approved,
            "is_verified_purchase": r.is_verified_purchase,
            "created_at": r.created_at.isoformat(),
            "images": [img.url for img in r.images]
        })

    return result

@app.post("/api/profile/reviews")
async def create_review(
    product_name: str = Form(...),
    rating: int = Form(...),
    text: str = Form(...),
    user_name: Optional[str] = Form(None),
    files: List[UploadFile] = File(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Создать отзыв с фото"""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    if rating < 1 or rating > 5:
        raise HTTPException(status_code=400, detail="Rating must be between 1 and 5")

    new_review = Review(
        user_id=current_user.id,
        user_name=user_name or current_user.full_name,
        product_name=product_name,
        text=text,
        rating=rating,
        is_verified_purchase=False,
        is_approved=True
    )

    db.add(new_review)
    db.commit()
    db.refresh(new_review)

    # Загрузка фото
    if files:
        os.makedirs("static/uploads/reviews", exist_ok=True)
        for file in files:
            if file.filename and file.filename.split('.')[-1].lower() in ['jpg', 'jpeg', 'png', 'webp']:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                unique_filename = f"review_{new_review.id}_{timestamp}_{file.filename}"
                file_path = f"static/uploads/reviews/{unique_filename}"

                with open(file_path, "wb") as buffer:
                    shutil.copyfileobj(file.file, buffer)

                review_img = ReviewImage(review_id=new_review.id, url=f"/static/uploads/reviews/{unique_filename}")
                db.add(review_img)

        db.commit()

    # Создаем уведомление
    create_notification(
        db=db,
        user_id=current_user.id,
        title="⭐ Отзыв ост����влен",
        message="Спасибо за ваш отзыв!",
        notification_type="info"
    )

    logger.info("⭐ Отзыв создан: %s", current_user.email)

    return {
        "id": new_review.id,
        "product_name": new_review.product_name,
        "rating": new_review.rating,
        "user_name": new_review.user_name
    }
@app.put("/api/profile/reviews/{review_id}")
async def update_review(
    review_id: int,
    text: Optional[str] = None,
    rating: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Обновить свой отзыв"""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    review = db.query(Review).filter(Review.id == review_id, Review.user_id == current_user.id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    if text is not None:
        review.text = text
    if rating is not None:
        if rating < 1 or rating > 5:
            raise HTTPException(status_code=400, detail="Rating must be between 1 and 5")
        review.rating = rating

    db.commit()
    db.refresh(review)

    return {"detail": "Review updated"}

@app.delete("/api/profile/reviews/{review_id}")
async def delete_review(
    review_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Удалить свой отзыв"""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    review = db.query(Review).filter(Review.id == review_id, Review.user_id == current_user.id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    # Удаляем фото
    for img in review.images:
        try:
            os.remove(img.url.lstrip('/'))
        except OSError:
            pass

    db.delete(review)
    db.commit()

    logger.info("🗑️ Отзыв #%s удалён", review_id)
    return {"detail": "Review deleted"}

# --- Admin Reviews API ---
@app.get("/api/admin/reviews")
async def get_all_reviews(
    approved: Optional[bool] = None,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    """Получить все отзывы (админ)"""
    query = db.query(Review)
    if approved is not None:
        query = query.filter(Review.is_approved == approved)
    return query.order_by(Review.created_at.desc()).all()

@app.put("/api/admin/reviews/{review_id}/approve")
async def approve_review(
    review_id: int,
    approved: bool,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    """Одобрить/отклонить отзыв"""
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    review.is_approved = approved
    db.commit()

    logger.info("%s Отзыв #%s %s", "✅" if approved else "❌", review_id, "одобрен" if approved else "отклонён")
    return {"detail": f"Review {'approved' if approved else 'rejected'}"}

@app.delete("/api/admin/reviews/{review_id}")
async def admin_delete_review(
    review_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    """Удалить отзыв (админ)"""
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    # Удаляем фото
    for img in review.images:
        try:
            os.remove(img.url.lstrip('/'))
        except OSError:
            pass

    db.delete(review)
    db.commit()

    logger.info("🗑️ Админ удалил отзыв #%s", review_id)
    return {"detail": "Review deleted"}

# --- Orders API ---
@app.get("/api/orders")
async def get_orders(db: Session = Depends(get_db), admin: User = Depends(get_current_admin)):
    orders = db.query(Order).all()
    result = []
    for o in orders:
        user = db.query(User).filter(User.id == o.user_id).first()

        # Парсим items из JSON строки в массив
        items_data = []
        if o.items:
            try:
                items_data = json.loads(o.items)
            except json.JSONDecodeError:
                items_data = o.items  # Если не JSON, оставляем как строку

        # Получаем информацию о курьере
        courier_info = None
        if o.courier_id:
            courier = db.query(Courier).filter(Courier.id == o.courier_id).first()
            if courier:
                courier_info = {
                    "id": courier.id,
                    "name": courier.name,
                    "phone": courier.phone
                }

        result.append({
            "id": o.id,
            "user_id": o.user_id,
            "user_name": user.full_name if user else "Аноним",
            "total_amount": o.total_amount,
            "status": o.status,
            "delivery_address": o.delivery_address,
            "phone": o.phone,
            "delivery_date": o.delivery_date,
            "delivery_time": o.delivery_time,
            "postcard_text": o.postcard_text,
            "comment": o.comment,
            "promo_code_used": o.promo_code_used,
            "is_paid": o.is_paid,
            "payment_method": o.payment_method,
            "payment_status": o.payment_status,
            "external_id": o.external_id,
            "lat": o.lat,
            "lng": o.lng,
            "created_at": o.created_at.isoformat(),
            "items": items_data,  # Возвращаем как массив
            "courier": courier_info
        })
    return result


@app.delete("/api/admin/orders/all")
async def clear_all_orders(db: Session = Depends(get_db), admin: User = Depends(get_current_admin)):
    """Удалить все заказы (админ)"""
    deleted_count = db.query(Order).delete()
    db.commit()
    logger.info("🗑️ Удалено %s заказов администратором", deleted_count)
    return {"detail": f"Deleted {deleted_count} orders", "count": deleted_count}


@app.post("/api/orders")
async def create_order(
    order: OrderCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        logger.info("📦 Новый заказ от user_id=%s | Телефон: %s | Адрес: %s | Сумма: %s",
                    current_user.id, order.phone, order.delivery_address, order.total_amount)
        new_order = Order(**order.model_dump(), user_id=current_user.id)
        db.add(new_order)
        db.commit()
        db.refresh(new_order)

        # Создаем уведомление о заказе
        create_notification(
            db=db,
            user_id=current_user.id,
            title="✅ Заказ принят",
            message=f"Ваш заказ #{new_order.id} на сумму {new_order.total_amount} сум принят в обработку",
            notification_type="order"
        )

        # Начисляем бонусы (10% от суммы заказа)
        bonus_amount = int(new_order.total_amount * 0.1)
        if bonus_amount > 0:
            add_bonus_points(
                db=db,
                user_id=current_user.id,
                amount=bonus_amount,
                description=f"Бонусы за заказ #{new_order.id}",
                order_id=new_order.id
            )

        logger.info("✅ Заказ #%s успешно создан", new_order.id)
        return new_order
    except Exception as e:
        logger.error("❌ ОШИБКА при создании заказа (user_id=%s, phone=%s): %s",
                     current_user.id, order.phone, str(e))
        raise HTTPException(status_code=500, detail="Ошибка на стороне сервера. Попробуйте ещё раз.")


@app.get("/api/payment/create-link/{order_id}")
async def create_payment_link(order_id: int, method: str, db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(404, "Order not found")

    amount = order.total_amount
    if method == "click":
        # Click link generation
        url = f"https://my.click.uz/services/pay?service_id={CLICK_SERVICE_ID}&merchant_id={CLICK_MERCHANT_ID}&amount={amount}&transaction_param={order.id}"
        return {"url": url}

    elif method == "payme":
        # Payme link generation (base64 params)
        params = f"m={PAYME_MERCHANT_ID};ac.order_id={order.id};a={int(amount * 100)}"
        encoded = base64.b64encode(params.encode()).decode()
        url = f"https://checkout.paycom.uz/{encoded}"
        return {"url": url}

    raise HTTPException(400, "Unsupported payment method")

# --- Click Callback Handler ---
@app.post("/api/payment/click/callback")
@app.get("/api/payment/click/callback")
async def click_callback(request: Request, db: Session = Depends(get_db)):
    params = await request.form() if request.method == "POST" else request.query_params

    click_trans_id = params.get("click_trans_id")
    service_id = params.get("service_id")
    merchant_trans_id = params.get("merchant_trans_id")
    amount = params.get("amount")
    action = params.get("action")
    error = params.get("error")
    error_note = params.get("error_note")
    sign_time = params.get("sign_time")
    sign_string = params.get("sign_string")

    # Verify signature
    my_sign = hashlib.md5(f"{click_trans_id}{service_id}{CLICK_SECRET_KEY}{merchant_trans_id}{amount}{action}{sign_time}".encode()).hexdigest()

    if my_sign != sign_string:
        return {"error": "-1", "error_note": "SIGN CHECK FAILED"}

    order_id = int(merchant_trans_id)
    order = db.query(Order).filter(Order.id == order_id).first()

    if not order:
        return {"error": "-5", "error_note": "ORDER NOT FOUND"}

    if action == "0": # Prepare
        if order.payment_status == "payed":
            return {"error": "-4", "error_note": "ALREADY PAID"}
        return {
            "click_trans_id": click_trans_id,
            "merchant_trans_id": merchant_trans_id,
            "merchant_prepare_id": order_id,
            "error": "0",
            "error_note": "Success"
        }

    elif action == "1": # Complete
        if error == "0":
            order.payment_status = "payed"
            order.external_id = click_trans_id
            db.commit()
            return {
                "click_trans_id": click_trans_id,
                "merchant_trans_id": merchant_trans_id,
                "merchant_confirm_id": order_id,
                "error": "0",
                "error_note": "Success"
            }
        else:
            order.payment_status = "error"
            db.commit()
            return {"error": error, "error_note": error_note}

    return {"error": "-3", "error_note": "ACTION NOT FOUND"}

# --- Payme Callback Handler (Simplified JSON-RPC) ---
@app.post("/api/payment/payme/callback")
async def payme_callback(request: Request, db: Session = Depends(get_db)):
    # Basic Payme Check
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Basic "):
        return {"error": {"code": -32504, "message": "Error Auth"}}

    # Payme logic is complex with methods like CheckPerformTransaction, CreateTransaction, etc.
    # Here is a placeholder for basic flow alignment
    body = await request.json()

    # We will implement full Payme RPC logic if needed, but for now, we focus on the flow
    return {"result": {"allow": True}}

@app.put("/api/orders/{order_id}/status")
async def update_order_status(order_id: int, status_data: dict, db: Session = Depends(get_db), admin: User = Depends(get_current_admin)):
    db_order = db.query(Order).filter(Order.id == order_id).first()
    if not db_order:
        raise HTTPException(status_code=404, detail="Order not found")

    old_status = db_order.status

    if "status" in status_data:
        db_order.status = status_data["status"]
    if "is_paid" in status_data:
        db_order.is_paid = status_data["is_paid"]

    db.commit()

    # Обновляем или создаем уведомление об изменении статуса
    status_messages = {
        "pending": "Ваш заказ принят в обработку",
        "confirmed": "Заказ подтверждён ✅",
        "processing": "Заказ собирается 📦",
        "shipping": "Заказ доставляется 🚚",
        "completed": "Заказ выполнен. Спасибо за покупку! 🎉",
        "cancelled": "Заказ отменен ❌"
    }

    new_status = status_data.get("status", old_status)
    message = status_messages.get(new_status, f"Статус заказа изменён на {new_status}")

    # Ищем существующее уведомление для этого заказа
    existing_notification = db.query(Notification).filter(
        Notification.user_id == db_order.user_id,
        Notification.type == "order",
        Notification.title.contains(f"Заказ #{order_id}")
    ).first()

    if existing_notification:
        # Обновляем существующее уведомление
        existing_notification.title = f"📦 Заказ #{order_id}"
        existing_notification.message = message
        existing_notification.is_read = False  # Помечаем как непрочитанное
        existing_notification.created_at = datetime.utcnow()  # Обновляем время
        db.commit()
        logger.info("🔔 Уведомление для заказа #%s обновлено", order_id)
    else:
        # Создаем новое уведомление
        create_notification(
            db=db,
            user_id=db_order.user_id,
            title=f"📦 Заказ #{order_id}",
            message=message,
            notification_type="order"
        )

    return db_order

# --- Support Chat API ---
@app.post("/api/support/send")
async def send_support_message(msg: SupportMessageCreate, db: Session = Depends(get_db)):
    new_msg = SupportMessage(user_id=msg.user_id, message=msg.message, is_admin=False)
    db.add(new_msg)
    db.commit()
    return {"status": "ok"}

@app.get("/api/support/messages")
async def get_support_messages(user_id: int, db: Session = Depends(get_db)):
    # Mark messages as read when fetched
    db.query(SupportMessage).filter(
        SupportMessage.user_id == user_id,
        SupportMessage.is_read.is_(False)
    ).update({"is_read": True})
    db.commit()

    messages = db.query(SupportMessage).filter(SupportMessage.user_id == user_id).order_by(SupportMessage.created_at.asc()).all()
    return [{
        "id": m.id,
        "message": m.message,
        "is_admin": m.is_admin,
        "created_at": m.created_at.isoformat()
    } for m in messages]

@app.get("/api/support/sessions")
async def get_support_sessions(db: Session = Depends(get_db), admin: User = Depends(get_current_admin)):
    sessions = db.query(SupportMessage.user_id).distinct().all()
    result = []
    for (u_id,) in sessions:
        user = db.query(User).filter(User.id == u_id).first()
        last_msg = db.query(SupportMessage).filter(SupportMessage.user_id == u_id).order_by(SupportMessage.created_at.desc()).first()
        unread_count = db.query(SupportMessage).filter(
            SupportMessage.user_id == u_id,
            SupportMessage.is_read.is_(False),
            SupportMessage.is_admin.is_(False)
        ).count()

        result.append({
            "user_id": u_id,
            "user_name": user.full_name if user else "Аноним",
            "last_message": last_msg.message if last_msg else "",
            "last_time": last_msg.created_at.isoformat() if last_msg else "",
            "unread_count": unread_count
        })
    return result

@app.get("/api/support/unread-total")
async def get_unread_total(db: Session = Depends(get_db), admin: User = Depends(get_current_admin)):
    total = db.query(SupportMessage).filter(
        SupportMessage.is_read.is_(False),
        SupportMessage.is_admin.is_(False)
    ).count()
    return {"total": total}


@app.post("/api/support/reply")
async def reply_support_message(reply: SupportReply, db: Session = Depends(get_db), admin: User = Depends(get_current_admin)):
    new_msg = SupportMessage(user_id=reply.user_id, message=reply.message, is_admin=True, is_read=True)
    db.add(new_msg)
    db.commit()
    return {"status": "ok"}


# --- Admin Extended APIs ---
@app.get("/api/admin/stats")
async def get_stats(db: Session = Depends(get_db), admin: User = Depends(get_current_admin)):
    total_revenue = db.query(func.sum(Order.total_amount)).filter(Order.status == 'completed').scalar() or 0
    total_orders = db.query(Order).count()
    total_customers = db.query(User).count()

    # Top products (by frequency in orders)
    # Simple implementation: parse items JSON or just count orders for now
    top_products = db.query(Product).order_by(Product.is_popular.desc()).limit(5).all()

    return {
        "revenue": total_revenue,
        "orders": total_orders,
        "customers": total_customers,
        "top_products": [{"name": p.name, "price": p.price} for p in top_products]
    }

@app.get("/api/admin/customers")
async def list_customers(db: Session = Depends(get_db), admin: User = Depends(get_current_admin)):
    # Возвращаем только обычных пользователей (не админов)
    return db.query(User).filter(User.is_admin.is_(False)).all()

# --- Admin Notifications API ---
@app.post("/api/admin/notifications/create")
async def create_global_notification(
    title: str,
    message: str,
    notification_type: str = "info",
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    """Создать уведомление для всех пользователей"""
    users = db.query(User).filter(User.is_admin.is_(False)).all()

    created_count = 0
    for user in users:
        try:
            notification = Notification(
                user_id=user.id,
                title=title,
                message=message,
                type=notification_type
            )
            db.add(notification)
            created_count += 1
        except Exception as e:
            logger.error("Ошибка при создании уведомления для пользователя #%s: %s", user.id, e)

    db.commit()
    logger.info("📢 Создано %s уведомлений для всех пользователей", created_count)
    return {"detail": f"Created {created_count} notifications", "count": created_count}

@app.get("/api/admin/notifications/check-reminders")
async def check_reminders(db: Session = Depends(get_db), admin: User = Depends(get_current_admin)):
    """Проверить напоминания и создать уведомления для тех, у кого скоро дата"""
    from datetime import datetime, timedelta

    today = datetime.now().date()
    tomorrow = today + timedelta(days=1)

    reminders = db.query(Reminder).filter(
        Reminder.is_active.is_(True)
    ).all()

    notified_count = 0
    for reminder in reminders:
        try:
            reminder_date = datetime.strptime(reminder.date, "%Y-%m-%d").date()

            # Проверяем если напоминание на завтра
            if reminder_date == tomorrow:
                create_notification(
                    db=db,
                    user_id=reminder.user_id,
                    title="⏰ Напоминание: завтра важный день!",
                    message=f"Завтра {reminder.title} ({reminder.recipient_name})",
                    notification_type="reminder"
                )
                notified_count += 1

            # Для повторяющихся напоминаний проверяем yearly/monthly
            if reminder.is_recurring and reminder.recurring_type == "yearly":
                # Проверяем день и месяц без года
                if reminder_date.month == tomorrow.month and reminder_date.day == tomorrow.day:
                    create_notification(
                        db=db,
                        user_id=reminder.user_id,
                        title="⏰ Напоминание: завтра важный день!",
                        message=f"Завтра {reminder.title} ({reminder.recipient_name})",
                        notification_type="reminder"
                    )
                    notified_count += 1
        except Exception as e:
            logger.error("Ошибка при проверке напоминания #%s: %s", reminder.id, e)

    db.commit()
    logger.info("🔔 Проверены напоминания, создано %s уведомлений", notified_count)
    return {"detail": f"Checked reminders, notified {notified_count} users", "notified_count": notified_count}

@app.put("/api/admin/customers/{user_id}/block")
async def toggle_block_user(user_id: int, block: bool, db: Session = Depends(get_db), admin: User = Depends(get_current_admin)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user: raise HTTPException(404)
    user.is_blocked = block
    db.commit()
    return {"status": "ok"}

@app.get("/api/admin/couriers")
async def list_couriers(db: Session = Depends(get_db), admin: User = Depends(get_current_admin)):
    return db.query(Courier).all()

@app.post("/api/admin/couriers")
async def add_courier(name: str, phone: str, db: Session = Depends(get_db), admin: User = Depends(get_current_admin)):
    c = Courier(name=name, phone=phone)
    db.add(c)
    db.commit()
    return c

class DeliveryZoneBase(BaseModel):
    name: str
    price: float

@app.get("/api/admin/delivery-zones")
async def list_zones(db: Session = Depends(get_db), admin: User = Depends(get_current_admin)):
    return db.query(DeliveryZone).all()

@app.post("/api/admin/delivery-zones")
async def add_zone(zone: DeliveryZoneBase, db: Session = Depends(get_db), admin: User = Depends(get_current_admin)):
    z = DeliveryZone(name=zone.name, price=zone.price)
    db.add(z)
    db.commit()
    db.refresh(z)
    logger.info("✅ Зона доставки добавлена: %s — %s сум", zone.name, zone.price)
    return z

@app.put("/api/admin/delivery-zones/{zone_id}")
async def update_zone(zone_id: int, zone: DeliveryZoneBase, db: Session = Depends(get_db), admin: User = Depends(get_current_admin)):
    z = db.query(DeliveryZone).filter(DeliveryZone.id == zone_id).first()
    if not z:
        raise HTTPException(status_code=404, detail="Zone not found")
    z.name = zone.name
    z.price = zone.price
    db.commit()
    return z

@app.delete("/api/admin/delivery-zones/{zone_id}")
async def delete_zone(zone_id: int, db: Session = Depends(get_db), admin: User = Depends(get_current_admin)):
    z = db.query(DeliveryZone).filter(DeliveryZone.id == zone_id).first()
    if not z:
        raise HTTPException(status_code=404, detail="Zone not found")
    db.delete(z)
    db.commit()
    logger.info("🗑️ Зона доставки #%s удалена", zone_id)
    return {"detail": "Zone deleted"}

@app.post("/api/admin/upload")
async def upload_file(file: UploadFile = File(...), admin: User = Depends(get_current_admin)):
    file_path = f"static/uploads/{file.filename}"
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return {"url": f"/static/uploads/{file.filename}"}

class BannerBase(BaseModel):
    image_url: Optional[str] = None
    video_url: Optional[str] = None
    media_type: str = "image"
    link: Optional[str] = None
    text: Optional[str] = None
    subtext: Optional[str] = None
    is_active: bool = True

@app.get("/api/banners")
async def get_banners(db: Session = Depends(get_db)):
    return db.query(Banner).filter(Banner.is_active.is_(True)).all()

@app.get("/api/admin/banners")
async def list_banners(db: Session = Depends(get_db), admin: User = Depends(get_current_admin)):
    return db.query(Banner).all()

@app.post("/api/admin/banners")
async def add_banner(banner: BannerBase, db: Session = Depends(get_db), admin: User = Depends(get_current_admin)):
    new_banner = Banner(**banner.dict())
    db.add(new_banner)
    db.commit()
    db.refresh(new_banner)
    logger.info("✅ Баннер добавлен: %s", banner.media_type)
    return new_banner

@app.put("/api/admin/banners/{banner_id}")
async def update_banner(banner_id: int, banner: BannerBase, db: Session = Depends(get_db), admin: User = Depends(get_current_admin)):
    db_banner = db.query(Banner).filter(Banner.id == banner_id).first()
    if not db_banner:
        raise HTTPException(status_code=404, detail="Banner not found")
    for key, value in banner.dict().items():
        setattr(db_banner, key, value)
    db.commit()
    db.refresh(db_banner)
    return db_banner

@app.delete("/api/admin/banners/{banner_id}")
async def delete_banner(banner_id: int, db: Session = Depends(get_db), admin: User = Depends(get_current_admin)):
    db_banner = db.query(Banner).filter(Banner.id == banner_id).first()
    if not db_banner:
        raise HTTPException(status_code=404, detail="Banner not found")
    db.delete(db_banner)
    db.commit()
    logger.info("🗑️ Баннер #%s удален", banner_id)
    return {"detail": "Banner deleted"}

@app.post("/api/admin/upload-banner")
async def upload_banner_file(file: UploadFile = File(...), admin: User = Depends(get_current_admin)):
    # Проверка типа файла
    allowed_image_extensions = [".jpg", ".jpeg", ".png", ".gif", ".webp"]
    allowed_video_extensions = [".mp4", ".webm", ".ogg", ".mov"]

    filename = file.filename
    ext = os.path.splitext(filename)[1].lower()

    if ext not in allowed_image_extensions + allowed_video_extensions:
        raise HTTPException(status_code=400, detail="Неподдерживаемый тип файла")

    # Генерируем уникальное имя файла
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_filename = f"{timestamp}_{filename}"

    file_path = f"static/uploads/{unique_filename}"
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    media_type = "video" if ext in allowed_video_extensions else "image"
    logger.info("✅ Файл баннера загружен: %s (%s)", unique_filename, media_type)

    return {"url": f"/static/uploads/{unique_filename}", "media_type": media_type}

# --- Pages ---
@app.get("/favicon.ico")
async def favicon():
    return Response(status_code=204)

@app.get("/", response_class=HTMLResponse)
async def read_item(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/admin", response_class=HTMLResponse)
async def read_admin(request: Request):
    return templates.TemplateResponse("admin.html", {"request": request})

@app.get("/profile", response_class=HTMLResponse)
async def read_profile(request: Request):
    return templates.TemplateResponse("profile.html", {"request": request})

@app.get("/login", response_class=HTMLResponse)
async def read_login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
