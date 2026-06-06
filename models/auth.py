from pydantic import BaseModel, Field
from typing import Optional

class LoginRequest(BaseModel):
    usuario: str = Field(..., max_length=100)
    password: str = Field(..., max_length=200)

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    usuario: str
    rol: str
    modulos: Optional[list[str]] = None
    submodulos: Optional[dict] = None
