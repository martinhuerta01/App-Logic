from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List
from datetime import date, datetime
from collections import defaultdict
from database import supabase
from auth_middleware import requiere_modulo

# Módulo Stock nuevo: stock por ubicación, conteos físicos y envíos entre ubicaciones.
# Usa las mismas tablas que el módulo de Stock actual (productos, ubicaciones, movimientos, stock_actual,
# equipos_estado). Las operaciones que tocan varias tablas son funciones de la base (migración 006).
router = APIRouter()
acceso = Depends(requiere_modulo("stock_nuevo", "stock"))


def _todos(consulta_fn):
    """Trae todas las filas (la base entrega de a 1000)."""
    filas, desde = [], 0
    while True:
        lote = consulta_fn().range(desde, desde + 999).execute().data
        filas += lote
        if len(lote) < 1000:
            return filas
        desde += 1000


def _momento(texto: str) -> datetime:
    return datetime.fromisoformat(texto.replace("Z", "+00:00"))


def _mensaje_de_error(e: Exception) -> str:
    # Los errores de las funciones de la base traen el texto en 'message'
    detalle = getattr(e, "message", None) or (e.args[0] if e.args and isinstance(e.args[0], dict) else None)
    if isinstance(detalle, dict):
        return detalle.get("message") or str(detalle)
    return str(detalle or e)


# ─── Modelos ────────────────────────────────────────────────────────

class LineaEnvio(BaseModel):
    producto_id: str
    cantidad: int
    series: Optional[List[str]] = None


class EnvioCreate(BaseModel):
    origen_id: str
    destino_id: str
    fecha: Optional[date] = None
    lineas: List[LineaEnvio]


class LineaConteo(BaseModel):
    producto_id: str
    contado: int
    motivo: Optional[str] = None
    series: Optional[List[str]] = None


class ConteoCreate(BaseModel):
    ubicacion_id: str
    fecha: Optional[date] = None
    observacion: Optional[str] = None
    lineas: List[LineaConteo]


# ─── Lectura ────────────────────────────────────────────────────────

@router.get("/ubicaciones/")
def listar_ubicaciones(usuario: dict = acceso):
    """Ubicaciones con la fecha de su último conteo y cuántos productos quedaron sin explicar (negativos)."""
    ubicaciones = supabase.table("ubicaciones").select("id, nombre, tipo").execute().data
    stock = _todos(lambda: supabase.table("stock_actual").select("ubicacion_id, cantidad"))
    conteos = _todos(lambda: supabase.table("conteos").select("ubicacion_id, fecha, creado_en").order("creado_en", desc=True))
    ultimo = {}
    for c in conteos:
        ultimo.setdefault(c["ubicacion_id"], c)
    productos = defaultdict(int)
    negativos = defaultdict(int)
    for s in stock:
        if s["cantidad"] != 0:
            productos[s["ubicacion_id"]] += 1
        if s["cantidad"] < 0:
            negativos[s["ubicacion_id"]] += 1
    return [
        {
            **u,
            "ultimo_conteo": ultimo.get(u["id"], {}).get("fecha"),
            "productos": productos[u["id"]],
            "negativos": negativos[u["id"]],
        }
        for u in ubicaciones
    ]


@router.get("/ubicaciones/{ubicacion_id}/stock/")
def stock_de_ubicacion(ubicacion_id: str, usuario: dict = acceso):
    """
    Una fila por producto: último conteo, envíos y tickets desde ese conteo, y stock ahora.
    Stock ahora = último conteo + envíos − tickets descontados desde esa fecha.
    """
    ubic = supabase.table("ubicaciones").select("id, nombre, tipo").eq("id", ubicacion_id).execute().data
    if not ubic:
        raise HTTPException(status_code=404, detail="Ubicación no encontrada")

    conteo = supabase.table("conteos").select("id, fecha, creado_en, hecho_por").eq("ubicacion_id", ubicacion_id) \
        .order("creado_en", desc=True).limit(1).execute().data
    conteo = conteo[0] if conteo else None
    contado = {}
    if conteo:
        for l in supabase.table("conteo_lineas").select("producto_id, contado").eq("conteo_id", conteo["id"]).execute().data:
            contado[l["producto_id"]] = l["contado"]

    stock = {s["producto_id"]: s["cantidad"] for s in
             supabase.table("stock_actual").select("producto_id, cantidad").eq("ubicacion_id", ubicacion_id).execute().data}

    envios, tickets = defaultdict(int), defaultdict(int)
    for origen_o_destino in ("origen_id", "destino_id"):
        movs = _todos(lambda: supabase.table("movimientos")
                      .select("tipo, producto_id, origen_id, destino_id, cantidad, created_at, conteo_id")
                      .eq(origen_o_destino, ubicacion_id))
        for m in movs:
            if m.get("conteo_id"):
                continue
            if conteo and _momento(m["created_at"]) <= _momento(conteo["creado_en"]):
                continue
            if m["tipo"] == "INSTALACION":
                if origen_o_destino == "origen_id":
                    tickets[m["producto_id"]] += m["cantidad"]
            else:
                envios[m["producto_id"]] += m["cantidad"] if origen_o_destino == "destino_id" else -m["cantidad"]

    productos = supabase.table("productos").select("id, codigo, descripcion, categoria, activo, lleva_serie").execute().data
    series = defaultdict(int)
    for e in _todos(lambda: supabase.table("equipos_estado").select("producto_id")
                    .eq("ubicacion_id", ubicacion_id).eq("estado", "EN_STOCK")):
        series[e["producto_id"]] += 1

    filas = []
    for p in productos:
        pid = p["id"]
        hay_actividad = pid in stock or envios[pid] or tickets[pid] or pid in contado
        if not hay_actividad:
            continue
        ahora = stock.get(pid, 0)
        filas.append({
            "producto_id": pid,
            "codigo": (p["codigo"] or "").strip(),
            "descripcion": p["descripcion"],
            "categoria": p["categoria"],
            "activo": p.get("activo", True),
            "lleva_serie": bool(p.get("lleva_serie")),
            "ultimo_conteo": contado.get(pid),
            "envios": envios[pid],
            "tickets": tickets[pid],
            "stock": ahora,
            "series_cargadas": series[pid] if p.get("lleva_serie") else None,
        })
    filas.sort(key=lambda f: (f["categoria"] or "", f["codigo"]))
    return {"ubicacion": ubic[0], "conteo": conteo, "filas": filas}


@router.get("/ubicaciones/{ubicacion_id}/series/")
def series_de_ubicacion(ubicacion_id: str, producto_id: str, usuario: dict = acceso):
    """Números de serie en stock de un producto en una ubicación."""
    return [e["serial"] for e in supabase.table("equipos_estado").select("serial")
            .eq("ubicacion_id", ubicacion_id).eq("producto_id", producto_id).eq("estado", "EN_STOCK")
            .order("serial").execute().data]


@router.get("/productos/")
def productos_activos(usuario: dict = acceso):
    return supabase.table("productos").select("id, codigo, descripcion, categoria, lleva_serie") \
        .eq("activo", True).order("codigo").execute().data


@router.get("/stock-por-producto/")
def stock_por_producto(ubicacion_id: str, usuario: dict = acceso):
    """Cantidades de una ubicación por producto (para mostrar lo disponible al armar un envío)."""
    return {s["producto_id"]: s["cantidad"] for s in
            supabase.table("stock_actual").select("producto_id, cantidad").eq("ubicacion_id", ubicacion_id).execute().data}


# ─── Escritura ──────────────────────────────────────────────────────

@router.post("/envios/")
def registrar_envio(data: EnvioCreate, usuario: dict = acceso):
    try:
        res = supabase.rpc("fn_registrar_envio", {
            "p_origen": data.origen_id,
            "p_destino": data.destino_id,
            "p_fecha": (data.fecha or date.today()).isoformat(),
            "p_cargado_por": usuario["nombre"],
            "p_lineas": [l.model_dump() for l in data.lineas],
        }).execute()
        return res.data
    except Exception as e:
        raise HTTPException(status_code=400, detail=_mensaje_de_error(e))


@router.post("/conteos/")
def confirmar_conteo(data: ConteoCreate, usuario: dict = acceso):
    try:
        res = supabase.rpc("fn_confirmar_conteo", {
            "p_ubicacion": data.ubicacion_id,
            "p_fecha": (data.fecha or date.today()).isoformat(),
            "p_hecho_por": usuario["nombre"],
            "p_observacion": data.observacion,
            "p_lineas": [l.model_dump() for l in data.lineas],
        }).execute()
        return res.data
    except Exception as e:
        raise HTTPException(status_code=400, detail=_mensaje_de_error(e))
