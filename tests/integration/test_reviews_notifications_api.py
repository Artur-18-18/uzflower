"""
Integration тесты API - Отзывы, Уведомления, Напоминания
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from main import User, Product, Review, Notification, Reminder


class TestReviewsAPI:
    """Тесты API отзывов"""
    
    def test_create_review(self, client: TestClient, test_user: User, test_product: Product, headers: dict):
        """Создание отзыва"""
        response = client.post("/api/profile/reviews", headers=headers, data={
            "product_name": test_product.name,
            "rating": "5",
            "text": "Great product!",
            "user_name": test_user.full_name
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["rating"] == 5
        assert data["product_name"] == test_product.name
    
    def test_create_review_with_photos(self, client: TestClient, test_user: User, test_product: Product, headers: dict):
        """Создание отзыва с фото"""
        # Создаём тестовое фото
        import io
        photo = io.BytesIO(b"fake image data")
        photo.name = "test.jpg"
        
        response = client.post("/api/profile/reviews", headers=headers, data={
            "product_name": test_product.name,
            "rating": "5",
            "text": "With photo!",
            "user_name": test_user.full_name
        }, files={"files": photo})
        
        assert response.status_code == 200
    
    def test_get_my_reviews(self, client: TestClient, test_user: User, test_review: Review, headers: dict):
        """Получение своих отзывов"""
        response = client.get("/api/profile/reviews", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
    
    def test_update_review(self, client: TestClient, test_user: User, test_review: Review, headers: dict):
        """Обновление отзыва"""
        response = client.put(f"/api/profile/reviews/{test_review.id}", headers=headers, data={
            "text": "Updated text",
            "rating": "4"
        })
        
        assert response.status_code == 200
    
    def test_delete_review(self, client: TestClient, test_user: User, test_review: Review, headers: dict):
        """Удаление отзыва"""
        response = client.delete(f"/api/profile/reviews/{test_review.id}", headers=headers)
        
        assert response.status_code == 200
    
    def test_get_all_reviews(self, client: TestClient, test_review: Review):
        """Получение всех отзывов (для главной)"""
        response = client.get("/api/reviews")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1


class TestAdminReviewsAPI:
    """Тесты API админа для отзывов"""
    
    def test_admin_get_all_reviews(self, client: TestClient, admin_headers: dict, test_review: Review):
        """Админ получает все отзывы"""
        response = client.get("/api/admin/reviews", headers=admin_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
    
    def test_admin_approve_review(self, client: TestClient, admin_headers: dict, test_review: Review):
        """Админ одобряет отзыв"""
        response = client.put(f"/api/admin/reviews/{test_review.id}/approve", headers=admin_headers, params={
            "approved": True
        })
        
        assert response.status_code == 200
    
    def test_admin_reject_review(self, client: TestClient, admin_headers: dict, test_review: Review):
        """Админ отклоняет отзыв"""
        response = client.put(f"/api/admin/reviews/{test_review.id}/approve", headers=admin_headers, params={
            "approved": False
        })
        
        assert response.status_code == 200
    
    def test_admin_delete_review(self, client: TestClient, admin_headers: dict, test_review: Review):
        """Админ удаляет отзыв"""
        response = client.delete(f"/api/admin/reviews/{test_review.id}", headers=admin_headers)
        
        assert response.status_code == 200


class TestNotificationsAPI:
    """Тесты API уведомлений"""
    
    def test_get_notifications(self, client: TestClient, test_user: User, headers: dict):
        """Получение уведомлений"""
        response = client.get("/api/profile/notifications", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "notifications" in data
        assert "unread_count" in data
    
    def test_mark_notification_read(self, client: TestClient, test_user: User, headers: dict):
        """Отметить уведомление как прочитанное"""
        # Сначала создадим уведомление
        from main import create_notification, get_db
        db = next(get_db())
        create_notification(db, test_user.id, "Test", "Test message", "info")
        
        # Получаем уведомления
        response = client.get("/api/profile/notifications", headers=headers)
        notifications = response.json()["notifications"]
        
        if notifications:
            notification_id = notifications[0]["id"]
            response = client.post(f"/api/profile/notifications/{notification_id}/read", headers=headers)
            assert response.status_code == 200
    
    def test_mark_all_notifications_read(self, client: TestClient, test_user: User, headers: dict):
        """Отметить все уведомления как прочитанные"""
        response = client.post("/api/profile/notifications/read-all", headers=headers)
        
        assert response.status_code == 200


class TestRemindersAPI:
    """Тесты API напоминаний"""
    
    def test_get_reminders(self, client: TestClient, test_user: User, headers: dict):
        """Получение напоминаний"""
        response = client.get("/api/profile/reminders", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_add_reminder(self, client: TestClient, test_user: User, headers: dict):
        """Добавление напоминания"""
        response = client.post("/api/profile/reminders", headers=headers, json={
            "title": "Mom's Birthday",
            "date": "2024-03-08",
            "recipient_name": "Mom",
            "recipient_phone": "+998901111111"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Mom's Birthday"
    
    def test_add_recurring_reminder(self, client: TestClient, test_user: User, headers: dict):
        """Добавление повторяющегося напоминания"""
        response = client.post("/api/profile/reminders", headers=headers, json={
            "title": "Anniversary",
            "date": "2024-12-31",
            "recipient_name": "Spouse",
            "is_recurring": True,
            "recurring_type": "yearly"
        })
        
        assert response.status_code == 200
    
    def test_update_reminder(self, client: TestClient, test_user: User, headers: dict):
        """Обновление напоминания"""
        # Создаём
        create_response = client.post("/api/profile/reminders", headers=headers, json={
            "title": "Old Title",
            "date": "2024-03-08",
            "recipient_name": "Test"
        })
        reminder_id = create_response.json()["id"]
        
        # Обновляем
        response = client.put(f"/api/profile/reminders/{reminder_id}", headers=headers, json={
            "title": "New Title"
        })
        
        assert response.status_code == 200
    
    def test_delete_reminder(self, client: TestClient, test_user: User, headers: dict):
        """Удаление напоминания"""
        # Создаём
        create_response = client.post("/api/profile/reminders", headers=headers, json={
            "title": "ToDelete",
            "date": "2024-03-08",
            "recipient_name": "Test"
        })
        reminder_id = create_response.json()["id"]
        
        # Удаляем
        response = client.delete(f"/api/profile/reminders/{reminder_id}", headers=headers)
        
        assert response.status_code == 200


class TestSavedCardsAPI:
    """Тесты API сохранённых карт"""
    
    def test_get_saved_cards(self, client: TestClient, test_user: User, headers: dict):
        """Получение сохранённых карт"""
        response = client.get("/api/profile/cards", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_add_saved_card(self, client: TestClient, test_user: User, headers: dict):
        """Сохранение карты"""
        response = client.post("/api/profile/cards", headers=headers, json={
            "card_last_four": "1234",
            "card_type": "visa",
            "is_default": True
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["card_last_four"] == "1234"
    
    def test_delete_saved_card(self, client: TestClient, test_user: User, headers: dict):
        """Удаление сохранённой карты"""
        # Создаём
        create_response = client.post("/api/profile/cards", headers=headers, json={
            "card_last_four": "5678",
            "card_type": "mastercard"
        })
        card_id = create_response.json()["id"]
        
        # Удаляем
        response = client.delete(f"/api/profile/cards/{card_id}", headers=headers)
        
        assert response.status_code == 200


class TestSupportChatAPI:
    """Тесты API поддержки"""
    
    def test_send_message(self, client: TestClient, test_user: User, headers: dict):
        """Отправка сообщения в поддержку"""
        response = client.post("/api/support/send", headers=headers, json={
            "message": "Help me please!"
        })
        
        assert response.status_code == 200
    
    def test_get_messages(self, client: TestClient, test_user: User, headers: dict):
        """Получение сообщений поддержки"""
        response = client.get("/api/support/messages", headers=headers, params={
            "user_id": test_user.id
        })
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_admin_get_sessions(self, client: TestClient, admin_headers: dict):
        """Админ получает сессии поддержки"""
        response = client.get("/api/support/sessions", headers=admin_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_admin_reply(self, client: TestClient, test_user: User, admin_headers: dict):
        """Админ отвечает в поддержке"""
        response = client.post("/api/support/reply", headers=admin_headers, json={
            "user_id": test_user.id,
            "message": "How can I help?"
        })
        
        assert response.status_code == 200


class TestBannersAPI:
    """Тесты API баннеров"""
    
    def test_get_banners(self, client: TestClient):
        """Получение баннеров"""
        response = client.get("/api/banners")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_admin_get_banners(self, client: TestClient, admin_headers: dict):
        """Админ получает все баннеры"""
        response = client.get("/api/admin/banners", headers=admin_headers)
        
        assert response.status_code == 200
    
    def test_admin_add_banner(self, client: TestClient, admin_headers: dict):
        """Админ добавляет баннер"""
        response = client.post("/api/admin/banners", headers=admin_headers, json={
            "image_url": "https://via.placeholder.com/1920x600",
            "media_type": "image",
            "text": "Spring Sale",
            "subtext": "Up to 50% off",
            "is_active": True
        })
        
        assert response.status_code == 200
    
    def test_admin_update_banner(self, client: TestClient, admin_headers: dict):
        """Админ обновляет баннер"""
        # Создаём
        create_response = client.post("/api/admin/banners", headers=admin_headers, json={
            "image_url": "https://via.placeholder.com/1920x600",
            "text": "Old Text",
            "is_active": True
        })
        banner_id = create_response.json()["id"]
        
        # Обновляем
        response = client.put(f"/api/admin/banners/{banner_id}", headers=admin_headers, json={
            "image_url": "https://via.placeholder.com/1920x600",
            "text": "New Text",
            "is_active": True
        })
        
        assert response.status_code == 200
    
    def test_admin_delete_banner(self, client: TestClient, admin_headers: dict):
        """Админ удаляет баннер"""
        # Создаём
        create_response = client.post("/api/admin/banners", headers=admin_headers, json={
            "image_url": "https://via.placeholder.com/1920x600",
            "is_active": True
        })
        banner_id = create_response.json()["id"]
        
        # Удаляем
        response = client.delete(f"/api/admin/banners/{banner_id}", headers=admin_headers)
        
        assert response.status_code == 200


class TestStatsAPI:
    """Тесты API статистики"""
    
    def test_admin_get_stats(self, client: TestClient, admin_headers: dict):
        """Админ получает статистику"""
        response = client.get("/api/admin/stats", headers=admin_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "revenue" in data
        assert "orders" in data
        assert "customers" in data
    
    def test_admin_get_customers(self, client: TestClient, admin_headers: dict):
        """Админ получает список клиентов"""
        response = client.get("/api/admin/customers", headers=admin_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_admin_block_user(self, client: TestClient, test_user: User, admin_headers: dict):
        """Админ блокирует пользователя"""
        response = client.put(f"/api/admin/customers/{test_user.id}/block", headers=admin_headers, params={
            "block": True
        })
        
        assert response.status_code == 200
    
    def test_admin_get_couriers(self, client: TestClient, admin_headers: dict):
        """Админ получает курьеров"""
        response = client.get("/api/admin/couriers", headers=admin_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_admin_get_delivery_zones(self, client: TestClient, admin_headers: dict):
        """Админ получает зоны доставки"""
        response = client.get("/api/admin/delivery-zones", headers=admin_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
