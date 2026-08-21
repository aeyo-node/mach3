from functools import lru_cache
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    # App
    app_name: str = "Swaram Market Engine"
    environment: str = "development"
    log_level: str = "INFO"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    timezone: str = "UTC"
    user_timezone: str = "Asia/Kolkata"

    # Databases
    database_url: str = "postgresql+asyncpg://swaram:swaram_secret@postgres:5432/swaram_db"
    redis_url: str = "redis://redis:6379/0"

    # Delta Exchange India Public Feeds
    delta_ws_url: str = "wss://public-socket.india.delta.exchange"
    delta_rest_url: str = "https://cdn.india.delta.exchange"
    delta_symbols: List[str] = ["BTCUSD", "ETHUSD"]
    delta_heartbeat_sec: int = 15
    delta_stale_threshold_sec: float = 10.0

    # Optional Providers (Future phases)
    bybit_ws_url: str = "wss://stream.bybit.com/v5/public/linear"
    deribit_ws_url: str = "wss://www.deribit.com/ws/api/v2"

    # Buffer & Batch sizes
    db_batch_size: int = 100
    db_flush_interval_sec: float = 1.0

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache()
def get_settings() -> Settings:
    return Settings()
