from aiogram import Dispatcher

from bot.middlewares.admin import AdminMiddleware
from bot.middlewares.album import AlbumMiddleware
from bot.middlewares.db_session import DbSessionMiddleware


def setup_middlewares(dp: Dispatcher) -> None:
    dp.update.outer_middleware(AdminMiddleware())
    dp.update.outer_middleware(DbSessionMiddleware())
    dp.message.middleware(AlbumMiddleware())
