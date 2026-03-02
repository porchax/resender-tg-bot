from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.callbacks.data import QueueCB
from bot.keyboards.queue_kb import queue_confirm_delete_kb, queue_nav_kb
from bot.services.queue_service import delete_post, get_post_at_index

router = Router()


async def _send_post(
    bot: Bot, chat_id: int, post, index: int, total: int
) -> None:
    kb = queue_nav_kb(post.id, index, total)

    if post.is_media_group:
        first = post.items[0]
        file_id = first.file_id
        file_type = first.file_type
        caption = f"Альбом ({len(post.items)} медиа)"
    else:
        file_id = post.file_id
        file_type = post.file_type
        caption = None

    if file_type == "photo":
        await bot.send_photo(chat_id, photo=file_id, caption=caption, reply_markup=kb)
    else:
        await bot.send_video(chat_id, video=file_id, caption=caption, reply_markup=kb)


@router.message(Command("queue"))
@router.message(F.text == "📋 Очередь")
async def cmd_queue(message: Message, session: AsyncSession) -> None:
    post, total = await get_post_at_index(session, 0)
    if post is None:
        await message.answer("📋 Очередь пуста.")
        return
    await _send_post(message.bot, message.chat.id, post, 0, total)


@router.callback_query(QueueCB.filter(F.action == "page"))
async def cb_queue_page(
    callback: CallbackQuery, callback_data: QueueCB, session: AsyncSession
) -> None:
    await callback.message.delete()
    index = callback_data.page
    post, total = await get_post_at_index(session, index)
    if post is None:
        await callback.bot.send_message(callback.from_user.id, "📋 Очередь пуста.")
    else:
        await _send_post(callback.bot, callback.from_user.id, post, index, total)
    await callback.answer()


@router.callback_query(QueueCB.filter(F.action == "delete"))
async def cb_queue_delete(
    callback: CallbackQuery, callback_data: QueueCB
) -> None:
    await callback.message.delete()
    await callback.bot.send_message(
        callback.from_user.id,
        "Удалить этот пост из очереди?",
        reply_markup=queue_confirm_delete_kb(callback_data.post_id, callback_data.page),
    )
    await callback.answer()


@router.callback_query(QueueCB.filter(F.action == "quick_delete"))
async def cb_quick_delete(
    callback: CallbackQuery, callback_data: QueueCB, session: AsyncSession
) -> None:
    ok = await delete_post(session, callback_data.post_id)
    if not ok:
        await callback.answer("Пост не найден", show_alert=True)
        return
    await callback.message.edit_text("🗑 Удалено из очереди")
    await callback.answer("Удалено!")


@router.callback_query(QueueCB.filter(F.action == "confirm_delete"))
async def cb_queue_confirm_delete(
    callback: CallbackQuery, callback_data: QueueCB, session: AsyncSession
) -> None:
    ok = await delete_post(session, callback_data.post_id)
    if not ok:
        await callback.answer("Пост не найден", show_alert=True)
        return

    await callback.answer("Удалено!")
    index = callback_data.page
    post, total = await get_post_at_index(session, index)

    # If we deleted the last item on the current index, step back
    if post is None and total > 0:
        index = total - 1
        post, total = await get_post_at_index(session, index)

    if post is None:
        await callback.message.edit_text("📋 Очередь пуста.")
    else:
        await callback.message.delete()
        await _send_post(callback.bot, callback.from_user.id, post, index, total)
