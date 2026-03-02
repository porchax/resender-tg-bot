from __future__ import annotations

from typing import TYPE_CHECKING

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.callbacks.data import ScheduleCB
from bot.keyboards.schedule_kb import (
    schedule_add_day_kb,
    schedule_add_time_kb,
    schedule_main_kb,
)
from bot.services.schedule_service import (
    add_slot,
    get_all_slots,
    remove_slot,
    toggle_slot,
)
from bot.services.settings_service import get_setting, set_setting

if TYPE_CHECKING:
    from bot.services.scheduler import SchedulerService

router = Router()


async def _schedule_text_and_kb(session: AsyncSession):
    mode = await get_setting(session, "schedule_mode")
    interval_str = await get_setting(session, "schedule_interval_minutes")
    interval = int(interval_str) if interval_str else 60
    slots = await get_all_slots(session)
    text = "⏰ Настройка расписания:"
    kb = schedule_main_kb(slots, mode, interval)
    return text, kb


async def _flush_and_rebuild(
    session: AsyncSession, scheduler_service: SchedulerService | None
) -> None:
    """Flush pending changes so the scheduler reads fresh data, then rebuild."""
    await session.flush()
    if scheduler_service:
        await scheduler_service.rebuild()


@router.message(Command("schedule"))
async def cmd_schedule(message: Message, session: AsyncSession) -> None:
    text, kb = await _schedule_text_and_kb(session)
    await message.answer(text, reply_markup=kb)


@router.callback_query(ScheduleCB.filter(F.action == "show"))
async def cb_schedule_show(
    callback: CallbackQuery, session: AsyncSession
) -> None:
    text, kb = await _schedule_text_and_kb(session)
    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()


@router.callback_query(ScheduleCB.filter(F.action == "mode"))
async def cb_schedule_mode(
    callback: CallbackQuery,
    session: AsyncSession,
    scheduler_service: SchedulerService | None = None,
) -> None:
    current = await get_setting(session, "schedule_mode")
    new_mode = "interval" if current == "slots" else "slots"
    await set_setting(session, "schedule_mode", new_mode)
    await _flush_and_rebuild(session, scheduler_service)

    text, kb = await _schedule_text_and_kb(session)
    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer(f"Режим: {'Слоты' if new_mode == 'slots' else 'Интервал'}")


@router.callback_query(ScheduleCB.filter(F.action == "toggle"))
async def cb_schedule_toggle(
    callback: CallbackQuery,
    callback_data: ScheduleCB,
    session: AsyncSession,
    scheduler_service: SchedulerService | None = None,
) -> None:
    slot = await toggle_slot(session, callback_data.slot_id)
    if slot is None:
        await callback.answer("Слот не найден", show_alert=True)
        return
    await _flush_and_rebuild(session, scheduler_service)
    text, kb = await _schedule_text_and_kb(session)
    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer("Переключено")


@router.callback_query(ScheduleCB.filter(F.action == "delete"))
async def cb_schedule_delete(
    callback: CallbackQuery,
    callback_data: ScheduleCB,
    session: AsyncSession,
    scheduler_service: SchedulerService | None = None,
) -> None:
    ok = await remove_slot(session, callback_data.slot_id)
    if not ok:
        await callback.answer("Слот не найден", show_alert=True)
        return
    await _flush_and_rebuild(session, scheduler_service)
    text, kb = await _schedule_text_and_kb(session)
    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer("Удалено")


@router.callback_query(ScheduleCB.filter(F.action == "add"))
async def cb_schedule_add(callback: CallbackQuery) -> None:
    await callback.message.edit_text(
        "Выберите время:", reply_markup=schedule_add_time_kb()
    )
    await callback.answer()


@router.callback_query(ScheduleCB.filter(F.action == "set_time"))
async def cb_schedule_set_time(
    callback: CallbackQuery, callback_data: ScheduleCB
) -> None:
    parts = callback_data.value.split(".")
    hour, minute = int(parts[0]), int(parts[1])
    await callback.message.edit_text(
        f"Время: {hour:02d}:{minute:02d}\nВыберите день:",
        reply_markup=schedule_add_day_kb(hour, minute),
    )
    await callback.answer()


@router.callback_query(ScheduleCB.filter(F.action == "confirm"))
async def cb_schedule_confirm(
    callback: CallbackQuery,
    callback_data: ScheduleCB,
    session: AsyncSession,
    scheduler_service: SchedulerService | None = None,
) -> None:
    parts = callback_data.value.split(".")
    hour, minute = int(parts[0]), int(parts[1])
    day_str = parts[2]
    day_of_week = None if day_str == "all" else int(day_str)
    await add_slot(session, hour, minute, day_of_week)
    await _flush_and_rebuild(session, scheduler_service)

    text, kb = await _schedule_text_and_kb(session)
    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer("Слот добавлен!")


@router.callback_query(ScheduleCB.filter(F.action == "interval"))
async def cb_schedule_interval(
    callback: CallbackQuery,
    callback_data: ScheduleCB,
    session: AsyncSession,
    scheduler_service: SchedulerService | None = None,
) -> None:
    await set_setting(session, "schedule_interval_minutes", callback_data.value)
    await _flush_and_rebuild(session, scheduler_service)
    text, kb = await _schedule_text_and_kb(session)
    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer(f"Интервал: {callback_data.value} мин")
