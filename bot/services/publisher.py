import logging
from datetime import datetime, timezone

from aiogram import Bot
from aiogram.types import InputMediaPhoto, InputMediaVideo
from sqlalchemy.ext.asyncio import AsyncSession

from bot.config import settings
from bot.db.models import Post
from bot.services.queue_service import get_next_queued
from bot.services.settings_service import get_setting, set_setting
from bot.utils.formatting import linkify_urls

log = logging.getLogger(__name__)


async def publish_post(bot: Bot, session: AsyncSession, post: Post) -> bool:
    raw_caption = post.caption_override or await get_setting(session, "global_caption") or None
    caption = linkify_urls(raw_caption) if raw_caption else None

    try:
        if post.is_media_group:
            media = []
            for i, item in enumerate(post.items):
                if item.file_type == "photo":
                    m = InputMediaPhoto(media=item.file_id, caption=caption if i == 0 else None, parse_mode="HTML" if i == 0 else None)
                else:
                    m = InputMediaVideo(media=item.file_id, caption=caption if i == 0 else None, parse_mode="HTML" if i == 0 else None)
                media.append(m)
            await bot.send_media_group(chat_id=settings.channel_id, media=media)
        else:
            if post.file_type == "photo":
                await bot.send_photo(chat_id=settings.channel_id, photo=post.file_id, caption=caption, parse_mode="HTML" if caption else None)
            else:
                await bot.send_video(chat_id=settings.channel_id, video=post.file_id, caption=caption, parse_mode="HTML" if caption else None)

        post.status = "published"
        post.published_at = datetime.now(timezone.utc)
        await set_setting(session, "last_publish_time", str(int(post.published_at.timestamp())))
        log.info("Published post #%d", post.id)
        return True

    except Exception:
        log.exception("Failed to publish post #%d", post.id)
        post.status = "error"
        return False


async def publish_next(bot: Bot, session: AsyncSession) -> Post | None:
    post = await get_next_queued(session)
    if post is None:
        return None
    ok = await publish_post(bot, session, post)
    return post if ok else None
