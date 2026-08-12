import asyncio
from collections import defaultdict
from typing import Any, AsyncGenerator, Dict, List

from app.config import settings

# Global event bus instance
class EventBus:
    """
    Very small in-process pub/sub. Each call to `subscribe()` returns an async generator
    that yields events. Events are `dict` objects (the normalized payload).
    """

    def __init__(self):
        self._queues: Dict[int, asyncio.Queue] = {}
        _id_counter = 0

    async def subscribe(self, maxsize: int = 1000) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Returns an async generator that yields events until the caller stops iterating
        or `unsubscribe` is called with the same queue.
        """
        queue: asyncio.Queue = asyncio.Queue(maxsize=maxsize)
        qid = id(queue)
        self._queues[qid] = queue
        try:
            while True:
                event = await queue.get()
                yield event
        finally:
            self._queues.pop(qid, None)

    def publish(self, event: Dict[str, Any]) -> None:
        """Fan‑out to all current subscribers (non‑blocking, drops if queue full)."""
        for queue in list(self._queues.values()):
            try:
                queue.put_nowait(event)
            except asyncio.QueueFull:
                # In a hackathon setting we prefer not to block the publisher.
                # Log and drop for this subscriber.
                pass


# Singleton instance used by the whole app
event_bus = EventBus()