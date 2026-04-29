from pydantic import BaseModel
from typing import Optional

class LoginRequest(BaseModel):
    usuario: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    usuario: str
    rol: str
    modulos: Optional[list[str]] = None
