from aiogram.types import InlineKeyboardButton


def back_button(callback_data: str, text: str = "◀️ Назад") -> InlineKeyboardButton:
    return InlineKeyboardButton(text=text, callback_data=callback_data)


def cancel_button(callback_data: str) -> InlineKeyboardButton:
    return InlineKeyboardButton(
        text="❌ Отмена", callback_data=callback_data, style="danger"
    )


def confirm_button(callback_data: str, text: str = "✅ Подтвердить") -> InlineKeyboardButton:
    return InlineKeyboardButton(
        text=text, callback_data=callback_data, style="success"
    )
