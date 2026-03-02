import asyncio
import logging
from datetime import datetime, timezone

from aiogram import Bot
from apscheduler import AsyncScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from bot.config import settings
from bot.db.engine import async_session
from bot.services.publisher import publish_next
from bot.services.settings_service import get_setting, is_paused

log = logging.getLogger(__name__)

SCHEDULE_JOB_ID = "publish_job"


class SchedulerService:
    def __init__(self, bot: Bot) -> None:
        self.bot = bot
        self.scheduler = AsyncScheduler()
        self._task: asyncio.Task | None = None

    async def _publish_tick(self) -> None:
        async with async_session() as session:
            if await is_paused(session):
                log.debug("Scheduler tick skipped — paused")
                return
            post = await publish_next(self.bot, session)
            if post:
                await session.commit()
                log.info("Scheduled publish: post #%d", post.id)
            else:
                log.debug("No posts to publish")

    async def _recover_missed(self) -> None:
        """Publish at most 1 missed post after restart."""
        async with async_session() as session:
            if await is_paused(session):
                return
            last_str = await get_setting(session, "last_publish_time")
            if not last_str:
                return

            from bot.services.schedule_service import compute_next_fire_time

            last_ts = int(last_str)
            last_dt = datetime.fromtimestamp(last_ts, tz=timezone.utc)
            now = datetime.now(timezone.utc)
            next_fire = await compute_next_fire_time(session)

            # Only recover if the next scheduled fire time is in the past
            # AND some time has actually passed since the last publish
            if next_fire and next_fire.astimezone(timezone.utc) < now and last_dt < now:
                post = await publish_next(self.bot, session)
                if post:
                    await session.commit()
                    log.info("Recovery: published missed post #%d", post.id)

    async def start(self) -> None:
        await self.scheduler.__aenter__()
        await self._recover_missed()
        await self._rebuild_triggers()
        self._task = asyncio.create_task(self.scheduler.run_until_stopped())
        log.info("Scheduler started")

    async def stop(self) -> None:
        try:
            await self.scheduler.stop()
        except TypeError:
            # Some APScheduler 4.x versions have sync stop()
            self.scheduler.stop()
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except (asyncio.CancelledError, Exception):
                pass
        try:
            await self.scheduler.__aexit__(None, None, None)
        except Exception:
            pass
        log.info("Scheduler stopped")

    async def rebuild(self) -> None:
        await self._rebuild_triggers()

    async def _rebuild_triggers(self) -> None:
        # Remove old interval trigger
        try:
            await self.scheduler.remove_schedule(SCHEDULE_JOB_ID)
        except Exception:
            pass

        # Remove old slot triggers
        from bot.db.models import ScheduleSlot
        from sqlalchemy import select

        async with async_session() as session:
            # Clean up any existing slot schedules
            result = await session.execute(select(ScheduleSlot))
            all_slots = list(result.scalars().all())
            for slot in all_slots:
                slot_id = f"{SCHEDULE_JOB_ID}_{slot.id}"
                try:
                    await self.scheduler.remove_schedule(slot_id)
                except Exception:
                    pass

            mode = await get_setting(session, "schedule_mode")

            if mode == "interval":
                interval_str = await get_setting(session, "schedule_interval_minutes")
                minutes = int(interval_str) if interval_str else 60
                await self.scheduler.add_schedule(
                    self._publish_tick,
                    IntervalTrigger(minutes=minutes),
                    id=SCHEDULE_JOB_ID,
                )
                log.info("Scheduler: interval mode, every %d min", minutes)
            else:
                active = [s for s in all_slots if s.is_active]

                if not active:
                    log.info("Scheduler: no active slots")
                    return

                for slot in active:
                    cron_kwargs = {
                        "hour": slot.time.hour,
                        "minute": slot.time.minute,
                    }
                    if slot.day_of_week is not None:
                        cron_kwargs["day_of_week"] = str(slot.day_of_week)

                    slot_id = f"{SCHEDULE_JOB_ID}_{slot.id}"
                    await self.scheduler.add_schedule(
                        self._publish_tick,
                        CronTrigger(**cron_kwargs, timezone=settings.timezone),
                        id=slot_id,
                    )
                log.info("Scheduler: slots mode, %d active slot(s)", len(active))
