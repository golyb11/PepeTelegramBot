





















import logging

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

import database
from config import AVAILABLE_MODELS


router: Router = Router(name="admin_router")


logger: logging.Logger = logging.getLogger(__name__)


async def build_model_keyboard() -> InlineKeyboardMarkup:

    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    

    _, current_model = await database.get_settings()
    
    for model_id, model_name in AVAILABLE_MODELS.items():

        display_name = f"✅ {model_name}" if model_id == current_model else model_name
        button = InlineKeyboardButton(
            text=display_name,
            callback_data=f"setmodel:{model_id}",
        )
        keyboard.inline_keyboard.append([button])

    return keyboard


@router.message(Command("setkey"))
async def handle_setkey(message: Message) -> None:






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




    model_id = callback.data.split(":", 1)[1]

    if model_id not in AVAILABLE_MODELS:
        await callback.answer("❌ Неизвестная модель.", show_alert=True)
        return


    await database.update_model(model_id)

    model_name = AVAILABLE_MODELS[model_id]
    

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





    help_text =

























    await message.reply(help_text, parse_mode="Markdown")
    logger.info("Справка отправлена user_id=%d", message.from_user.id)
