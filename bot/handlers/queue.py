from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.callbacks.data import QueueCB
from bot.keyboards.queue_kb import (
    queue_confirm_delete_kb,
    queue_list_kb,
    queue_post_actions_kb,
)
from bot.services.queue_service import (
    delete_post,
    get_post_by_id,
    get_queue_page,
    swap_positions,
)

router = Router()


def _queue_text(posts, total: int, page: int) -> str:
    if total == 0:
        return "📋 Очередь пуста."
    from bot.keyboards.queue_kb import _post_label, PAGE_SIZE

    lines = [f"📋 Очередь постов ({total} шт.):\n"]
    for i, post in enumerate(posts):
        idx = page * PAGE_SIZE + i + 1
        lines.append(_post_label(idx, post))
    return "\n".join(lines)


def _is_media_msg(message) -> bool:
    return bool(message.photo or message.video)


async def _send_queue_list(
    chat_id: int, bot, session: AsyncSession, page: int
) -> None:
    posts, total = await get_queue_page(session, page)
    text = _queue_text(posts, total, page)
    if total == 0:
        await bot.send_message(chat_id, text)
    else:
        await bot.send_message(
            chat_id, text, reply_markup=queue_list_kb(posts, total, page)
        )


@router.message(Command("queue"))
async def cmd_queue(message: Message, session: AsyncSession) -> None:
    posts, total = await get_queue_page(session, page=0)
    text = _queue_text(posts, total, 0)
    if total == 0:
        await message.answer(text)
    else:
        await message.answer(text, reply_markup=queue_list_kb(posts, total, 0))


@router.callback_query(QueueCB.filter(F.action == "page"))
async def cb_queue_page(
    callback: CallbackQuery, callback_data: QueueCB, session: AsyncSession
) -> None:
    page = callback_data.page
    posts, total = await get_queue_page(session, page)
    text = _queue_text(posts, total, page)

    if _is_media_msg(callback.message):
        await callback.message.delete()
        if total == 0:
            await callback.bot.send_message(callback.from_user.id, text)
        else:
            await callback.bot.send_message(
                callback.from_user.id,
                text,
                reply_markup=queue_list_kb(posts, total, page),
            )
    else:
        if total == 0:
            await callback.message.edit_text(text)
        else:
            await callback.message.edit_text(
                text, reply_markup=queue_list_kb(posts, total, page)
            )
    await callback.answer()


@router.callback_query(QueueCB.filter(F.action == "select"))
async def cb_queue_select(
    callback: CallbackQuery, callback_data: QueueCB, session: AsyncSession
) -> None:
    post = await get_post_by_id(session, callback_data.post_id)
    if post is None or post.status != "queued":
        await callback.answer("Пост не найден", show_alert=True)
        return

    kb = queue_post_actions_kb(post.id, callback_data.page)

    if post.is_media_group:
        first = post.items[0]
        file_id = first.file_id
        file_type = first.file_type
        caption = f"Пост #{post.id} — Альбом ({len(post.items)} медиа)\nПозиция: {post.position}"
    else:
        file_id = post.file_id
        file_type = post.file_type
        caption = f"Пост #{post.id}\nПозиция: {post.position}"

    await callback.message.delete()

    chat_id = callback.from_user.id
    if file_type == "photo":
        await callback.bot.send_photo(
            chat_id, photo=file_id, caption=caption, reply_markup=kb
        )
    else:
        await callback.bot.send_video(
            chat_id, video=file_id, caption=caption, reply_markup=kb
        )
    await callback.answer()


@router.callback_query(QueueCB.filter(F.action.in_({"up", "down"})))
async def cb_queue_move(
    callback: CallbackQuery, callback_data: QueueCB, session: AsyncSession
) -> None:
    ok = await swap_positions(session, callback_data.post_id, callback_data.action)
    if not ok:
        await callback.answer("Нельзя переместить", show_alert=True)
        return

    await callback.answer("Перемещено!")
    await callback.message.delete()
    await _send_queue_list(
        callback.from_user.id, callback.bot, session, callback_data.page
    )


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


@router.callback_query(QueueCB.filter(F.action == "confirm_delete"))
async def cb_queue_confirm_delete(
    callback: CallbackQuery, callback_data: QueueCB, session: AsyncSession
) -> None:
    ok = await delete_post(session, callback_data.post_id)
    if not ok:
        await callback.answer("Пост не найден", show_alert=True)
        return

    await callback.answer("Удалено!")
    posts, total = await get_queue_page(session, callback_data.page)
    text = _queue_text(posts, total, callback_data.page)
    if total == 0:
        await callback.message.edit_text(text)
    else:
        await callback.message.edit_text(
            text, reply_markup=queue_list_kb(posts, total, callback_data.page)
        )
