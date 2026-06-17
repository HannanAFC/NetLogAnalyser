from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from starlette.middleware.base import BaseHTTPMiddleware


class Settings( BaseSettings ):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8"
    )

    # Metadata
    app_name:                      str = "NetLogAnalyser"
    app_version:                   str = "0.1.0"
    debug:                         bool = False
    environment:                   str = "development"
    frontend_url:                  str = "http://localhost:3000"

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

settings = Settings( ) # type: ignore[call-arg] # loaded from .env file

JSON_API_CSP = (
    "default-src 'none'; "
    "frame-ancestors 'none'; "
    "base-uri 'none'; "
    "object-src 'none'"
)

LANDING_CSP = (
    "default-src 'self'; "
    "script-src 'self'; "
    "style-src 'self' https://fonts.googleapis.com; "
    "font-src 'self' https://fonts.gstatic.com; "
    "img-src 'self' data:; "
    "connect-src 'self'; "
    "frame-ancestors 'none'; "
    "base-uri 'self'; "
    "object-src 'none'"
)

DOCS_CSP = (
    "default-src 'self'; "
    "script-src 'self' https://cdn.jsdelivr.net 'unsafe-inline'; "
    "style-src 'self' https://cdn.jsdelivr.net https://fonts.googleapis.com 'unsafe-inline'; "
    "img-src 'self' data: https://cdn.jsdelivr.net https://fastapi.tiangolo.com https://cdn.redoc.ly; "
    "font-src 'self' https://fonts.gstatic.com; "
    "connect-src 'self'; "
    "frame-ancestors 'none'; "
    "base-uri 'self'; "
    "object-src 'none'"
)

class SecurityHeadersMiddleware( BaseHTTPMiddleware ):
    async def dispatch( self, request, call_next ):
        response = await call_next (request )
        path = request.url.path

        if path.startswith( "/docs" ) or path.startswith( "/redoc" ):
            csp = DOCS_CSP
        elif path == "/":
            csp = LANDING_CSP
        else:
            csp = JSON_API_CSP

        response.headers[ "Content-Security-Policy" ]   = csp
        response.headers[ "Strict-Transport-Security" ] = "max-age=63072000; includeSubDomains"
        response.headers[ "X-Content-Type-Options" ]    = "nosniff"
        response.headers[ "X-Frame-Options" ]           = "DENY"
        response.headers[ "Referrer-Policy" ]           = "no-referrer"
        response.headers[ "Permissions-Policy" ]        = "geolocation=(), camera=(), microphone=()"
        return response