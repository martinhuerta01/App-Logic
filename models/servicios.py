from pydantic import BaseModel
from typing import Optional
from datetime import date

class ServicioCreate(BaseModel):
    fecha: date
    cliente: str
    es_serenisima: bool = False
    tipo_servicio: str
    tipo_unidad: Optional[str] = None
    alcance: Optional[str] = None
    patente: Optional[str] = None
    responsable: Optional[str] = None
    estado: str = "PENDIENTE"
    observaciones: Optional[str] = None
    cargado_por: Optional[str] = None

class ServicioUpdate(BaseModel):
    fecha: Optional[date] = None
    cliente: Optional[str] = None
    tipo_servicio: Optional[str] = None
    tipo_unidad: Optional[str] = None
    alcance: Optional[str] = None
    patente: Optional[str] = None
    responsable: Optional[str] = None
    estado: Optional[str] = None
    observaciones: Optional[str] = None