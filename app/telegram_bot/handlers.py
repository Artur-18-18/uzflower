"""
Обработчики сообщений Telegram-бота.
"""

import re
import uuid
import logging
import httpx
from typing import Optional

from aiogram import Bot, Dispatcher, F, Router, types
from aiogram.types import Message, PhotoSize, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, InputFile
from aiogram.filters import CommandStart, Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.exceptions import TelegramBadRequest

from .config import settings
from .services import UzFlowerAPI

logger = logging.getLogger(__name__)

router = Router()

# Хранилище данных сессии (в памяти для простоты)
# В продакшене используйте Redis или базу данных
user_sessions: dict = {}


# ============================================================
# Машина состояний для оформления заказа
# ============================================================

class OrderState(StatesGroup):
    """Состояния для оформления заказа."""
    waiting_for_name = State()
    waiting_for_phone = State()
    waiting_for_delivery = State()  # Выбор доставки или самовывоза
    waiting_for_address = State()  # Адрес доставки (если нужна доставка)
    waiting_for_datetime = State()  # Выбор "Как можно скорее" или "Выбрать дату/время"
    waiting_for_custom_datetime = State() # Ввод конкретной даты и времени
    waiting_for_payment = State()  # Оплата - показ номера карты
    waiting_for_payment_proof = State()  # Загрузка скриншота чека
    waiting_for_comment = State()  # Комментарий к заказу


# ============================================================
# Хендлеры
# ============================================================

@router.channel_post()
async def handle_channel_post(message: Message, bot: Bot):
    """
    Обработка новых постов в канале.
    Автоматическое создание товара на сайте.
    Поддержка альбомов (несколько фото в одном посте).
    """
    # Пропускаем посты без текста
    caption = message.caption
    if not caption:
        return

    # Проверяем, есть ли фото
    if not message.photo:
        logger.warning("Пост без фото: %s", caption[:100])
        return

    # ВАЖНО: Telegram отправляет КАЖДОЕ фото в 3-4 размерах
    # message.photo содержит ВСЕ версии всех фото
    # Нужно сгруппировать их по оригинальным изображениям

    # Группируем фото по file_unique_id (одинаковые для всех версий одного фото)
    # и берём только максимальное качество (последнее в группе - наибольшее)
    photo_groups: dict[str, list] = {}

    for photo_size in message.photo:
        # file_unique_id одинаков для всех версий одного фото
        unique_id = photo_size.file_unique_id

        if unique_id not in photo_groups:
            photo_groups[unique_id] = []
        photo_groups[unique_id].append(photo_size)

    # Для каждой группы берём фото максимального качества (последнее в списке - largest)
    unique_photos: list[PhotoSize] = []
    for unique_id, sizes in photo_groups.items():
        # Сортируем по размеру файла (наибольшее = лучшее качество)
        sizes.sort(key=lambda p: p.file_size, reverse=True)
        unique_photos.append(sizes[0])  # Берём лучшее качество

    logger.info("📸 В сообщении %s фото (после группировки)", len(unique_photos))

    # Скачиваем и загружаем каждое фото на сервер
    photo_urls = []
    api = UzFlowerAPI()

    for i, photo in enumerate(unique_photos):
        try:
            # Скачиваем фото
            file = await bot.get_file(photo.file_id)
            photo_file = await bot.download_file(file.file_path)
            photo_bytes = photo_file.read()

            # Генерируем уникальное имя файла
            ext = file.file_path.split('.')[-1] if '.' in file.file_path else 'jpg'
            filename = f"{uuid.uuid4().hex}.{ext}"

            # Загружаем на сервер
            image_url = await api.upload_photo_from_telegram(photo_bytes, filename)

            if image_url:
                photo_urls.append(image_url)
                logger.info("✅ Фото %s/%s загружено: %s", i+1, len(unique_photos), image_url[:50])
            else:
                logger.warning("⚠️ Не удалось загрузить фото %s/%s", i+1, len(unique_photos))
        except Exception as e:
            logger.error("❌ Ошибка при загрузке фото %s: %s", i+1, e)

    if not photo_urls:
        logger.error("Нет фото для товара после загрузки")
        return

    # Парсим текст поста
    parsed_data = parse_post_caption(caption)

    if not parsed_data:
        logger.warning("Не удалось распарсить пост: %s", caption[:100])
        return

    # Создаём товар через API
    # Главное фото - первое из загруженных
    main_image_url = photo_urls[0]

    result = await api.create_product_from_telegram(
        name=parsed_data["name"],
        price=parsed_data["price"],
        description=parsed_data["description"],
        image_url=main_image_url
    )

    if result:
        product_id = result.get("id")
        logger.info("✅ Товар создан: %s (ID: %s)", parsed_data["name"], product_id)

        # Добавляем остальные фото как дополнительные
        if len(photo_urls) > 1:
            added_count = 0
            for photo_url in photo_urls[1:]:  # Все кроме главного
                try:
                    await api.add_product_image(product_id, photo_url)
                    added_count += 1
                except Exception as e:
                    logger.error("❌ Ошибка при добавлении фото: %s", e)

            logger.info("✅ Добавлено %s дополнительных фото к товару #%s", added_count, product_id)
    else:
        logger.error("❌ Не удалось создать товар: %s", parsed_data["name"])


@router.message(CommandStart())
async def handle_start_command(message: Message, command: CommandStart = None):
    """
    Обработка команды /start, включая deep-links.
    """
    args = command.args if command else None

    # Если есть аргументы (например, product_12)
    if args and args.startswith("product_"):
        match = re.match(r"product_(\d+)", args)
        if match:
            product_id = int(match.group(1))
            api = UzFlowerAPI()
            product = await api.get_product(product_id)

            if not product:
                await message.answer(
                    "❌ Товар не найден или уже недоступен.\n\n"
                    "Возможно, он был удалён или продан."
                )
                return

            # Показываем товар пользователю
            caption = (
                f"🌸 **Вы хотите заказать:**\n\n"
                f"**{product['name']}**\n\n"
                f"💰 Цена: {product['price']:,.0f} сум\n\n"
                f"📝 Описание:\n{product.get('description', 'Нет описания')}\n\n"
                f"Для оформления заказа нажмите кнопку ниже."
            )

            # Отправляем сообщение с фото (если есть) или без
            image_url = product.get("image_url", "")
            if image_url and image_url.strip():
                # Формируем полный URL для фото
                if not image_url.startswith(("http://", "https://")):
                    base_api_url = settings.api_url.rstrip("/")
                    image_url = f"{base_api_url}{image_url}"
                
                try:
                    # Скачиваем фото через httpx и отправляем файлом
                    async with httpx.AsyncClient() as client:
                        response = await client.get(image_url, timeout=10.0)
                        if response.status_code == 200:
                            # Создаем InputFile из байтов
                            photo_file = InputFile.from_memory(
                                response.content,
                                filename=f"product_{product_id}.jpg"
                            )
                            await message.answer_photo(
                                photo=photo_file,
                                caption=caption,
                                parse_mode="Markdown",
                                reply_markup=create_order_keyboard(product_id)
                            )
                            return
                        else:
                            logger.warning("⚠️ Не удалось скачать фото: HTTP %s", response.status_code)
                except Exception as e:
                    logger.warning("⚠️ Не удалось отправить фото товара: %s", e)
                    # Если фото не отправилось, отправим текст

            await message.answer(
                caption,
                parse_mode="Markdown",
                reply_markup=create_order_keyboard(product_id)
            )
            return

    # Если обычный /start (без аргументов или неизвестный формат)
    await message.answer(
        "🌸 **Добро пожаловать в UzFlower!**\n\n"
        "Я помогу вам оформить заказ на цветы.\n\n"
        "📋 **Как сделать заказ:**\n"
        "1. Выберите товар в канале или на сайте\n"
        "2. Нажмите кнопку «Заказать»\n"
        "3. Следуйте инструкциям бота\n\n"
        "🆘 **Команды:**\n"
        "/start - Начать сначала\n"
        "/help - Помощь",
        parse_mode="Markdown"
    )



@router.callback_query(F.data.startswith("order_"))
async def handle_order_callback(callback: types.CallbackQuery, state: FSMContext):
    """Нажата кнопка оформления заказа (callback)."""
    # Извлекаем ID товара из callback_data
    product_id = int(callback.data.split("_")[1])

    logger.info("🛒 Начат заказ товара #%s пользователем #%s", product_id, callback.from_user.id)

    await state.update_data(product_id=product_id)
    await state.set_state(OrderState.waiting_for_name)

    await callback.message.answer(
        "👤 **Шаг 1/7**\n\n"
        "Введите ваше имя:\n"
        "Например: Хасан\n\n"
        "❌ Отмена - отменить заказ",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="❌ Отмена")]],
            resize_keyboard=True
        )
    )

    await callback.answer()

# ============================================================
# Глобальные обработчики Отмены и Назад для заказов
# ============================================================

@router.message(F.text == "❌ Отмена", StateFilter(OrderState))
async def process_order_cancel(message: Message, state: FSMContext):
    """Отмена заказа."""
    await state.clear()
    await message.answer(
        "❌ Заказ отменен.\n\n"
        "Для повторного оформления отправьте /start",
        reply_markup=types.ReplyKeyboardRemove()
    )

@router.message(OrderState.waiting_for_name)
async def handle_name_input(message: Message, state: FSMContext):
    """Пользователь ввёл имя."""
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer(
            "❌ Заказ отменен.\n\n"
            "Для повторного оформления отправьте /start",
            reply_markup=types.ReplyKeyboardRemove()
        )
        return

    name = message.text.strip()
    if len(name) < 2:
        await message.answer("❌ Имя слишком короткое. Введите имя заново:")
        return

    await state.update_data(name=name)
    await state.set_state(OrderState.waiting_for_phone)

    await message.answer(
        "📱 **Шаг 2/7**\n\n"
        "Введите ваш номер телефона в формате +998-XX-XXX-XX-XX:\n"
        "Например: +998-90-123-45-67\n\n"
        "⬅️ Назад - вернуться к предыдущему шагу",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="⬅️ Назад")]],
            resize_keyboard=True
        )
    )

@router.message(OrderState.waiting_for_phone)
async def handle_phone_input(message: Message, state: FSMContext):
    """Пользователь ввёл номер телефона."""
    if message.text == "⬅️ Назад":
        await state.set_state(OrderState.waiting_for_name)
        await message.answer(
            "👤 **Шаг 1/7**\n\n"
            "Введите ваше имя:\n"
            "Например: Хасан\n\n"
            "❌ Отмена - отменить заказ",
            parse_mode="Markdown",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="❌ Отмена")]],
                resize_keyboard=True
            )
        )
        return
        
    phone = message.text.strip()
    if not phone.startswith("+") or len(phone) < 12:
        await message.answer("❌ Неверный формат. Нужно +998-88-123-45-67:")
        return

    await state.update_data(phone=phone)
    await state.set_state(OrderState.waiting_for_delivery)

    await message.answer(
        "🚚 **Шаг 3/7**\n\n"
        "Выберите способ получения заказа:",
        parse_mode="Markdown",
        reply_markup=create_delivery_keyboard()
    )



@router.callback_query(F.data.in_({"delivery_yes", "delivery_no"}))
async def handle_delivery_choice(callback: types.CallbackQuery, state: FSMContext):
    """Пользователь выбрал доставку или самовывоз."""
    delivery_option = callback.data == "delivery_yes"
    await state.update_data(delivery_option=delivery_option)

    # Стоимость доставки
    delivery_price = 50000 if delivery_option else 0
    await state.update_data(delivery_price=delivery_price)

    if delivery_option:
        await state.set_state(OrderState.waiting_for_address)
        await callback.message.answer(
            "**шаг 4/7**\n\n"
            "Введите адрес доставки:\n"
            "Например: Amir Temur 10, кв. 25\n\n"
            "⬅️ Назад - вернуться к выбору способа получения\n"
            "❌ Отмена - отменить заказ",
            parse_mode="Markdown",
            reply_markup=create_back_cancel_keyboard()
        )
    else:
        await state.set_state(OrderState.waiting_for_datetime)
        await callback.message.answer(
            "**шаг 5/7**\n\n"
            "Когда вам нужен заказ?\n"
            "Как можно скорее - Заказ будет готов в кратчайшие сроки\n"
            "\n\n"
            "⬅️ Назад - вернуться к выбору способа получения\n"
            "❌ Отмена - отменить заказ",
            parse_mode="Markdown",
            reply_markup=create_back_cancel_keyboard()
        )

    await callback.answer()


@router.message(OrderState.waiting_for_address)
async def handle_address_input(message: Message, state: FSMContext):
    """Пользователь ввёл адрес доставки."""
    if message.text == "⬅️ Назад":
        await state.set_state(OrderState.waiting_for_delivery)
        await message.answer(
            "🚚 Выберите способ получения заказа:",
            reply_markup=create_delivery_keyboard()
        )
        return

    address = message.text.strip()
    if len(address) < 5:
        await message.answer("❌ Адрес слишком короткий. Попробуйте ещё раз:")
        return

    await state.update_data(delivery_address=address)
    await state.set_state(OrderState.waiting_for_datetime)

    await message.answer(
        "🕒 **Шаг 5/7**\n\n"
        "Когда вам нужен заказ?",
        parse_mode="Markdown",
        reply_markup=create_datetime_keyboard()
    )


@router.message(F.text == "⬅️ Назад", OrderState.waiting_for_datetime)
async def back_to_address_or_delivery(message: Message, state: FSMContext):
    """Обработка текстовой кнопки Назад в состоянии выбора времени."""
    data = await state.get_data()
    if data.get("delivery_option"): # Была доставка
        await state.set_state(OrderState.waiting_for_address)
        await message.answer(
            "📍 Введите адрес доставки:",
            reply_markup=create_back_cancel_keyboard()
        )
    else: # Был самовывоз
        await state.set_state(OrderState.waiting_for_delivery)
        await message.answer(
            "🚚 Выберите способ получения заказа:",
            reply_markup=create_delivery_keyboard()
        )


@router.message(OrderState.waiting_for_datetime)
async def handle_datetime_text_input(message: Message, state: FSMContext):
    """Если пользователь ввёл текст вместо нажатия инлайн-кнопки."""
    await message.answer(
        "❌ Пожалуйста, выберите вариант из меню ниже или нажмите кнопки на клавиатуре:",
        reply_markup=create_datetime_keyboard()
    )


@router.callback_query(OrderState.waiting_for_datetime, F.data.in_({"datetime_asap", "datetime_custom", "datetime_back"}))
async def handle_datetime_choice(callback: types.CallbackQuery, state: FSMContext):
    """Пользователь выбрал дату/время доставки."""
    if callback.data == "datetime_back":
        data = await state.get_data()
        if data.get("delivery_option"): # Delivery
            await state.set_state(OrderState.waiting_for_address)
            await callback.message.answer("📍 Введите адрес доставки:", reply_markup=create_back_cancel_keyboard())
        else: # Pickup
            await state.set_state(OrderState.waiting_for_delivery)
            await callback.message.answer("🚚 Выберите способ получения:", reply_markup=create_delivery_keyboard())
        await callback.answer()
        return

    if callback.data == "datetime_asap":
        await state.update_data(delivery_date="ASAP", delivery_time="Как можно скорее")
        await proceed_to_payment(callback.message, state)
    else:
        await state.set_state(OrderState.waiting_for_custom_datetime)
        await callback.message.answer(
            "📅 **Шаг 6/7**\n\n"
            "Введите дату и время когда должен быть готов букет:\n"
            "Например: Завтра к 14:00 или 15.03\n\n"
            "⬅️ Назад - вернуться к выбору времени\n"
            "❌ Отмена - отменить заказ",
            parse_mode="Markdown",
            reply_markup=create_back_cancel_keyboard()
        )

    await callback.answer()


@router.message(OrderState.waiting_for_custom_datetime)
async def handle_custom_datetime_input(message: Message, state: FSMContext):
    """Пользователь ввёл дату/время доставки в свободном формате."""
    if message.text == "⬅️ Назад":
        await state.set_state(OrderState.waiting_for_datetime)
        await message.answer(
            "🕒 Когда вам нужен заказ?",
            reply_markup=create_datetime_keyboard()
        )
        return

    datetime_text = message.text.strip()
    await state.update_data(delivery_date=datetime_text, delivery_time=datetime_text)
    await proceed_to_payment(message, state)


async def proceed_to_payment(message: Message, state: FSMContext):
    """Перейти к этапу оплаты."""
    await state.set_state(OrderState.waiting_for_payment_proof)

    # Получаем номер карты из API
    api = UzFlowerAPI()
    card_number = await api.get_card_number()

    if not card_number:
        card_number = "4000 0000 0000 0000"  # Заглушка

    # Получаем данные заказа для отображения суммы
    data = await state.get_data()
    product_id = data.get("product_id")
    delivery_option = data.get("delivery_option", True)
    delivery_price = data.get("delivery_price", 0)

    product = await api.get_product(product_id)
    if not product:
        await message.answer("❌ Товар больше недоступен")
        await state.clear()
        return

    total_amount = product["price"] + delivery_price

    await message.answer(
        f"💳 **Шаг 7/7 - Оплата**\n\n"
        f"💰 Сумма заказа: <b>{total_amount:,.0f} сум</b>\n"
        f"  • Товар: {product['name']}\n"
        f"  • Доставка: {delivery_price:,.0f} сум\n\n"
        f"Оплатите заказ по номеру карты:\n"
        f"<code>{card_number}</code>\n\n"
        f"После оплаты отправьте <b>скриншот чека</b> (как фото).\n\n"
        f"⬅️ Назад - вернуться к дате/времени\n"
        f"❌ Отмена - отменить заказ",
        parse_mode="HTML",
        reply_markup=create_back_cancel_keyboard()
    )


@router.message(F.text == "⬅️ Назад", OrderState.waiting_for_payment_proof)
async def back_to_datetime(message: Message, state: FSMContext):
    await state.set_state(OrderState.waiting_for_datetime)
    await message.answer(
        "🕒 Когда вам нужен заказ?",
        reply_markup=create_datetime_keyboard()
    )


@router.message(F.photo, OrderState.waiting_for_payment_proof)
async def handle_payment_proof(message: Message, state: FSMContext):
    """Пользователь отправил скриншот чека."""
    # Получаем file_id скриншота
    photo = message.photo[-1]  # Берём фото наилучшего качества
    payment_proof_file_id = photo.file_id

    await state.update_data(payment_proof_file_id=payment_proof_file_id)
    await finalize_order(message, state)


@router.message(OrderState.waiting_for_payment_proof)
async def handle_payment_proof_text(message: Message, state: FSMContext):
    """Пользователь отправил текст вместо фото (или кнопку Назад/Отмена)."""
    # Текст Назад/Отмена уже обрабатывается глобально или специальными хендлерами выше
    await message.answer(
        "❌ Пожалуйста, отправьте скриншот чека (фотографией).\n\n"
        "⬅️ Назад - вернуться к выбору времени\n"
        "❌ Отмена - отменить заказ",
        reply_markup=create_back_cancel_keyboard()
    )


async def finalize_order(message: Message, state: FSMContext):
    """Завершение оформления заказа."""
    await state.set_state(None)  # Сброс состояния, но данные ещё в state

    # Получаем все данные заказа
    data = await state.get_data()
    product_id = data.get("product_id")
    name = data.get("name")
    phone = data.get("phone")
    delivery_option = data.get("delivery_option", True)
    delivery_address = data.get("delivery_address", "")
    delivery_date = data.get("delivery_date", "")
    delivery_time = data.get("delivery_time", "")
    delivery_price = data.get("delivery_price", 0)
    payment_proof_file_id = data.get("payment_proof_file_id")

    # Получаем Telegram ID пользователя
    customer_telegram_id = message.from_user.id
    logger.info("📦 Завершение заказа: product_id=%s, name=%s, phone=%s, telegram_id=%s", 
               product_id, name, phone, customer_telegram_id)

    # Проверяем, что product_id существует
    if not product_id:
        logger.error("❌ product_id не найден в состоянии!")
        await message.answer(
            "❌ Произошла ошибка: не указан товар.\n\n"
            "Пожалуйста, оформите заказ снова, выбрав товар на сайте."
        )
        await state.clear()
        return

    # Получаем товар
    api = UzFlowerAPI()
    product = await api.get_product(product_id)

    if not product:
        logger.error("❌ Товар #%s не найден в API", product_id)
        await message.answer("❌ Товар больше недоступен. Попробуйте оформить заказ снова.")
        await state.clear()
        return

    logger.info("✅ Товар получен: %s (цена: %s)", product.get('name', 'Unknown'), product.get('price', 0))

    total_amount = product["price"] + delivery_price

    # Получаем номер карты
    card_number = await api.get_card_number()
    if not card_number:
        card_number = "4000 0000 0000 0000"

    # Создаём заказ через API с передачей Telegram ID
    order = await api.create_order(
        product_id=product_id,
        customer_name=name,
        customer_phone=phone,
        delivery_address=delivery_address if delivery_option else "Самовывоз",
        comment=f"Доставка: {'Да' if delivery_option else 'Нет (Самовывоз)'}\nДата/время: {delivery_date}",
        delivery_option=delivery_option,
        delivery_price=delivery_price,
        card_number=card_number,
        customer_telegram_id=customer_telegram_id
    )

    if order:
        # Загружаем скриншот чека на сервер (если есть)
        payment_proof_url = None
        if payment_proof_file_id:
            temp_bot = None
            try:
                temp_bot = Bot(token=settings.bot_token)
                file = await temp_bot.get_file(payment_proof_file_id)
                photo_file = await temp_bot.download_file(file.file_path)
                photo_bytes = photo_file.read()

                # Загружаем на сервер
                payment_proof_url = await api.upload_payment_proof(
                    order_id=order["id"],
                    photo_bytes=photo_bytes,
                    filename=f"payment_proof_{order['id']}.jpg"
                )
            except Exception as e:
                logger.error("Ошибка при загрузке скриншота чека: %s", e)
            finally:
                # Закрываем сессию бота
                if temp_bot:
                    await temp_bot.session.close()

        # Обновляем заказ с proof
        if payment_proof_url:
            await api.update_order_payment(order["id"], payment_proof_url=payment_proof_url)

        # Отправляем уведомление в админ-бот
        logger.info("📢 Отправка уведомления в админ-бот для заказа #%s", order["id"])
        
        notification_sent = await api.send_order_to_admin_bot(
            order_id=order["id"],
            product_name=product["name"],
            product_price=product["price"],
            customer_name=name,
            customer_phone=phone,
            delivery_address=delivery_address if delivery_option else "Самовывоз",
            delivery_date=delivery_date,
            total_amount=total_amount,
            delivery_option=delivery_option,
            payment_proof_url=payment_proof_url,
            card_number=card_number
        )
        
        logger.info("   Результат отправки: %s", "✅ Успешно" if notification_sent else "❌ Ошибка")

        await message.answer(
            "✅ <b>Заказ оформлен!</b>\n\n"
            f"📦 Товар: {product['name']}\n"
            f"💰 Сумма: {total_amount:,.0f} сум\n"
            f"  • Товар: {product['price']:,.0f} сум\n"
            f"  • Доставка: {delivery_price:,.0f} сум\n\n"
            f"👤 Клиент: {name}\n"
            f"📞 Телефон: {phone}\n"
            f"🚚 Доставка: {'Да' if delivery_option else 'Нет (Самовывоз)'}\n"
            f"� Адрес: {delivery_address if delivery_option else 'Самовывоз'}\n"
            f"📅 Дата/время: {delivery_date}\n\n"
            f"💳 Оплата:\n"
            f"  • Номер карты: <code>{card_number}</code>\n"
            f"  • Чек отправлен\n\n"
            f"Администратор получит уведомление и проверит ваш заказ.\n"
            f"Менеджер свяжется с вами в ближайшее время.",
            parse_mode="HTML",
            reply_markup=types.ReplyKeyboardRemove()
        )
    else:
        await message.answer(
            "❌ Произошла ошибка при создании заказа.\n\n"
            "Пожалуйста, попробуйте позже или свяжитесь с нами напрямую."
        )

    await state.clear()


@router.message(Command("help"))
async def handle_help_command(message: Message):
    """Команда помощи."""
    await message.answer(
        "🌸 **UzFlower Bot**\n\n"
        "Я помогаю заказывать цветы через Telegram.\n\n"
        "📋 **Как сделать заказ:**\n"
        "1. Перейдите на сайт uzflower.uz\n"
        "2. Выберите букет\n"
        "3. Нажмите «Заказать в Telegram»\n"
        "4. Следуйте инструкциям бота\n\n"
        "🆘 **Команды:**\n"
        "/help - Эта справка\n"
        "/start - Начать сначала",
        parse_mode="Markdown"
    )


# ============================================================
# Вспомогательные функции
# ============================================================

def parse_post_caption(caption: str) -> Optional[dict]:
    """
    Распарсить текст поста из Telegram.

    Ожидаемые форматы:
    1. Название
       Ќона: 250000 суП
       Описание...

    2. Название - 250000 сум
       Описание...
    """
    lines = caption.strip().split("\n")

    name = None
    price = None
    description_parts = []

    # Паттерн для поиска цены
    price_pattern = re.compile(r"(\d{3,}(?:\s?\d{3})*)\s*(?:суП|UZS|UZS\.|sum)?", re.IGNORECASE)

    for i, line in enumerate(lines):
        line = line.strip()

        # Первая строка - название (если не цена)
        if i == 0 and not price_pattern.match(line):
            # Проверяем формат "Название - 250000 сум"
            match = re.match(r"(.+?)\s*[-–—]\s*(\d{3,})", line)
            if match:
                name = match.group(1).strip()
                price = int(match.group(2).replace(" ", ""))
            else:
                name = line
            continue

        # Ищем цену
        if price is None:
            match = price_pattern.search(line)
            if match:
                price = int(match.group(1).replace(" ", ""))
                # Если название ещё не найдено, берём часть до цены
                if not name:
                    name = line[:match.start()].strip(" -–—:")
                continue

        # Всё остальное - описание
        if line and not line.startswith("Ќона"):
            description_parts.append(line)

    if not name or not price:
        return None

    description = "\n".join(description_parts).strip()

    return {
        "name": name,
        "price": price,
        "description": description if description else name
    }


def create_order_keyboard(product_id: int):
    """Создать клавиатуру с кнопкой заказа."""
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🛒 Оформить заказ",
                    callback_data=f"order_{product_id}"
                )
            ]
        ]
    )
    return keyboard


def create_delivery_keyboard() -> InlineKeyboardMarkup:
    """Создать клавиатуру выбора доставки."""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🚚 Доставка", callback_data="delivery_yes"),
                InlineKeyboardButton(text="🏃 Самовывоз", callback_data="delivery_no")
            ],
            [
                InlineKeyboardButton(text="⬅️ Назад", callback_data="delivery_back")
            ]
        ]
    )
    return keyboard


def create_datetime_keyboard() -> InlineKeyboardMarkup:
    """Создать клавиатуру выбора даты/времени."""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="⏰ Как можно скорее", callback_data="datetime_asap"),
                InlineKeyboardButton(text="📅 Выбрать время", callback_data="datetime_custom")
            ],
            [
                InlineKeyboardButton(text="⬅️ Назад", callback_data="datetime_back")
            ]
        ]
    )
    return keyboard


def create_back_cancel_keyboard() -> ReplyKeyboardMarkup:
    """Создать клавиатуру с кнопками Назад/Отмена."""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="⬅️ Назад"), KeyboardButton(text="❌ Отмена")]
        ],
        resize_keyboard=True
    )
    return keyboard
