# ============================================================================
# main.py — Точка входа бота "Пэпэ"
# ============================================================================

import asyncio
import logging

from aiogram import Bot, Dispatcher
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from config import BOT_TOKEN
import db
from handlers import router
from keep_alive import keep_alive

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


async def check_reminders(bot: Bot):
    """Фоновая задача: проверяет напоминания каждую минуту."""
    try:
        due = await db.get_due_reminders()
        for r in due:
            try:
                await bot.send_message(
                    chat_id=r["chat_id"],
                    text=(
                        f"⏰ Эй, @{r['username']}! "
                        f"Ты просил напомнить: <b>{r['remind_text']}</b>. Бегом!"
                    ),
                    parse_mode="HTML",
                )
            except Exception as e:
                logger.error("Failed to send reminder %s: %s", r["id"], e)
            await db.delete_reminder(r["id"])
    except Exception as e:
        logger.error("check_reminders error: %s", e)


async def main():
    await db.init_db()
    logger.info("Database initialized")

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(router)

    scheduler = AsyncIOScheduler()
    scheduler.add_job(check_reminders, "interval", seconds=60, args=[bot])
    scheduler.start()
    logger.info("Scheduler started")

    # Запускаем фоновый веб-сервер для Render.com
    keep_alive()
    logger.info("Keep-alive server started")

    logger.info("Bot polling started...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
