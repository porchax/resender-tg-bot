from aiogram.types import Message
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db.models import MediaGroupItem, Post


async def _next_position(session: AsyncSession) -> int:
    result = await session.execute(
        select(func.coalesce(func.max(Post.position), 0))
    )
    return result.scalar_one() + 1


async def create_single_post(
    session: AsyncSession,
    file_id: str,
    file_type: str,
) -> Post:
    position = await _next_position(session)
    post = Post(
        is_media_group=False,
        file_id=file_id,
        file_type=file_type,
        position=position,
        status="queued",
    )
    session.add(post)
    await session.flush()
    return post


async def create_album_post(
    session: AsyncSession,
    items: list[tuple[str, str]],
) -> Post:
    position = await _next_position(session)
    post = Post(
        is_media_group=True,
        position=position,
        status="queued",
    )
    session.add(post)
    await session.flush()

    for idx, (file_id, file_type) in enumerate(items):
        item = MediaGroupItem(
            post_id=post.id,
            file_id=file_id,
            file_type=file_type,
            position=idx,
        )
        session.add(item)

    await session.flush()
    return post


def extract_file_info(message: Message) -> tuple[str, str] | None:
    if message.photo:
        return message.photo[-1].file_id, "photo"
    if message.video:
        return message.video.file_id, "video"
    return None
