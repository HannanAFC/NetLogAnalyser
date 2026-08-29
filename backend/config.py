import re
from typing import Literal

from pydantic import Field, SecretStr, computed_field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from starlette.middleware.base import BaseHTTPMiddleware


class Settings( BaseSettings ):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8"
    )

    # Metadata
    app_name:                            str = "NetLogAnalyser"
    app_version:                         str = "0.0.0"
    environment:                         str = "development"
    frontend_url:                        str = "http://localhost:3000"
    backend_url:                         str = "http://localhost:8000"

    frontend_port:                       int = 3000
    backend_port:                        int = 8000

    # Database
    database_url:                        str
    geoip_db_path:                       str = "shared/geoip/GeoLite2-Country.mmdb"

    # Auth
    secret_key:                          SecretStr
    algorithm:                           str = "HS256"
    jwt_access_token_expire_minutes:     int = 30
    jwt_refresh_token_expire_days:       int = 30
    password_reset_token_expire_minutes: int = 5

    cors_allowed_origins:                list[ str ] = [ "http://localhost:3000" ]

    @computed_field
    @property
    def cors_allowed_origin_regex( self ) -> str | None:
        if self.cors_allowed_origins:
            return None
        return rf"^https?://[^/]+:{self.frontend_port}$"

    # API keys
    api_key_prefix_length:               int = 8
    api_key_max_per_user:                int = 10

    # Ingestion
    ingest_max_batch_size:               int = 500

    # Websocket
    ws_heartbeat_interval:               int = 30
    ws_max_connections_per_user:         int = 5
    ws_ticket_ttl_seconds:               int = 30
    ws_stale_connection_seconds:         int = 90

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
    email_verification_enabled:              bool = False
    resend_api_key:                          str = ""
    resend_onboarding_email:                 str = "NetLogAnalyser <onboarding@netloganalyser.com>"
    resend_verify_email:                     str = "NetLogAnalyser <verify@netloganalyser.com>"
    resend_recovery_email:                   str = "NetLogAnalyser <recovery@netloganalyser.com>"
    resend_general_email:                    str = "NetLogAnalyser <robot@netloganalyser.com>"
    support_email:                           str = "support@netloganalyser.com"
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

    # Analytics endpoint
    analytics_max_range_days:            int = 30
    analytics_summary_expire_seconds:    int = 30
    analytics_timeseries_expire_seconds: int = 30

    # Data retention
    retention_enabled:                    bool = True
    retention_days:                       int = 30
    retention_grace_period_days:          int = 7
    retention_export_email_enabled:       bool = True
    retention_delete_chunk_size:          int = 5000
    retention_job_lock_ttl_seconds:       int = 30

    # Export storage
    export_storage_backend:                Literal[ "local", "s3" ] = "local"
    export_local_path:                     str = "data/exports"
    export_s3_bucket:                      str | None = None
    export_s3_endpoint_url:                str | None = None
    export_s3_region:                      str | None = None
    export_s3_access_key_id:               SecretStr | None = None
    export_s3_secret_access_key:           SecretStr | None = None
    export_link_ttl_hours:                 int = 72
    export_max_per_user_per_day:           int = 3
    export_authenticated_link_ttl_seconds: int = 300

    @model_validator( mode="after" )
    def _check_email_verification_config( self ) -> "Settings":
        if self.email_verification_enabled == True and self.resend_api_key == "":
            raise ValueError(
                "EMAIL_VERIFICATION_ENABLED=true requires RESEND_API_KEY to be "
                "set - otherwise verification emails can never be sent and new "
                "users would be locked out permanently. Set RESEND_API_KEY, or "
                "set EMAIL_VERIFICATION_ENABLED=false to skip verification."
            )
        return self

    @model_validator( mode="after" )
    def _check_export_s3_config( self ) -> "Settings":
        if self.export_storage_backend == "s3":
            missing = [
                name for name, val in [
                    ( "EXPORT_S3_BUCKET",           self.export_s3_bucket ),
                    ( "EXPORT_S3_ACCESS_KEY_ID",     self.export_s3_access_key_id ),
                    ( "EXPORT_S3_SECRET_ACCESS_KEY", self.export_s3_secret_access_key ),
                ]
                if not val
            ]
            if missing:
                raise ValueError(
                    f"EXPORT_STORAGE_BACKEND=s3 requires: { ', '.join( missing ) }"
                )
        return self

settings = Settings( ) # type: ignore[call-arg] # loaded from .env file


def resolve_frontend_url( origin: str | None ) -> str:
    if origin:
        if settings.cors_allowed_origins and ( origin in settings.cors_allowed_origins or "*" in settings.cors_allowed_origins ):
            return origin
        if settings.cors_allowed_origin_regex and re.match( settings.cors_allowed_origin_regex, origin ):
            return origin
    return settings.frontend_url

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

        if path.startswith( ("/docs", "/redoc") ):
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