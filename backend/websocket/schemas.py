from pydantic import BaseModel


class CreateTicketResponse( BaseModel ):
    ticket:     str
    expires_in: int