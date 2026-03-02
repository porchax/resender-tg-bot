import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import BotCommand

from bot.config import settings
from bot.handlers import setup_routers
from bot.middlewares import setup_middlewares
from bot.services.scheduler import SchedulerService

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
log = logging.getLogger(__name__)

COMMANDS = [
    BotCommand(command="start", description="Приветствие и инструкция"),
    BotCommand(command="help", description="Справка по командам"),
    BotCommand(command="caption", description="Показать/изменить подпись"),
    BotCommand(command="queue", description="Очередь постов"),
    BotCommand(command="schedule", description="Настройка расписания"),
    BotCommand(command="next", description="Следующий пост и время публикации"),
    BotCommand(command="publish", description="Опубликовать сейчас"),
    BotCommand(command="pause", description="Пауза публикаций"),
    BotCommand(command="resume", description="Возобновить публикации"),
    BotCommand(command="stats", description="Статистика"),
]


async def main() -> None:
    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()

    setup_middlewares(dp)
    setup_routers(dp)

    await bot.set_my_commands(COMMANDS)
    log.info("Bot commands registered")

    scheduler_service = SchedulerService(bot)
    await scheduler_service.start()
    dp["scheduler_service"] = scheduler_service

    try:
        log.info("Starting polling…")
        await dp.start_polling(bot)
    finally:
        await scheduler_service.stop()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
