
















import asyncio
import logging

from aiogram import Bot, Dispatcher

import database
from config import BOT_TOKEN
from handlers import all_routers




logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)
logger: logging.Logger = logging.getLogger(__name__)


async def main() -> None:









    logger.info("Инициализация базы данных...")
    await database.init_db()
    logger.info("База данных готова.")


    bot: Bot = Bot(token=BOT_TOKEN)
    logger.info("Экземпляр Bot создан.")


    dp: Dispatcher = Dispatcher()

    for router in all_routers:
        dp.include_router(router)
        logger.info("Роутер '%s' подключён к диспетчеру.", router.name)


    logger.info("Запуск polling... Бот 'Пэпэ' активен! 🐸")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
