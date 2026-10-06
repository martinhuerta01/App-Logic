from fastapi import APIRouter, HTTPException, Depends
from models.stock import MovimientoCreate, InstalacionCreate
from pydantic import BaseModel
from typing import Optional, List
from datetime import date, datetime
from database import supabase
from auth_middleware import get_current_user

router = APIRouter(dependencies=[Depends(get_current_user)])

class ProductoCreate(BaseModel):
    codigo: str
    descripcion: str
    categoria: str
    proveedor_id: Optional[str] = None
    plazo_entrega_dias: Optional[int] = None

class ProductoUpdate(BaseModel):
    codigo: Optional[str] = None
    descripcion: Optional[str] = None
    categoria: Optional[str] = None
    proveedor_id: Optional[str] = None
    plazo_entrega_dias: Optional[int] = None
    activo: Optional[bool] = None

# ─── MAPEO SERENÍSIMA ──────────────────────────────────────────────

class MapeoSerCreate(BaseModel):
    codigo_serenisima: int
    descripcion: str
    producto_ids: List[str]

class MapeoSerUpdate(BaseModel):
    codigo_serenisima: Optional[int] = None
    descripcion: Optional[str] = None
    producto_ids: Optional[List[str]] = None

@router.get("/productos/")
def listar_productos():
    result = supabase.table("productos").select("*, proveedores(nombre)").order("codigo").execute()
    return result.data

@router.post("/productos/")
def crear_producto(data: ProductoCreate):
    try:
        result = supabase.table("productos").insert(data.model_dump(exclude_none=True)).execute()
        return result.data
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/productos/{producto_id}")
def actualizar_producto(producto_id: str, data: ProductoUpdate):
    result = supabase.table("productos").update(data.model_dump(exclude_none=True)).eq("id", producto_id).execute()
    return result.data

@router.delete("/productos/{producto_id}")
def eliminar_producto(producto_id: str):
    try:
        supabase.table("productos").delete().eq("id", producto_id).execute()
        return {"ok": True}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

class UbicacionCreate(BaseModel):
    nombre: str
    tipo: Optional[str] = None  # oficina | cd | general
    segmento: Optional[str] = None  # oficina | cd | taller | tecnico | equipo | otras
    localidad: Optional[str] = None
    equipo_id: Optional[str] = None  # enlace opcional con el equipo de Personal (Camioneta 1 -> Equipo 1)
    ubicacion_materiales_id: Optional[str] = None  # de dónde salen los materiales de instalación de sus tickets

class UbicacionUpdate(BaseModel):
    nombre: Optional[str] = None
    tipo: Optional[str] = None
    segmento: Optional[str] = None
    localidad: Optional[str] = None
    equipo_id: Optional[str] = None
    ubicacion_materiales_id: Optional[str] = None

@router.get("/ubicaciones/")
def listar_ubicaciones():
    result = supabase.table("ubicaciones").select("*").execute()
    return result.data

@router.post("/ubicaciones/")
def crear_ubicacion(data: UbicacionCreate):
    result = supabase.table("ubicaciones").insert(data.model_dump(exclude_none=True)).execute()
    return result.data

@router.put("/ubicaciones/{ubicacion_id}")
def actualizar_ubicacion(ubicacion_id: str, data: UbicacionUpdate):
    result = supabase.table("ubicaciones").update(data.model_dump(exclude_none=True)).eq("id", ubicacion_id).execute()
    return result.data

@router.delete("/ubicaciones/{ubicacion_id}")
def eliminar_ubicacion(ubicacion_id: str):
    supabase.table("ubicaciones").delete().eq("id", ubicacion_id).execute()
    return {"ok": True}

@router.get("/actual/")
def stock_actual(ubicacion_id: str = None):
    query = supabase.table("stock_actual").select(
        "*, productos(codigo, descripcion, categoria), ubicaciones(nombre, tipo)"
    )
    if ubicacion_id:
        query = query.eq("ubicacion_id", ubicacion_id)
    result = query.execute()
    return result.data

class StockActualUpdate(BaseModel):
    cantidad: int

@router.patch("/actual/{stock_id}/")
def actualizar_stock_actual(stock_id: str, data: StockActualUpdate):
    result = supabase.table("stock_actual").update({"cantidad": data.cantidad}).eq("id", stock_id).execute()
    return result.data

@router.post("/movimiento/")
def registrar_movimiento(data: MovimientoCreate):
    mov = supabase.table("movimientos").insert(data.model_dump(mode="json")).execute()
    if data.origen_id:
        _actualizar_stock(data.producto_id, data.origen_id, -data.cantidad)
    if data.destino_id:
        _actualizar_stock(data.producto_id, data.destino_id, data.cantidad)
    return mov.data

class EntradaCreate(BaseModel):
    producto_id: str
    ubicacion_id: str
    cantidad: int
    fecha: str
    observaciones: Optional[str] = None

class TransferenciaCreate(BaseModel):
    producto_id: str
    ubicacion_origen_id: str
    ubicacion_destino_id: str
    cantidad: int
    fecha: str

@router.post("/entradas/")
def registrar_entrada(data: EntradaCreate):
    mov = supabase.table("movimientos").insert({
        "tipo": "ENTRADA",
        "producto_id": data.producto_id,
        "destino_id": data.ubicacion_id,
        "cantidad": data.cantidad,
        "fecha": data.fecha,
        "observacion": data.observaciones,
    }).execute()
    _actualizar_stock(data.producto_id, data.ubicacion_id, data.cantidad)
    return mov.data

@router.post("/transferencias/")
def registrar_transferencia(data: TransferenciaCreate):
    mov = supabase.table("movimientos").insert({
        "tipo": "TRANSFERENCIA",
        "producto_id": data.producto_id,
        "origen_id": data.ubicacion_origen_id,
        "destino_id": data.ubicacion_destino_id,
        "cantidad": data.cantidad,
        "fecha": data.fecha,
    }).execute()
    _actualizar_stock(data.producto_id, data.ubicacion_origen_id, -data.cantidad)
    _actualizar_stock(data.producto_id, data.ubicacion_destino_id, data.cantidad)
    return mov.data

@router.get("/movimientos/")
def listar_movimientos(ubicacion_id: str = None, producto_id: str = None, serial: str = None):
    query = supabase.table("movimientos").select(
        "*, productos(codigo, descripcion), ubicaciones!movimientos_origen_id_fkey(nombre)"
    )
    if ubicacion_id:
        query = query.or_(f"origen_id.eq.{ubicacion_id},destino_id.eq.{ubicacion_id}")
    if producto_id:
        query = query.eq("producto_id", producto_id)
    if serial:
        query = query.eq("serial", serial)
    result = query.order("fecha", desc=True).execute()
    return result.data

class MovimientoUpdate(BaseModel):
    cantidad: Optional[int] = None
    fecha: Optional[str] = None
    observacion: Optional[str] = None

@router.patch("/movimientos/{movimiento_id}/")
def actualizar_movimiento(movimiento_id: str, data: MovimientoUpdate):
    mov = supabase.table("movimientos").select("*").eq("id", movimiento_id).execute()
    if not mov.data:
        raise HTTPException(status_code=404, detail="Movimiento no encontrado")
    m = mov.data[0]
    update_data = data.model_dump(exclude_none=True)
    if "cantidad" in update_data:
        delta = update_data["cantidad"] - m["cantidad"]
        if m.get("destino_id"):
            _actualizar_stock(m["producto_id"], m["destino_id"], delta)
        if m.get("origen_id"):
            _actualizar_stock(m["producto_id"], m["origen_id"], -delta)
    result = supabase.table("movimientos").update(update_data).eq("id", movimiento_id).execute()
    return result.data

@router.delete("/movimientos/{movimiento_id}/")
def eliminar_movimiento(movimiento_id: str):
    mov = supabase.table("movimientos").select("*").eq("id", movimiento_id).execute()
    if not mov.data:
        raise HTTPException(status_code=404, detail="Movimiento no encontrado")
    m = mov.data[0]
    if m.get("destino_id"):
        _actualizar_stock(m["producto_id"], m["destino_id"], -m["cantidad"])
    if m.get("origen_id"):
        _actualizar_stock(m["producto_id"], m["origen_id"], m["cantidad"])
    supabase.table("movimientos").delete().eq("id", movimiento_id).execute()
    return {"ok": True}

@router.post("/instalacion/")
def registrar_instalacion(data: InstalacionCreate):
    receta = supabase.table("recetas").select("*, productos(id, codigo, descripcion)").eq("tipo_instalacion", data.tipo_instalacion).execute()
    if not receta.data:
        raise HTTPException(status_code=404, detail="Tipo de instalacion no encontrado")
    movimientos = []
    for item in receta.data:
        producto_id = item["producto_id"]
        cantidad = item["cantidad"]
        stock = supabase.table("stock_actual").select("cantidad").eq("producto_id", producto_id).eq("ubicacion_id", data.ubicacion_id).execute()
        stock_disponible = stock.data[0]["cantidad"] if stock.data else 0
        if stock_disponible < cantidad:
            raise HTTPException(
                status_code=400,
                detail=f"Stock insuficiente de {item['productos']['descripcion']}: hay {stock_disponible}, se necesitan {cantidad}"
            )
        _actualizar_stock(producto_id, data.ubicacion_id, -cantidad)
        movimientos.append({
            "tipo": "INSTALACION",
            "producto_id": producto_id,
            "origen_id": data.ubicacion_id,
            "cantidad": cantidad,
            "fecha": str(data.fecha),
            "jornada_id": data.jornada_id,
            "cargado_por": data.cargado_por,
            "observacion": f"{data.tipo_instalacion} - {data.observacion or ''}",
        })
    supabase.table("movimientos").insert(movimientos).execute()
    return {"ok": True, "insumos_descontados": len(movimientos)}


# ─── MAPEO SERENÍSIMA ENDPOINTS ────────────────────────────────────

@router.get("/mapeo-serenisima/")
def listar_mapeo():
    result = supabase.table("mapeo_serenisima").select("*").order("codigo_serenisima").execute()
    return result.data

@router.post("/mapeo-serenisima/")
def crear_mapeo(data: MapeoSerCreate):
    try:
        result = supabase.table("mapeo_serenisima").insert(data.model_dump()).execute()
        return result.data
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/mapeo-serenisima/{mapeo_id}")
def actualizar_mapeo(mapeo_id: str, data: MapeoSerUpdate):
    result = supabase.table("mapeo_serenisima").update(data.model_dump(exclude_none=True)).eq("id", mapeo_id).execute()
    return result.data

@router.delete("/mapeo-serenisima/{mapeo_id}")
def eliminar_mapeo(mapeo_id: str):
    supabase.table("mapeo_serenisima").delete().eq("id", mapeo_id).execute()
    return {"ok": True}


# ─── EQUIPOS SERIALIZADOS (estado actual por serial) ──────────────

@router.get("/equipos/")
def listar_equipos(estado: str = None, ubicacion_id: str = None, patente: str = None, q: str = None):
    query = supabase.table("equipos_estado").select(
        "*, productos(codigo, descripcion), ubicaciones(nombre)"
    )
    if estado:
        query = query.eq("estado", estado)
    if ubicacion_id:
        query = query.eq("ubicacion_id", ubicacion_id)
    if patente:
        query = query.eq("patente", patente)
    if q:
        query = query.ilike("serial", f"%{q}%")
    result = query.order("updated_at", desc=True).execute()
    return result.data

class EquipoEstadoUpdate(BaseModel):
    estado: Optional[str] = None
    ubicacion_id: Optional[str] = None
    patente: Optional[str] = None
    configuracion: Optional[str] = None
    cliente: Optional[str] = None
    sin_control: Optional[bool] = None

@router.patch("/equipos/{serial}/")
def actualizar_equipo(serial: str, data: EquipoEstadoUpdate):
    result = supabase.table("equipos_estado").update(data.model_dump(exclude_none=True)).eq("serial", serial).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Equipo no encontrado")
    return result.data


RESULTADOS_CONTROL = {"USADO_OK_CAMPO", "USADO_OK_OFICINA", "FALLA_RMA", "BAJA"}

class ControlEquipo(BaseModel):
    resultado: str   # USADO_OK_CAMPO | USADO_OK_OFICINA | FALLA_RMA | BAJA
    observacion: Optional[str] = None
    cargado_por: Optional[str] = None

@router.post("/equipos/{serial}/control/")
def registrar_control_equipo(serial: str, data: ControlEquipo):
    """Resultado del control de un equipo retirado: actualiza su estado y deja el movimiento registrado."""
    if data.resultado not in RESULTADOS_CONTROL:
        raise HTTPException(status_code=400, detail="Resultado de control inválido")
    equipo = supabase.table("equipos_estado").select("*").eq("serial", serial).execute().data
    if not equipo:
        raise HTTPException(status_code=404, detail="Equipo no encontrado")
    e = equipo[0]
    if e["estado"] != "RETIRADO_PENDIENTE":
        raise HTTPException(status_code=400, detail="Solo se controla un equipo retirado pendiente de control")
    actualizado = supabase.table("equipos_estado").update({"estado": data.resultado, "sin_control": False}).eq("serial", serial).execute()
    supabase.table("movimientos").insert({
        "tipo": "RESULTADO_CONTROL",
        "producto_id": e["producto_id"],
        "cantidad": 1,
        "fecha": date.today().isoformat(),
        "serial": serial,
        "cargado_por": data.cargado_por,
        "observacion": f"Control: {data.resultado}" + (f" - {data.observacion}" if data.observacion else ""),
    }).execute()
    return actualizado.data


# ─── STOCK MÍNIMO POR ÁMBITO (vista del Dashboard de Stock) ───────

class MinimoUpsert(BaseModel):
    producto_id: str
    ambito: str          # oficina | serenisima | camioneta1 | camioneta2
    cantidad_minima: int

@router.get("/minimos/")
def listar_minimos(ambito: str = None):
    query = supabase.table("stock_minimo").select("*")
    if ambito:
        query = query.eq("ambito", ambito)
    return query.execute().data

@router.put("/minimos/")
def guardar_minimo(data: MinimoUpsert):
    if data.cantidad_minima < 0:
        raise HTTPException(status_code=400, detail="El mínimo no puede ser negativo")
    result = supabase.table("stock_minimo").upsert(
        {**data.model_dump(), "updated_at": datetime.utcnow().isoformat()},
        on_conflict="producto_id,ambito",
    ).execute()
    return result.data

@router.delete("/minimos/")
def quitar_minimo(producto_id: str, ambito: str):
    supabase.table("stock_minimo").delete().eq("producto_id", producto_id).eq("ambito", ambito).execute()
    return {"ok": True}


def _actualizar_stock(producto_id: str, ubicacion_id: str, delta: int):
    existing = supabase.table("stock_actual").select("id, cantidad").eq("producto_id", producto_id).eq("ubicacion_id", ubicacion_id).execute()
    if existing.data:
        nueva_cantidad = existing.data[0]["cantidad"] + delta
        supabase.table("stock_actual").update({"cantidad": nueva_cantidad}).eq("id", existing.data[0]["id"]).execute()
    else:
        supabase.table("stock_actual").insert({
            "producto_id": producto_id,
            "ubicacion_id": ubicacion_id,
            "cantidad": max(0, delta)
        }).execute()