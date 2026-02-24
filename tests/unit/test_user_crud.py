"""
Unit тесты для User CRUD операций
"""
import pytest
from sqlalchemy.orm import Session
from passlib.context import CryptContext

from main import User, pwd_context, Order, UserAddress


class TestUserCreate:
    """Тесты создания пользователя"""
    
    def test_create_user_success(self, db_session: Session):
        """Успешное создание пользователя"""
        user = User(
            email="newuser@example.com",
            hashed_password=pwd_context.hash("password123"),
            full_name="New User",
            phone="+998901111111"
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        assert user.id is not None
        assert user.email == "newuser@example.com"
        assert user.full_name == "New User"
        assert user.is_admin is False
        assert user.bonus_points == 0
    
    def test_create_user_unique_email(self, db_session: Session):
        """Проверка уникальности email"""
        user1 = User(
            email="duplicate@example.com",
            hashed_password=pwd_context.hash("password123"),
            full_name="User 1"
        )
        db_session.add(user1)
        db_session.commit()
        
        # Попытка создать пользователя с тем же email должна вызвать ошибку
        user2 = User(
            email="duplicate@example.com",
            hashed_password=pwd_context.hash("password123"),
            full_name="User 2"
        )
        db_session.add(user2)
        
        with pytest.raises(Exception):
            db_session.commit()
    
    def test_create_admin_user(self, db_session: Session):
        """Создание администратора"""
        admin = User(
            email="admin@example.com",
            hashed_password=pwd_context.hash("adminpass"),
            full_name="Admin",
            is_admin=True
        )
        db_session.add(admin)
        db_session.commit()
        db_session.refresh(admin)
        
        assert admin.is_admin is True


class TestUserRead:
    """Тесты чтения пользователя"""
    
    def test_get_user_by_id(self, db_session: Session, test_user: User):
        """Получение пользователя по ID"""
        user = db_session.query(User).filter(User.id == test_user.id).first()
        
        assert user is not None
        assert user.email == test_user.email
        assert user.full_name == test_user.full_name
    
    def test_get_user_by_email(self, db_session: Session, test_user: User):
        """Получение пользователя по email"""
        user = db_session.query(User).filter(User.email == test_user.email).first()
        
        assert user is not None
        assert user.id == test_user.id
    
    def test_get_nonexistent_user(self, db_session: Session):
        """Получение несуществующего пользователя"""
        user = db_session.query(User).filter(User.id == 99999).first()
        
        assert user is None


class TestUserUpdate:
    """Тесты обновления пользователя"""
    
    def test_update_user_name(self, db_session: Session, test_user: User):
        """Обновление имени пользователя"""
        test_user.full_name = "Updated Name"
        db_session.commit()
        db_session.refresh(test_user)
        
        assert test_user.full_name == "Updated Name"
    
    def test_update_user_phone(self, db_session: Session, test_user: User):
        """Обновление телефона"""
        test_user.phone = "+998909999999"
        db_session.commit()
        db_session.refresh(test_user)
        
        assert test_user.phone == "+998909999999"
    
    def test_update_user_bonus_points(self, db_session: Session, test_user: User):
        """Обновление бонусных баллов"""
        test_user.bonus_points = 500
        db_session.commit()
        db_session.refresh(test_user)
        
        assert test_user.bonus_points == 500
    
    def test_update_user_password(self, db_session: Session, test_user: User):
        """Обновление пароля"""
        new_password = pwd_context.hash("newpassword123")
        test_user.hashed_password = new_password
        db_session.commit()
        
        assert pwd_context.verify("newpassword123", test_user.hashed_password)


class TestUserDelete:
    """Тесты удаления пользователя"""
    
    def test_delete_user(self, db_session: Session, test_user: User):
        """Удаление пользователя"""
        user_id = test_user.id
        db_session.delete(test_user)
        db_session.commit()
        
        user = db_session.query(User).filter(User.id == user_id).first()
        assert user is None
    
    def test_delete_nonexistent_user(self, db_session: Session):
        """Попытка удаления несуществующего пользователя"""
        # SQLite просто ничего не удаляет, не вызывая ошибку
        result = db_session.query(User).filter(User.id == 99999).delete()
        db_session.commit()
        
        assert result == 0  # Ничего не удалено


class TestUserRelationships:
    """Тесты связей пользователя"""
    
    def test_user_orders_relationship(self, db_session: Session, test_user: User, test_order: Order):
        """Проверка связи пользователя с заказами"""
        orders = test_user.orders
        assert len(orders) >= 1
        assert test_order.id in [o.id for o in orders]
    
    def test_user_addresses_relationship(self, db_session: Session, test_user: User):
        """Проверка связи пользователя с адресами"""
        from main import UserAddress
        
        address = UserAddress(
            user_id=test_user.id,
            title="Home",
            address="Test Address",
            phone="+998901234567",
            recipient_name="Test User"
        )
        db_session.add(address)
        db_session.commit()
        
        assert len(test_user.addresses) >= 1
        assert address.id in [a.id for a in test_user.addresses]


class TestUserValidators:
    """Тесты валидации пользователя"""
    
    def test_password_hashing(self, db_session: Session):
        """Проверка хеширования пароля"""
        password = "mypassword123"
        hashed = pwd_context.hash(password)
        
        assert hashed != password
        assert pwd_context.verify(password, hashed)
        assert not pwd_context.verify("wrongpassword", hashed)
    
    def test_default_values(self, db_session: Session):
        """Проверка значений по умолчанию"""
        user = User(
            email="defaults@example.com",
            hashed_password=pwd_context.hash("password")
        )
        db_session.add(user)
        db_session.commit()
        
        assert user.is_admin is False
        assert user.is_blocked is False
        assert user.bonus_points == 0
        assert user.phone is None
