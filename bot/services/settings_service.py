from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db.models import Setting

DEFAULTS: dict[str, str] = {
    "global_caption": "",
    "timezone": "Europe/Moscow",
    "schedule_paused": "false",
    "schedule_mode": "slots",
    "schedule_interval_minutes": "60",
    "last_publish_time": "",
}


async def get_setting(session: AsyncSession, key: str) -> str:
    result = await session.execute(select(Setting).where(Setting.key == key))
    row = result.scalar_one_or_none()
    if row is not None:
        return row.value
    return DEFAULTS.get(key, "")


async def set_setting(session: AsyncSession, key: str, value: str) -> None:
    result = await session.execute(select(Setting).where(Setting.key == key))
    row = result.scalar_one_or_none()
    if row is not None:
        row.value = value
    else:
        session.add(Setting(key=key, value=value))


async def is_paused(session: AsyncSession) -> bool:
    return (await get_setting(session, "schedule_paused")) == "true"
