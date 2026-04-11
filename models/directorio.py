from pydantic import BaseModel
from typing import Optional

class DirectorioCreate(BaseModel):
    nombre: str                            # Responsable principal
    tipo: str                              # interno | interior | cliente | proveedor
    empresa: Optional[str] = None          # para clientes y proveedores
    base: Optional[str] = None             # para clientes
    producto: Optional[str] = None         # para proveedores
    celular: Optional[str] = None
    email: Optional[str] = None
    direccion: Optional[str] = None
    localidad: Optional[str] = None
    equipo_id: Optional[str] = None        # solo para internos
    contacto: Optional[str] = None
    observaciones: Optional[str] = None
    activo: bool = True

class DirectorioUpdate(BaseModel):
    nombre: Optional[str] = None
    tipo: Optional[str] = None
    empresa: Optional[str] = None
    base: Optional[str] = None
    producto: Optional[str] = None
    celular: Optional[str] = None
    email: Optional[str] = None
    direccion: Optional[str] = None
    localidad: Optional[str] = None
    equipo_id: Optional[str] = None
    contacto: Optional[str] = None
    observaciones: Optional[str] = None
    activo: Optional[bool] = None

class SubresponsableCreate(BaseModel):
    contacto_id: str
    nombre: str
    celular: Optional[str] = None
    email: Optional[str] = None
