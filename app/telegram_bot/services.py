"""
Сервис для взаимодействия с API UzFlower.
"""

import logging
import httpx
from typing import Optional, Dict, Any

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
                timeout=60.0  # Увеличенный таймаут для медленных соединений
            )
        return self._client

    async def create_product_from_telegram(
        self,
        name: str,
        price: float,
        description: str,
        image_url: str,
        category_id: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Создать товар из Telegram-поста.

        Args:
            name: Название товара
            price: Цена
            description: Описание
            image_url: URL изображения
            category_id: ID категории (опционально)

        Returns:
            Данные созданного товара или None
        """
        try:
            client = await self._get_client()
            response = await client.post(
                "/api/telegram/products",
                json={
                    "name": name,
                    "price": price,
                    "description": description,
                    "image_url": image_url,
                    "category_id": category_id
                }
            )
            response.raise_for_status()
            data = response.json()
            logger.info("✅ Товар создан через Telegram: %s (ID: %s)", name, data.get("id"))
            return data
        except httpx.HTTPStatusError as e:
            logger.error("❌ Ошибка API при создании товара: %s - %s", e.response.status_code, e.response.text)
            return None
        except Exception as e:
            logger.error("❌ Ошибка при создании товара: %s", e)
            return None

    async def get_product(self, product_id: int) -> Optional[Dict[str, Any]]:
        """
        Получить товар по ID.

        Args:
            product_id: ID товара

        Returns:
            Данные товара или None
        """
        try:
            client = await self._get_client()
            request_url = f"/api/products/{product_id}"
            logger.info("🔍 Запрос товара #%s: GET %s%s", product_id, self.base_url, request_url)
            
            response = await client.get(request_url)
            logger.info("📥 Ответ API: статус=%s, тело=%s", response.status_code, response.text[:200] if response.text else "пусто")
            
            response.raise_for_status()
            data = response.json()
            logger.info("✅ Товар #%s получен успешно: %s", product_id, data.get("name", "unknown"))
            return data
        except httpx.HTTPStatusError as e:
            logger.error("❌ Ошибка API при получении товара #%s: статус=%s, ответ=%s", 
                        product_id, e.response.status_code, e.response.text)
            return None
        except Exception as e:
            logger.error("❌ Ошибка при получении товара #%s: %s", product_id, e, exc_info=True)
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
            # Используем специальный эндпоинт для Telegram-бота
            response = await client.post(
                f"/api/telegram/products/{product_id}/images",
                json={"image_url": image_url}
            )
            response.raise_for_status()
            logger.info("✅ Изображение добавлено к товару #%s", product_id)
            return True
        except httpx.HTTPStatusError as e:
            logger.error("❌ Ошибка API при добавлении изображения: %s", e.response.text)
            return False
        except Exception as e:
            logger.error("❌ Ошибка при добавлении изображения: %s", e)
            return False

    async def upload_photo_from_telegram(
        self,
        file_bytes: bytes,
        filename: str
    ) -> Optional[str]:
        """
        Загрузить фото из Telegram на сервер.

        Args:
            file_bytes: Байты файла
            filename: Имя файла

        Returns:
            URL загруженного фото или None
        """
        try:
            # Создаём multipart/form-data запрос
            files = {'file': (filename, file_bytes, 'image/jpeg')}
            data = {'api_secret': self.api_secret}

            # Используем прямой URL без base_url для загрузки файлов
            upload_url = f"{self.base_url}/api/telegram/upload-photo"

            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(upload_url, files=files, data=data)
                response.raise_for_status()
                result = response.json()
                url = result.get('url')
                logger.info("✅ Фото загружено из Telegram: %s", url)
                return url
        except Exception as e:
            logger.error("❌ Ошибка при загрузке фото из Telegram: %s", e)
            return None

    async def send_order_notification(
        self,
        product_name: str,
        product_price: float,
        customer_name: str,
        customer_phone: str,
        delivery_address: str,
        comment: Optional[str] = None
    ) -> bool:
        """
        Отправить уведомление о заказе владельцу.

        Args:
            product_name: Название товара
            product_price: Цена
            customer_name: Имя клиента
            customer_phone: Телефон клиента
            delivery_address: Адрес доставки
            comment: Комментарий (опционально)

        Returns:
            True если успешно
        """
        try:
            client = await self._get_client()
            response = await client.post(
                "/api/telegram/orders",
                json={
                    "product_name": product_name,
                    "product_price": product_price,
                    "customer_name": customer_name,
                    "customer_phone": customer_phone,
                    "delivery_address": delivery_address,
                    "comment": comment
                }
            )
            response.raise_for_status()
            logger.info("✅ Уведомление о заказе отправлено: %s", product_name)
            return True
        except httpx.HTTPStatusError as e:
            logger.error("❌ Ошибка API при отправке заказа: %s", e.response.text)
            return False
        except Exception as e:
            logger.error("❌ Ошибка при отправке заказа: %s", e)
            return False

    async def create_order(
        self,
        product_id: int,
        customer_name: str,
        customer_phone: str,
        delivery_address: str,
        comment: Optional[str] = None,
        delivery_option: bool = True,
        delivery_price: float = 0.0,
        card_number: Optional[str] = None,
        customer_telegram_id: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Создать заказ в системе.

        Args:
            product_id: ID товара
            customer_name: Имя клиента
            customer_phone: Телефон клиента
            delivery_address: Адрес доставки
            comment: Комментарий (опционально)
            delivery_option: True = доставка, False = самовывоз
            delivery_price: Стоимость доставки
            card_number: Номер карты для оплаты
            customer_telegram_id: Telegram ID клиента (для уведомлений)

        Returns:
            Данные заказа или None
        """
        try:
            client = await self._get_client()
            payload = {
                "product_id": product_id,
                "customer_name": customer_name,
                "customer_phone": customer_phone,
                "delivery_address": delivery_address,
                "comment": comment,
                "delivery_option": delivery_option,
                "delivery_price": delivery_price,
                "card_number": card_number
            }
            
            # Добавляем Telegram ID если указан
            if customer_telegram_id:
                payload["customer_telegram_id"] = customer_telegram_id
            
            logger.info("📤 Создание заказа: %s", payload)
            
            response = await client.post(
                "/api/telegram/orders/create",
                json=payload
            )
            response.raise_for_status()
            data = response.json()
            logger.info("✅ Заказ создан через Telegram: ID=%s", data.get("id"))
            return data
        except httpx.HTTPStatusError as e:
            logger.error("❌ Ошибка API при создании заказа: %s", e.response.text)
            return None
        except Exception as e:
            logger.error("❌ Ошибка при создании заказа: %s", e)
            return None

    async def get_card_number(self) -> Optional[str]:
        """
        Получить номер карты для оплаты.

        Returns:
            Номер карты или None
        """
        try:
            client = await self._get_client()
            response = await client.get("/api/telegram/card-number")
            response.raise_for_status()
            data = response.json()
            return data.get("card_number")
        except Exception as e:
            logger.error("❌ Ошибка при получении номера карты: %s", e)
            return None

    async def upload_payment_proof(
        self,
        order_id: int,
        photo_bytes: bytes,
        filename: str
    ) -> Optional[str]:
        """
        Загрузить скриншот чека на сервер.

        Args:
            order_id: ID заказа
            photo_bytes: Байты файла
            filename: Имя файла

        Returns:
            URL загруженного файла или None
        """
        try:
            files = {'file': (filename, photo_bytes, 'image/jpeg')}
            data = {'api_secret': self.api_secret}
            upload_url = f"{self.base_url}/api/telegram/orders/{order_id}/payment-proof"

            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(upload_url, files=files, data=data)
                response.raise_for_status()
                result = response.json()
                url = result.get('url')
                logger.info("✅ Скриншот чека загружен для заказа #%s: %s", order_id, url)
                return url
        except Exception as e:
            logger.error("❌ Ошибка при загрузке скриншота чека: %s", e)
            return None

    async def update_order_payment(
        self,
        order_id: int,
        payment_proof_url: Optional[str] = None
    ) -> bool:
        """
        Обновить информацию об оплате заказа.

        Args:
            order_id: ID заказа
            payment_proof_url: URL скриншота чека

        Returns:
            True если успешно
        """
        try:
            client = await self._get_client()
            response = await client.put(
                f"/api/telegram/orders/{order_id}/payment",
                json={"payment_proof_url": payment_proof_url}
            )
            response.raise_for_status()
            logger.info("✅ Оплата заказа #%s обновлена", order_id)
            return True
        except Exception as e:
            logger.error("❌ Ошибка при обновлении оплаты заказа: %s", e)
            return False

    async def send_order_to_admin_bot(
        self,
        order_id: int,
        product_name: str,
        product_price: float,
        customer_name: str,
        customer_phone: str,
        delivery_address: str,
        delivery_date: str,
        total_amount: float,
        delivery_option: bool,
        payment_proof_url: Optional[str] = None,
        card_number: Optional[str] = None
    ) -> bool:
        """
        Отправить уведомление о заказе в админ-бот.

        Args:
            order_id: ID заказа
            product_name: Название товара
            product_price: Цена товара
            customer_name: Имя клиента
            customer_phone: Телефон клиента
            delivery_address: Адрес доставки
            delivery_date: Дата/время доставки
            total_amount: Общая сумма
            delivery_option: True = доставка, False = самовывоз
            payment_proof_url: URL скриншота чека
            card_number: Номер карты

        Returns:
            True если успешно
        """
        try:
            logger.info("🔔 Вызов send_order_to_admin_bot для заказа #%s", order_id)
            logger.info("   API URL: %s", self.base_url)
            
            client = await self._get_client()
            payload = {
                "order_id": order_id,
                "product_name": product_name,
                "product_price": product_price,
                "customer_name": customer_name,
                "customer_phone": customer_phone,
                "delivery_address": delivery_address,
                "delivery_date": delivery_date,
                "total_amount": total_amount,
                "delivery_option": delivery_option,
                "payment_proof_url": payment_proof_url,
                "card_number": card_number
            }
            
            logger.info("📤 Отправка POST /api/telegram/orders/notify-admin с данными: %s", 
                       {**payload, "payment_proof_url": "PRESENT" if payment_proof_url else None})
            
            response = await client.post(
                "/api/telegram/orders/notify-admin",
                json=payload
            )
            
            logger.info("   Статус ответа: %s", response.status_code)
            response.raise_for_status()
            logger.info("✅ Уведомление о заказе #%s отправлено в админ-бот", order_id)
            return True
        except Exception as e:
            logger.error("❌ Ошибка при отправке уведомления в админ-бот: %s", e, exc_info=True)
            return False
