"""Queue consumer main entrypoint (P0-P1). Consumes jobs from Redis queue."""
from __future__ import annotations

import asyncio
import logging

log = logging.getLogger("photoai.worker")


async def main() -> None:
    log.info("worker starting (mock mode)")
    # P0: real Redis consumer implemented in P1/S13.
    await asyncio.sleep(0)


if __name__ == "__main__":
    asyncio.run(main())
