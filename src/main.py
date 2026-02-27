import asyncio
import os
import socket
from contextlib import asynccontextmanager

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI

from src.adapters.outbound.grpc.push_metrics import MetricsPusher
from src.config.settings import settings
from src.presentation.api.cpu_router import cpu_router
from src.presentation.api.mem_router import mem_router
from src.shared.config_logging import configure_logging

load_dotenv()

SERVER_IP: str = settings.server.ip
SERVER_PORT: int = settings.server.port
TIME_INTERVAL = settings.time_interval

HOST_PORT: int = settings.port


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()

    grpc_target = f"{SERVER_IP}:{SERVER_PORT}"
    port = HOST_PORT
    hostname = socket.gethostname()
    ip = socket.gethostbyname(hostname)
    node_id = os.getenv("NODE_ID", f"{ip}_{port}")

    pusher = MetricsPusher(
        node_id=node_id,
        port=port,
        grpc_target=grpc_target,
    )
    app.state.metrics_pusher = pusher
    app.state.metrics_task = asyncio.create_task(pusher.start(interval_s=TIME_INTERVAL))

    yield

    task = getattr(app.state, "metrics_task", None)
    pusher = getattr(app.state, "metrics_pusher", None)

    if task:
        task.cancel()
        await asyncio.gather(task, return_exceptions=True)

    if pusher:
        await pusher.stop()


app = FastAPI(lifespan=lifespan)
app.include_router(cpu_router)
app.include_router(mem_router)


@app.get("/")
def read_root():
    return {"Hello": f"World_{os.getenv('PORT')}"}


if __name__ == "__main__":
    uvicorn.run(app, port=15000, loop="asyncio")
