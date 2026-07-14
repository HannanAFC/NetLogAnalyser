from pydantic import BaseModel


class HealthResponse( BaseModel ):
    database:       str
    version:        str
    uptime_seconds: float
    environment:    str