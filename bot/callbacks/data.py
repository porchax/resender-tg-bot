from aiogram.filters.callback_data import CallbackData


class QueueCB(CallbackData, prefix="q"):
    action: str  # page, delete, confirm_delete, quick_delete
    post_id: int = 0
    page: int = 0


class ScheduleCB(CallbackData, prefix="sch"):
    action: str  # show, add, delete, toggle, mode, interval, set_time, set_day, confirm
    slot_id: int = 0
    value: str = ""


class CaptionCB(CallbackData, prefix="cap"):
    action: str  # save, cancel
