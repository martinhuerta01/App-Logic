from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import date

class MovimientoCreate(BaseModel):
    tipo: str
    # ENTRADA, SALIDA, TRANSFERENCIA, INSTALACION, RETIRO, AJUSTE
    producto_id: str
    origen_id: Optional[str] = None
    destino_id: Optional[str] = None
    cantidad: int
    fecha: date
    cargado_por: Optional[str] = None
    observacion: Optional[str] = None
    serial: Optional[str] = None

class InstalacionCreate(BaseModel):
    tipo_instalacion: str
    # CHASIS, SEMI, TRACTOR, RFID, BASICO
    ubicacion_id: str
    fecha: date
    cargado_por: Optional[str] = None
    jornada_id: Optional[str] = None
    observacion: Optional[str] = None


# ─── MAPEO DE TALLERES (localidad -> ubicación, para el import de tickets) ──
# aplica_a: "serenisima" (va al CD) u "otros" (va al pool del taller/técnico
# que atiende otros clientes en esa misma zona — ver plan de stock).

class MapeoTallerCreate(BaseModel):
    keyword: str
    ubicacion_id: str
    aplica_a: Optional[str] = "serenisima"
    activo: Optional[bool] = True

class MapeoTallerUpdate(BaseModel):
    keyword: Optional[str] = None
    ubicacion_id: Optional[str] = None
    aplica_a: Optional[str] = None
    activo: Optional[bool] = None


# ─── RECETAS / KITS (composición de insumos por tipo de instalación) ──

class RecetaItemCreate(BaseModel):
    tipo_instalacion: str
    producto_id: str
    cantidad: int

class RecetaItemUpdate(BaseModel):
    tipo_instalacion: Optional[str] = None
    producto_id: Optional[str] = None
    cantidad: Optional[int] = None


# ─── IMPORT DE TICKETS DE SOPORTE ──────────────────────────────────────

class TicketMovimientoItem(BaseModel):
    tipo: str
    producto_id: str
    origen_id: Optional[str] = None
    destino_id: Optional[str] = None
    cantidad: int
    fecha: date
    observacion: Optional[str] = None
    serial: Optional[str] = None
    patente: Optional[str] = None
    configuracion: Optional[str] = None

class TicketConfirmarItem(BaseModel):
    ticket_numero: str
    distrito: Optional[str] = None
    archivo_nombre: Optional[str] = None
    fila_excel: Optional[Any] = None
    cargado_por: Optional[str] = None
    movimientos: List[TicketMovimientoItem]