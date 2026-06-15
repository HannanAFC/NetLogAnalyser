from functools import lru_cache

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings( BaseSettings ):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8"
    )

    # Metadata
    app_name:                      str = "NetLogAnalyser"
    app_version:                   str = "0.1.0"
    debug:                         bool = False
    environment:                          str = "development"
    frontend_url:                  str = "localhost:3000"

    # Database
    database_url:                  str

    # Auth
    secret_key:                    SecretStr
    algorithm:                     str = "HS256"
    access_token_expire_minutes:   int = 30
    jwt_refresh_token_expire_days: int = 30
    reset_token_expire_minutes:    int = 5

    # CORS
    cors_allowed_origins:          list[ str ] = [ "http://localhost:3000" ]

    # API Keys
    api_key_prefix_length:         int = 8
    api_key_max_per_user:          int = 10

    # Ingestion
    ingest_max_batch_size:         int = 500
    ingest_rate_limit:             str = "1000/minute"

    # Websocket
    ws_heartbeat_interval:         int = 30
    ws_max_connections_per_user:   int = 5

    # Cookies
    cookie_secure:                 bool = True
    cookie_samesite:               str = "lax"

@lru_cache
def get_settings() -> Settings:
    return Settings() # type: ignore[call-arg] # loaded from .env file