from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.services.settings_service import get_setting, set_setting

router = Router()


@router.message(Command("pause"))
async def cmd_pause(message: Message, session: AsyncSession) -> None:
    current = await get_setting(session, "schedule_paused")
    if current == "true":
        await message.answer("Публикации уже на паузе.")
        return
    await set_setting(session, "schedule_paused", "true")
    await message.answer("⏸ Публикации приостановлены.\nИспользуйте /resume для возобновления.")


@router.message(Command("resume"))
async def cmd_resume(message: Message, session: AsyncSession) -> None:
    current = await get_setting(session, "schedule_paused")
    if current != "true":
        await message.answer("Публикации не на паузе.")
        return
    await set_setting(session, "schedule_paused", "false")
    await message.answer("▶️ Публикации возобновлены!")
