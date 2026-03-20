"""
Сервис для взаимодействия с API UzFlower из админ-бота.
"""

import logging
import httpx
from typing import Optional, Dict, Any, List

from .config import settings

logger = logging.getLogger(__name__)


class UzFlowerAPI:
    """Клиент для взаимодействия с API UzFlower."""

    def __init__(self, base_url: str = None, api_secret: str = None):
        self.base_url = base_url or settings.api_url
        self.api_secret = api_secret or settings.api_secret
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Получить HTTP клиент с заголовками авторизации."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers={
                    "Authorization": f"Bearer {self.api_secret}",
                    "Content-Type": "application/json"
                },
                timeout=30.0
            )
        return self._client

    # ============================================================
    # Order API
    # ============================================================

    async def get_order(self, order_id: int) -> Optional[Dict[str, Any]]:
        """
        Получить заказ по ID.

        Args:
            order_id: ID заказа

        Returns:
            Данные заказа или None
        """
        try:
            client = await self._get_client()
            response = await client.get(f"/api/admin/bot/orders/{order_id}")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error("❌ Ошибка API при получении заказа: %s", e)
            return None
        except Exception as e:
            logger.error("❌ Ошибка при получении заказа: %s", e)
            return None

    async def update_order_status(
        self,
        order_id: int,
        status: str,
        admin_id: int
    ) -> bool:
        """
        Обновить статус заказа.

        Args:
            order_id: ID заказа
            status: Новый статус (accepted, cancelled, completed)
            admin_id: ID администратора

        Returns:
            True если успешно
        """
        try:
            client = await self._get_client()
            response = await client.patch(
                f"/api/admin/orders/{order_id}/status",
                json={
                    "status": status,
                    "admin_id": admin_id,
                    "api_secret": self.api_secret
                }
            )
            response.raise_for_status()
            logger.info("✅ Статус заказа #%s обновлён: %s", order_id, status)
            return True
        except httpx.HTTPStatusError as e:
            logger.error("❌ Ошибка API при обновлении статуса: %s", e.response.text)
            return False
        except Exception as e:
            logger.error("❌ Ошибка при обновлении статуса: %s", e)
            return False

    async def get_user_telegram_id(self, user_id: int) -> Optional[int]:
        """
        Получить Telegram ID пользователя по ID в БД.

        Args:
            user_id: ID пользователя в БД

        Returns:
            Telegram ID или None
        """
        try:
            client = await self._get_client()
            response = await client.get(f"/api/users/{user_id}/telegram")
            response.raise_for_status()
            data = response.json()
            return data.get("telegram_id")
        except Exception as e:
            logger.error("❌ Ошибка при получении Telegram ID: %s", e)
            return None

    # ============================================================
    # Product API
    # ============================================================

    async def get_products(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Получить список товаров.

        Args:
            limit: Максимальное количество товаров

        Returns:
            Список товаров
        """
        try:
            client = await self._get_client()
            response = await client.get(f"/api/admin/bot/products?limit={limit}")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error("❌ Ошибка при получении товаров: %s", e)
            return []

    async def create_product(
        self,
        name: str,
        price: float,
        description: str,
        category_slug: str,
        image_url: Optional[str] = None,
        composition: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Создать товар.

        Args:
            name: Название товара
            price: Цена
            description: Описание
            category_slug: Слаг категории
            image_url: URL изображения (опционально)

        Returns:
            Данные созданного товара или None
        """
        try:
            client = await self._get_client()
            response = await client.post(
                "/api/admin/bot/products",
                json={
                    "name": name,
                    "price": price,
                    "description": description,
                    "composition": composition,
                    "category_slug": category_slug,
                    "image_url": image_url
                }
            )
            response.raise_for_status()
            logger.info("✅ Товар создан: %s", name)
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error("❌ Ошибка API при создании товара: %s", e.response.text)
            return None
        except Exception as e:
            logger.error("❌ Ошибка при создании товара: %s", e)
            return None

    async def update_product(
        self,
        product_id: int,
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """
        Обновить товар.

        Args:
            product_id: ID товара
            **kwargs: Поля для обновления (name, price, description, etc.)

        Returns:
            Данные обновлённого товара или None
        """
        try:
            client = await self._get_client()
            response = await client.put(
                f"/api/admin/bot/products/{product_id}",
                json=kwargs
            )
            response.raise_for_status()
            logger.info("✅ Товар #%s обновлён", product_id)
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error("❌ Ошибка API при обновлении товара: %s", e.response.text)
            return None
        except Exception as e:
            logger.error("❌ Ошибка при обновлении товара: %s", e)
            return None

    async def add_product_image(self, product_id: int, image_url: str) -> bool:
        """
        Добавить изображение к товару.

        Args:
            product_id: ID товара
            image_url: URL изображения

        Returns:
            True если успешно
        """
        try:
            client = await self._get_client()
            response = await client.post(
                f"/api/admin/bot/products/{product_id}/images",
                json={"image_url": image_url}
            )
            response.raise_for_status()
            result = response.json()
            logger.info("✅ Изображение добавлено к товару #%s (ID изображения: %s)", product_id, result.get('id'))
            return True
        except httpx.HTTPStatusError as e:
            logger.error("❌ Ошибка API при добавлении изображения к товару #%s: %s", product_id, e.response.text)
            return False
        except Exception as e:
            logger.error("❌ Ошибка при добавлении изображения к товару #%s: %s", product_id, e)
            return False

    async def delete_product(self, product_id: int) -> bool:
        """
        Удалить товар.

        Args:
            product_id: ID товара

        Returns:
            True если успешно
        """
        try:
            client = await self._get_client()
            response = await client.delete(f"/api/admin/bot/products/{product_id}")
            response.raise_for_status()
            logger.info("✅ Товар #%s удалён", product_id)
            return True
        except httpx.HTTPStatusError as e:
            logger.error("❌ Ошибка API при удалении товара: %s", e.response.text)
            return False
        except Exception as e:
            logger.error("❌ Ошибка при удалении товара: %s", e)
            return False

    async def upload_image(self, file_bytes: bytes, filename: str) -> Optional[str]:
        """
        Загрузить изображение на сервер.
        """
        try:
            # Подготовка данных: файл в files
            files = {
                "file": (filename, file_bytes, "image/jpeg")
            }

            # Создаём клиент с заголовком Authorization
            async with httpx.AsyncClient(
                base_url=self.base_url,
                timeout=60.0,
                headers={
                    "Authorization": f"Bearer {self.api_secret}"
                }
            ) as client:
                logger.info("📤 Загрузка фото на сервер: %s, размер: %s байт", filename, len(file_bytes))
                response = await client.post(
                    "/api/admin/bot/upload",
                    files=files
                )
                logger.info("📥 Ответ сервера: статус=%s", response.status_code)
                if response.status_code != 200:
                    logger.error("❌ Ошибка сервера: %s", response.text)
                response.raise_for_status()
                data_resp = response.json()
                logger.info("✅ Фото загружено: %s", data_resp.get("url"))
                return data_resp.get("url")
        except httpx.HTTPStatusError as e:
            logger.error("❌ HTTP ошибка при загрузке фото: %s - %s", e.response.status_code, e.response.text)
            return None
        except Exception as e:
            logger.error("❌ Ошибка при загрузке фото: %s", e, exc_info=True)
            return None

    # ============================================================
    # Stats API
    # ============================================================

    async def get_stats(self) -> Dict[str, Any]:
        """
        Получить статистику магазина.

        Returns:
            Данные статистики
        """
        try:
            client = await self._get_client()
            response = await client.get("/api/admin/bot/stats")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error("❌ Ошибка при получении статистики: %s", e)
            return {
                "total_products": 0,
                "orders_today": 0,
                "revenue_today": 0,
                "total_users": 0,
                "total_orders": 0,
                "total_revenue": 0
            }

    # ============================================================
    # Orders API
    # ============================================================

    async def get_orders(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Получить список заказов.

        Args:
            limit: Максимальное количество заказов

        Returns:
            Список заказов
        """
        try:
            client = await self._get_client()
            response = await client.get(f"/api/admin/bot/orders?limit={limit}")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error("❌ Ошибка при получении заказов: %s", e)
            return []

    # ============================================================
    # Broadcast API
    # ============================================================

    async def send_broadcast(self, message: str) -> Dict[str, Any]:
        """
        Отправить рассылку всем пользователям.

        Args:
            message: Текст сообщения

        Returns:
            Результат рассылки
        """
        try:
            client = await self._get_client()
            response = await client.post(
                "/api/admin/broadcast",
                json={"message": message}
            )
            response.raise_for_status()
            logger.info("✅ Рассылка отправлена")
            return response.json()
        except Exception as e:
            logger.error("❌ Ошибка при отправке рассылки: %s", e)
            return {"sent_count": 0}

    # ============================================================
    # Settings API (номер карты и сообщение)
    # ============================================================

    async def get_card_number(self) -> str:
        """Получить текущий номер карты."""
        try:
            client = await self._get_client()
            response = await client.get("/api/admin/bot/settings/card")
            response.raise_for_status()
            data = response.json()
            return data.get("card_number", "")
        except Exception as e:
            logger.error("❌ Ошибка при получении номера карты: %s", e)
            return ""

    async def set_card_number(self, card_number: str) -> bool:
        """Сохранить номер карты."""
        try:
            client = await self._get_client()
            response = await client.post(
                "/api/admin/bot/settings/card",
                json={"card_number": card_number}
            )
            response.raise_for_status()
            logger.info("✅ Номер карты обновлён: %s", card_number)
            return True
        except Exception as e:
            logger.error("❌ Ошибка при обновлении номера карты: %s", e)
            return False

    async def get_customer_message(self) -> str:
        """Получить текущее сообщение покупателю."""
        try:
            client = await self._get_client()
            response = await client.get("/api/admin/bot/settings/message")
            response.raise_for_status()
            data = response.json()
            return data.get("message", "")
        except Exception as e:
            logger.error("❌ Ошибка при получении сообщения: %s", e)
            return ""

    async def set_customer_message(self, message: str) -> bool:
        """Сохранить сообщение покупателю."""
        try:
            client = await self._get_client()
            response = await client.post(
                "/api/admin/bot/settings/message",
                json={"message": message}
            )
            response.raise_for_status()
            logger.info("✅ Сообщение покупателю обновлено")
            return True
        except Exception as e:
            logger.error("❌ Ошибка при обновлении сообщения: %s", e)
            return False

    async def send_message_to_customer(
        self,
        customer_telegram_id: int,
        message: str,
        order_id: int
    ) -> bool:
        """
        Отправить сообщение покупателю через основной бот.

        Args:
            customer_telegram_id: Telegram ID покупателя
            message: Текст сообщения
            order_id: ID заказа

        Returns:
            True если успешно
        """
        try:
            client = await self._get_client()
            response = await client.post(
                "/api/admin/send-message-to-customer",
                json={
                    "customer_telegram_id": customer_telegram_id,
                    "message": message,
                    "order_id": order_id
                }
            )
            response.raise_for_status()
            logger.info("✅ Сообщение отправлено покупателю #%s (заказ #%s)", 
                       customer_telegram_id, order_id)
            return True
        except httpx.HTTPStatusError as e:
            logger.error("❌ Ошибка API при отправке сообщения: %s", e.response.text)
            return False
        except Exception as e:
            logger.error("❌ Ошибка при отправке сообщения покупателю: %s", e)
            return False

    async def save_support_message(
        self,
        user_id: int,
        message: str,
        is_admin: bool = True
    ) -> bool:
        """
        Сохранить сообщение поддержки в базу.

        Args:
            user_id: ID пользователя
            message: Текст сообщения
            is_admin: True если сообщение от админа

        Returns:
            True если успешно
        """
        try:
            client = await self._get_client()
            response = await client.post(
                "/api/admin/support-message",
                json={
                    "user_id": user_id,
                    "message": message,
                    "is_admin": is_admin
                }
            )
            response.raise_for_status()
            return True
        except Exception as e:
            logger.error("❌ Ошибка при сохранении сообщения поддержки: %s", e)
            return False

    async def notify_customer_order_status(
        self,
        order_id: int,
        status: str,
        customer_telegram_id: int,
        customer_name: str
    ) -> bool:
        """
        Отправить уведомление покупателю об изменении статуса заказа.

        Args:
            order_id: ID заказа
            status: Новый статус (accepted, cancelled)
            customer_telegram_id: Telegram ID покупателя
            customer_name: Имя покупателя

        Returns:
            True если успешно
        """
        try:
            logger.info("📬 Вызов notify_customer_order_status: order_id=%s, status=%s, telegram_id=%s", 
                       order_id, status, customer_telegram_id)
            
            client = await self._get_client()
            payload = {
                "order_id": order_id,
                "status": status,
                "customer_telegram_id": customer_telegram_id,
                "customer_name": customer_name
            }
            
            logger.info("   Отправка POST /api/admin/notify-customer-order-status: %s", payload)
            
            response = await client.post(
                "/api/admin/notify-customer-order-status",
                json=payload
            )
            
            logger.info("   Статус ответа: %s", response.status_code)
            logger.info("   Тело ответа: %s", response.text)
            
            response.raise_for_status()
            logger.info("✅ Покупатель #%s уведомлён о статусе заказа #%s: %s", 
                       customer_telegram_id, order_id, status)
            return True
        except httpx.HTTPStatusError as e:
            logger.error("❌ Ошибка API при уведомлении покупателя: %s | Ответ: %s", 
                        e, e.response.text if hasattr(e, 'response') else 'N/A')
            return False
        except Exception as e:
            logger.error("❌ Ошибка при уведомлении покупателя: %s", e, exc_info=True)
            return False
