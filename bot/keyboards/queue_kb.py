from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.callbacks.data import QueueCB


def queue_nav_kb(post_id: int, index: int, total: int) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = [
        [
            InlineKeyboardButton(
                text="🗑 Удалить",
                callback_data=QueueCB(action="delete", post_id=post_id, page=index).pack(),
            ),
        ],
    ]

    nav_row: list[InlineKeyboardButton] = []
    if index > 0:
        nav_row.append(
            InlineKeyboardButton(
                text="◀️",
                callback_data=QueueCB(action="page", page=index - 1).pack(),
            )
        )
    nav_row.append(
        InlineKeyboardButton(
            text=f"{index + 1}/{total}",
            callback_data="noop",
        )
    )
    if index < total - 1:
        nav_row.append(
            InlineKeyboardButton(
                text="▶️",
                callback_data=QueueCB(action="page", page=index + 1).pack(),
            )
        )
    rows.append(nav_row)
    return InlineKeyboardMarkup(inline_keyboard=rows)


def quick_delete_kb(post_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🗑 Удалить",
                    callback_data=QueueCB(action="quick_delete", post_id=post_id).pack(),
                ),
            ]
        ]
    )


def queue_confirm_delete_kb(post_id: int, index: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Да, удалить",
                    callback_data=QueueCB(action="confirm_delete", post_id=post_id, page=index).pack(),
                ),
                InlineKeyboardButton(
                    text="❌ Отмена",
                    callback_data=QueueCB(action="page", page=index).pack(),
                ),
            ]
        ]
    )
