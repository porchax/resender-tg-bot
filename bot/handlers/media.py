from aiogram import F, Router
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.queue_kb import quick_delete_kb
from bot.services.post_service import create_album_post, create_single_post, extract_file_info
from bot.utils.caption import get_caption

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
    caption, parse_mode = await get_caption(session)
    first_id, first_type = items[0]
    if first_type == "photo":
        await message.answer_photo(photo=first_id, caption=caption, parse_mode=parse_mode)
    else:
        await message.answer_video(video=first_id, caption=caption, parse_mode=parse_mode)
    await message.answer("✅ В очереди", reply_markup=quick_delete_kb(post.id))


@router.message(F.photo)
async def handle_photo(message: Message, session: AsyncSession) -> None:
    file_id = message.photo[-1].file_id
    post = await create_single_post(session, file_id, "photo")
    caption, parse_mode = await get_caption(session)
    await message.answer_photo(
        photo=file_id,
        caption=caption,
        parse_mode=parse_mode,
    )
    await message.answer("✅ В очереди", reply_markup=quick_delete_kb(post.id))


@router.message(F.video)
async def handle_video(message: Message, session: AsyncSession) -> None:
    file_id = message.video.file_id
    post = await create_single_post(session, file_id, "video")
    caption, parse_mode = await get_caption(session)
    await message.answer_video(
        video=file_id,
        caption=caption,
        parse_mode=parse_mode,
    )
    await message.answer("✅ В очереди", reply_markup=quick_delete_kb(post.id))
