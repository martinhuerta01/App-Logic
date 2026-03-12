from pydantic import BaseModel
from typing import Optional
from datetime import date

class MovimientoCreate(BaseModel):
    tipo: str
    # ENTRADA, SALIDA, TRANSFERENCIA
    producto_id: str
    origen_id: Optional[str] = None
    destino_id: Optional[str] = None
    cantidad: int
    fecha: date
    cargado_por: Optional[str] = None
    observacion: Optional[str] = None

class InstalacionCreate(BaseModel):
    tipo_instalacion: str
    # CHASIS, SEMI, TRACTOR, RFID, BASICO
    ubicacion_id: str
    fecha: date
    cargado_por: Optional[str] = None
    jornada_id: Optional[str] = None
    observacion: Optional[str] = None