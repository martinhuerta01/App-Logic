from fastapi import APIRouter, HTTPException
from models.stock import MovimientoCreate, InstalacionCreate
from pydantic import BaseModel
from typing import Optional, List
from database import supabase

router = APIRouter()

class ProductoCreate(BaseModel):
    codigo: str
    descripcion: str
    categoria: str
    proveedor_id: Optional[str] = None

class ProductoUpdate(BaseModel):
    codigo: Optional[str] = None
    descripcion: Optional[str] = None
    categoria: Optional[str] = None
    proveedor_id: Optional[str] = None
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
        result = supabase.table("productos").insert(data.model_dump()).execute()
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
    tipo: Optional[str] = None  # oficina | cd | camioneta | tecnico

class UbicacionUpdate(BaseModel):
    nombre: Optional[str] = None
    tipo: Optional[str] = None

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
def listar_movimientos(ubicacion_id: str = None, producto_id: str = None):
    query = supabase.table("movimientos").select(
        "*, productos(codigo, descripcion), ubicaciones!movimientos_origen_id_fkey(nombre)"
    )
    if ubicacion_id:
        query = query.or_(f"origen_id.eq.{ubicacion_id},destino_id.eq.{ubicacion_id}")
    if producto_id:
        query = query.eq("producto_id", producto_id)
    result = query.order("fecha", desc=True).execute()
    return result.data

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