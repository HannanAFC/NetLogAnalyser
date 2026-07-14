import time
from contextlib import asynccontextmanager
from math import floor
from typing import Annotated

from auth import router as auth_router
from config import SecurityHeadersMiddleware, settings
from database import engine, get_db
from fastapi import Depends, FastAPI, Request, status
from fastapi.exceptions import HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from schemas import HealthResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from users import router as users_router


@asynccontextmanager
async def lifespan( _app: FastAPI ):
    # application runtime
    yield

    # shutdown
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

app.include_router( auth_router.router, prefix="/auth", tags=[ "auth" ] )
app.include_router( users_router.router, prefix="/users", tags=[ "users" ] )

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