from datetime import datetime, time, timedelta, timezone

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.config import settings as app_settings
from bot.db.models import ScheduleSlot
from bot.services.settings_service import get_setting

import zoneinfo


def _tz():
    return zoneinfo.ZoneInfo(app_settings.timezone)


async def get_active_slots(session: AsyncSession) -> list[ScheduleSlot]:
    result = await session.execute(
        select(ScheduleSlot)
        .where(ScheduleSlot.is_active.is_(True))
        .order_by(ScheduleSlot.time)
    )
    return list(result.scalars().all())


async def get_all_slots(session: AsyncSession) -> list[ScheduleSlot]:
    result = await session.execute(
        select(ScheduleSlot).order_by(ScheduleSlot.time)
    )
    return list(result.scalars().all())


async def add_slot(
    session: AsyncSession,
    hour: int,
    minute: int,
    day_of_week: int | None = None,
) -> ScheduleSlot:
    slot = ScheduleSlot(
        day_of_week=day_of_week,
        time=time(hour, minute),
        is_active=True,
    )
    session.add(slot)
    await session.flush()
    return slot


async def remove_slot(session: AsyncSession, slot_id: int) -> bool:
    result = await session.execute(
        select(ScheduleSlot).where(ScheduleSlot.id == slot_id)
    )
    slot = result.scalar_one_or_none()
    if slot is None:
        return False
    await session.delete(slot)
    return True


async def toggle_slot(session: AsyncSession, slot_id: int) -> ScheduleSlot | None:
    result = await session.execute(
        select(ScheduleSlot).where(ScheduleSlot.id == slot_id)
    )
    slot = result.scalar_one_or_none()
    if slot is None:
        return None
    slot.is_active = not slot.is_active
    return slot


DAY_NAMES = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]


def slot_label(slot: ScheduleSlot) -> str:
    t = slot.time.strftime("%H:%M")
    if slot.day_of_week is not None:
        return f"{DAY_NAMES[slot.day_of_week]} {t}"
    return f"Каждый день {t}"


async def compute_next_fire_time(session: AsyncSession) -> datetime | None:
    mode = await get_setting(session, "schedule_mode")
    now = datetime.now(_tz())

    if mode == "interval":
        interval_str = await get_setting(session, "schedule_interval_minutes")
        interval = int(interval_str) if interval_str else 60
        last_str = await get_setting(session, "last_publish_time")
        if last_str:
            last = datetime.fromtimestamp(int(last_str), tz=timezone.utc).astimezone(_tz())
            nxt = last + timedelta(minutes=interval)
            if nxt < now:
                nxt = now + timedelta(minutes=interval)
            return nxt
        return now + timedelta(minutes=interval)

    slots = await get_active_slots(session)
    if not slots:
        return None

    candidates: list[datetime] = []
    for slot in slots:
        dt = now.replace(hour=slot.time.hour, minute=slot.time.minute, second=0, microsecond=0)
        if slot.day_of_week is not None:
            days_ahead = slot.day_of_week - now.weekday()
            if days_ahead < 0 or (days_ahead == 0 and dt <= now):
                days_ahead += 7
            dt += timedelta(days=days_ahead)
        else:
            if dt <= now:
                dt += timedelta(days=1)
        candidates.append(dt)

    return min(candidates) if candidates else None
