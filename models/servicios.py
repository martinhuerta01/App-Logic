from pydantic import BaseModel
from typing import Optional
from datetime import date

class ServicioCreate(BaseModel):
    fecha: date
    hora_programada: Optional[str] = None
    equipo_id: Optional[str] = None
    cliente: str
    cliente_ref: Optional[str] = None
    tipo_servicio: str       # INSTALACION | REVISION | DESINSTALACION
    dispositivo: Optional[str] = None  # GPS | LECTORA | GPS y LECTORA
    patente: Optional[str] = None
    estado: str = "PENDIENTE"
    observaciones: Optional[str] = None
    cargado_por: Optional[str] = None

class ServicioUpdate(BaseModel):
    fecha: Optional[date] = None
    hora_programada: Optional[str] = None
    equipo_id: Optional[str] = None
    cliente: Optional[str] = None
    cliente_ref: Optional[str] = None
    tipo_servicio: Optional[str] = None
    dispositivo: Optional[str] = None
    patente: Optional[str] = None
    estado: Optional[str] = None
    observaciones: Optional[str] = None
