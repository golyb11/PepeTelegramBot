# ============================================================================
# handlers/pepe_handlers.py — Обработчик ключевого слова "Пэпэ" (Режим A)
# ============================================================================
# Режим A: "Шутник / Персона Пэпэ"
#
# Триггер 1: любое текстовое сообщение, содержащее подстроку "пэпэ"
# (регистронезависимо). Бот отвечает как саркастичный, токсичный,
# но смешной друг-тролль. Видит последние 5 сообщений чата.
#
# Триггер 2: фразы комментирования на основе 10 сообщений:
#   - "че скажешь пэпа"
#   - "че думаешь"
#   - "на твой вкус"
#
# Фильтрация в aiogram 3.x:
#   Используем F.text — магический фильтр aiogram, проверяющий наличие
#   текста в сообщении. Дополнительно применяем лямбда-фильтр.
# ============================================================================

import logging
import re

from aiogram import Router, F
from aiogram.types import Message
from aiogram.enums import ChatAction

import llm_service
import database
from config import PEPE_SYSTEM_PROMPT, COMMENT_SYSTEM_PROMPT

# Роутер для перехвата ключевого слова "Пэпэ"
router: Router = Router(name="pepe_router")

# Логгер модуля
logger: logging.Logger = logging.getLogger(__name__)

# Регулярные выражения для триггеров комментирования
COMMENT_TRIGGERS: list[str] = [
    r"че\s+скаж[еэ]шь\s+п[эе]п[аэ]",
    r"че\s+дума[еэ]шь",
    r"на\s+твой\s+вкус",
]


def is_comment_trigger(text: str) -> bool:
    """Проверить, содержит ли текст триггер комментирования."""
    text_lower = text.lower()
    for pattern in COMMENT_TRIGGERS:
        if re.search(pattern, text_lower):
            return True
    return False


def contains_pepe(text: str) -> bool:
    """Проверить, содержит ли текст упоминание 'пэпэ' (но не триггеры комментирования)."""
    text_lower = text.lower()
    # Сначала проверяем, не является ли это триггером комментирования
    if is_comment_trigger(text):
        return False
    return "пэпэ" in text_lower


def is_not_command(text: str | None) -> bool:
    """Проверить, что сообщение не является командой (не начинается с /)."""
    if not text:
        return False
    return not text.startswith("/")


@router.message(F.text, lambda msg: is_not_command(msg.text))
async def save_and_handle_message(message: Message) -> None:
    """
    Обработчик текстовых сообщений (не команд).

    1. Сохраняет сообщение в историю чата.
    2. Проверяет триггеры комментирования (10 сообщений).
    3. Проверяет упоминание "пэпэ" (5 сообщений).
    """
    if not message.text:
        return

    # Сохраняем сообщение в БД
    await database.save_message(
        chat_id=message.chat.id,
        user_id=message.from_user.id,
        username=message.from_user.username or message.from_user.full_name,
        message_text=message.text,
    )

    text = message.text

    # Проверяем триггеры комментирования (приоритет выше, т.к. они специфичнее)
    if is_comment_trigger(text):
        await handle_comment_trigger(message)
        return

    # Проверяем упоминание "пэпэ"
    if contains_pepe(text):
        await handle_pepe_mention(message)


async def handle_comment_trigger(message: Message) -> None:
    """
    Обработчик триггеров комментирования.

    Получает последние 10 сообщений из чата и генерирует комментарий Пэпэ.
    """
    logger.info(
        "Триггер комментирования от user_id=%d в chat_id=%d: '%s'",
        message.from_user.id,
        message.chat.id,
        message.text[:80],
    )

    # Индикатор "печатает..."
    await message.bot.send_chat_action(
        chat_id=message.chat.id,
        action=ChatAction.TYPING,
    )

    # Получаем последние 10 сообщений (включая текущее)
    context = await database.get_chat_history(message.chat.id, limit=10)

    # Генерируем комментарий через LLM с контекстом
    reply_text: str = await llm_service.generate_reply_with_context(
        system_prompt=COMMENT_SYSTEM_PROMPT,
        user_text=message.text,
        context_messages=context,
    )

    # Отвечаем реплаем
    await message.reply(reply_text)
    logger.info("Комментарий Пэпэ отправлен в chat_id=%d.", message.chat.id)


async def handle_pepe_mention(message: Message) -> None:
    """
    Обработчик упоминания "Пэпэ" в тексте сообщения.

    Режим A — бот ведёт себя как саркастичный, токсичный друг-тролль.
    Видит последние 5 сообщений чата для контекста.
    """
    logger.info(
        "Триггер 'Пэпэ' от user_id=%d в chat_id=%d: '%s'",
        message.from_user.id,
        message.chat.id,
        message.text[:80],
    )

    # Индикатор "печатает..."
    await message.bot.send_chat_action(
        chat_id=message.chat.id,
        action=ChatAction.TYPING,
    )

    # Получаем последние 5 сообщений для контекста
    context = await database.get_chat_history(message.chat.id, limit=5)

    # Генерируем ответ через LLM с персоной Пэпэ и контекстом
    reply_text: str = await llm_service.generate_reply_with_context(
        system_prompt=PEPE_SYSTEM_PROMPT,
        user_text=message.text,
        context_messages=context,
    )

    # Отвечаем реплаем на сообщение-триггер
    await message.reply(reply_text)
    logger.info("Ответ Пэпэ отправлен в chat_id=%d.", message.chat.id)
