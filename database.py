# ============================================================================
# database.py — Асинхронный слой работы с SQLite (aiosqlite)
# ============================================================================
# Модуль отвечает за:
#   1. Инициализацию базы данных и создание таблицы `settings` при первом
#      запуске (init_db).
#   2. Чтение текущих настроек — API-ключа и имени модели (get_settings).
#   3. Обновление API-ключа (update_api_key) и модели (update_model)
#      по команде пользователя.
#
# Таблица `settings` содержит ровно одну строку (id=1), которая хранит
# актуальную конфигурацию. При первом запуске она заполняется дефолтными
# значениями из config.py.
# ============================================================================

import logging
import aiosqlite

from config import DATABASE_PATH, DEFAULT_API_KEY, DEFAULT_MODEL

# Получаем логгер для этого модуля
logger: logging.Logger = logging.getLogger(__name__)


async def init_db() -> None:
    """
    Инициализация базы данных.

    1. Создаёт таблицу `settings`, если она не существует.
    2. Создаёт таблицу `chat_history` для хранения истории сообщений.
    3. Проверяет, есть ли запись с id=1 в settings.
    4. Если записи нет — вставляет дефолтные значения (API-ключ и модель).

    Эта функция вызывается ОДИН раз при старте бота (в bot.py → main()).
    """
    # aiosqlite.connect() — асинхронный контекстный менеджер, который
    # автоматически откроет и закроет соединение с SQLite-файлом.
    async with aiosqlite.connect(DATABASE_PATH) as db:
        # --- Создание таблицы settings ---
        # IF NOT EXISTS гарантирует идемпотентность: повторный вызов
        # init_db() не сломает существующую таблицу.
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS settings (
                id          INTEGER PRIMARY KEY,
                api_key     TEXT    NOT NULL,
                model_name  TEXT    NOT NULL
            )
            """
        )
        await db.commit()
        logger.info("Таблица 'settings' проверена / создана.")

        # --- Создание таблицы chat_history ---
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS chat_history (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id     INTEGER NOT NULL,
                user_id     INTEGER NOT NULL,
                username    TEXT,
                message_text TEXT NOT NULL,
                created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        # Создаем индекс для быстрого поиска по chat_id
        await db.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_chat_history_chat_id
            ON chat_history(chat_id)
            """
        )
        await db.commit()
        logger.info("Таблица 'chat_history' проверена / создана.")

        # --- Проверка наличия дефолтной записи ---
        cursor: aiosqlite.Cursor = await db.execute(
            "SELECT id FROM settings WHERE id = 1"
        )
        row = await cursor.fetchone()

        if row is None:
            # Первый запуск — вставляем дефолтные учётные данные
            await db.execute(
                "INSERT INTO settings (id, api_key, model_name) VALUES (?, ?, ?)",
                (1, DEFAULT_API_KEY, DEFAULT_MODEL),
            )
            await db.commit()
            logger.info(
                "Дефолтные настройки вставлены в БД: model=%s", DEFAULT_MODEL
            )
        else:
            logger.info("Настройки уже существуют в БД, пропускаем вставку.")


async def get_settings() -> tuple[str, str]:
    """
    Получить текущие настройки (API-ключ и имя модели) из БД.

    Returns:
        tuple[str, str]: Кортеж (api_key, model_name).

    Raises:
        ValueError: Если запись id=1 не найдена (теоретически невозможно
                     после корректного вызова init_db).
    """
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor: aiosqlite.Cursor = await db.execute(
            "SELECT api_key, model_name FROM settings WHERE id = 1"
        )
        row = await cursor.fetchone()

    if row is None:
        # Защитный fallback — не должен срабатывать в нормальном потоке
        logger.error("Критическая ошибка: запись настроек id=1 не найдена!")
        raise ValueError("Settings row (id=1) not found in database.")

    api_key: str = row[0]
    model_name: str = row[1]
    logger.info("Настройки загружены из БД: model=%s", model_name)
    return api_key, model_name


async def update_api_key(new_key: str) -> None:
    """
    Обновить API-ключ OpenRouter в базе данных.

    Args:
        new_key: Новый API-ключ, переданный пользователем через /setkey.
    """
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            "UPDATE settings SET api_key = ? WHERE id = 1",
            (new_key,),
        )
        await db.commit()
    logger.info("API-ключ успешно обновлён в БД.")


async def update_model(new_model: str) -> None:
    """
    Обновить имя модели OpenRouter в базе данных.

    Args:
        new_model: Новое имя модели, переданное пользователем через /setmodel.
    """
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            "UPDATE settings SET model_name = ? WHERE id = 1",
            (new_model,),
        )
        await db.commit()
    logger.info("Модель успешно обновлена в БД: model=%s", new_model)


async def save_message(chat_id: int, user_id: int, username: str | None, message_text: str) -> None:
    """
    Сохранить сообщение в историю чата.

    Args:
        chat_id: ID чата.
        user_id: ID пользователя.
        username: Имя пользователя (может быть None).
        message_text: Текст сообщения.
    """
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            """
            INSERT INTO chat_history (chat_id, user_id, username, message_text)
            VALUES (?, ?, ?, ?)
            """,
            (chat_id, user_id, username, message_text),
        )
        await db.commit()


async def get_chat_history(chat_id: int, limit: int = 5) -> list[dict]:
    """
    Получить последние сообщения из чата.

    Args:
        chat_id: ID чата.
        limit: Количество сообщений для возврата (по умолчанию 5).

    Returns:
        list[dict]: Список словарей с ключами chat_id, user_id, username, message_text, created_at.
    """
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor: aiosqlite.Cursor = await db.execute(
            """
            SELECT chat_id, user_id, username, message_text, created_at
            FROM chat_history
            WHERE chat_id = ?
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (chat_id, limit),
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


async def clear_old_messages(days: int = 7) -> None:
    """
    Очистить сообщения старше указанного количества дней.

    Args:
        days: Количество дней для хранения (по умолчанию 7).
    """
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            """
            DELETE FROM chat_history
            WHERE created_at < datetime('now', '-{} days')
            """.format(days)
        )
        await db.commit()
    logger.info("Очищены сообщения старше %d дней.", days)
