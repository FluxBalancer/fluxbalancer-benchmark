import asyncio
import mmap
import random
import time

import psutil
from fastapi import APIRouter, HTTPException
from starlette.requests import Request
from starlette.responses import Response

from src.config.settings import settings
from src.shared.node_id import get_node_id

mem_router = APIRouter(prefix="/mem", tags=["mem"])
NODE_ID = get_node_id()


def allocate_memory_mmap(mb: int):
    size = mb * 1024 * 1024
    page = 4096

    m = mmap.mmap(-1, size)

    for i in range(0, size, page):
        m[i] = 1

    return [m]


async def mem_workload(request, end_time, maps):
    try:
        while time.perf_counter() < end_time:
            if await request.is_disconnected():
                return

            await asyncio.sleep(0.1)
    finally:
        for m in maps:
            m.close()


@mem_router.get("")
async def mem_burn(
        request: Request,
        response: Response,
        mb: int = 100,
        seconds: int = 10,

        fail_rate: float = 0.05,
        slow_rate: float = 0.1,
        slow_multiplier: float = 3.0,
        jitter_mean: float = 0.3,

        extra_delay_prob: float = 0.1,
        extra_delay_min: float = 1.0,
        extra_delay_max: float = 3.0,
):
    if mb <= 0 or seconds <= 0:
        raise HTTPException(status_code=400, detail="invalid params")

    if random.random() < fail_rate:
        await asyncio.sleep(random.uniform(0.05, 0.2))
        raise HTTPException(status_code=500, detail="controlled failure")

    t0 = time.perf_counter()
    maps = await asyncio.to_thread(allocate_memory_mmap, mb)

    jitter = random.expovariate(1 / jitter_mean) if jitter_mean > 0 else 0
    slowdown = slow_multiplier if random.random() < slow_rate else 1.0

    end = time.perf_counter() + (seconds * slowdown) + jitter

    try:
        while time.perf_counter() < end:
            if await request.is_disconnected():
                for m in maps:
                    m.close()
                return {"cancelled": True, "port": settings.port}

            await asyncio.sleep(0.1)
    finally:
        for m in maps:
            m.close()

    if random.random() < extra_delay_prob:
        await asyncio.sleep(random.uniform(extra_delay_min, extra_delay_max))

    net_io = psutil.net_io_counters()
    response.headers["X-Backend-Node"] = NODE_ID

    service_time_ms = (time.perf_counter() - t0) * 1000
    return {
        "mem_burn": True,
        "mb": mb,
        "seconds": service_time_ms,
        "port": settings.port,
        "cpu_util": psutil.cpu_percent(interval=None),
        "mem_util": psutil.virtual_memory().percent,
        "net_in_bytes": net_io.bytes_recv,
        "net_out_bytes": net_io.bytes_sent,
    }
