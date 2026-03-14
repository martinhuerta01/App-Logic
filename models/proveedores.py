from pydantic import BaseModel
from typing import Optional

class ProveedorCreate(BaseModel):
    nombre: str
    responsable: Optional[str] = None
    telefono: Optional[str] = None
    email: Optional[str] = None
    direccion: Optional[str] = None
    productos_que_vende: Optional[str] = None
    observaciones: Optional[str] = None

class ProveedorUpdate(BaseModel):
    nombre: Optional[str] = None
    responsable: Optional[str] = None
    telefono: Optional[str] = None
    email: Optional[str] = None
    direccion: Optional[str] = None
    productos_que_vende: Optional[str] = None
    observaciones: Optional[str] = None
    activo: Optional[bool] = None