from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.callbacks.data import ScheduleCB
from bot.db.models import ScheduleSlot
from bot.services.schedule_service import DAY_NAMES, slot_label


def schedule_main_kb(
    slots: list[ScheduleSlot], mode: str, interval: int
) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []

    if mode == "slots":
        rows.append([
            InlineKeyboardButton(
                text="📋 Режим: Слоты (по часам)",
                callback_data="noop",
            )
        ])
        for slot in slots:
            status = "✅" if slot.is_active else "❌"
            rows.append([
                InlineKeyboardButton(
                    text=f"{status} {slot_label(slot)}",
                    callback_data=ScheduleCB(action="toggle", slot_id=slot.id).pack(),
                ),
                InlineKeyboardButton(
                    text="🗑",
                    callback_data=ScheduleCB(action="delete", slot_id=slot.id).pack(),
                    style="danger",
                ),
            ])
        rows.append([
            InlineKeyboardButton(
                text="➕ Добавить слот",
                callback_data=ScheduleCB(action="add").pack(),
                style="success",
            )
        ])
    else:
        rows.append([
            InlineKeyboardButton(
                text=f"⏱ Режим: Интервал ({interval} мин)",
                callback_data="noop",
            )
        ])
        rows.append([
            InlineKeyboardButton(
                text="15 мин",
                callback_data=ScheduleCB(action="interval", value="15").pack(),
            ),
            InlineKeyboardButton(
                text="30 мин",
                callback_data=ScheduleCB(action="interval", value="30").pack(),
            ),
            InlineKeyboardButton(
                text="60 мин",
                callback_data=ScheduleCB(action="interval", value="60").pack(),
            ),
            InlineKeyboardButton(
                text="120 мин",
                callback_data=ScheduleCB(action="interval", value="120").pack(),
            ),
        ])

    rows.append([
        InlineKeyboardButton(
            text="🔄 Сменить режим",
            callback_data=ScheduleCB(action="mode").pack(),
            style="primary",
        )
    ])

    return InlineKeyboardMarkup(inline_keyboard=rows)


HOURS = list(range(8, 24))


def schedule_add_time_kb() -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    row: list[InlineKeyboardButton] = []
    for h in HOURS:
        row.append(
            InlineKeyboardButton(
                text=f"{h:02d}:00",
                callback_data=ScheduleCB(action="set_time", value=f"{h}.0").pack(),
            )
        )
        if len(row) == 4:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([
        InlineKeyboardButton(
            text="◀️ Назад",
            callback_data=ScheduleCB(action="show").pack(),
        )
    ])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def schedule_add_day_kb(hour: int, minute: int) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    rows.append([
        InlineKeyboardButton(
            text="Каждый день",
            callback_data=ScheduleCB(action="confirm", value=f"{hour}.{minute}.all").pack(),
            style="success",
        )
    ])
    row: list[InlineKeyboardButton] = []
    for i, name in enumerate(DAY_NAMES):
        row.append(
            InlineKeyboardButton(
                text=name,
                callback_data=ScheduleCB(action="confirm", value=f"{hour}.{minute}.{i}").pack(),
            )
        )
        if len(row) == 4:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([
        InlineKeyboardButton(
            text="◀️ Назад",
            callback_data=ScheduleCB(action="add").pack(),
        )
    ])
    return InlineKeyboardMarkup(inline_keyboard=rows)
