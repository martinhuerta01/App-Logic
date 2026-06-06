from pydantic import BaseModel, Field
from typing import Optional

class EmpleadoCreate(BaseModel):
    nombre: str = Field(..., max_length=150)
    telefono: Optional[str] = Field(None, max_length=30)
    dni: Optional[str] = Field(None, max_length=20)
    zona: Optional[str] = Field(None, max_length=100)
    vehiculo: Optional[str] = Field(None, max_length=100)
    patente: Optional[str] = Field(None, max_length=20)
    observaciones: Optional[str] = Field(None, max_length=500)

class EmpleadoUpdate(BaseModel):
    telefono: Optional[str] = None
    dni: Optional[str] = None
    zona: Optional[str] = None
    vehiculo: Optional[str] = None
    patente: Optional[str] = None
    observaciones: Optional[str] = None
    activo: Optional[bool] = None