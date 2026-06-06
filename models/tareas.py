from pydantic import BaseModel, Field
from typing import Optional
from datetime import date

class TareaCreate(BaseModel):
    titulo: str = Field(..., max_length=200)
    descripcion: Optional[str] = Field(None, max_length=2000)
    fecha_vencimiento: Optional[date] = None
    prioridad: str = "media"           # alta | media | baja
    estado: str = "pendiente"          # pendiente | en_progreso | completada
    tipo: str = "tarea"               # tarea | investigacion | bug | mejora
    categoria: Optional[str] = Field(None, max_length=100)
    asignado_a: Optional[str] = Field(None, max_length=100)
    cargado_por: Optional[str] = Field(None, max_length=100)

class TareaUpdate(BaseModel):
    titulo: Optional[str] = Field(None, max_length=200)
    descripcion: Optional[str] = Field(None, max_length=2000)
    fecha_vencimiento: Optional[date] = None
    prioridad: Optional[str] = None
    estado: Optional[str] = None
    tipo: Optional[str] = None
    categoria: Optional[str] = Field(None, max_length=100)
    asignado_a: Optional[str] = Field(None, max_length=100)

class NotaCreate(BaseModel):
    texto: str = Field(..., max_length=2000)
    cargado_por: Optional[str] = Field(None, max_length=100)
