import re

from aiogram import F, Router
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.callbacks.data import CaptionCB
from bot.keyboards.caption_kb import caption_confirm_kb
from bot.services.settings_service import get_setting, set_setting
from bot.utils.formatting import linkify_urls

router = Router()

_CMD_PREFIX_RE = re.compile(r"^/caption(?:@\S+)?\s*", re.IGNORECASE)


class CaptionStates(StatesGroup):
    waiting_confirm = State()


@router.message(Command("caption"))
async def cmd_caption(
    message: Message,
    command: CommandObject,
    session: AsyncSession,
    state: FSMContext,
) -> None:
    if not command.args:
        current = await get_setting(session, "global_caption")
        if current:
            await message.answer(
                f"Текущая подпись:\n────────\n{current}\n────────",
                parse_mode="HTML",
            )
        else:
            await message.answer(
                "Подпись не задана.\n\nИспользуйте: /caption <текст>"
            )
        return

    # Extract HTML from message to preserve Telegram entities (inline links, bold, etc.)
    new_caption = _CMD_PREFIX_RE.sub("", message.html_text, count=1)

    await state.set_state(CaptionStates.waiting_confirm)
    await state.update_data(new_caption=new_caption)
    preview = linkify_urls(new_caption)
    await message.answer(
        f"Предпросмотр:\n────────\n{preview}\n────────\n\n💡 URL будут кликабельны автоматически.",
        reply_markup=caption_confirm_kb(),
        parse_mode="HTML",
    )


@router.callback_query(CaptionCB.filter(F.action == "save"))
async def cb_caption_save(
    callback: CallbackQuery,
    session: AsyncSession,
    state: FSMContext,
) -> None:
    data = await state.get_data()
    new_caption = data.get("new_caption")
    if not new_caption:
        await callback.answer("Нет данных для сохранения", show_alert=True)
        return

    await set_setting(session, "global_caption", new_caption)
    await state.clear()
    await callback.message.edit_text(
        f"Подпись сохранена:\n────────\n{new_caption}\n────────",
        parse_mode="HTML",
    )
    await callback.answer("Сохранено!")


@router.callback_query(CaptionCB.filter(F.action == "cancel"))
async def cb_caption_cancel(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    await state.clear()
    await callback.message.edit_text("Изменение подписи отменено.")
    await callback.answer()
