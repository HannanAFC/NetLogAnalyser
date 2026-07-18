from __future__ import annotations

from config import settings
from fastapi import APIRouter, Header, HTTPException
from testing.token_capture import get_token

router = APIRouter( prefix="/test-only", tags=[ "test-only" ] )


@router.get( "/last-token" )
async def last_token(
    email: str,
    token_type: str,
    x_test_endpoint_key: str = Header( default="" ),
):
    if not settings.enable_test_endpoints:
        raise HTTPException( status_code=404 )

    if not settings.test_endpoint_key or x_test_endpoint_key != settings.test_endpoint_key:
        raise HTTPException( status_code=404 )

    if not email.endswith( settings.test_email_domain ):
        raise HTTPException( status_code=404 )

    if token_type not in ( "verification", "reset" ):
        raise HTTPException( status_code=400, detail="token_type must be 'verification' or 'reset'" )

    raw_token = get_token( email=email, token_type=token_type )
    if raw_token is None:
        raise HTTPException( status_code=404, detail="No token recorded for this email/type" )

    return { "token": raw_token }
