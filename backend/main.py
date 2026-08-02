import time
from contextlib import asynccontextmanager
from math import floor
from typing import Annotated

import rate_limiter as _rl  # access to the module for rebinding globals
from api_keys import router as api_keys_router
from auth import router as auth_router
from cache import close_redis, init_redis, new_redis_client
from config import SecurityHeadersMiddleware, settings
from database import engine, get_db
from fastapi import Depends, FastAPI, Request, status
from fastapi.exceptions import HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from geoip import close_geoip, init_geoip
from ingest import router as ingest_router
from logs import router as logs_router
from rate_limiter import (
    create_rate_limiter,
)
from schemas import HealthResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from users import router as users_router
from websocket import router as websocket_router
from websocket.pubsub import start_pubsub_listener, stop_pubsub_listener


@asynccontextmanager
async def lifespan( _app: FastAPI ):
    # startup
    init_redis( )
    init_geoip( )
    start_pubsub_listener( new_redis_client )

    # Replace default rate limits with ones built from env variables
    _rl.auth_rate_limiter = await create_rate_limiter(
        settings.ratelimit_auth_times,
        settings.ratelimit_auth_seconds,
        "auth",
    )
    _rl.forgot_password_rate_limiter = await create_rate_limiter(
        settings.ratelimit_forgot_password_times,
        settings.ratelimit_forgot_password_seconds,
        "forgot-password",
    )
    _rl.ingest_rate_limiter = await create_rate_limiter(
        settings.ratelimit_ingest_times,
        settings.ratelimit_ingest_seconds,
        "ingest",
    )
    _rl.general_rate_limiter = await create_rate_limiter(
        settings.ratelimit_general_times,
        settings.ratelimit_general_seconds,
        "gener al",
    )

    yield

    # shutdown
    await stop_pubsub_listener( )
    await close_redis( )
    close_geoip( )
    await engine.dispose( )


startTime = time.time( )

app = FastAPI( lifespan=lifespan )

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins,
    allow_credentials=True,
    allow_methods=[ "GET", "POST", "PATCH", "DELETE", "OPTIONS" ],
    allow_headers=[ "*" ],
)

app.add_middleware( SecurityHeadersMiddleware )

app.mount( "/static", StaticFiles( directory="static" ), name="static" )

app.include_router( auth_router.router, prefix="/auth", tags=[ "Auth" ] )
app.include_router( users_router.router, prefix="/users", tags=[ "Users" ] )
app.include_router( api_keys_router.router, prefix="/api-keys", tags=[ "API keys" ] )
app.include_router( ingest_router.router, prefix="/ingest", tags=[ "Ingest" ] )
app.include_router( websocket_router.router, prefix="/ws", tags=[ "Websocket" ] )
app.include_router( logs_router.router, prefix="/logs", tags=[ "Logs" ] )
if settings.enable_test_endpoints:
    from testing.router import router as test_only_router
    app.include_router( test_only_router )

templates = Jinja2Templates( directory="templates" )

@app.get( "/", include_in_schema=False, name="Index", tags=[ "utilities" ] )
def root( request: Request ):
    uptime_seconds = "0s"
    uptime_exact   = time.time( ) - startTime
    if uptime_exact < 60:
        uptime_seconds = f"{ floor( uptime_exact ) }s"
    elif uptime_exact < 3600:
        uptime_seconds = f"{ floor( uptime_exact / 60 ) }m"
    else:
        uptime_seconds = f"{ floor( uptime_exact / 3600 ) }h { floor( ( uptime_exact % 3600 ) / 60 ) }m"

    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "frontend_url": settings.frontend_url,
            "backend_url": settings.backend_url,
            "environment": settings.environment,
            "version": settings.app_version,
            "uptime_seconds": uptime_seconds
        }
    )

@app.get( "/health", response_model=HealthResponse )
async def health_check( db: Annotated[ AsyncSession, Depends( get_db ) ] ):
    try:
        await db.execute( text( "SELECT 1") )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database unavailable"
        ) from exc
    return {
        "database": "ok",
        "version": settings.app_version,
        "uptime_seconds": time.time( ) - startTime,
        "environment": settings.environment
    }