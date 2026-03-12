from pydantic import BaseModel
from typing import Optional
from datetime import date

class JornadaCreate(BaseModel):
    empleado_id: str
    nombre: str
    fecha: date
    tipo_asistencia: str
    # ACTIVO, LLEGADA_TARDE, AUSENCIA_SJ, AUSENCIA_J, VACACIONES, LICENCIA
    hora_entrada: Optional[str] = None
    hora_salida: Optional[str] = None
    inicio_ruta: Optional[str] = None
    fin_ruta: Optional[str] = None
    instalaciones: Optional[int] = 0
    desinstalaciones: Optional[int] = 0
    revisiones: Optional[int] = 0
    motivo: Optional[str] = None
    tipo_licencia: Optional[str] = None
    detalle: Optional[str] = None
    cargado_por: Optional[str] = None

class AusenciaCreate(BaseModel):
    empleado_id: str
    nombre: str
    tipo: str
    fecha_desde: date
    fecha_hasta: date
    tipo_licencia: Optional[str] = None
    motivo: Optional[str] = None
    cargado_por: Optional[str] = None