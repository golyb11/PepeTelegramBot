# ============================================================================
# keyboards.py — Inline-клавиатуры бота
# ============================================================================

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import AVAILABLE_MODELS, PERSONAS


def main_menu_kb() -> InlineKeyboardMarkup:
    """Главное меню настроек."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🎭 Сменить личность", callback_data="menu_persona"),
            InlineKeyboardButton(text="🧠 Сменить модель", callback_data="menu_model"),
        ],
        [
            InlineKeyboardButton(text="❌ Закрыть меню", callback_data="menu_close"),
        ],
    ])


def persona_menu_kb() -> InlineKeyboardMarkup:
    """Меню выбора персоны (в 2 колонки)."""
    buttons = []
    row = []
    for key, data in PERSONAS.items():
        row.append(InlineKeyboardButton(text=data["name"], callback_data=f"set_persona:{key}"))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([
        InlineKeyboardButton(text="🔙 Назад", callback_data="menu_back")
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def model_menu_kb() -> InlineKeyboardMarkup:
    """Меню выбора модели (все старые + новые)."""
    buttons = []
    for model_id, display_name in AVAILABLE_MODELS.items():
        buttons.append([
            InlineKeyboardButton(text=display_name, callback_data=f"set_model:{model_id}")
        ])
    buttons.append([
        InlineKeyboardButton(text="🔙 Назад", callback_data="menu_back")
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def setmodel_direct_kb() -> InlineKeyboardMarkup:
    """Клавиатура для прямого выбора модели (для команды /setmodel)."""
    buttons = []
    for model_id, display_name in AVAILABLE_MODELS.items():
        buttons.append([
            InlineKeyboardButton(text=display_name, callback_data=f"smd:{model_id}")
        ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)
