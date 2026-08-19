from auth.schemas import PasswordComplexityMixin
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UpdateUserRequest( BaseModel ):
    model_config = ConfigDict( str_strip_whitespace=True )
    
    email:            EmailStr | None = Field( max_length=255 )
    display_name:     str | None      = Field( min_length=1, max_length=50 )

class UpdateUserPasswordRequest( PasswordComplexityMixin ):
    current_password:     str

class UpdatePasswordResponse( BaseModel ):
    detail: str = "Password has been update successfully. All sessions will be terminated so you will be required to log back in."

class DeleteUserRequest( BaseModel ):
    password:         str
    confirm_password: str