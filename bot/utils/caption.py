from sqlalchemy.ext.asyncio import AsyncSession

from bot.services.settings_service import get_setting
from bot.utils.formatting import linkify_urls


async def get_caption(session: AsyncSession) -> tuple[str | None, str | None]:
    """Return (caption, parse_mode) from global caption setting."""
    raw = await get_setting(session, "global_caption")
    if raw:
        return linkify_urls(raw), "HTML"
    return None, None
