import logging
from datetime import datetime, timezone

from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
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
        self.scheduler = AsyncIOScheduler(timezone=settings.timezone)

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

            now = datetime.now(timezone.utc)
            next_fire = await compute_next_fire_time(session)

            if next_fire and next_fire.astimezone(timezone.utc) < now:
                post = await publish_next(self.bot, session)
                if post:
                    await session.commit()
                    log.info("Recovery: published missed post #%d", post.id)

    async def start(self) -> None:
        await self._recover_missed()
        await self._rebuild_triggers()
        self.scheduler.start()
        log.info("Scheduler started")

    async def stop(self) -> None:
        self.scheduler.shutdown(wait=False)
        log.info("Scheduler stopped")

    async def rebuild(self) -> None:
        await self._rebuild_triggers()

    async def _rebuild_triggers(self) -> None:
        # Remove all existing jobs
        self.scheduler.remove_all_jobs()

        async with async_session() as session:
            mode = await get_setting(session, "schedule_mode")

            if mode == "interval":
                interval_str = await get_setting(session, "schedule_interval_minutes")
                minutes = int(interval_str) if interval_str else 60
                self.scheduler.add_job(
                    self._publish_tick,
                    IntervalTrigger(minutes=minutes),
                    id=SCHEDULE_JOB_ID,
                    replace_existing=True,
                )
                log.info("Scheduler: interval mode, every %d min", minutes)
            else:
                from bot.db.models import ScheduleSlot
                from sqlalchemy import select

                result = await session.execute(
                    select(ScheduleSlot).where(ScheduleSlot.is_active.is_(True))
                )
                slots = list(result.scalars().all())

                if not slots:
                    log.info("Scheduler: no active slots")
                    return

                for slot in slots:
                    cron_kwargs: dict = {
                        "hour": slot.time.hour,
                        "minute": slot.time.minute,
                        "timezone": settings.timezone,
                    }
                    if slot.day_of_week is not None:
                        cron_kwargs["day_of_week"] = str(slot.day_of_week)

                    slot_id = f"{SCHEDULE_JOB_ID}_{slot.id}"
                    self.scheduler.add_job(
                        self._publish_tick,
                        CronTrigger(**cron_kwargs),
                        id=slot_id,
                        replace_existing=True,
                    )
                log.info("Scheduler: slots mode, %d active slot(s)", len(slots))
