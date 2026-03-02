import re
import shutil

from aiogram import F, Router
from aiogram.types import FSInputFile, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.queue_kb import quick_delete_kb
from bot.services.instagram_service import InstagramDownloadError, download_instagram
from bot.services.post_service import create_single_post
from bot.utils.caption import get_caption

router = Router()

_INSTAGRAM_RE = re.compile(
    r"https?://(?:www\.)?instagram\.com/(?:reel|p)/[\w-]+"
)


@router.message(F.text.regexp(_INSTAGRAM_RE))
async def handle_instagram_link(message: Message, session: AsyncSession) -> None:
    match = _INSTAGRAM_RE.search(message.text)
    if not match:
        return

    url = match.group()
    status_msg = await message.answer("⏳ Скачиваю...")

    tmp_dir: str | None = None
    try:
        path, media_type, tmp_dir = await download_instagram(url)
        caption, parse_mode = await get_caption(session)

        input_file = FSInputFile(path)
        if media_type == "photo":
            sent = await message.answer_photo(
                photo=input_file, caption=caption, parse_mode=parse_mode
            )
            file_id = sent.photo[-1].file_id
        else:
            sent = await message.answer_video(
                video=input_file, caption=caption, parse_mode=parse_mode
            )
            file_id = sent.video.file_id

        post = await create_single_post(session, file_id, media_type)
        await status_msg.delete()
        await message.answer("✅ В очереди", reply_markup=quick_delete_kb(post.id))

    except (InstagramDownloadError, Exception):
        await status_msg.delete()
        await message.answer("😔 Не удалось скачать медиа из Instagram")

    finally:
        if tmp_dir:
            shutil.rmtree(tmp_dir, ignore_errors=True)
