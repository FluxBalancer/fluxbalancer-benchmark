import asyncio
import gc
import os
import time
from contextlib import asynccontextmanager

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from starlette.requests import Request

from src.app.push_metrics import MetricsPusher

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    grpc_target = os.getenv("METRICS_GRPC_TARGET", "host.docker.internal:50051")
    port = int(os.getenv("PORT", "8001"))
    node_id = os.getenv("NODE_ID", f"server_{port}")

    pusher = MetricsPusher(
        node_id=node_id,
        host="127.0.0.1",
        port=port,
        grpc_target=grpc_target,
    )
    app.state.metrics_pusher = pusher
    app.state.metrics_task = asyncio.create_task(pusher.start(interval_s=0.25))

    yield

    task = getattr(app.state, "metrics_task", None)
    pusher = getattr(app.state, "metrics_pusher", None)

    if task:
        task.cancel()
        await asyncio.gather(task, return_exceptions=True)

    if pusher:
        await pusher.stop()


app = FastAPI()


@app.get("/")
def read_root():
    return {"Hello": f"World_{os.getenv('PORT')}"}


@app.get("/cpu")
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
            return {"cancelled": True, "port": os.getenv("PORT")}

        _ = sum(i * i for i in range(complexity))
        del _
        await asyncio.sleep(0)

    return {
        "cpu_burn": f"completed {seconds}s × complexity={complexity}",
        "port": os.getenv("PORT"),
    }


@app.get("/mem")
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
            return {"cancelled": True, "port": os.getenv("PORT")}

        await asyncio.sleep(0.1)

    del data
    gc.collect()

    return {"mem_burn": f"allocated {mb} MB for {seconds}s", "port": os.getenv("PORT")}


if __name__ == "__main__":
    uvicorn.run(app, port=15000, loop="asyncio")

