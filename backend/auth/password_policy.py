from __future__ import annotations

import re

MIN_LENGTH = 8

# Each rule is (regex, human-readable reason for failure).
_RULES: list[tuple[str, str]] = [
    (r"[A-Z]", "Password must contain at least one uppercase letter"),
    (r"[a-z]", "Password must contain at least one lowercase letter"),
    (r"[0-9]", "Password must contain at least one digit"),
    (r"[^A-Za-z0-9]", "Password must contain at least one special character"),
]


def check_password_complexity( password: str ) -> tuple[ bool, str | None ]:
    """
    Check password meets length and complexity requirements
    Parameters:
        password (str): Plain text password.
    Returns:
        dict (dict[pass, fail_reason]): A dictionary containing if the password meets requirements and a fail reason (if it doesn't).
    """
    if len( password ) < MIN_LENGTH:
        return False, f"Password must be at least { MIN_LENGTH } characters long"

    for pattern, message in _RULES:
        if not re.search( pattern, password ):
            return False, message

    return True, None