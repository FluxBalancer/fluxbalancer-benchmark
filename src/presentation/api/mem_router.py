import asyncio
import time

from fastapi import APIRouter, HTTPException
from starlette.requests import Request

from src.config.settings import settings

mem_router = APIRouter(prefix="/mem", tags=["mem"])


def allocate_memory(mb: int):
    chunk_size = 1024 * 1024
    data = [bytearray(chunk_size) for _ in range(mb)]
    for block in data:
        block[0] = 1
    return data


@mem_router.get("")
async def mem_burn(request: Request, mb: int = 100, seconds: int = 10):
    if mb <= 0 or seconds <= 0:
        raise HTTPException(status_code=400, detail="invalid params")

    data = await asyncio.to_thread(allocate_memory, mb)

    end = time.perf_counter() + seconds

    while time.perf_counter() < end:
        if await request.is_disconnected():
            data.clear()
            return {"cancelled": True, "port": settings.port}

        await asyncio.sleep(0.1)

    data.clear()

    return {
        "mem_burn": True,
        "mb": mb,
        "seconds": seconds,
        "port": settings.port,
    }
