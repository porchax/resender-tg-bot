import math

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.callbacks.data import QueueCB
from bot.db.models import Post
from bot.services.queue_service import PAGE_SIZE


def _post_label(idx: int, post: Post) -> str:
    if post.is_media_group:
        count = len(post.items)
        types = ""
        for item in post.items:
            types += "🖼️" if item.file_type == "photo" else "🎬"
        return f"{idx}. {types} Альбом ({count})"
    icon = "🖼" if post.file_type == "photo" else "🎬"
    label = "Фото" if post.file_type == "photo" else "Видео"
    return f"{idx}. {icon} {label}"


def queue_list_kb(
    posts: list[Post], total: int, page: int
) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []

    for i, post in enumerate(posts):
        idx = page * PAGE_SIZE + i + 1
        rows.append([
            InlineKeyboardButton(
                text=_post_label(idx, post),
                callback_data=QueueCB(action="select", post_id=post.id, page=page).pack(),
            )
        ])

    total_pages = max(1, math.ceil(total / PAGE_SIZE))
    nav_row: list[InlineKeyboardButton] = []
    if page > 0:
        nav_row.append(
            InlineKeyboardButton(
                text="◀️",
                callback_data=QueueCB(action="page", page=page - 1).pack(),
            )
        )
    nav_row.append(
        InlineKeyboardButton(
            text=f"{page + 1}/{total_pages}",
            callback_data="noop",
        )
    )
    if page < total_pages - 1:
        nav_row.append(
            InlineKeyboardButton(
                text="▶️",
                callback_data=QueueCB(action="page", page=page + 1).pack(),
            )
        )
    rows.append(nav_row)
    return InlineKeyboardMarkup(inline_keyboard=rows)


def queue_post_actions_kb(post_id: int, page: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⬆️ Вверх",
                    callback_data=QueueCB(action="up", post_id=post_id, page=page).pack(),
                    style="primary",
                ),
                InlineKeyboardButton(
                    text="⬇️ Вниз",
                    callback_data=QueueCB(action="down", post_id=post_id, page=page).pack(),
                    style="primary",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🗑 Удалить",
                    callback_data=QueueCB(action="delete", post_id=post_id, page=page).pack(),
                    style="danger",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="◀️ К очереди",
                    callback_data=QueueCB(action="page", page=page).pack(),
                ),
            ],
        ]
    )


def queue_confirm_delete_kb(post_id: int, page: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Да, удалить",
                    callback_data=QueueCB(action="confirm_delete", post_id=post_id, page=page).pack(),
                    style="danger",
                ),
                InlineKeyboardButton(
                    text="❌ Отмена",
                    callback_data=QueueCB(action="select", post_id=post_id, page=page).pack(),
                    style="primary",
                ),
            ]
        ]
    )
