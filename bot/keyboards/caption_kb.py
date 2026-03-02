from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.callbacks.data import CaptionCB


def caption_confirm_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Сохранить",
                    callback_data=CaptionCB(action="save").pack(),
                    style="success",
                ),
                InlineKeyboardButton(
                    text="❌ Отмена",
                    callback_data=CaptionCB(action="cancel").pack(),
                    style="danger",
                ),
            ]
        ]
    )
