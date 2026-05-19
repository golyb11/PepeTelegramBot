# ============================================================================
# handlers.py — Все хэндлеры и роутеры бота "Пэпэ"
# ============================================================================

import re
import random
import logging
from datetime import datetime, timedelta

from aiogram import Router, Bot, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, CommandStart
from aiogram.enums import ParseMode

import db
from llm_router import ask_llm
from keyboards import main_menu_kb, persona_menu_kb, model_menu_kb
from config import (
    PERSONAS,
    AVAILABLE_MODELS,
    ASSISTANT_SYSTEM_PROMPT,
    COMMENT_SYSTEM_PROMPT,
    FINDSONG_SYSTEM_PROMPT,
    FACTCHECK_SYSTEM_PROMPT,
    AURA_POSITIVE_TRIGGERS,
    AURA_NEGATIVE_TRIGGERS,
    AURA_POSITIVE_COMMENTS,
    AURA_NEGATIVE_COMMENTS,
    CURSE_ROOTS,
    CONTEXT_LIMIT,
)

logger = logging.getLogger(__name__)
router = Router()

# ---------------------------------------------------------------------------
# Вспомогательные функции
# ---------------------------------------------------------------------------

def _has_curse(text: str) -> bool:
    """Проверяет наличие мата в тексте по корням слов."""
    low = text.lower()
    return any(root in low for root in CURSE_ROOTS)


def _check_aura_trigger(text: str):
    """Возвращает +1, -1 или 0 в зависимости от триггера ауры."""
    stripped = text.strip().lower()
    for trigger in AURA_POSITIVE_TRIGGERS:
        if stripped == trigger or stripped.startswith(trigger):
            return 1
    for trigger in AURA_NEGATIVE_TRIGGERS:
        if stripped == trigger or stripped.startswith(trigger):
            return -1
    return 0


def _parse_remind_time(arg: str):
    """Парсит строку вида '10m' или '2h'. Возвращает timedelta или None."""
    match = re.match(r"^(\d+)([mhMH])$", arg.strip())
    if not match:
        return None
    value = int(match.group(1))
    unit = match.group(2).lower()
    if value <= 0:
        return None
    if unit == "m":
        return timedelta(minutes=value)
    if unit == "h":
        return timedelta(hours=value)
    return None


# ---------------------------------------------------------------------------
# /start и /help
# ---------------------------------------------------------------------------
HELP_TEXT = (
    "👋 <b>Ку, я Пэпэ!</b> Твой токсичный (или не очень) ИИ-сосед.\n\n"
    "Вот что я умею:\n\n"
    "⚙️ /menu — Настройки бота (Личность и Модели)\n"
    "❓ /ask <i>[вопрос]</i> — Задать вопрос умному ассистенту без шуток.\n"
    "🧹 /clear — Очистить мою память в этом диалоге.\n"
    "🎵 /findsong <i>[текст]</i> — Найти песню по обрывкам слов (AI).\n"
    "🤥 /factcheck — (Реплай на сообщение) Проверить факт на лживость.\n"
    "⏰ /remind <i>[время] [текст]</i> — Напомнить что-то.\n"
    "    Пример: <code>/remind 15m Снять макароны</code>\n"
    "📊 /stats — Итоги чата: спамеры, матершинники.\n"
    "✨ /aura — Топ-3 лучших и худших по ауре.\n"
    "🔑 /setkey <i>[ключ]</i> — Сменить API ключ OpenRouter.\n\n"
    "<i>Просто напиши 'Пэпэ' в сообщении, чтобы я ответил!</i>"
)


@router.message(CommandStart())
@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(HELP_TEXT, parse_mode=ParseMode.HTML)


# ---------------------------------------------------------------------------
# /setkey — сохранённая логика
# ---------------------------------------------------------------------------
@router.message(Command("setkey"))
async def cmd_setkey(message: Message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2 or not args[1].strip():
        await message.answer("❌ Укажи ключ: <code>/setkey sk-or-v1-...</code>", parse_mode=ParseMode.HTML)
        return
    key = args[1].strip()
    await db.set_api_key(message.chat.id, key)
    await message.answer("✅ API-ключ обновлён!")


# ---------------------------------------------------------------------------
# /menu — Inline-меню настроек
# ---------------------------------------------------------------------------
@router.message(Command("menu"))
async def cmd_menu(message: Message):
    settings = await db.get_chat_settings(message.chat.id)
    persona_key = settings["current_persona"]
    persona_name = PERSONAS.get(persona_key, {}).get("name", persona_key)
    model_name = AVAILABLE_MODELS.get(settings["current_model"], settings["current_model"])

    text = (
        f"⚙️ <b>Настройки чата</b> {message.chat.title or 'Личка'}\n\n"
        f"🎭 Текущая личность: <b>{persona_name}</b>\n"
        f"🧠 Текущая модель: <b>{model_name}</b>"
    )
    await message.answer(text, parse_mode=ParseMode.HTML, reply_markup=main_menu_kb())


# ---------------------------------------------------------------------------
# Callback: навигация меню
# ---------------------------------------------------------------------------
@router.callback_query(F.data == "menu_persona")
async def cb_menu_persona(callback: CallbackQuery):
    await callback.message.edit_text(
        "🎭 <b>Выбери личность бота:</b>",
        parse_mode=ParseMode.HTML,
        reply_markup=persona_menu_kb(),
    )
    await callback.answer()


@router.callback_query(F.data == "menu_model")
async def cb_menu_model(callback: CallbackQuery):
    await callback.message.edit_text(
        "🧠 <b>Выбери модель LLM:</b>",
        parse_mode=ParseMode.HTML,
        reply_markup=model_menu_kb(),
    )
    await callback.answer()


@router.callback_query(F.data == "menu_close")
async def cb_menu_close(callback: CallbackQuery):
    await callback.message.delete()
    await callback.answer("Меню закрыто")


@router.callback_query(F.data == "menu_back")
async def cb_menu_back(callback: CallbackQuery):
    settings = await db.get_chat_settings(callback.message.chat.id)
    persona_key = settings["current_persona"]
    persona_name = PERSONAS.get(persona_key, {}).get("name", persona_key)
    model_name = AVAILABLE_MODELS.get(settings["current_model"], settings["current_model"])

    text = (
        f"⚙️ <b>Настройки чата</b> {callback.message.chat.title or 'Личка'}\n\n"
        f"🎭 Текущая личность: <b>{persona_name}</b>\n"
        f"🧠 Текущая модель: <b>{model_name}</b>"
    )
    await callback.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=main_menu_kb())
    await callback.answer()


# ---------------------------------------------------------------------------
# Callback: выбор персоны / модели
# ---------------------------------------------------------------------------
@router.callback_query(F.data.startswith("set_persona:"))
async def cb_set_persona(callback: CallbackQuery):
    persona_key = callback.data.split(":", 1)[1]
    if persona_key not in PERSONAS:
        await callback.answer("❌ Неизвестная персона")
        return
    await db.set_persona(callback.message.chat.id, persona_key)
    name = PERSONAS[persona_key]["name"]
    await callback.message.edit_text(f"✅ Личность изменена на <b>{name}</b>", parse_mode=ParseMode.HTML)
    await callback.answer("Готово!")


@router.callback_query(F.data.startswith("set_model:"))
async def cb_set_model(callback: CallbackQuery):
    model_id = callback.data.split(":", 1)[1]
    if model_id not in AVAILABLE_MODELS:
        await callback.answer("❌ Неизвестная модель")
        return
    await db.set_model(callback.message.chat.id, model_id)
    name = AVAILABLE_MODELS[model_id]
    await callback.message.edit_text(f"✅ Модель изменена на <b>{name}</b>", parse_mode=ParseMode.HTML)
    await callback.answer("Готово!")


# ---------------------------------------------------------------------------
# /ask — умный помощник (без персоны)
# ---------------------------------------------------------------------------
@router.message(Command("ask"))
async def cmd_ask(message: Message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2 or not args[1].strip():
        await message.answer("❌ Напиши вопрос после команды. Пример: <code>/ask Что такое фотосинтез?</code>", parse_mode=ParseMode.HTML)
        return

    question = args[1].strip()
    settings = await db.get_chat_settings(message.chat.id)

    thinking = await message.answer("🤔 Думаю...")
    answer = await ask_llm(
        api_key=settings["api_key"],
        model=settings["current_model"],
        system_prompt=ASSISTANT_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": question}],
    )
    await thinking.edit_text(answer)


# ---------------------------------------------------------------------------
# /clear — очистка контекста
# ---------------------------------------------------------------------------
@router.message(Command("clear"))
async def cmd_clear(message: Message):
    await db.clear_context(message.chat.id)
    await message.answer("🧹 Память очищена! Я забыл всё, что было.")


# ---------------------------------------------------------------------------
# /findsong — поиск песни (AI)
# ---------------------------------------------------------------------------
@router.message(Command("findsong"))
async def cmd_findsong(message: Message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2 or not args[1].strip():
        await message.answer("❌ А слова где? Пиши <code>/findsong ляляля три рубля</code>", parse_mode=ParseMode.HTML)
        return

    lyrics = args[1].strip()
    settings = await db.get_chat_settings(message.chat.id)

    thinking = await message.answer("🎧 Ищу песню...")
    answer = await ask_llm(
        api_key=settings["api_key"],
        model=settings["current_model"],
        system_prompt=FINDSONG_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": lyrics}],
    )
    await thinking.edit_text(answer)


# ---------------------------------------------------------------------------
# /factcheck — детектор лжи (AI, по реплаю)
# ---------------------------------------------------------------------------
@router.message(Command("factcheck"))
async def cmd_factcheck(message: Message):
    if not message.reply_to_message or not message.reply_to_message.text:
        await message.answer("❌ Сделай реплай на сообщение, которое хочешь проверить!")
        return

    original_text = message.reply_to_message.text
    settings = await db.get_chat_settings(message.chat.id)

    thinking = await message.answer("🔍 Проверяю факт...")
    answer = await ask_llm(
        api_key=settings["api_key"],
        model=settings["current_model"],
        system_prompt=FACTCHECK_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": original_text}],
    )
    await thinking.edit_text(answer)


# ---------------------------------------------------------------------------
# /remind — напоминания (APScheduler)
# ---------------------------------------------------------------------------
@router.message(Command("remind"))
async def cmd_remind(message: Message):
    parts = message.text.split(maxsplit=2)
    # /remind 10m Текст напоминания
    if len(parts) < 3:
        await message.answer(
            "❌ Ошибка. Пиши так: <code>/remind 15m Полить огород</code>\n"
            "(m — минуты, h — часы)",
            parse_mode=ParseMode.HTML,
        )
        return

    delta = _parse_remind_time(parts[1])
    if delta is None:
        await message.answer(
            "❌ Неверный формат времени. Примеры: <code>10m</code>, <code>2h</code>",
            parse_mode=ParseMode.HTML,
        )
        return

    remind_text = parts[2].strip()
    trigger_time = datetime.now() + delta
    username = message.from_user.username or message.from_user.first_name or "anon"

    await db.add_reminder(
        chat_id=message.chat.id,
        user_id=message.from_user.id,
        username=username,
        text=remind_text,
        trigger_time=trigger_time,
    )
    await message.answer("✅ Запомнил. Пну тебя позже. ⏰")


# ---------------------------------------------------------------------------
# /stats — статистика чата
# ---------------------------------------------------------------------------
@router.message(Command("stats"))
async def cmd_stats(message: Message):
    data = await db.get_chat_stats(message.chat.id)
    top_msg = data["top_messages"]
    top_curse = data["top_curses"]

    if not top_msg:
        await message.answer("📊 Статистики пока нет. Пишите больше!")
        return

    lines = ["📊 <b>Статистика чата</b>\n"]

    lines.append("💬 <b>Топ болтунов:</b>")
    for i, row in enumerate(top_msg, 1):
        lines.append(f"  {i}. @{row['username']} — {row['messages_count']} сообщ. ({row['words_count']} слов)")

    if top_curse:
        lines.append("\n🤬 <b>Топ матершинников:</b>")
        for i, row in enumerate(top_curse, 1):
            lines.append(f"  {i}. @{row['username']} — {row['curses_count']} матов")

    await message.answer("\n".join(lines), parse_mode=ParseMode.HTML)


# ---------------------------------------------------------------------------
# /aura — топ ауры
# ---------------------------------------------------------------------------
@router.message(Command("aura"))
async def cmd_aura(message: Message):
    top = await db.get_top_aura(message.chat.id)
    bottom = await db.get_bottom_aura(message.chat.id)

    if not top and not bottom:
        await message.answer("🔮 Вы все пока серые мыши, ауры нет. Начните плюсовать и минусовать!")
        return

    lines = ["🔮 <b>Аура чата</b>\n"]

    if top:
        lines.append("😇 <b>Топ святых:</b>")
        for i, row in enumerate(top, 1):
            lines.append(f"  {i}. @{row['username']} — +{row['aura']} ✨")

    if bottom:
        lines.append("\n😈 <b>Топ грешников:</b>")
        for i, row in enumerate(bottom, 1):
            lines.append(f"  {i}. @{row['username']} — {row['aura']} 💀")

    await message.answer("\n".join(lines), parse_mode=ParseMode.HTML)


# ---------------------------------------------------------------------------
# Универсальный обработчик всех текстовых сообщений
# (статистика + аура + триггер бота)
# ---------------------------------------------------------------------------
@router.message(F.text)
async def on_message(message: Message, bot: Bot):
    # Пропускаем сообщения без автора
    if not message.from_user:
        return

    text = message.text
    user_id = message.from_user.id
    chat_id = message.chat.id
    username = message.from_user.username or message.from_user.first_name or "anon"

    # --- 1. Обновляем статистику ---
    words = len(text.split())
    curse = _has_curse(text)
    await db.update_user_stats(user_id, chat_id, username, words, curse)

    # --- 2. Проверяем ауру (реплай на чужое сообщение) ---
    if message.reply_to_message and message.reply_to_message.from_user:
        target = message.reply_to_message.from_user
        bot_info = await bot.get_me()
        # Не самому себе и не боту
        if target.id != user_id and target.id != bot_info.id:
            delta = _check_aura_trigger(text)
            if delta != 0:
                target_username = target.username or target.first_name or "anon"
                new_aura = await db.update_aura(target.id, chat_id, target_username, delta)
                if delta > 0:
                    comment = random.choice(AURA_POSITIVE_COMMENTS)
                else:
                    comment = random.choice(AURA_NEGATIVE_COMMENTS)
                await message.answer(
                    f"🔮 Аура @{target_username} изменена: <b>{new_aura}</b>. {comment}",
                    parse_mode=ParseMode.HTML,
                )
                return  # Не отвечаем как бот-ИИ на ауру

    # --- 3. Проверяем триггер бота ---
    bot_info = await bot.get_me()
    text_lower = text.lower()

    is_reply_to_bot = (
        message.reply_to_message
        and message.reply_to_message.from_user
        and message.reply_to_message.from_user.id == bot_info.id
    )
    is_mention = "пэпэ" in text_lower or "пепе" in text_lower

    if not is_reply_to_bot and not is_mention:
        return  # Бота не вызвали — выходим

    # --- 4. Определяем системный промпт ---
    settings = await db.get_chat_settings(chat_id)
    persona_key = settings["current_persona"]
    system_prompt = PERSONAS.get(persona_key, PERSONAS["pepe"])["prompt"]

    # Проверка на триггеры комментирования
    comment_triggers = ["че скажешь", "что скажешь", "че думаешь", "что думаешь", "на твой вкус"]
    if any(t in text_lower for t in comment_triggers):
        system_prompt = COMMENT_SYSTEM_PROMPT

    # --- 5. Сохраняем сообщение пользователя в контекст ---
    user_label = f"@{username}"
    await db.add_context(chat_id, "user", f"{user_label}: {text}")

    # --- 6. Собираем историю из БД ---
    context_rows = await db.get_context(chat_id, CONTEXT_LIMIT)
    messages = []
    for row in context_rows:
        messages.append({"role": row["message_role"], "content": row["message_content"]})

    # --- 7. Запрос к LLM ---
    thinking = await message.answer("💭...")
    answer = await ask_llm(
        api_key=settings["api_key"],
        model=settings["current_model"],
        system_prompt=system_prompt,
        messages=messages,
    )

    # --- 8. Сохраняем ответ бота в контекст ---
    await db.add_context(chat_id, "assistant", answer)

    await thinking.edit_text(answer)
