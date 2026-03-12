from fastapi import APIRouter, HTTPException
from models.stock import MovimientoCreate, InstalacionCreate
from database import supabase

router = APIRouter()

# ── Productos ──────────────────────────────
@router.get("/productos/")
def listar_productos():
    result = supabase.table("productos").select("*").eq("activo", True).order("codigo").execute()
    return result.data

# ── Ubicaciones ────────────────────────────
@router.get("/ubicaciones/")
def listar_ubicaciones():
    result = supabase.table("ubicaciones").select("*").execute()
    return result.data

# ── Stock actual ───────────────────────────
@router.get("/actual/")
def stock_actual(ubicacion_id: str = None):
    query = supabase.table("stock_actual").select(
        "*, productos(codigo, descripcion, categoria), ubicaciones(nombre, tipo)"
    )
    if ubicacion_id:
        query = query.eq("ubicacion_id", ubicacion_id)
    result = query.execute()
    return result.data

# ── Movimientos ────────────────────────────
@router.post("/movimiento/")
def registrar_movimiento(data: MovimientoCreate):
    # 1. Registrar el movimiento
    mov = supabase.table("movimientos").insert(data.model_dump(mode="json")).execute()

    # 2. Actualizar stock origen (si hay)
    if data.origen_id:
        _actualizar_stock(data.producto_id, data.origen_id, -data.cantidad)

    # 3. Actualizar stock destino (si hay)
    if data.destino_id:
        _actualizar_stock(data.producto_id, data.destino_id, data.cantidad)

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

# ── Instalacion automatica ─────────────────
@router.post("/instalacion/")
def registrar_instalacion(data: InstalacionCreate):
    # Obtener receta
    receta = supabase.table("recetas")\
        .select("*, productos(id, codigo, descripcion)")\
        .eq("tipo_instalacion", data.tipo_instalacion)\
        .execute()

    if not receta.data:
        raise HTTPException(status_code=404, detail="Tipo de instalacion no encontrado")

    movimientos = []
    for item in receta.data:
        producto_id = item["producto_id"]
        cantidad = item["cantidad"]

        # Verificar stock disponible
        stock = supabase.table("stock_actual")\
            .select("cantidad")\
            .eq("producto_id", producto_id)\
            .eq("ubicacion_id", data.ubicacion_id)\
            .execute()

        stock_disponible = stock.data[0]["cantidad"] if stock.data else 0
        if stock_disponible < cantidad:
            raise HTTPException(
                status_code=400,
                detail=f"Stock insuficiente de {item['productos']['descripcion']}: hay {stock_disponible}, se necesitan {cantidad}"
            )

        # Descontar stock
        _actualizar_stock(producto_id, data.ubicacion_id, -cantidad)

        # Registrar movimiento
        mov_data = {
            "tipo": "INSTALACION",
            "producto_id": producto_id,
            "origen_id": data.ubicacion_id,
            "cantidad": cantidad,
            "fecha": str(data.fecha),
            "jornada_id": data.jornada_id,
            "cargado_por": data.cargado_por,
            "observacion": f"{data.tipo_instalacion} - {data.observacion or ''}",
        }
        movimientos.append(mov_data)

    supabase.table("movimientos").insert(movimientos).execute()
    return {"ok": True, "insumos_descontados": len(movimientos)}


# ── Helper ─────────────────────────────────
def _actualizar_stock(producto_id: str, ubicacion_id: str, delta: int):
    existing = supabase.table("stock_actual")\
        .select("id, cantidad")\
        .eq("producto_id", producto_id)\
        .eq("ubicacion_id", ubicacion_id)\
        .execute()

    if existing.data:
        nueva_cantidad = existing.data[0]["cantidad"] + delta
        supabase.table("stock_actual")\
            .update({"cantidad": nueva_cantidad})\
            .eq("id", existing.data[0]["id"])\
            .execute()
    else:
        supabase.table("stock_actual").insert({
            "producto_id": producto_id,
            "ubicacion_id": ubicacion_id,
            "cantidad": max(0, delta)
        }).execute()