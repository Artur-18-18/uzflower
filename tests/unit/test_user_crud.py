"""
Unit-тесты для CRUD операций с User.
"""

import pytest
from sqlalchemy.orm import Session
from main import User


@pytest.mark.unit
class TestUserCreate:
    """Тесты создания пользователей"""
    
    def test_create_user_success(self, db_session: Session):
        """Успешное создание пользователя"""
        user = User(
            email="newuser@example.com",
            hashed_password="hashed_pass_123",
            full_name="New User",
            phone="+998901111111",
            is_admin=False,
            bonus_points=50,
        )
        db_session.add(user)
        db_session.commit()
        
        assert user.id is not None
        assert user.email == "newuser@example.com"
        assert user.full_name == "New User"
        assert user.is_admin is False
        assert user.bonus_points == 50
    
    def test_create_admin_user(self, db_session: Session):
        """Создание администратора"""
        admin = User(
            email="admin@example.com",
            hashed_password="admin_pass",
            full_name="Admin User",
            is_admin=True,
        )
        db_session.add(admin)
        db_session.commit()
        
        assert admin.is_admin is True
    
    def test_create_user_with_unique_email(self, db_session: Session, sample_user: User):
        """Проверка уникальности email"""
        # Попытка создать пользователя с существующим email должна вызвать ошибку
        duplicate_user = User(
            email=sample_user.email,
            hashed_password="different_pass",
            full_name="Duplicate Name",
        )
        db_session.add(duplicate_user)
        
        try:
            db_session.commit()
            pytest.fail("Должна быть ошибка при добавлении email дубликата")
        except Exception:
            db_session.rollback()
            assert True


@pytest.mark.unit
class TestUserRead:
    """Тесты чтения пользователей"""
    
    def test_read_user_by_id(self, db_session: Session, sample_user: User):
        """Чтение пользователя по ID"""
        user = db_session.query(User).filter(User.id == sample_user.id).first()
        
        assert user is not None
        assert user.email == sample_user.email
        assert user.full_name == sample_user.full_name
    
    def test_read_user_by_email(self, db_session: Session, sample_user: User):
        """Чтение пользователя по email"""
        user = db_session.query(User).filter(User.email == sample_user.email).first()
        
        assert user is not None
        assert user.id == sample_user.id
    
    def test_read_nonexistent_user(self, db_session: Session):
        """Чтение несуществующего пользователя"""
        user = db_session.query(User).filter(User.id == 99999).first()
        assert user is None
    
    def test_read_user_list(self, db_session: Session, sample_user: User):
        """Чтение списка пользователей"""
        users = db_session.query(User).all()
        
        assert len(users) >= 1
        assert any(u.id == sample_user.id for u in users)


@pytest.mark.unit
class TestUserUpdate:
    """Тесты обновления пользователей"""
    
    def test_update_user_phone(self, db_session: Session, sample_user: User):
        """Обновление номера телефона"""
        new_phone = "+998909999999"
        sample_user.phone = new_phone
        db_session.commit()
        
        updated = db_session.query(User).filter(User.id == sample_user.id).first()
        assert updated.phone == new_phone
    
    def test_update_user_full_name(self, db_session: Session, sample_user: User):
        """Обновление полного имени"""
        new_name = "Updated Name"
        sample_user.full_name = new_name
        db_session.commit()
        
        updated = db_session.query(User).filter(User.id == sample_user.id).first()
        assert updated.full_name == new_name
    
    def test_update_user_bonus_points(self, db_session: Session, sample_user: User):
        """Обновление бонусных баллов"""
        new_points = 250
        sample_user.bonus_points = new_points
        db_session.commit()
        
        updated = db_session.query(User).filter(User.id == sample_user.id).first()
        assert updated.bonus_points == new_points
    
    def test_block_user(self, db_session: Session, sample_user: User):
        """Блокировка пользователя"""
        sample_user.is_blocked = True
        db_session.commit()
        
        updated = db_session.query(User).filter(User.id == sample_user.id).first()
        assert updated.is_blocked is True


@pytest.mark.unit
class TestUserDelete:
    """Тесты удаления пользователей"""
    
    def test_delete_user(self, db_session: Session, sample_user: User):
        """Удаление пользователя"""
        user_id = sample_user.id
        db_session.delete(sample_user)
        db_session.commit()
        
        deleted = db_session.query(User).filter(User.id == user_id).first()
        assert deleted is None


@pytest.mark.unit
class TestUserValidation:
    """Тесты валидации данных пользователей"""
    
    def test_user_bonus_points_non_negative(self, db_session: Session, sample_user: User):
        """Проверка, что бонусные баллы не отрицательные"""
        assert sample_user.bonus_points >= 0
    
    def test_user_has_email(self, db_session: Session, sample_user: User):
        """Проверка наличия email"""
        assert sample_user.email is not None
        assert "@" in sample_user.email
    
    def test_user_has_hashed_password(self, db_session: Session, sample_user: User):
        """Проверка наличия хэшированного пароля"""
        assert sample_user.hashed_password is not None
        assert len(sample_user.hashed_password) > 0
