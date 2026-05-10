# ============================================================================
# handlers/__init__.py — Пакет обработчиков Telegram-бота "Пэпэ"
# ============================================================================
# Этот файл делает директорию handlers/ полноценным Python-пакетом и
# экспортирует все роутеры (aiogram Router) для удобного импорта в bot.py.
#
# Архитектура роутеров aiogram 3.x:
#   • Каждый файл-обработчик создаёт свой Router() — изолированный набор
#     хендлеров (message handlers, callback handlers и т. д.).
#   • В bot.py все роутеры подключаются к Dispatcher через
#     dp.include_router(router).
#   • Порядок подключения ВАЖЕН: роутеры проверяются сверху вниз.
#     Команды (/setkey, /setmodel, /ask) должны проверяться ДО
#     текстового фильтра Пэпэ, иначе сообщение вида "/ask Пэпэ ..."
#     будет перехвачено текстовым фильтром.
# ============================================================================

from handlers.admin_handlers import router as admin_router
from handlers.assistant_handlers import router as assistant_router
from handlers.pepe_handlers import router as pepe_router

# Список всех роутеров для удобного импорта:
#   from handlers import all_routers
#   for r in all_routers:
#       dp.include_router(r)
all_routers: list = [admin_router, assistant_router, pepe_router]
