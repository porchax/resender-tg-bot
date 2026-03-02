import asyncio
from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject

ALBUM_COLLECT_DELAY = 0.6


class AlbumMiddleware(BaseMiddleware):
    def __init__(self) -> None:
        super().__init__()
        self._albums: dict[str, list[Message]] = {}
        self._locks: dict[str, asyncio.Event] = {}

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        if not isinstance(event, Message):
            return await handler(event, data)

        if not event.media_group_id:
            return await handler(event, data)

        group_id = event.media_group_id

        if group_id not in self._albums:
            self._albums[group_id] = []
            self._locks[group_id] = asyncio.Event()
            self._albums[group_id].append(event)

            await asyncio.sleep(ALBUM_COLLECT_DELAY)

            self._locks[group_id].set()

            data["album"] = list(self._albums[group_id])
            del self._albums[group_id]
            del self._locks[group_id]

            return await handler(event, data)
        else:
            self._albums[group_id].append(event)
            await self._locks[group_id].wait()
            return None
