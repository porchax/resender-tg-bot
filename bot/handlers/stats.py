from datetime import datetime, timezone

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message, MessageEntity
from sqlalchemy.ext.asyncio import AsyncSession

from bot.services.queue_service import get_published_count, get_queued_count
from bot.services.schedule_service import compute_next_fire_time
from bot.services.settings_service import get_setting, is_paused
from bot.utils.formatting import format_dt

router = Router()


@router.message(Command("stats"))
async def cmd_stats(message: Message, session: AsyncSession) -> None:
    queued = await get_queued_count(session)
    published = await get_published_count(session)
    paused = await is_paused(session)
    mode = await get_setting(session, "schedule_mode")
    last_str = await get_setting(session, "last_publish_time")

    status = "⏸ Пауза" if paused else "▶️ Активно"
    mode_label = "Слоты" if mode == "slots" else "Интервал"

    lines = [
        "📊 Статистика:\n",
        f"Статус: {status}",
        f"Режим: {mode_label}",
        f"В очереди: {queued}",
        f"Опубликовано: {published}",
    ]

    entities: list[MessageEntity] = []

    if last_str:
        last_ts = int(last_str)
        last_dt = datetime.fromtimestamp(last_ts, tz=timezone.utc)
        last_fmt = format_dt(last_dt)
        last_line = f"Последняя публикация: {last_fmt}"
        lines.append(last_line)

    next_time = await compute_next_fire_time(session)
    if next_time:
        next_fmt = format_dt(next_time)
        next_line = f"Следующая публикация: {next_fmt}"
        lines.append(next_line)

    text = "\n".join(lines)

    # Build date_time entities
    if last_str:
        last_ts = int(last_str)
        last_fmt = format_dt(datetime.fromtimestamp(last_ts, tz=timezone.utc))
        idx = text.index(last_fmt)
        entities.append(
            MessageEntity(
                type="date_time",
                offset=idx,
                length=len(last_fmt),
                unix_time=last_ts,
            )
        )

    if next_time:
        next_fmt = format_dt(next_time)
        next_ts = int(next_time.astimezone(timezone.utc).timestamp())
        idx = text.rindex(next_fmt)
        entities.append(
            MessageEntity(
                type="date_time",
                offset=idx,
                length=len(next_fmt),
                unix_time=next_ts,
            )
        )

    await message.answer(text, entities=entities if entities else None, parse_mode=None)
