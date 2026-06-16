import time
from contextlib import asynccontextmanager

from config import settings
from database import engine
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates


@asynccontextmanager
async def lifespan( _app: FastAPI ):
    # application runtime
    yield

    # shutdown
    await engine.dispose( )


startTime = time.time( )

app = FastAPI( lifespan=lifespan )

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
def health_check( ):
    return {
        "database": "ok",
        "version": settings.app_version,
        "uptime_seconds": time.time( ) - startTime,
        "environment": settings.environment
    }