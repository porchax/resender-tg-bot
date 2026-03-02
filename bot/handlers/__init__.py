from aiogram import Dispatcher

from bot.handlers.caption import router as caption_router
from bot.handlers.control import router as control_router
from bot.handlers.instagram import router as instagram_router
from bot.handlers.media import router as media_router
from bot.handlers.publish import router as publish_router
from bot.handlers.queue import router as queue_router
from bot.handlers.schedule import router as schedule_router
from bot.handlers.start import router as start_router
from bot.handlers.stats import router as stats_router


def setup_routers(dp: Dispatcher) -> None:
    dp.include_routers(
        start_router,
        caption_router,
        queue_router,
        schedule_router,
        publish_router,
        control_router,
        stats_router,
        instagram_router,  # before media — media is catch-all
        media_router,  # last — catches photo/video
    )
