# ============================================================================
# bot.py — Главная точка входа бота "Пэпэ" для группы "Огород"
# ============================================================================
# Этот файл:
#   1. Настраивает логирование (logging).
#   2. Создаёт экземпляры Bot и Dispatcher (aiogram 3.x).
#   3. Подключает все роутеры (handlers) к диспетчеру.
#   4. Инициализирует SQLite-базу данных (init_db).
#   5. Запускает long-polling для получения обновлений от Telegram.
#
# Порядок подключения роутеров ВАЖЕН:
#   admin_router → assistant_router → pepe_router
#   Команды (/setkey, /setmodel, /ask) должны проверяться ДО текстового
#   фильтра Пэпэ, чтобы сообщение "/ask Пэпэ, что такое Python?"
#   обрабатывалось как /ask, а не как упоминание Пэпэ.
# ============================================================================

import asyncio
import logging

from aiogram import Bot, Dispatcher

import database
from config import BOT_TOKEN
from handlers import all_routers

# ---------------------------------------------------------------------------
# Настройка логирования
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)
logger: logging.Logger = logging.getLogger(__name__)


async def main() -> None:
    """
    Главная асинхронная функция бота.

    1. Инициализирует SQLite-базу (создаёт таблицу, вставляет дефолты).
    2. Создаёт экземпляр Bot с токеном Telegram.
    3. Создаёт Dispatcher и подключает все роутеры.
    4. Запускает long-polling (dp.start_polling).
    """
    # --- Инициализация базы данных ---
    logger.info("Инициализация базы данных...")
    await database.init_db()
    logger.info("База данных готова.")

    # --- Создание экземпляра бота ---
    bot: Bot = Bot(token=BOT_TOKEN)
    logger.info("Экземпляр Bot создан.")

    # --- Создание диспетчера и подключение роутеров ---
    dp: Dispatcher = Dispatcher()

    for router in all_routers:
        dp.include_router(router)
        logger.info("Роутер '%s' подключён к диспетчеру.", router.name)

    # --- Запуск polling ---
    logger.info("Запуск polling... Бот 'Пэпэ' активен! 🐸")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
