import asyncio
import time

from fastapi import APIRouter, HTTPException
from starlette.requests import Request

from src.config.settings import settings

cpu_router = APIRouter(prefix="/cpu", tags=["cpu"])


@cpu_router.get("")
async def cpu_burn(request: Request, seconds: int = 10, complexity: int = 10_000):
    """
    Нагружает процессор «пустыми» вычислениями.

    seconds     — сколько секунд крутить цикл
    complexity  — сколько итераций в каждой сумме (чем больше, тем сильнее нагрузка)
    """
    if seconds <= 0:
        raise HTTPException(status_code=400, detail="seconds must be > 0")

    end = time.time() + seconds
    while time.time() < end:
        if await request.is_disconnected():
            return {"cancelled": True, "port": settings.port}

        _ = sum(i * i for i in range(complexity))
        del _
        await asyncio.sleep(0)

    return {
        "cpu_burn": f"completed {seconds}s × complexity={complexity}",
        "port": settings.port,
    }
