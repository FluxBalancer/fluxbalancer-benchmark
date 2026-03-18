import os
import socket

from src.config.settings import settings


def get_node_id() -> str:
    port = settings.port
    hostname = socket.gethostname()
    node_id = os.getenv("NODE_ID", f"{hostname}_{port}")
    return node_id