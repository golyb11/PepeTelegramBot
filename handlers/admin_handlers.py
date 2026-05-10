# ============================================================================
# handlers/admin_handlers.py — Обработчики команд /setkey, /setmodel и /help
# ============================================================================
# Этот модуль реализует динамическое управление конфигурацией бота.
#
# Команды:
#   /setkey <new_key>   — заменяет API-ключ OpenRouter в SQLite
#   /setmodel           — показывает inline keyboard для выбора модели
#   /help               — показывает справку по функционалу бота
#
# ВАЖНО: По ТЗ эти команды доступны ЛЮБОМУ пользователю в групповом чате
# (никакой проверки admin ID не производится). Это сделано намеренно для
# удобства маленькой доверенной группы из 6 человек.
#
# Технические детали aiogram 3.x:
#   • Router() — независимый контейнер хендлеров, который позже
#     подключается к Dispatcher через dp.include_router(router).
#   • Command("setkey") — встроенный фильтр aiogram, срабатывающий на
#     сообщения вида "/setkey ...". Аргумент команды извлекается через
#     command.args (объект CommandObject).
# ============================================================================

import logging

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

import database
from config import AVAILABLE_MODELS

# Создаём роутер для административных команд
router: Router = Router(name="admin_router")

# Логгер модуля
logger: logging.Logger = logging.getLogger(__name__)


async def build_model_keyboard() -> InlineKeyboardMarkup:
    """Создать inline keyboard с доступными моделями, отмечая текущую."""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    
    # Получаем текущую модель из БД
    _, current_model = await database.get_settings()
    
    for model_id, model_name in AVAILABLE_MODELS.items():
        # Отмечаем текущую модель
        display_name = f"✅ {model_name}" if model_id == current_model else model_name
        button = InlineKeyboardButton(
            text=display_name,
            callback_data=f"setmodel:{model_id}",
        )
        keyboard.inline_keyboard.append([button])

    return keyboard


@router.message(Command("setkey"))
async def handle_setkey(message: Message) -> None:
    """
    Обработчик команды /setkey <new_key>.

    Извлекает новый API-ключ из аргументов команды, сохраняет его
    в SQLite через database.update_api_key() и отправляет подтверждение.
    """
    raw_text: str = message.text or ""
    parts: list[str] = raw_text.split(maxsplit=1)

    if len(parts) < 2 or not parts[1].strip():
        await message.reply(
            "⚠️ Использование: `/setkey <новый_ключ>`\n"
            "Пример: `/setkey sk-or-v1-abc123...`",
            parse_mode="Markdown",
        )
        logger.warning(
            "Команда /setkey без аргумента от user_id=%d", message.from_user.id
        )
        return

    new_key: str = parts[1].strip()
    await database.update_api_key(new_key)

    await message.reply("✅ API ключ успешно обновлен.")
    logger.info(
        "API-ключ обновлён пользователем user_id=%d", message.from_user.id
    )


@router.message(Command("setmodel"))
async def handle_setmodel(message: Message) -> None:
    """
    Обработчик команды /setmodel.

    Показывает inline keyboard с доступными моделями для выбора.
    """
    keyboard = await build_model_keyboard()
    
    await message.reply(
        "🤖 Выбери модель ИИ для бота Пэпэ:\n\n"
        "✅ — текущая модель\n"
        "Нажми на кнопку, чтобы сменить:",
        reply_markup=keyboard,
    )
    logger.info("Показан выбор моделей для user_id=%d", message.from_user.id)


@router.callback_query(F.data.startswith("setmodel:"))
async def handle_model_selection(callback: CallbackQuery) -> None:
    """
    Обработчик выбора модели из inline keyboard.
    """
    # Извлекаем model_id из callback_data
    model_id = callback.data.split(":", 1)[1]

    if model_id not in AVAILABLE_MODELS:
        await callback.answer("❌ Неизвестная модель.", show_alert=True)
        return

    # Обновляем модель в БД
    await database.update_model(model_id)

    model_name = AVAILABLE_MODELS[model_id]
    
    # Убираем клавиатуру и показываем только подтверждение
    await callback.message.edit_text(
        f"✅ Модель успешно изменена на:\n*{model_name}*",
        parse_mode="Markdown",
        reply_markup=None,
    )
    await callback.answer(f"✅ {model_name}")

    logger.info(
        "Модель изменена пользователем user_id=%d на: %s",
        callback.from_user.id,
        model_id,
    )


@router.message(Command("help"))
async def handle_help(message: Message) -> None:
    """
    Обработчик команды /help.

    Показывает справку по всем функциям бота.
    """
    help_text = """
🐸 **Пэпэ — ваш саркастичный ИИ-ассистент**

**Основные функции:**

🔹 *Режим Пэпэ* — Напиши "пэпэ" в любом сообщении и получи саркастичный, токсичный, но смешной ответ. Бот видит последние 5 сообщений чата для контекста.

💬 *Комментирование чата* — напиши одну из фраз:
   • "че скажешь пэпа"
   • "че думаешь"
   • "на твой вкус"
   
   Пэпэ проанализирует последние 10 сообщений и даст свой разбор с юмором.

🧠 *Режим ассистента* — команда `/ask <вопрос>` — вежливый и точный помощник для фактов и вопросов.

⚙️ *Управление моделью* — `/setmodel` — выбери модель ИИ из списка (GPT-4o Mini, Gemini, Llama и др.).

🔑 *Смена API-ключа* — `/setkey <ключ>` — установи свой ключ OpenRouter.

❓ *Справка* — `/help` — показать это сообщение.

---
📌 *Бот работает через OpenRouter — платформу с доступом к разным ИИ-моделям.*
    """

    await message.reply(help_text, parse_mode="Markdown")
    logger.info("Справка отправлена user_id=%d", message.from_user.id)
