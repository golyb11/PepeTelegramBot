














import logging
import aiosqlite

from config import DATABASE_PATH, DEFAULT_API_KEY, DEFAULT_MODEL


logger: logging.Logger = logging.getLogger(__name__)


async def init_db() -> None:












    async with aiosqlite.connect(DATABASE_PATH) as db:



        await db.execute(







        )
        await db.commit()
        logger.info("Таблица 'settings' проверена / создана.")


        await db.execute(










        )

        await db.execute(




        )
        await db.commit()
        logger.info("Таблица 'chat_history' проверена / создана.")


        cursor: aiosqlite.Cursor = await db.execute(
            "SELECT id FROM settings WHERE id = 1"
        )
        row = await cursor.fetchone()

        if row is None:

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










    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor: aiosqlite.Cursor = await db.execute(
            "SELECT api_key, model_name FROM settings WHERE id = 1"
        )
        row = await cursor.fetchone()

    if row is None:

        logger.error("Критическая ошибка: запись настроек id=1 не найдена!")
        raise ValueError("Settings row (id=1) not found in database.")

    api_key: str = row[0]
    model_name: str = row[1]
    logger.info("Настройки загружены из БД: model=%s", model_name)
    return api_key, model_name


async def update_api_key(new_key: str) -> None:






    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            "UPDATE settings SET api_key = ? WHERE id = 1",
            (new_key,),
        )
        await db.commit()
    logger.info("API-ключ успешно обновлён в БД.")


async def update_model(new_model: str) -> None:






    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            "UPDATE settings SET model_name = ? WHERE id = 1",
            (new_model,),
        )
        await db.commit()
    logger.info("Модель успешно обновлена в БД: model=%s", new_model)


async def save_message(chat_id: int, user_id: int, username: str | None, message_text: str) -> None:









    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(



,
            (chat_id, user_id, username, message_text),
        )
        await db.commit()


async def get_chat_history(chat_id: int, limit: int = 5) -> list[dict]:










    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor: aiosqlite.Cursor = await db.execute(






,
            (chat_id, limit),
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


async def clear_old_messages(days: int = 7) -> None:






    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(



.format(days)
        )
        await db.commit()
    logger.info("Очищены сообщения старше %d дней.", days)
