from datetime import timezone

from aiogram import Bot, Router
from aiogram.filters import Command
from aiogram.types import Message, MessageEntity
from sqlalchemy.ext.asyncio import AsyncSession

from bot.services.publisher import publish_next
from bot.services.queue_service import get_next_queued
from bot.services.schedule_service import compute_next_fire_time
from bot.utils.formatting import format_dt

router = Router()


@router.message(Command("publish"))
async def cmd_publish(message: Message, session: AsyncSession) -> None:
    bot: Bot = message.bot  # type: ignore[assignment]
    post = await publish_next(bot, session)
    if post is None:
        await message.answer("Очередь пуста — нечего публиковать.")
        return

    if post.is_media_group:
        desc = f"Альбом ({len(post.items)} медиа)"
    else:
        desc = "Фото" if post.file_type == "photo" else "Видео"
    await message.answer(f"Опубликовано: {desc} (пост #{post.id})")


@router.message(Command("next"))
async def cmd_next(message: Message, session: AsyncSession) -> None:
    post = await get_next_queued(session)
    if post is None:
        await message.answer("Очередь пуста.")
        return

    if post.is_media_group:
        desc = f"Альбом ({len(post.items)} медиа)"
    else:
        icon = "🖼" if post.file_type == "photo" else "🎬"
        label = "Фото" if post.file_type == "photo" else "Видео"
        desc = f"{icon} {label}"

    next_time = await compute_next_fire_time(session)
    entities: list[MessageEntity] | None = None

    if next_time:
        time_str = format_dt(next_time)
        time_label = f"⏰ Публикация: {time_str}"
        base_text = f"📌 Следующий пост:\nТип: {desc}\nПозиция: {post.position}\n\n{time_label}"

        ts = int(next_time.astimezone(timezone.utc).timestamp())
        offset = base_text.index(time_str)
        entities = [
            MessageEntity(
                type="date_time",
                offset=offset,
                length=len(time_str),
                date_time=ts,
            )
        ]
    else:
        base_text = f"📌 Следующий пост:\nТип: {desc}\nПозиция: {post.position}\n\n⏰ Расписание не настроено"

    await message.answer(base_text, entities=entities, parse_mode=None)
