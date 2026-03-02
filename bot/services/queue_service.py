from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from bot.db.models import Post

PAGE_SIZE = 5


async def get_queue_page(
    session: AsyncSession, page: int = 0
) -> tuple[list[Post], int]:
    count_q = select(func.count(Post.id)).where(Post.status == "queued")
    total = (await session.execute(count_q)).scalar_one()

    q = (
        select(Post)
        .where(Post.status == "queued")
        .order_by(Post.position)
        .offset(page * PAGE_SIZE)
        .limit(PAGE_SIZE)
        .options(selectinload(Post.items))
    )
    posts = list((await session.execute(q)).scalars().all())
    return posts, total


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


async def swap_positions(
    session: AsyncSession, post_id: int, direction: str
) -> bool:
    post = await get_post_by_id(session, post_id)
    if post is None or post.status != "queued":
        return False

    if direction == "up":
        neighbor_q = (
            select(Post)
            .where(Post.status == "queued", Post.position < post.position)
            .order_by(Post.position.desc())
            .limit(1)
        )
    else:
        neighbor_q = (
            select(Post)
            .where(Post.status == "queued", Post.position > post.position)
            .order_by(Post.position)
            .limit(1)
        )

    neighbor = (await session.execute(neighbor_q)).scalar_one_or_none()
    if neighbor is None:
        return False

    # Use a temporary value to avoid UNIQUE constraint violation
    old_post_pos = post.position
    old_neighbor_pos = neighbor.position

    post.position = -1
    await session.flush()

    post.position = old_neighbor_pos
    neighbor.position = old_post_pos
    await session.flush()

    return True


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
