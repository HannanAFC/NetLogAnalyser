from datetime import datetime
from uuid import UUID
from typing import Annotated

from auth.password_policy import check_password_complexity
from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
    model_validator,
)

class PasswordComplexityMixin( BaseModel ):
    password:         str = Field( min_length=8, max_length=120 )
    confirm_password: str

    @field_validator("password", check_fields=False )
    @classmethod
    def password_complexity( cls, value: str ) -> str:
        is_valid, error_message = check_password_complexity( value )
        if not is_valid:
            raise ValueError( error_message )
        return value
    
    @model_validator( mode="after" )
    def passwords_match( self ) -> "PasswordComplexityMixin":
        if self.password != self.confirm_password:
            raise ValueError( "Passwords don't match" )
        return self

class UserPublic( BaseModel ):
    model_config = ConfigDict( from_attributes=True )

    id:           UUID
    email:        EmailStr
    display_name: str
    created_at:   datetime

class RegisterRequest( PasswordComplexityMixin ):
    email:            EmailStr = Field( max_length=255 )
    display_name:     str      = Field( min_length=1, max_length=50 )
    
class RegisterResponse( BaseModel ):
    user: UserPublic
    
class LoginRequest( BaseModel ):
    email:    EmailStr
    password: str

class LoginResponse( BaseModel ):
    access_token: str
    token_type:   str = "bearer"
    user:         UserPublic

class RefreshResponse( BaseModel ):
    access_token: str
    token_type:   str = "bearer"
    user:         UserPublic

class LogoutResponse( BaseModel ):
    detail: str = "Logged out successfully."

class TokenPayload( BaseModel ):
    sub: str
    exp: datetime
    iat: datetime

class ForgotPasswordRequest( BaseModel ):
    email: EmailStr

class ForgotPasswordResponse( BaseModel ):
    detail: str = "If the email has an associated account, a reset email will be sent to it."

class ResetPasswordRequest( PasswordComplexityMixin ):
    token:            str

class ResetPasswordResponse( BaseModel ):
    detail: str = "Password reset successfully"