from pydantic import BaseModel
from typing import Optional

class TerceroCreate(BaseModel):
    nombre: str
    ciudad: str
    telefono: Optional[str] = None
    email: Optional[str] = None
    empresa: Optional[str] = None
    observaciones: Optional[str] = None

class TerceroUpdate(BaseModel):
    nombre: Optional[str] = None
    ciudad: Optional[str] = None
    telefono: Optional[str] = None
    email: Optional[str] = None
    empresa: Optional[str] = None
    observaciones: Optional[str] = None
    activo: Optional[bool] = None