from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parent.parent.parent


class ServerGRPC(BaseSettings):
    ip: str
    port: int


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ROOT_DIR / ".env",
        env_prefix="",
        extra="forbid",
        env_nested_delimiter="__",
    )

    server: ServerGRPC = Field(default_factory=ServerGRPC)
    time_interval: float
    port: int


settings = Settings()
