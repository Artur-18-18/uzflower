"""
Обработчики сообщений Admin Telegram-бота.
Версия 2.0 с полным функционалом админ-панели.
"""

import logging
import os
import re
import secrets
from datetime import datetime
from decimal import Decimal

from aiogram import Bot, Dispatcher, F, Router, types
from aiogram.types import (
    Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton, FSInputFile
)
from aiogram.filters import CommandStart, Command, StateFilter
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from .config import settings
from .services import UzFlowerAPI

logger = logging.getLogger(__name__)

router = Router()


# ============================================================
# States (состояния FSM)
# ============================================================

class AdminState(StatesGroup):
    """Состояния для диалогов с админом."""
    # Добавление товара
    waiting_product_name = State()
    waiting_product_price = State()
    waiting_product_composition = State()
    waiting_product_description = State()
    waiting_product_category = State()
    waiting_product_photo = State()

    # Редактирование товара
    waiting_edit_select = State()
    waiting_edit_field = State()
    waiting_edit_name = State()
    waiting_edit_price = State()
    waiting_edit_description = State()
    waiting_edit_composition = State()

    # Редактирование номера карты
    waiting_card_number = State()

    # Сообщение покупателю (шаблон)
    waiting_customer_message = State()

    # Связь с покупателем (чат)
    waiting_chat_order_select = State()  # Выбор заказа для чата
    waiting_chat_message = State()  # Отправка сообщения покупателю

    # Удаление товара
    waiting_delete_product = State()

    # Рассылка
    waiting_broadcast = State()


# ============================================================
# Вспомогательные функции
# ============================================================

def check_admin_access(user_id: int) -> bool:
    """
    Проверить доступ администратора.
    
    Args:
        user_id: Telegram ID пользователя
        
    Returns:
        True если пользователь имеет доступ
    """
    is_admin = settings.is_admin(user_id)
    if not is_admin:
        logger.warning("⚠️ Попытка доступа от неавторизованного пользователя: %s", user_id)
    return is_admin


def create_admin_menu() -> ReplyKeyboardMarkup:
    """
    Создать главное меню админ-бота.

    Returns:
        ReplyKeyboardMarkup с кнопками меню
    """
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="📦 Добавить товар"),
                KeyboardButton(text="✏️ Редактировать товар")
            ],
            [
                KeyboardButton(text="💳 Изменить номер карты"),
                KeyboardButton(text="💬 Связаться с покупателем")
            ],
            [
                KeyboardButton(text="📋 Список товаров"),
                KeyboardButton(text="❌ Удалить товар")
            ],
            [
                KeyboardButton(text="📊 Статистика"),
                KeyboardButton(text="📦 Заказы")
            ],
            [
                KeyboardButton(text="📢 Рассылка")
            ]
        ],
        resize_keyboard=True,
        persistent=True
    )
    return keyboard


def create_product_categories_keyboard() -> InlineKeyboardMarkup:
    """
    Создать клавиатуру с категориями товаров.
    
    Returns:
        InlineKeyboardMarkup с категориями
    """
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🌸 8 Марта", callback_data="cat_8-march")],
            [InlineKeyboardButton(text="🎂 День рождения", callback_data="cat_birthday")],
            [InlineKeyboardButton(text="💕 Романтика", callback_data="cat_romance")],
            [InlineKeyboardButton(text="💒 Свадьба", callback_data="cat_wedding")],
            [InlineKeyboardButton(text="🏢 Корпоративные", callback_data="cat_corporate")],
            [InlineKeyboardButton(text="📦 Цветы в коробке", callback_data="cat_box-flowers")],
        ]
    )
    return keyboard


def create_admin_back_keyboard() -> ReplyKeyboardMarkup:
    """
    Создать клавиатуру с кнопкой "Назад".
    
    Returns:
        ReplyKeyboardMarkup с кнопкой назад
    """
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="❌ Отмена")]
        ],
        resize_keyboard=True
    )
    return keyboard


def create_product_list_keyboard(products: list, prefix: str = "prod") -> InlineKeyboardMarkup:
    """
    Создать клавиатуру со списком товаров.
    
    Args:
        products: Список товаров
        prefix: Префикс для callback_data
        
    Returns:
        InlineKeyboardMarkup с товарами
    """
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text=f"{p['name']} - {p['price']:,.0f} сум", 
                callback_data=f"{prefix}_{p['id']}"
            )]
            for p in products[:10]  # Максимум 10 товаров
        ]
    )
    keyboard.inline_keyboard.append([InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")])
    return keyboard


def create_edit_field_keyboard(product_id: int) -> InlineKeyboardMarkup:
    """
    Создать клавиатуру для выбора поля редактирования.
    
    Args:
        product_id: ID товара
        
    Returns:
        InlineKeyboardMarkup с полями
    """
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📝 Название", callback_data=f"editf_name_{product_id}")],
            [InlineKeyboardButton(text="💰 Цена", callback_data=f"editf_price_{product_id}")],
            [InlineKeyboardButton(text="📄 Описание", callback_data=f"editf_desc_{product_id}")],
            [InlineKeyboardButton(text="🌿 Состав", callback_data=f"editf_comp_{product_id}")],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")]
        ]
    )
    return keyboard


# ============================================================
# Хендлеры главного меню
# ============================================================

@router.message(CommandStart())
async def handle_start(message: Message):
    """Команда /start для админ-бота."""
    user_id = message.from_user.id

    if not check_admin_access(user_id):
        await message.answer(
            "❌ <b>У вас нет доступа к этому боту!</b>\n\n"
            "Только авторизованные администраторы могут использовать этот бот.\n"
            "Обратитесь к владельцу магазина."
        )
        return

    await message.answer(
        f"👋 <b>Добро пожаловать, {message.from_user.full_name}!</b>\n\n"
        "🌸 <b>UzFlower Admin Panel</b>\n\n"
        "Я помогаю управлять магазином цветов.\n"
        "Выберите действие в меню ниже 👇",
        reply_markup=create_admin_menu()
    )


@router.message(Command("help"))
async def handle_help(message: Message):
    """Команда помощи."""
    user_id = message.from_user.id

    if not check_admin_access(user_id):
        return

    await message.answer(
        "🌸 <b>UzFlower Admin Bot - Справка</b>\n\n"
        "📋 <b>Возможности:</b>\n"
        "• 📦 Добавление товаров\n"
        "• ✏️ Редактирование товаров (название, цена, описание)\n"
        "• 💳 Изменение номера карты для оплаты\n"
        "• 💬 Настройка сообщения покупателям\n"
        "• 📋 Просмотр и удаление товаров\n"
        "• 📊 Статистика заказов и доходов\n"
        "• 📦 Просмотр последних заказов\n"
        "• 📢 Рассылка сообщений пользователям\n\n"
        "🔔 <b>Команды:</b>\n"
        "/start - Главное меню\n"
        "/help - Эта справка\n"
        "/stats - Статистика\n"
        "/orders - Последние заказы"
    )


# ============================================================
# Глобальная отмена
# ============================================================

@router.message(F.text == "❌ Отмена")
async def handle_cancel(message: Message, state: FSMContext):
    """Отмена любого действия."""
    current_state = await state.get_state()
    if current_state:
        await state.clear()
        await message.answer("❌ Действие отменено", reply_markup=create_admin_menu())
    else:
        await message.answer("Вы в главном меню", reply_markup=create_admin_menu())


@router.callback_query(F.data == "cancel")
async def handle_cancel_callback(callback: CallbackQuery, state: FSMContext):
    """Отмена через inline кнопку."""
    await state.clear()
    await callback.message.answer("❌ Действие отменено", reply_markup=create_admin_menu())
    await callback.answer()


# ============================================================
# 📦 Добавить товар
# ============================================================

@router.message(F.text == "📦 Добавить товар")
async def handle_add_product(message: Message, state: FSMContext):
    """Начать процесс добавления товара."""
    user_id = message.from_user.id

    if not check_admin_access(user_id):
        return

    await state.set_state(AdminState.waiting_product_name)
    await message.answer(
        "📦 <b>Добавление товара</b>\n\n"
        "Введите <b>название товара</b>:\n"
        "(например: Букет \"Red Love\")\n\n"
        "❌ Отмена - вернуться в меню",
        reply_markup=create_admin_back_keyboard()
    )


@router.message(AdminState.waiting_product_name)
async def process_product_name(message: Message, state: FSMContext):
    """Сохранить название товара."""
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("❌ Добавление товара отменено", reply_markup=create_admin_menu())
        return

    await state.update_data(product_name=message.text)
    await state.set_state(AdminState.waiting_product_price)
    await message.answer(
        "💰 Введите <b>цену товара</b> (в сумах):\n"
        "(например: 180000)\n\n"
        "❌ Отмена - вернуться в меню",
        reply_markup=create_admin_back_keyboard()
    )


@router.message(AdminState.waiting_product_price)
async def process_product_price(message: Message, state: FSMContext):
    """Сохранить цену товара."""
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("❌ Добавление товара отменено", reply_markup=create_admin_menu())
        return

    # Проверяем, что цена - число
    try:
        price = float(message.text.replace(",", "").replace(" ", ""))
        if price <= 0:
            raise ValueError()
    except ValueError:
        await message.answer(
            "❌ Неверный формат цены!\n"
            "Введите число больше 0 (например: 180000)\n\n"
            "❌ Отмена - вернуться в меню",
            reply_markup=create_admin_back_keyboard()
        )
        return

    await state.update_data(product_price=price)
    await state.set_state(AdminState.waiting_product_composition)
    await message.answer(
        "🌿 Введите <b>состав товара</b> (через запятую или списком):\n"
        "(например: 15 роз, упаковка, лента)\n\n"
        "❌ Отмена - вернуться в меню",
        reply_markup=create_admin_back_keyboard()
    )


@router.message(AdminState.waiting_product_composition)
async def process_product_composition(message: Message, state: FSMContext):
    """Сохранить состав товара."""
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("❌ Добавление товара отменено", reply_markup=create_admin_menu())
        return

    await state.update_data(product_composition=message.text)
    await state.set_state(AdminState.waiting_product_description)
    await message.answer(
        "📝 Введите <b>описание товара</b>:\n"
        "(особенности, для кого подходит)\n\n"
        "❌ Отмена - вернуться в меню",
        reply_markup=create_admin_back_keyboard()
    )


@router.message(AdminState.waiting_product_description)
async def process_product_description(message: Message, state: FSMContext):
    """Сохранить описание товара."""
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("❌ Добавление товара отменено", reply_markup=create_admin_menu())
        return

    await state.update_data(product_description=message.text)
    await state.set_state(AdminState.waiting_product_category)
    await message.answer(
        "📂 Выберите <b>категорию товара</b>:",
        reply_markup=create_product_categories_keyboard()
    )


@router.callback_query(AdminState.waiting_product_category, F.data.startswith("cat_"))
async def process_product_category(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """Сохранить категорию и запросить фото."""
    category_slug = callback.data.replace("cat_", "")
    await state.update_data(product_category=category_slug)
    await state.set_state(AdminState.waiting_product_photo)

    await callback.message.answer(
        "📸 <b>Отправьте фотографии товара</b>:\n\n"
        "• Можно отправить <b>несколько фото сразу</b> (до 10)\n"
        "• Для <b>максимального качества</b> отправляйте как 'Файл'\n"
        "• Первое фото будет <b>главным</b>\n\n"
        "✅ Когда все фото отправлены, нажмите кнопку ниже\n\n"
        "❌ Отмена - вернуться в меню",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="✅ Готово, создаю товар")],
                [KeyboardButton(text="❌ Отмена")]
            ],
            resize_keyboard=True
        )
    )
    await callback.answer()


@router.message(AdminState.waiting_product_photo, F.photo)
async def process_product_photo(message: Message, state: FSMContext, bot: Bot):
    """Сохранить одно фото в список. В одном сообщении Telegram присылает одно фото в 3–4 размерах — берём только лучшее качество, чтобы в галерее не было дубликатов одной картинки."""
    data = await state.get_data()
    photos = data.get("photos", [])

    if len(photos) >= 10:
        await message.answer("⚠️ Достигнут лимит 10 фото. Нажмите «Готово» или отмените.")
        return

    try:
        # В одном сообщении — одно логическое фото, но в нескольких размерах. Берём только один (лучший по размеру файла).
        best_photo = max(message.photo, key=lambda p: (p.file_size or 0) or (p.width or 0) * (p.height or 0))
        unique_id = best_photo.file_unique_id

        if any(p["unique_id"] == unique_id for p in photos):
            await message.answer("Это фото уже добавлено. Отправьте другое фото или нажмите «Готово».")
            return

        logger.info("📸 Одно фото: %sx%s, %s байт", best_photo.width, best_photo.height, best_photo.file_size)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        random_hex = secrets.token_hex(4)
        unique_filename = f"telegram_{timestamp}_{random_hex}_{unique_id}.jpg"

        # В FSM храним только file_id и метаданные — без bytes, иначе состояние «раздувается» и теряются остальные фото
        photos.append({
            "file_id": best_photo.file_id,
            "unique_id": unique_id,
            "filename": unique_filename,
        })
        await state.update_data(photos=photos)

        limit_warning = "\n⚠️ <b>Достигнут лимит (10 фото)</b>" if len(photos) >= 10 else ""
        await message.answer(
            f"✅ <b>Фото принято!</b>\n\n"
            f"📸 В галерее фото: <b>{len(photos)}</b>\n"
            f"Максимум: 10 (разные кадры){limit_warning}\n\n"
            "📤 Отправьте ещё <b>другое</b> фото или нажмите «Готово»",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[
                    [KeyboardButton(text="✅ Готово, создаю товар")],
                    [KeyboardButton(text="❌ Отмена")]
                ],
                resize_keyboard=True
            )
        )
    except Exception as e:
        logger.error("❌ Ошибка при загрузке фото: %s", e)
        await message.answer(
            "❌ Ошибка при обработке фото. Попробуйте ещё раз.",
            reply_markup=create_admin_back_keyboard()
        )


@router.message(AdminState.waiting_product_photo, F.document)
async def process_product_document(message: Message, state: FSMContext, bot: Bot):
    """Сохранить фото, отправленное как файл (без сжатия)."""
    data = await state.get_data()
    photos = data.get("photos", [])

    if len(photos) >= 10:
        await message.answer("⚠️ Достигнут лимит 10 фото. Это фото не добавлено.")
        return

    # Проверка типа файла
    if not message.document.mime_type or not message.document.mime_type.startswith("image/"):
        await message.answer("❌ Это не изображение! Пожалуйста, отправляйте только фото.")
        return

    try:
        import os

        unique_id = message.document.file_unique_id
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        random_hex = secrets.token_hex(4)
        original_filename = message.document.file_name or f"photo_{unique_id}.jpg"
        ext = os.path.splitext(original_filename)[1] if '.' in original_filename else '.jpg'
        unique_filename = f"telegram_doc_{timestamp}_{random_hex}{ext}"

        # В FSM храним только file_id и метаданные (без bytes), чтобы не терять остальные фото
        photos.append({
            "file_id": message.document.file_id,
            "unique_id": unique_id,
            "filename": unique_filename,
        })
        await state.update_data(photos=photos)

        await message.answer(
            f"✅ <b>Файл принят (оригинальное качество)!</b>\n\n"
            f"📸 Загружено фото: {len(photos)}\n"
            f"📤 Отправьте ещё фото или нажмите 'Готово'",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[
                    [KeyboardButton(text="✅ Готово, создаю товар")],
                    [KeyboardButton(text="❌ Отмена")]
                ],
                resize_keyboard=True
            )
        )
    except Exception as e:
        logger.error("❌ Ошибка при загрузке документа: %s", e)
        await message.answer("❌ Ошибка при обработке файла.")


@router.message(AdminState.waiting_product_photo, F.text == "✅ Готово, создаю товар")
async def finish_product_photos(message: Message, state: FSMContext, bot: Bot):
    """Завершить загрузку фото и создать товар."""
    data = await state.get_data()
    photos = data.get("photos", [])

    if not photos:
        await message.answer(
            "❌ Вы не отправили ни одного фото!\n"
            "Отправьте хотя бы одно фото товара.",
            reply_markup=create_admin_back_keyboard()
        )
        return

    product_name = data.get("product_name")
    product_price = data.get("product_price")
    product_description = data.get("product_description")
    product_composition = data.get("product_composition")
    product_category = data.get("product_category")

    api = UzFlowerAPI()

    try:
        import io

        # Сначала скачиваем каждое фото по file_id, затем загружаем на сервер (bytes в FSM не храним, чтобы не терять список)
        image_urls = []
        for i, photo_data in enumerate(photos):
            file_id = photo_data.get("file_id")
            filename = photo_data.get("filename", f"photo_{i+1}.jpg")
            if not file_id:
                logger.warning("⚠️ Нет file_id для фото %s", i+1)
                continue
            try:
                photo_file = io.BytesIO()
                await bot.download(file_id, destination=photo_file)
                photo_bytes = photo_file.getvalue()
            except Exception as e:
                logger.warning("⚠️ Не удалось скачать фото %s с Telegram: %s", i+1, e)
                continue
            if not photo_bytes:
                continue
            logger.info("📸 Загрузка фото %s/%s на сервер, размер: %s байт", i+1, len(photos), len(photo_bytes))
            image_url = await api.upload_image(file_bytes=photo_bytes, filename=filename)
            if image_url:
                image_urls.append(image_url)
                logger.info("✅ Фото %s загружено: %s", i+1, image_url[:60])
            else:
                logger.warning("⚠️ Не удалось загрузить фото %s на сервер", i+1)

        if not image_urls:
            await message.answer(
                "❌ Не удалось загрузить ни одно фото!\n"
                "Проверьте подключение к серверу.",
                reply_markup=create_admin_menu()
            )
            await state.clear()
            return

        # Главное фото (первое)
        main_image_url = image_urls[0]

        # Создаём товар с главным фото
        result = await api.create_product(
            name=product_name,
            price=product_price,
            description=product_description,
            composition=product_composition,
            category_slug=product_category,
            image_url=main_image_url
        )

        if not result:
            await message.answer(
                "❌ Ошибка при создании товара.\n"
                "Проверьте логи сервера.",
                reply_markup=create_admin_menu()
            )
            await state.clear()
            return

        product_id = result.get("id")
        logger.info("✅ Создан товар ID=%s, название=%s", product_id, product_name)

        # Если есть дополнительные фото, загружаем их через API
        if len(image_urls) > 1 and product_id:
            logger.info("📸 Добавляю %s дополнительных изображений к товару #%s", len(image_urls) - 1, product_id)
            for i, img_url in enumerate(image_urls[1:], start=1):
                success = await api.add_product_image(product_id, img_url)
                if success:
                    logger.info("✅ Изображение %s/%s добавлено: %s", i, len(image_urls) - 1, img_url[:50])
                else:
                    logger.error("❌ Не удалось добавить изображение %s: %s", i, img_url[:50])

        # Формируем сообщение
        msg_text = (
            f"✅ <b>Товар добавлен!</b>\n\n"
            f"🌸 {product_name}\n"
            f"💰 {product_price:,.0f} сум\n"
            f"📝 {product_description[:50]}...\n\n"
            f"📸 <b>Загружено фото:</b> {len(image_urls)}"
        )

        if len(image_urls) < len(photos):
            msg_text += f"\n\n⚠️ {len(photos) - len(image_urls)} фото не загрузились"

        await message.answer(
            msg_text,
            reply_markup=create_admin_menu()
        )

    except Exception as e:
        logger.error("❌ Ошибка при добавлении товара: %s", e, exc_info=True)
        await message.answer(
            f"❌ Ошибка: {str(e)}\n"
            "Попробуйте ещё раз.",
            reply_markup=create_admin_menu()
        )

    await state.clear()


@router.message(AdminState.waiting_product_photo, F.text == "❌ Отмена")
async def cancel_product_photo(message: Message, state: FSMContext):
    """Отменить добавление товара."""
    await state.clear()
    await message.answer("❌ Добавление товара отменено", reply_markup=create_admin_menu())


# ============================================================
# ✏️ Редактировать товар
# ============================================================

@router.message(F.text == "✏️ Редактировать товар")
async def handle_edit_product(message: Message, state: FSMContext):
    """Начать процесс редактирования товара."""
    user_id = message.from_user.id

    if not check_admin_access(user_id):
        return

    api = UzFlowerAPI()
    products = await api.get_products()
    
    if not products:
        await message.answer(
            "✏️ <b>Редактирование товара</b>\n\n"
            "Нет товаров для редактирования.\n"
            "Добавьте товар кнопкой 📦 Добавить товар",
            reply_markup=create_admin_menu()
        )
        return

    await state.set_state(AdminState.waiting_edit_select)
    await state.update_data(products=products)
    
    await message.answer(
        "✏️ <b>Редактирование товара</b>\n\n"
        "Выберите товар для редактирования:",
        reply_markup=create_product_list_keyboard(products, prefix="edit")
    )


@router.callback_query(AdminState.waiting_edit_select, F.data.startswith("edit_"))
async def select_product_to_edit(callback: CallbackQuery, state: FSMContext):
    """Выбрать товар для редактирования."""
    product_id = int(callback.data.replace("edit_", ""))
    data = await state.get_data()
    products = data.get("products", [])
    
    # Находим товар
    product = next((p for p in products if p["id"] == product_id), None)
    
    if not product:
        await callback.answer("❌ Товар не найден", show_alert=True)
        return
    
    await state.update_data(edit_product_id=product_id, edit_product=product)
    await state.set_state(AdminState.waiting_edit_field)
    
    await callback.message.answer(
        f"✏️ <b>Редактирование товара</b>\n\n"
        f"🌸 <b>{product['name']}</b>\n"
        f"💰 Цена: {product['price']:,.0f} сум\n"
        f"📝 Описание: {product.get('description', 'Нет')[:100]}\n\n"
        "Что хотите изменить?",
        reply_markup=create_edit_field_keyboard(product_id)
    )
    await callback.answer()


@router.callback_query(AdminState.waiting_edit_field, F.data.startswith("editf_name_"))
async def edit_product_name(callback: CallbackQuery, state: FSMContext):
    """Начать редактирование названия."""
    await state.set_state(AdminState.waiting_edit_name)
    data = await state.get_data()
    product = data.get("edit_product", {})
    
    await callback.message.answer(
        f"📝 <b>Редактирование названия</b>\n\n"
        f"Текущее: <b>{product.get('name', '')}</b>\n\n"
        "Введите <b>новое название</b>:\n\n"
        "❌ Отмена - вернуться в меню",
        reply_markup=create_admin_back_keyboard()
    )
    await callback.answer()


@router.callback_query(AdminState.waiting_edit_field, F.data.startswith("editf_price_"))
async def edit_product_price(callback: CallbackQuery, state: FSMContext):
    """Начать редактирование цены."""
    await state.set_state(AdminState.waiting_edit_price)
    data = await state.get_data()
    product = data.get("edit_product", {})
    
    await callback.message.answer(
        f"💰 <b>Редактирование цены</b>\n\n"
        f"Текущая: <b>{product.get('price', 0):,.0f} сум</b>\n\n"
        "Введите <b>новую цену</b> (в сумах):\n"
        "(например: 250000)\n\n"
        "❌ Отмена - вернуться в меню",
        reply_markup=create_admin_back_keyboard()
    )
    await callback.answer()


@router.callback_query(AdminState.waiting_edit_field, F.data.startswith("editf_desc_"))
async def edit_product_description(callback: CallbackQuery, state: FSMContext):
    """Начать редактирование описания."""
    await state.set_state(AdminState.waiting_edit_description)
    data = await state.get_data()
    product = data.get("edit_product", {})
    
    await callback.message.answer(
        f"📄 <b>Редактирование описания</b>\n\n"
        f"Текущее:\n<i>{product.get('description', 'Нет описания')[:200]}</i>\n\n"
        "Введите <b>новое описание</b>:\n\n"
        "❌ Отмена - вернуться в меню",
        reply_markup=create_admin_back_keyboard()
    )
    await callback.answer()


@router.callback_query(AdminState.waiting_edit_field, F.data.startswith("editf_comp_"))
async def edit_product_composition(callback: CallbackQuery, state: FSMContext):
    """Начать редактирование состава."""
    await state.set_state(AdminState.waiting_edit_composition)
    data = await state.get_data()
    product = data.get("edit_product", {})
    
    await callback.message.answer(
        f"🌿 <b>Редактирование состава</b>\n\n"
        f"Текущий:\n<i>{product.get('composition', 'Не указан')}</i>\n\n"
        "Введите <b>новый состав</b>:\n\n"
        "❌ Отмена - вернуться в меню",
        reply_markup=create_admin_back_keyboard()
    )
    await callback.answer()


@router.message(AdminState.waiting_edit_name)
async def process_edit_name(message: Message, state: FSMContext):
    """Сохранить новое название."""
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("❌ Редактирование отменено", reply_markup=create_admin_menu())
        return

    data = await state.get_data()
    product_id = data.get("edit_product_id")
    new_name = message.text.strip()
    
    api = UzFlowerAPI()
    result = await api.update_product(product_id, name=new_name)
    
    if result:
        await message.answer(
            f"✅ <b>Название обновлено!</b>\n\n"
            f"Новое название: <b>{new_name}</b>",
            reply_markup=create_admin_menu()
        )
    else:
        await message.answer(
            "❌ Ошибка при обновлении названия.\n"
            "Попробуйте ещё раз.",
            reply_markup=create_admin_menu()
        )
    
    await state.clear()


@router.message(AdminState.waiting_edit_price)
async def process_edit_price(message: Message, state: FSMContext):
    """Сохранить новую цену."""
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("❌ Редактирование отменено", reply_markup=create_admin_menu())
        return

    try:
        new_price = float(message.text.replace(",", "").replace(" ", ""))
        if new_price <= 0:
            raise ValueError()
    except ValueError:
        await message.answer(
            "❌ Неверный формат цены!\n"
            "Введите число больше 0 (например: 250000)\n\n"
            "❌ Отмена - вернуться в меню",
            reply_markup=create_admin_back_keyboard()
        )
        return

    data = await state.get_data()
    product_id = data.get("edit_product_id")
    
    api = UzFlowerAPI()
    result = await api.update_product(product_id, price=new_price)
    
    if result:
        await message.answer(
            f"✅ <b>Цена обновлена!</b>\n\n"
            f"Новая цена: <b>{new_price:,.0f} сум</b>",
            reply_markup=create_admin_menu()
        )
    else:
        await message.answer(
            "❌ Ошибка при обновлении цены.\n"
            "Попробуйте ещё раз.",
            reply_markup=create_admin_menu()
        )
    
    await state.clear()


@router.message(AdminState.waiting_edit_description)
async def process_edit_description(message: Message, state: FSMContext):
    """Сохранить новое описание."""
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("❌ Редактирование отменено", reply_markup=create_admin_menu())
        return

    data = await state.get_data()
    product_id = data.get("edit_product_id")
    new_desc = message.text.strip()
    
    api = UzFlowerAPI()
    result = await api.update_product(product_id, description=new_desc)
    
    if result:
        await message.answer(
            "✅ <b>Описание обновлено!</b>",
            reply_markup=create_admin_menu()
        )
    else:
        await message.answer(
            "❌ Ошибка при обновлении описания.\n"
            "Попробуйте ещё раз.",
            reply_markup=create_admin_menu()
        )
    
    await state.clear()


@router.message(AdminState.waiting_edit_composition)
async def process_edit_composition(message: Message, state: FSMContext):
    """Сохранить новый состав."""
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("❌ Редактирование отменено", reply_markup=create_admin_menu())
        return

    data = await state.get_data()
    product_id = data.get("edit_product_id")
    new_comp = message.text.strip()
    
    api = UzFlowerAPI()
    result = await api.update_product(product_id, composition=new_comp)
    
    if result:
        await message.answer(
            "✅ <b>Состав обновлен!</b>",
            reply_markup=create_admin_menu()
        )
    else:
        await message.answer(
            "❌ Ошибка при обновлении состава.\n"
            "Попробуйте ещё раз.",
            reply_markup=create_admin_menu()
        )
    
    await state.clear()


# ============================================================
# 💳 Изменить номер карты
# ============================================================

@router.message(F.text == "💳 Изменить номер карты")
async def handle_change_card(message: Message, state: FSMContext):
    """Начать процесс изменения номера карты."""
    user_id = message.from_user.id

    if not check_admin_access(user_id):
        return

    # Получаем текущий номер карты из API
    api = UzFlowerAPI()
    current_card = await api.get_card_number()
    if not current_card:
        current_card = "Не установлен"
    
    await state.set_state(AdminState.waiting_card_number)
    await message.answer(
        f"💳 <b>Изменение номера карты</b>\n\n"
        f"Текущий номер: <code>{current_card}</code>\n\n"
        "Введите <b>новый номер карты</b>:\n\n"
        "❌ Отмена - вернуться в меню",
        reply_markup=create_admin_back_keyboard()
    )


@router.message(AdminState.waiting_card_number)
async def process_card_number(message: Message, state: FSMContext):
    """Сохранить новый номер карты."""
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("❌ Изменение отменено", reply_markup=create_admin_menu())
        return

    new_card = message.text.strip()
    
    # Простая валидация (16 цифр, возможно с пробелами)
    card_digits = re.sub(r"\D", "", new_card)
    if len(card_digits) != 16:
        await message.answer(
            "❌ Неверный формат номера карты!\n"
            "Введите 16 цифр (например: 4000000000000000)\n\n"
            "❌ Отмена - вернуться в меню",
            reply_markup=create_admin_back_keyboard()
        )
        return

    # Форматируем номер (группы по 4 цифры)
    formatted_card = f"{card_digits[:4]} {card_digits[4:8]} {card_digits[8:12]} {card_digits[12:16]}"
    
    # Сохраняем через API
    api = UzFlowerAPI()
    success = await api.set_card_number(formatted_card)
    
    await state.clear()
    
    if success:
        await message.answer(
            f"✅ <b>Номер карты обновлён!</b>\n\n"
            f"Новый номер: <code>{formatted_card}</code>\n\n"
            "Теперь покупатели будут видеть этот номер при оплате.",
            reply_markup=create_admin_menu()
        )
    else:
        await message.answer(
            f"⚠️ <b>Номер карты сохранён локально</b>\n\n"
            f"Номер: <code>{formatted_card}</code>\n\n"
            "Примечание: Не удалось сохранить на сервере, но номер запомнен.",
            reply_markup=create_admin_menu()
        )


# ============================================================
# 💬 Сообщение покупателю
# ============================================================

@router.message(F.text == "💬 Сообщение покупателю")
async def handle_customer_message(message: Message, state: FSMContext):
    """Начать процесс изменения сообщения покупателю."""
    user_id = message.from_user.id

    if not check_admin_access(user_id):
        return

    # Получаем текущее сообщение из API
    api = UzFlowerAPI()
    current_message = await api.get_customer_message()
    if not current_message:
        current_message = "Спасибо за заказ! Наш менеджер скоро свяжется с вами."
    
    await state.set_state(AdminState.waiting_customer_message)
    await message.answer(
        f"💬 <b>Сообщение покупателю</b>\n\n"
        f"Текущее сообщение:\n"
        f"<i>{current_message}</i>\n\n"
        "Введите <b>новое сообщение</b>:\n\n"
        "❌ Отмена - вернуться в меню",
        reply_markup=create_admin_back_keyboard()
    )


@router.message(AdminState.waiting_customer_message)
async def process_customer_message(message: Message, state: FSMContext):
    """Сохранить новое сообщение покупателю."""
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("❌ Изменение отменено", reply_markup=create_admin_menu())
        return

    new_message = message.text.strip()
    
    # Сохраняем через API
    api = UzFlowerAPI()
    success = await api.set_customer_message(new_message)
    
    await state.clear()
    
    if success:
        await message.answer(
            f"✅ <b>Сообщение обновлено!</b>\n\n"
            f"Новое сообщение:\n"
            f"<i>{new_message}</i>\n\n"
            "Теперь покупатели будут видеть это сообщение после заказа.",
            reply_markup=create_admin_menu()
        )
    else:
        await message.answer(
            f"⚠️ <b>Сообщение сохранено локально</b>\n\n"
            f"Сообщение:\n<i>{new_message}</i>\n\n"
            "Примечание: Не удалось сохранить на сервере.",
            reply_markup=create_admin_menu()
        )


# ============================================================
# 💬 Связаться с покупателем (чат)
# ============================================================

@router.message(F.text == "💬 Связаться с покупателем")
async def handle_chat_with_customer(message: Message, state: FSMContext):
    """Начать чат с покупателем."""
    user_id = message.from_user.id

    if not check_admin_access(user_id):
        return

    await state.set_state(AdminState.waiting_chat_order_select)
    await message.answer(
        "💬 <b>Связь с покупателем</b>\n\n"
        "Введите <b>номер заказа</b> (например: 123),\n"
        "чтобы начать чат с покупателем.\n\n"
        "❌ Отмена - вернуться в меню",
        reply_markup=create_admin_back_keyboard()
    )


@router.message(AdminState.waiting_chat_order_select)
async def process_chat_order_select(message: Message, state: FSMContext):
    """Обработка выбора заказа для чата."""
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("❌ Действие отменено", reply_markup=create_admin_menu())
        return

    # Проверяем, что введено число
    try:
        order_id = int(message.text.strip())
    except ValueError:
        await message.answer(
            "❌ Пожалуйста, введите <b>число</b> - номер заказа.\n\n"
            "❌ Отмена - вернуться в меню",
            reply_markup=create_admin_back_keyboard()
        )
        return

    # Получаем заказ из API
    api = UzFlowerAPI()
    order = await api.get_order(order_id)

    if not order:
        await message.answer(
            f"❌ Заказ #{order_id} не найден.\n\n"
            "Попробуйте другой номер или отмените действие.\n"
            "❌ Отмена - вернуться в меню",
            reply_markup=create_admin_back_keyboard()
        )
        return

    # Получаем Telegram ID покупателя
    customer_telegram_id = None
    user_id_from_order = order.get("user_id")
    
    if user_id_from_order:
        customer_telegram_id = await api.get_user_telegram_id(user_id_from_order)
    
    # Если не нашли через user_id, пробуем получить из заказа напрямую
    if not customer_telegram_id:
        customer_telegram_id = order.get("customer_telegram_id")

    if not customer_telegram_id:
        await message.answer(
            f"❌ Не удалось найти Telegram ID покупателя для заказа #{order_id}.\n\n"
            f"Покупатель: {order.get('customer_name', 'Не указан')}\n"
            f"Телефон: {order.get('phone', 'Не указан')}\n\n"
            "Возможно, покупатель не авторизован в Telegram.\n"
            "❌ Отмена - вернуться в меню",
            reply_markup=create_admin_back_keyboard()
        )
        return

    # Сохраняем информацию о чате в состоянии
    await state.update_data(
        chat_order_id=order_id,
        customer_telegram_id=customer_telegram_id,
        customer_name=order.get("customer_name", "Не указан")
    )
    await state.set_state(AdminState.waiting_chat_message)

    # Информация о заказе
    status_emoji = {
        "pending": "⏳",
        "accepted": "✅",
        "cancelled": "❌",
        "delivering": "🚚",
        "completed": "⭐"
    }.get(order.get("status", "pending"), "⏳")

    await message.answer(
        f"✅ <b>Чат с покупателем заказа #{order_id}</b>\n\n"
        f"👤 Покупатель: {order.get('customer_name', 'Не указан')}\n"
        f"📞 Телефон: {order.get('phone', 'Не указан')}\n"
        f"📦 Товар: {order.get('product_name', 'Не указан')}\n"
        f"💰 Сумма: {order.get('total_amount', 0):,.0f} сум\n"
        f"{status_emoji} Статус: {order.get('status', 'pending')}\n\n"
        f"Теперь введите <b>сообщение</b>, которое будет отправлено покупателю.\n\n"
        f"❌ Отмена - завершить чат",
        reply_markup=create_admin_back_keyboard()
    )


@router.message(AdminState.waiting_chat_message)
async def process_chat_message(message: Message, state: FSMContext):
    """Отправка сообщения покупателю."""
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("💬 Чат завершён", reply_markup=create_admin_menu())
        return

    # Пропускаем пересылку сообщений (они обрабатываются отдельно)
    if message.forward_from or message.forward_from_chat:
        await message.answer(
            "❌ Пожалуйста, введите текст сообщения, а не пересылайте.\n\n"
            "❌ Отмена - завершить чат"
        )
        return

    message_text = message.text.strip()

    # Получаем данные из состояния
    data = await state.get_data()
    customer_telegram_id = data.get("customer_telegram_id")
    order_id = data.get("chat_order_id")
    customer_name = data.get("customer_name")

    if not customer_telegram_id:
        await message.answer(
            "❌ Ошибка: не найден Telegram ID покупателя.\n\n"
            "Чат завершён.",
            reply_markup=create_admin_menu()
        )
        await state.clear()
        return

    # Отправляем сообщение покупателю через основной бот
    api = UzFlowerAPI()
    success = await api.send_message_to_customer(
        customer_telegram_id=customer_telegram_id,
        message=message_text,
        order_id=order_id
    )

    if success:
        # Сохраняем сообщение в базу как исходящее от админа
        await api.save_support_message(
            user_id=data.get("user_id_from_order"),
            message=message_text,
            is_admin=True
        )

        await message.answer(
            f"✅ <b>Сообщение отправлено!</b>\n\n"
            f"👤 Покупатель: {customer_name}\n"
            f"📦 Заказ: #{order_id}\n"
            f"📝 Текст: {message_text[:100]}{'...' if len(message_text) > 100 else ''}\n\n"
            "Введите следующее сообщение или отмените чат.\n"
            "❌ Отмена - завершить чат",
            reply_markup=create_admin_back_keyboard()
        )
    else:
        await message.answer(
            f"❌ <b>Ошибка при отправке</b>\n\n"
            "Возможно, покупатель заблокировал бота или не запускал его.\n\n"
            "Введите другое сообщение или отмените чат.\n"
            "❌ Отмена - завершить чат",
            reply_markup=create_admin_back_keyboard()
        )


# ============================================================
# 📋 Список товаров
# ============================================================

@router.message(F.text == "📋 Список товаров")
async def handle_product_list(message: Message):
    """Показать список товаров."""
    user_id = message.from_user.id

    if not check_admin_access(user_id):
        return

    api = UzFlowerAPI()
    products = await api.get_products()
    
    if not products:
        await message.answer(
            "📋 <b>Список товаров</b>\n\n"
            "Пока нет товаров в каталоге.\n"
            "Добавьте первый товар! 📦",
            reply_markup=create_admin_menu()
        )
        return

    # Формируем сообщение со списком товаров
    text = f"📋 <b>Список товаров ({len(products)} шт.)</b>\n\n"
    for i, product in enumerate(products[:20], 1):  # Максимум 20 товаров
        sale_badge = " 🔥" if product.get('is_sale') else ""
        text += f"{i}. <b>{product['name']}</b> — {product['price']:,.0f} сум{sale_badge}\n"
    
    if len(products) > 20:
        text += f"\n... и ещё {len(products) - 20} товаров"
    
    await message.answer(text, reply_markup=create_admin_menu())


# ============================================================
# ❌ Удалить товар
# ============================================================

@router.message(F.text == "❌ Удалить товар")
async def handle_delete_product(message: Message, state: FSMContext):
    """Начать процесс удаления товара."""
    user_id = message.from_user.id

    if not check_admin_access(user_id):
        return

    api = UzFlowerAPI()
    products = await api.get_products()
    
    if not products:
        await message.answer(
            "❌ Нет товаров для удаления.",
            reply_markup=create_admin_menu()
        )
        return

    await state.set_state(AdminState.waiting_delete_product)
    await state.update_data(products=products)
    
    await message.answer(
        "❌ <b>Удаление товара</b>\n\n"
        "Выберите товар для удаления:",
        reply_markup=create_product_list_keyboard(products, prefix="prod")
    )


@router.callback_query(AdminState.waiting_delete_product, F.data.startswith("prod_"))
async def process_delete_product(callback: CallbackQuery, state: FSMContext):
    """Удалить товар."""
    product_id = int(callback.data.replace("prod_", ""))
    data = await state.get_data()
    products = data.get("products", [])
    
    # Находим товар
    product = next((p for p in products if p["id"] == product_id), None)
    
    if not product:
        await callback.answer("❌ Товар не найден", show_alert=True)
        return
    
    api = UzFlowerAPI()
    success = await api.delete_product(product_id)
    
    if success:
        await callback.message.answer(
            f"✅ <b>Товар удалён!</b>\n\n"
            f"{product['name']} удалён из каталога.",
            reply_markup=create_admin_menu()
        )
    else:
        await callback.answer("❌ Ошибка при удалении товара", show_alert=True)
    
    await state.clear()
    await callback.answer()


# ============================================================
# 📊 Статистика
# ============================================================

@router.message(F.text == "📊 Статистика")
async def handle_stats_button(message: Message):
    """Показать статистику (кнопка)."""
    await _show_stats(message)


@router.message(Command("stats"))
async def handle_stats_command(message: Message):
    """Показать статистику (команда)."""
    await _show_stats(message)


async def _show_stats(message: Message):
    """Показать статистику магазина."""
    user_id = message.from_user.id

    if not check_admin_access(user_id):
        return

    api = UzFlowerAPI()
    
    # Получаем статистику из API
    stats = await api.get_stats()
    
    text = (
        "📊 <b>Статистика магазина</b>\n\n"
        f"📦 Товаров: {stats.get('total_products', 0)}\n"
        f"🛒 Заказов сегодня: {stats.get('orders_today', 0)}\n"
        f"💰 Доход сегодня: {stats.get('revenue_today', 0):,.0f} сум\n"
        f"👥 Пользователей: {stats.get('total_users', 0)}\n\n"
        f"📈 За всё время:\n"
        f"  • Заказов: {stats.get('total_orders', 0)}\n"
        f"  • Доход: {stats.get('total_revenue', 0):,.0f} сум"
    )
    
    await message.answer(text, reply_markup=create_admin_menu())


# ============================================================
# 📦 Заказы  
# ============================================================

@router.message(F.text == "📦 Заказы")
async def handle_orders_button(message: Message):
    """Показать заказы (кнопка)."""
    await _show_orders(message)


@router.message(Command("orders"))
async def handle_orders_command(message: Message):
    """Показать заказы (команда)."""
    await _show_orders(message)


async def _show_orders(message: Message):
    """Показать последние заказы."""
    user_id = message.from_user.id

    if not check_admin_access(user_id):
        return

    api = UzFlowerAPI()
    orders = await api.get_orders(limit=10)
    
    if not orders:
        await message.answer(
            "📦 <b>Заказы</b>\n\n"
            "Пока нет заказов.",
            reply_markup=create_admin_menu()
        )
        return

    text = "📦 <b>Последние заказы</b>\n\n"
    for order in orders[:10]:
        status_emoji = {
            "pending": "🆕",
            "new": "🆕",
            "accepted": "✅",
            "cancelled": "❌",
            "delivering": "🚚",
            "completed": "✔️"
        }.get(order.get("status", "pending"), "📦")
        
        text += (
            f"{status_emoji} <b>Заказ #{order['id']}</b>\n"
            f"  👤 {order.get('customer_name', 'Аноним')}\n"
            f"  💰 {order.get('total_amount', 0):,.0f} сум\n"
        )
        
        address = order.get('delivery_address', '')
        if address:
            text += f"  📍 {address[:30]}...\n"
        
        text += "\n"
    
    await message.answer(text, reply_markup=create_admin_menu())


# ============================================================
# 📢 Рассылка
# ============================================================

@router.message(F.text == "📢 Рассылка")
async def handle_broadcast(message: Message, state: FSMContext):
    """Начать процесс рассылки."""
    user_id = message.from_user.id

    if not check_admin_access(user_id):
        return

    await state.set_state(AdminState.waiting_broadcast)
    await message.answer(
        "📢 <b>Рассылка сообщений</b>\n\n"
        "Введите текст сообщения для всех пользователей:\n\n"
        "❌ Отмена - вернуться в меню",
        reply_markup=create_admin_back_keyboard()
    )


@router.message(AdminState.waiting_broadcast)
async def process_broadcast(message: Message, state: FSMContext):
    """Отправить рассылку."""
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("❌ Рассылка отменена", reply_markup=create_admin_menu())
        return

    broadcast_text = message.text.strip()
    
    api = UzFlowerAPI()
    result = await api.send_broadcast(broadcast_text)
    
    await state.clear()
    await message.answer(
        f"✅ <b>Рассылка отправлена!</b>\n\n"
        f"Получателей: {result.get('sent_count', 0)}\n\n"
        f"Текст:\n<i>{broadcast_text[:200]}...</i>",
        reply_markup=create_admin_menu()
    )


# ============================================================
# Обработка заказов (уведомления о новых заказах)
# ============================================================

def create_order_keyboard(order_id: int, user_id: int) -> InlineKeyboardMarkup:
    """Создать клавиатуру для управления заказом."""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Принять", callback_data=f"accept_{order_id}"),
                InlineKeyboardButton(text="❌ Отменить", callback_data=f"cancel_{order_id}")
            ],
            [
                InlineKeyboardButton(text="💬 Написать покупателю", url=f"tg://user?id={user_id}")
            ],
            [
                InlineKeyboardButton(text="📋 Детали заказа", callback_data=f"details_{order_id}"),
                InlineKeyboardButton(text="🚚 В доставке", callback_data=f"delivering_{order_id}")
            ],
            [
                InlineKeyboardButton(text="✔️ Завершён", callback_data=f"completed_{order_id}")
            ]
        ]
    )
    return keyboard


def create_order_message(order: dict) -> str:
    """Сформировать текст сообщения о заказе."""
    order_id = order.get("id", "???")
    customer_name = order.get("customer_name", "Не указано")
    product_name = order.get("product_name", "Не указано")
    total_amount = order.get("total_amount", 0)
    phone = order.get("phone", "Не указано")
    address = order.get("delivery_address", "Не указано")
    comment = order.get("comment", "")
    status = order.get("status", "new")

    status_emoji = {
        "new": "🆕",
        "accepted": "✅",
        "cancelled": "❌",
        "completed": "✔️",
        "delivering": "🚚"
    }.get(status, "📦")

    message = (
        f"{status_emoji} <b>Заказ #{order_id}</b>\n\n"
        f"👤 <b>Покупатель:</b> {customer_name}\n"
        f"🌸 <b>Товар:</b> {product_name}\n"
        f"💰 <b>Цена:</b> {total_amount:,.0f} сум\n"
        f"📞 <b>Телефон:</b> {phone}\n"
        f"📍 <b>Адрес:</b> {address}"
    )

    if comment:
        message += f"\n💬 <b>Комментарий:</b> {comment}"

    message += f"\n\n<b>Статус:</b> {status}"
    message += "\n\nВыберите действие:"

    return message


@router.callback_query(F.data.startswith("accept_"))
async def handle_accept_order(callback: CallbackQuery, bot: Bot):
    """Обработка кнопки «Принять»."""
    order_id = int(callback.data.split("_")[1])
    admin_id = callback.from_user.id

    logger.info("🔔 Получен callback на принятие заказа #%s", order_id)

    if not check_admin_access(admin_id):
        await callback.answer("❌ У вас нет прав для этого действия", show_alert=True)
        return

    api = UzFlowerAPI()

    # Получаем информацию о заказе для уведомления
    order = await api.get_order(order_id)
    customer_telegram_id = None
    customer_name = "Покупатель"

    logger.info("   Получен заказ: %s", order)

    if order:
        customer_name = order.get("customer_name", "Покупатель")
        # Получаем Telegram ID напрямую из заказа
        customer_telegram_id = order.get("customer_telegram_id")
        logger.info("   Telegram ID покупателя из заказа: %s", customer_telegram_id)

    # Обновляем статус заказа
    success = await api.update_order_status(order_id, "accepted", admin_id)
    logger.info("   Статус заказа обновлён: %s", success)

    if success:
        # Отправляем уведомление покупателю
        if customer_telegram_id:
            logger.info("   Отправка уведомления покупателю #%s", customer_telegram_id)
            notify_result = await api.notify_customer_order_status(
                order_id=order_id,
                status="accepted",
                customer_telegram_id=customer_telegram_id,
                customer_name=customer_name
            )
            logger.info("   Результат отправки уведомления: %s", notify_result)
        else:
            logger.warning("   ⚠️ Telegram ID не найден, уведомление не отправлено")

        await callback.message.edit_text(
            callback.message.text.replace("Выберите действие:", "✅ <b>Заказ принят!</b>"),
            parse_mode="HTML"
        )
        await callback.answer("✅ Заказ принят", show_alert=False)
    else:
        await callback.answer("❌ Ошибка при обновлении статуса", show_alert=True)


@router.callback_query(F.data.startswith("cancel_"))
async def handle_cancel_order(callback: CallbackQuery, bot: Bot):
    """Обработка кнопки «Отменить»."""
    # Проверяем, не является ли это cancel кнопкой из списка товаров
    parts = callback.data.split("_")
    if len(parts) < 2 or not parts[1].isdigit():
        return

    order_id = int(parts[1])
    admin_id = callback.from_user.id

    logger.info("🔔 Получен callback на отмену заказа #%s", order_id)

    if not check_admin_access(admin_id):
        await callback.answer("❌ У вас нет прав для этого действия", show_alert=True)
        return

    api = UzFlowerAPI()

    # Получаем информацию о заказе для уведомления
    order = await api.get_order(order_id)
    customer_telegram_id = None
    customer_name = "Покупатель"

    logger.info("   Получен заказ: %s", order)

    if order:
        customer_name = order.get("customer_name", "Покупатель")
        # Получаем Telegram ID напрямую из заказа
        customer_telegram_id = order.get("customer_telegram_id")
        logger.info("   Telegram ID покупателя из заказа: %s", customer_telegram_id)

    # Обновляем статус заказа
    success = await api.update_order_status(order_id, "cancelled", admin_id)
    logger.info("   Статус заказа обновлён: %s", success)

    if success:
        # Отправляем уведомление покупателю
        if customer_telegram_id:
            logger.info("   Отправка уведомления покупателю #%s", customer_telegram_id)
            notify_result = await api.notify_customer_order_status(
                order_id=order_id,
                status="cancelled",
                customer_telegram_id=customer_telegram_id,
                customer_name=customer_name
            )
            logger.info("   Результат отправки уведомления: %s", notify_result)
        else:
            logger.warning("   ⚠️ Telegram ID не найден, уведомление не отправлено")

        await callback.message.edit_text(
            callback.message.text.replace("Выберите действие:", "❌ <b>Заказ отменён</b>"),
            parse_mode="HTML"
        )
        await callback.answer("❌ Заказ отменён", show_alert=False)
    else:
        await callback.answer("❌ Ошибка при отмене заказа", show_alert=True)


@router.callback_query(F.data.startswith("delivering_"))
async def handle_delivering_order(callback: CallbackQuery, bot: Bot):
    """Обработка кнопки «В доставке»."""
    order_id = int(callback.data.split("_")[1])
    admin_id = callback.from_user.id

    if not check_admin_access(admin_id):
        await callback.answer("❌ У вас нет прав для этого действия", show_alert=True)
        return

    api = UzFlowerAPI()
    success = await api.update_order_status(order_id, "delivering", admin_id)

    if success:
        await callback.message.edit_text(
            callback.message.text.replace("Выберите действие:", "🚚 <b>Заказ в доставке!</b>"),
            parse_mode="HTML"
        )
        await callback.answer("🚚 Статус обновлён", show_alert=False)
    else:
        await callback.answer("❌ Ошибка при обновлении статуса", show_alert=True)


@router.callback_query(F.data.startswith("completed_"))
async def handle_completed_order(callback: CallbackQuery, bot: Bot):
    """Обработка кнопки «Завершён»."""
    order_id = int(callback.data.split("_")[1])
    admin_id = callback.from_user.id

    if not check_admin_access(admin_id):
        await callback.answer("❌ У вас нет прав для этого действия", show_alert=True)
        return

    api = UzFlowerAPI()
    success = await api.update_order_status(order_id, "completed", admin_id)

    if success:
        await callback.message.edit_text(
            callback.message.text.replace("Выберите действие:", "✔️ <b>Заказ завершён!</b>"),
            parse_mode="HTML"
        )
        await callback.answer("✔️ Статус обновлён", show_alert=False)
    else:
        await callback.answer("❌ Ошибка при обновлении статуса", show_alert=True)


@router.callback_query(F.data.startswith("details_"))
async def handle_details_order(callback: CallbackQuery, bot: Bot):
    """Обработка кнопки «Детали заказа»."""
    order_id = int(callback.data.split("_")[1])
    admin_id = callback.from_user.id

    if not check_admin_access(admin_id):
        await callback.answer("❌ У вас нет прав для этого действия", show_alert=True)
        return

    api = UzFlowerAPI()
    order = await api.get_order(order_id)

    if order:
        # Определяем тип доставки
        delivery_option = order.get("delivery_option", True)
        delivery_emoji = "🚚" if delivery_option else "🏃"
        delivery_text = order.get("delivery_address", "Самовывоз") if delivery_option else "Самовывоз"

        # Информация об оплате
        payment_status = order.get("payment_status", "waiting")
        payment_emoji = "✅" if payment_status == "paid" else "⏳"
        payment_text = "Оплачен" if payment_status == "paid" else "Ожидает оплаты"

        details_text = (
            f"📋 <b>Детали заказа #{order_id}</b>\n\n"
            f"👤 Покупатель: {order.get('customer_name', 'Не указано')}\n"
            f"📞 Телефон: {order.get('phone', 'Не указано')}\n"
            f"{delivery_emoji} <b>Доставка:</b> {delivery_text}\n"
            f"🌸 Товар: {order.get('product_name', 'Не указано')}\n"
            f"💰 Цена товара: {order.get('product_price', 0):,.0f} сум\n"
            f"💳 <b>Общая сумма:</b> {order.get('total_amount', 0):,.0f} сум\n"
            f"📅 Дата/время: {order.get('delivery_date', 'Не указана')}\n"
            f"💬 Комментарий: {order.get('comment', 'Нет')}\n"
            f"💳 <b>Оплата:</b> {payment_emoji} {payment_text}\n"
        )

        # Добавляем номер карты
        card_number = order.get("card_number", "Не указан")
        if card_number:
            details_text += f"  • Карта: <code>{card_number}</code>\n"

        # Добавляем информацию о чеке
        payment_proof_url = order.get("payment_proof_url")
        if payment_proof_url:
            details_text += f"  • ✅ <b>Чек загружен</b>\n"
        else:
            details_text += f"  • ⏳ Чек ещё не загружен\n"

        details_text += f"\n📊 Статус: {order.get('status', 'pending')}"

        # Отправляем детали
        await callback.message.answer(details_text, parse_mode="HTML")

        # Если есть скриншот чека, отправляем его
        if payment_proof_url:
            try:
                await callback.message.answer_photo(
                    photo=payment_proof_url,
                    caption=f"🧾 Чек оплаты заказа #{order_id}"
                )
            except Exception as e:
                logger.error("Ошибка при отправке скриншота чека: %s", e)

    await callback.answer()
