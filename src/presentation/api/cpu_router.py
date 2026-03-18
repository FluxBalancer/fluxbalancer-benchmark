import asyncio
import random
import time

import psutil
from fastapi import APIRouter, HTTPException
from starlette.requests import Request
from starlette.responses import Response

from src.config.settings import settings
from src.shared.node_id import get_node_id

cpu_router = APIRouter(prefix="/cpu", tags=["cpu"])
NODE_ID = get_node_id()


def cpu_chunk(start: int, end: int) -> None:
    _ = sum(i * i for i in range(start, end))
    return


async def cpu_workload(request, end_time, complexity=10_000):
    while time.perf_counter() < end_time:
        for chunk_start in range(0, complexity, 2000):
            if await request.is_disconnected():
                return

            chunk_end = min(chunk_start + 2000, complexity)
            await asyncio.to_thread(cpu_chunk, chunk_start, chunk_end)


@cpu_router.get("")
async def cpu_burn(
        request: Request,
        response: Response,
        seconds: float = 10,
        complexity: int = 10_000,

        fail_rate: float = 0.05,
        slow_rate: float = 0.1,
        slow_multiplier: float = 3.0,
        jitter_mean: float = 0.5,

        extra_delay_prob: float = 0.1,
        extra_delay_min: float = 1.0,
        extra_delay_max: float = 3.0,
):
    if seconds <= 0:
        raise HTTPException(status_code=400, detail="seconds must be > 0")

    if random.random() < fail_rate:
        await asyncio.sleep(random.uniform(0.05, 0.2))
        raise HTTPException(status_code=500, detail="controlled failure")

    t0 = time.perf_counter()
    jitter = random.expovariate(1 / jitter_mean) if jitter_mean > 0 else 0
    slowdown = slow_multiplier if random.random() < slow_rate else 1.0

    end_time = time.perf_counter() + (seconds * slowdown) + jitter

    while time.perf_counter() < end_time:
        for chunk_start in range(0, complexity, 2000):
            if await request.is_disconnected():
                return {"cancelled": True, "port": settings.port}

            chunk_end = min(chunk_start + 2000, complexity)
            await asyncio.to_thread(cpu_chunk, chunk_start, chunk_end)

    if random.random() < extra_delay_prob:
        await asyncio.sleep(random.uniform(extra_delay_min, extra_delay_max))

    net_io = psutil.net_io_counters()
    response.headers["X-Backend-Node"] = NODE_ID

    service_time_ms = (time.perf_counter() - t0) * 1000
    return {
        "cpu_burn": True,
        "seconds": service_time_ms,
        "complexity": complexity,
        "port": settings.port,
        "cpu_util": psutil.cpu_percent(interval=None),
        "mem_util": psutil.virtual_memory().percent,
        "net_in_bytes": net_io.bytes_recv,
        "net_out_bytes": net_io.bytes_sent,
    }
