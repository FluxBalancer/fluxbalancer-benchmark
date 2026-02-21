import asyncio
import gc
import time

from fastapi import APIRouter, HTTPException
from starlette.requests import Request

from src.config.settings import settings

mem_router = APIRouter(prefix="/mem", tags=["mem"])


@mem_router.get("")
async def mem_burn(request: Request, mb: int = 100, seconds: int = 10):
    """
    Выделяет mb мегабайт памяти и держит их seconds секунд.

    mb       — объём памяти, МБ
    seconds  — время удержания данных в памяти
    """
    if mb <= 0 or seconds <= 0:
        raise HTTPException(status_code=400, detail="mb and seconds must be > 0")

    chunk = 1024 * 1024
    data = [bytearray(chunk) for _ in range(mb)]
    end = time.time() + seconds

    while time.time() < end:
        if await request.is_disconnected():
            del data
            gc.collect()
            return {"cancelled": True, "port": settings.port}

        await asyncio.sleep(0.1)

    del data
    gc.collect()

    return {"mem_burn": f"allocated {mb} MB for {seconds}s", "port": settings.port}
