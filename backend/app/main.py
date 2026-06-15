import time

from config import Settings, get_settings
from fastapi import Depends, FastAPI, Request
from fastapi.templating import Jinja2Templates

startTime = time.time( )

app = FastAPI( )

templates = Jinja2Templates( directory="templates" )

@app.get( "/", include_in_schema=False, name="Index" )
def root( request: Request, settings: Settings = Depends( get_settings ) ):
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "frontend_url": settings.frontend_url
        }
    )

@app.get( "/health" )
def health_check( settings: Settings = Depends( get_settings ) ):
    return {
        "database": "ok",
        "version": settings.app_version,
        "uptime_seconds": time.time( ) - startTime,
        "environment": settings.environment
    }