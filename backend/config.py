from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from starlette.middleware.base import BaseHTTPMiddleware


class Settings( BaseSettings ):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8"
    )

    # Metadata
    app_name:                            str = "NetLogAnalyser"
    app_version:                         str = "0.1.0"
    debug:                               bool = False
    environment:                         str = "development"
    frontend_url:                        str = "http://localhost:3000"
    backend_url:                         str = "http://localhost:8000"

    # Database
    database_url:                        str
    geoip_db_path:                       str = "geoip/GeoLite2-Country.mmdb"

    # Auth
    secret_key:                          SecretStr
    algorithm:                           str = "HS256"
    jwt_access_token_expire_minutes:     int = 30
    jwt_refresh_token_expire_days:       int = 30
    password_reset_token_expire_minutes: int = 5

    # CORS
    cors_allowed_origins:                list[ str ] = [ "http://localhost:3000" ]

    # API keys
    api_key_prefix_length:               int = 8
    api_key_max_per_user:                int = 10

    # Ingestion
    ingest_max_batch_size:               int = 500

    # Websocket
    ws_heartbeat_interval:               int = 30
    ws_max_connections_per_user:         int = 5

    # Cookies
    cookie_secure:                       bool = True
    cookie_samesite:                     Literal[ "lax", "strict", "none" ] = "lax"

    # Redis
    redis_url:                           SecretStr

    # Rate limits
    ratelimit_auth_times:                int = 10
    ratelimit_auth_seconds:              int = 60
    ratelimit_forgot_password_times:     int = 3
    ratelimit_forgot_password_seconds:   int = 60
    ratelimit_ingest_times:              int = 1000
    ratelimit_ingest_seconds:            int = 60
    ratelimit_ws_times:                  int = 50
    ratelimit_ws_seconds:                int = 60
    ratelimit_general_times:             int = 100
    ratelimit_general_seconds:           int = 60

    # Email service
    resend_api_key:                          str = ""
    resend_onboarding_email:                 str = "NetLogAnalyser <onboarding@netloganalyser.com>"
    resend_verify_email:                     str = "NetLogAnalyser <verify@netloganalyser.com>"
    resend_recovery_email:                   str = "NetLogAnalyser <recovery@netloganalyser.com>"
    email_verification_token_expire_minutes: int = 60

    # Test config
    enable_test_endpoints:               bool = False
    test_endpoint_key:                   str = ""
    test_email_domain:                   str = "@example.com"

    # Anomaly detection
    anomaly_packet_size_mtu:             int = 1500
    anomaly_packet_size_jumbo_max:       int = 9000
    anomaly_packet_size_tiny_max:        int = 40
    anomaly_port_scan_low:               int = 5
    anomaly_port_scan_high:              int = 25
    anomaly_host_sweep_low:              int = 5
    anomaly_host_sweep_high:             int = 20
    anomaly_weight_packet_size:          float = Field( ge=0.0, le=1.0, default=0.5 )
    anomaly_weight_tcp_flags:            float = Field( ge=0.0, le=1.0, default=0.9 )
    anomaly_weight_mismatch_ports:       float = Field( ge=0.0, le=1.0, default=0.6 )
    anomaly_weight_port_scan_shape:      float = Field( ge=0.0, le=1.0, default=0.7 )
    anomaly_weight_host_sweep_shape:     float = Field( ge=0.0, le=1.0, default=0.6 )

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