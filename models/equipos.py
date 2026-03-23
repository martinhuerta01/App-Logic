from pydantic import BaseModel
from typing import Optional

class EquipoCreate(BaseModel):
    nombre: str
    patente: str
    activo: bool = True

class EquipoUpdate(BaseModel):
    nombre: Optional[str] = None
    patente: Optional[str] = None
    activo: Optional[bool] = None
