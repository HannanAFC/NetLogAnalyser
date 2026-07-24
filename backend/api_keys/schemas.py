from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class APIKeyCreateRequest( BaseModel ):
    model_config = ConfigDict( str_strip_whitespace=True )
    
    label: str = Field( min_length=1, max_length=100 )


class APIKeyCreateResponse( BaseModel ):
    model_config = ConfigDict( from_attributes=True )
    
    id:         UUID
    label:      str
    key_prefix: str
    api_key:    str
    created_at: datetime


class APIKeyPublic( BaseModel ):
    model_config = ConfigDict( from_attributes=True )

    id:           UUID
    label:        str
    key_prefix:   str
    created_at:   datetime
    last_used_at: datetime | None
    revoked_at:   datetime | None