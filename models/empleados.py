from pydantic import BaseModel
from typing import Optional

class EmpleadoCreate(BaseModel):
    nombre: str
    telefono: Optional[str] = None
    dni: Optional[str] = None
    zona: Optional[str] = None
    vehiculo: Optional[str] = None
    patente: Optional[str] = None
    observaciones: Optional[str] = None

class EmpleadoUpdate(BaseModel):
    telefono: Optional[str] = None
    dni: Optional[str] = None
    zona: Optional[str] = None
    vehiculo: Optional[str] = None
    patente: Optional[str] = None
    observaciones: Optional[str] = None
    activo: Optional[bool] = None