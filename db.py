# ============================================================================
# db.py — Модуль базы данных SQLite (aiosqlite)
# ============================================================================

import aiosqlite
from datetime import datetime
from config import DATABASE_PATH, DEFAULT_API_KEY, DEFAULT_MODEL


# ---------------------------------------------------------------------------
# Инициализация БД (создание таблиц + миграция)
# ---------------------------------------------------------------------------
async def init_db():
    """Создаёт все таблицы и мигрирует данные из старой схемы."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("PRAGMA journal_mode=WAL")

        # --- chat_settings ---
        await db.execute("""
            CREATE TABLE IF NOT EXISTS chat_settings (
                chat_id   INTEGER PRIMARY KEY,
                api_key   TEXT,
                current_model   TEXT,
                current_persona TEXT DEFAULT 'pepe'
            )
        """)

        # Миграция: если есть старая таблица settings — перенести данные
        cursor = await db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='settings'"
        )
        if await cursor.fetchone():
            await db.execute("""
                INSERT OR IGNORE INTO chat_settings (chat_id, api_key, current_model)
                SELECT chat_id, api_key, model FROM settings
            """)
            await db.execute("DROP TABLE settings")

        # --- users_stats ---
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users_stats (
                user_id        INTEGER,
                chat_id        INTEGER,
                username       TEXT,
                messages_count INTEGER DEFAULT 0,
                aura           INTEGER DEFAULT 0,
                words_count    INTEGER DEFAULT 0,
                curses_count   INTEGER DEFAULT 0,
                PRIMARY KEY (user_id, chat_id)
            )
        """)

        # --- reminders ---
        await db.execute("""
            CREATE TABLE IF NOT EXISTS reminders (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id      INTEGER,
                user_id      INTEGER,
                username     TEXT,
                remind_text  TEXT,
                trigger_time TIMESTAMP
            )
        """)

        # --- context_memory ---
        await db.execute("""
            CREATE TABLE IF NOT EXISTS context_memory (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id         INTEGER,
                message_role    TEXT,
                message_content TEXT,
                timestamp       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        await db.commit()


# ---------------------------------------------------------------------------
# Chat Settings (API key, model, persona)
# ---------------------------------------------------------------------------
async def get_chat_settings(chat_id: int) -> dict:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM chat_settings WHERE chat_id = ?", (chat_id,)
        )
        row = await cursor.fetchone()
        if row:
            return {
                "api_key": row["api_key"] or DEFAULT_API_KEY,
                "current_model": row["current_model"] or DEFAULT_MODEL,
                "current_persona": row["current_persona"] or "pepe",
            }
        return {
            "api_key": DEFAULT_API_KEY,
            "current_model": DEFAULT_MODEL,
            "current_persona": "pepe",
        }


async def _ensure_chat(chat_id: int):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO chat_settings (chat_id, api_key, current_model) VALUES (?, ?, ?)",
            (chat_id, DEFAULT_API_KEY, DEFAULT_MODEL),
        )
        await db.commit()


async def set_api_key(chat_id: int, key: str):
    await _ensure_chat(chat_id)
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            "UPDATE chat_settings SET api_key = ? WHERE chat_id = ?", (key, chat_id)
        )
        await db.commit()


async def set_model(chat_id: int, model: str):
    await _ensure_chat(chat_id)
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            "UPDATE chat_settings SET current_model = ? WHERE chat_id = ?",
            (model, chat_id),
        )
        await db.commit()


async def set_persona(chat_id: int, persona: str):
    await _ensure_chat(chat_id)
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            "UPDATE chat_settings SET current_persona = ? WHERE chat_id = ?",
            (persona, chat_id),
        )
        await db.commit()


# ---------------------------------------------------------------------------
# Users Stats (messages, words, curses, aura)
# ---------------------------------------------------------------------------
async def update_user_stats(
    user_id: int, chat_id: int, username: str, words: int, has_curse: bool
):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            """
            INSERT INTO users_stats (user_id, chat_id, username, messages_count, words_count, curses_count)
            VALUES (?, ?, ?, 1, ?, ?)
            ON CONFLICT(user_id, chat_id) DO UPDATE SET
                username       = excluded.username,
                messages_count = messages_count + 1,
                words_count    = words_count + excluded.words_count,
                curses_count   = curses_count + excluded.curses_count
            """,
            (user_id, chat_id, username or "anon", words, 1 if has_curse else 0),
        )
        await db.commit()


async def update_aura(user_id: int, chat_id: int, username: str, delta: int) -> int:
    """Обновляет ауру и возвращает новое значение."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            """
            INSERT INTO users_stats (user_id, chat_id, username, aura)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id, chat_id) DO UPDATE SET
                username = excluded.username,
                aura     = aura + ?
            """,
            (user_id, chat_id, username or "anon", delta, delta),
        )
        await db.commit()
        cursor = await db.execute(
            "SELECT aura FROM users_stats WHERE user_id = ? AND chat_id = ?",
            (user_id, chat_id),
        )
        row = await cursor.fetchone()
        return row[0] if row else 0


async def get_top_aura(chat_id: int, limit: int = 3):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT username, aura FROM users_stats WHERE chat_id = ? AND aura > 0 ORDER BY aura DESC LIMIT ?",
            (chat_id, limit),
        )
        return await cursor.fetchall()


async def get_bottom_aura(chat_id: int, limit: int = 3):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT username, aura FROM users_stats WHERE chat_id = ? AND aura < 0 ORDER BY aura ASC LIMIT ?",
            (chat_id, limit),
        )
        return await cursor.fetchall()


async def get_chat_stats(chat_id: int):
    """Возвращает dict с топами: messages, curses."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur_msg = await db.execute(
            "SELECT username, messages_count, words_count FROM users_stats WHERE chat_id = ? ORDER BY messages_count DESC LIMIT 5",
            (chat_id,),
        )
        top_msg = await cur_msg.fetchall()

        cur_curse = await db.execute(
            "SELECT username, curses_count FROM users_stats WHERE chat_id = ? AND curses_count > 0 ORDER BY curses_count DESC LIMIT 5",
            (chat_id,),
        )
        top_curse = await cur_curse.fetchall()

        return {"top_messages": top_msg, "top_curses": top_curse}


# ---------------------------------------------------------------------------
# Reminders
# ---------------------------------------------------------------------------
async def add_reminder(
    chat_id: int, user_id: int, username: str, text: str, trigger_time: datetime
):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            "INSERT INTO reminders (chat_id, user_id, username, remind_text, trigger_time) VALUES (?, ?, ?, ?, ?)",
            (chat_id, user_id, username, text, trigger_time.isoformat()),
        )
        await db.commit()


async def get_due_reminders():
    now = datetime.now().isoformat()
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM reminders WHERE trigger_time <= ?", (now,)
        )
        return await cursor.fetchall()


async def delete_reminder(reminder_id: int):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("DELETE FROM reminders WHERE id = ?", (reminder_id,))
        await db.commit()


# ---------------------------------------------------------------------------
# Context Memory (последние N сообщений для LLM)
# ---------------------------------------------------------------------------
async def add_context(chat_id: int, role: str, content: str):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            "INSERT INTO context_memory (chat_id, message_role, message_content) VALUES (?, ?, ?)",
            (chat_id, role, content),
        )
        # FIFO: оставляем только последние 10
        await db.execute(
            """
            DELETE FROM context_memory WHERE id IN (
                SELECT id FROM context_memory WHERE chat_id = ?
                ORDER BY timestamp ASC
                LIMIT MAX(0, (SELECT COUNT(*) FROM context_memory WHERE chat_id = ?) - 10)
            )
            """,
            (chat_id, chat_id),
        )
        await db.commit()


async def get_context(chat_id: int, limit: int = 10):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT message_role, message_content FROM context_memory WHERE chat_id = ? ORDER BY timestamp ASC LIMIT ?",
            (chat_id, limit),
        )
        return await cursor.fetchall()


async def clear_context(chat_id: int):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            "DELETE FROM context_memory WHERE chat_id = ?", (chat_id,)
        )
        await db.commit()
