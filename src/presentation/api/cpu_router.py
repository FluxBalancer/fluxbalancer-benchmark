import asyncio
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


@cpu_router.get("")
async def cpu_burn(
        request: Request,
        response: Response,
        seconds: int = 10,
        complexity: int = 10_000
):
    if seconds <= 0:
        raise HTTPException(status_code=400, detail="seconds must be > 0")

    end_time = time.perf_counter() + seconds

    while time.perf_counter() < end_time:
        for chunk_start in range(0, complexity, 2000):
            if await request.is_disconnected():
                return {"cancelled": True, "port": settings.port}

            chunk_end = min(chunk_start + 2000, complexity)

            await asyncio.to_thread(cpu_chunk, chunk_start, chunk_end)

    net_io = psutil.net_io_counters()
    response.headers["X-Backend-Node"] = NODE_ID
    return {
        "cpu_burn": True,
        "seconds": seconds,
        "complexity": complexity,
        "port": settings.port,
        "cpu_util": psutil.cpu_percent(interval=None),
        "mem_util": psutil.virtual_memory().percent,
        "net_in_bytes": net_io.bytes_recv,
        "net_out_bytes": net_io.bytes_sent,
    }
