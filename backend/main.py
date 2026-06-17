import time
from contextlib import asynccontextmanager
from typing import Annotated

from config import SecurityHeadersMiddleware, settings
from database import engine, get_db
from fastapi import Depends, FastAPI, Request, status
from fastapi.exceptions import HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


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

templates = Jinja2Templates( directory="templates" )

@app.get( "/", include_in_schema=False, name="Index" )
def root( request: Request ):
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "frontend_url": settings.frontend_url
        }
    )

@app.get( "/health" )
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