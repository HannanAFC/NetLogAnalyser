from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone

import jwt
from config import settings
from pwdlib import PasswordHash

password_hash = PasswordHash.recommended( )


def hash_password( plain_password: str ) -> str:
    """
    Hashed as plain text password into a hashed password.
    Parameters:
        plain_password (str): Plain text password.
    Return:
        password_hash (str): Hashed password.
    """
    return password_hash.hash( plain_password )

def verify_password( plain_password: str, hashed_password: str ) -> bool:
    """
    Compares the hash of a plain password to a hashed password.
    Parameters:
        plain_password (str): Plain text password.
        hashed_password (str): Already hashed password to compare to.
    Returns:
        match (bool): Whether the passwords match.
    """
    return password_hash.verify( plain_password, hashed_password )

def hash_token( raw_token: str ) -> str:
    """
    Utility to hash tokens:
    Parameters:
        raw_token (str): Token to be hashed.
    Returns:
        token_hash (str): Hashed token.
    """
    return hashlib.sha256( raw_token.encode( ) ).hexdigest( ) 

def generate_api_key( ) -> str:
    """
    Generates an API keh to be used with the API.
    Returns:
        api_key (str): API key.
    """
    return f"key_{ secrets.token_hex( 32 ) }"

def create_access_token( user_id: str ) -> str:
    """
    Creates a new JWT access token.
    Parameters:
        user_id (str): UUID of the user the access token is for.
    Returns:
        access_token (str): New access token.
    """
    now = datetime.now( timezone.utc )
    expire = now + timedelta( minutes=settings.jwt_access_token_expire_minutes )

    payload = {
        "sub": user_id,
        "iat": now,
        "exp": expire
    }
    return jwt.encode( payload, settings.secret_key.get_secret_value( ), algorithm=settings.algorithm )

def decode_access_token( token: str ) -> dict:
    """
    Decodes an access token received by the user.
    Parameters:
        token (str): Access token.
    Returns:
        payload (dict): Dictionary containing information about the JWT.
    """
    return jwt.decode( token, settings.secret_key.get_secret_value( ), algorithms=[ settings.algorithm ] )

def generate_url_safe_token( bytes: int ) -> str:
    """
    Generic URL safe token generator.
    Parameters:
        bytes (int): The amount of random bytes.
    Returns:
        token (str): URL safe token.
    """
    return secrets.token_urlsafe( bytes )

def generate_ws_ticket ( ) -> str:
    """
    Create an authentication token/ticket for establishing a websocket.
    Returns:
        ws_ticket (str): The websocket ticket.
    """
    return secrets.token_urlsafe( 32 )