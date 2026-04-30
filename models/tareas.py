from pydantic import BaseModel
from typing import Optional
from datetime import date

class TareaCreate(BaseModel):
    titulo: str
    descripcion: Optional[str] = None
    fecha_vencimiento: date
    prioridad: str = "media"           # alta | media | baja
    estado: str = "pendiente"          # pendiente | en_progreso | completada
    asignado_a: Optional[str] = None
    cargado_por: Optional[str] = None

class TareaUpdate(BaseModel):
    titulo: Optional[str] = None
    descripcion: Optional[str] = None
    fecha_vencimiento: Optional[date] = None
    prioridad: Optional[str] = None
    estado: Optional[str] = None
    asignado_a: Optional[str] = None
