from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from bot.db.models import Post

async def get_post_by_id(session: AsyncSession, post_id: int) -> Post | None:
    q = (
        select(Post)
        .where(Post.id == post_id)
        .options(selectinload(Post.items))
    )
    return (await session.execute(q)).scalar_one_or_none()


async def delete_post(session: AsyncSession, post_id: int) -> bool:
    post = await get_post_by_id(session, post_id)
    if post is None or post.status != "queued":
        return False
    post.status = "deleted"
    return True


async def get_post_at_index(
    session: AsyncSession, index: int
) -> tuple[Post | None, int]:
    count_q = select(func.count(Post.id)).where(Post.status == "queued")
    total = (await session.execute(count_q)).scalar_one()

    q = (
        select(Post)
        .where(Post.status == "queued")
        .order_by(Post.position)
        .offset(index)
        .limit(1)
        .options(selectinload(Post.items))
    )
    post = (await session.execute(q)).scalar_one_or_none()
    return post, total


async def get_next_queued(session: AsyncSession) -> Post | None:
    q = (
        select(Post)
        .where(Post.status == "queued")
        .order_by(Post.position)
        .limit(1)
        .options(selectinload(Post.items))
    )
    return (await session.execute(q)).scalar_one_or_none()


async def get_queued_count(session: AsyncSession) -> int:
    result = await session.execute(
        select(func.count(Post.id)).where(Post.status == "queued")
    )
    return result.scalar_one()


async def get_published_count(session: AsyncSession) -> int:
    result = await session.execute(
        select(func.count(Post.id)).where(Post.status == "published")
    )
    return result.scalar_one()
