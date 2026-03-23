from pydantic import BaseModel
from typing import Optional

class DirectorioCreate(BaseModel):
    nombre: str
    tipo: str  # interno | interior | cliente
    telefono: Optional[str] = None
    email: Optional[str] = None
    equipo_id: Optional[str] = None      # solo para internos
    ciudad: Optional[str] = None         # para interior
    contacto: Optional[str] = None       # para interior/cliente
    observaciones: Optional[str] = None
    activo: bool = True

class DirectorioUpdate(BaseModel):
    nombre: Optional[str] = None
    tipo: Optional[str] = None
    telefono: Optional[str] = None
    email: Optional[str] = None
    equipo_id: Optional[str] = None
    ciudad: Optional[str] = None
    contacto: Optional[str] = None
    observaciones: Optional[str] = None
    activo: Optional[bool] = None
