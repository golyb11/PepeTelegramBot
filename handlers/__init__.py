
















from handlers.admin_handlers import router as admin_router
from handlers.assistant_handlers import router as assistant_router
from handlers.pepe_handlers import router as pepe_router





all_routers: list = [admin_router, assistant_router, pepe_router]
