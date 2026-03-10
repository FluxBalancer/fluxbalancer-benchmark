import asyncio
import mmap
import time

import psutil
from fastapi import APIRouter, HTTPException
from starlette.requests import Request

from src.config.settings import settings

mem_router = APIRouter(prefix="/mem", tags=["mem"])


def allocate_memory_mmap(mb: int):
    chunk_size = 1024 * 1024
    maps = []

    for _ in range(mb):
        m = mmap.mmap(-1, chunk_size)
        m[0] = 1
        maps.append(m)

    return maps


@mem_router.get("")
async def mem_burn(request: Request, mb: int = 100, seconds: int = 10):
    if mb <= 0 or seconds <= 0:
        raise HTTPException(status_code=400, detail="invalid params")

    maps = await asyncio.to_thread(allocate_memory_mmap, mb)

    end = time.perf_counter() + seconds

    while time.perf_counter() < end:
        if await request.is_disconnected():
            for m in maps:
                m.close()
            return {"cancelled": True, "port": settings.port}

        await asyncio.sleep(0.1)

    for m in maps:
        m.close()

    net_io = psutil.net_io_counters()
    return {
        "mem_burn": True,
        "mb": mb,
        "seconds": seconds,
        "port": settings.port,
        "cpu_util": psutil.cpu_percent(interval=None),
        "mem_util": psutil.virtual_memory().percent,
        "net_in_bytes": net_io.bytes_recv,
        "net_out_bytes": net_io.bytes_sent,
    }
