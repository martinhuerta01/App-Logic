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
    llegada_gr_lch: Optional[str] = None
    salida_gr_lch: Optional[str] = None
    observaciones: Optional[str] = None
    cargado_por: Optional[str] = None
    tecnicos: Optional[List[TecnicoJornadaItem]] = []

class MovimientoCamionetaUpdate(BaseModel):
    equipo_id: Optional[str] = None
    fecha: Optional[date] = None
    hora_salida: Optional[str] = None
    hora_llegada: Optional[str] = None
    punto_inicio: Optional[str] = None
    punto_fin: Optional[str] = None
    llegada_gr_lch: Optional[str] = None
    salida_gr_lch: Optional[str] = None
    observaciones: Optional[str] = None
