import gc
import os
import time

import dotenv
from fastapi import FastAPI, HTTPException

app = FastAPI()

dotenv.load_dotenv()


@app.get("/")
def read_root():
    return {"Hello": f"World_{os.getenv('PORT')}"}


@app.get("/cpu")
def cpu_burn(seconds: int = 10, complexity: int = 10_000):
    """
    Нагружает процессор «пустыми» вычислениями.

    seconds     — сколько секунд крутить цикл
    complexity  — сколько итераций в каждой сумме (чем больше, тем сильнее нагрузка)
    """
    if seconds <= 0:
        raise HTTPException(status_code=400, detail="seconds must be > 0")

    end = time.time() + seconds
    while time.time() < end:
        _ = sum(i * i for i in range(complexity))
        del _

    return {"cpu_burn": f"completed {seconds}s × complexity={complexity}", "port": os.getenv("PORT")}


@app.get("/mem")
def mem_burn(mb: int = 100, seconds: int = 10):
    """
    Выделяет mb мегабайт памяти и держит их seconds секунд.

    mb       — объём памяти, МБ
    seconds  — время удержания данных в памяти
    """
    if mb <= 0 or seconds <= 0:
        raise HTTPException(status_code=400, detail="mb and seconds must be > 0")

    chunk = 1024 * 1024
    data = [bytearray(chunk) for _ in range(mb)]

    time.sleep(seconds)
    del data
    gc.collect()

    return {"mem_burn": f"allocated {mb} MB for {seconds}s", "port": os.getenv("PORT")}
