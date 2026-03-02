from aiogram import F, Router
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.services.post_service import create_album_post, create_single_post, extract_file_info

router = Router()


@router.message(F.media_group_id, F.photo | F.video)
async def handle_album(
    message: Message, session: AsyncSession, album: list[Message]
) -> None:
    items: list[tuple[str, str]] = []
    for msg in album:
        info = extract_file_info(msg)
        if info:
            items.append(info)

    if not items:
        return

    post = await create_album_post(session, items)
    caption = f"✅ Альбом ({len(items)} медиа) добавлен в очередь (позиция {post.position})"
    first_id, first_type = items[0]
    if first_type == "photo":
        await message.answer_photo(photo=first_id, caption=caption)
    else:
        await message.answer_video(video=first_id, caption=caption)


@router.message(F.photo)
async def handle_photo(message: Message, session: AsyncSession) -> None:
    file_id = message.photo[-1].file_id
    post = await create_single_post(session, file_id, "photo")
    await message.reply_photo(
        photo=file_id,
        caption=f"✅ Фото добавлено в очередь (позиция {post.position})",
    )


@router.message(F.video)
async def handle_video(message: Message, session: AsyncSession) -> None:
    file_id = message.video.file_id
    post = await create_single_post(session, file_id, "video")
    await message.reply_video(
        video=file_id,
        caption=f"✅ Видео добавлено в очередь (позиция {post.position})",
    )
