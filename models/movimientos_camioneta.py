from pydantic import BaseModel
from typing import Optional, List
from datetime import date

class TecnicoJornadaItem(BaseModel):
    tecnico_id: str
    presente: bool = True
    motivo_ausencia: Optional[str] = None

class MovimientoCamionetaCreate(BaseModel):
    equipo_id: str
    fecha: date
    hora_salida: Optional[str] = None
    hora_llegada: Optional[str] = None
    punto_inicio: Optional[str] = None
    punto_fin: Optional[str] = None
    observaciones: Optional[str] = None
    cargado_por: Optional[str] = None
    tecnicos: Optional[List[TecnicoJornadaItem]] = []

class MovimientoCamionetaUpdate(BaseModel):
    hora_salida: Optional[str] = None
    hora_llegada: Optional[str] = None
    punto_inicio: Optional[str] = None
    punto_fin: Optional[str] = None
    observaciones: Optional[str] = None
