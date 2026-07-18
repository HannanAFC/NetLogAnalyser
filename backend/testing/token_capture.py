from __future__ import annotations

_latest_tokens: dict[ tuple[ str, str ], str ] = { }


def record_token( *, email: str, token_type: str, raw_token: str ) -> None:
    """
    TESTING ONLY - records raw token for storage to be used in end to end tests
    Parameters:
        email (str): Email the token is related to.
        token_type (str): The type of token being stored.
        raw_token (str) The raw token value.
    """
    _latest_tokens[ ( email, token_type ) ] = raw_token


def get_token( *, email: str, token_type: str ) -> str | None:
    """
    TESTING ONLY - retrieves a stored token.
    Parameters:
        email (str): The email the token is related to.
        token_type (str): The type of token being stored.
    Returns:
        raw_token (str | None): The token from the given parameters.
    """
    return _latest_tokens.get( ( email, token_type ) )
