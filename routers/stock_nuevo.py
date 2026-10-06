from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List, Any
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
    # Antes de aplicar las migraciones 008 y 009 todavía no existen el segmento y la localidad
    ubicaciones = None
    for columnas in ("id, nombre, tipo, segmento, localidad", "id, nombre, tipo, segmento", "id, nombre, tipo"):
        try:
            ubicaciones = supabase.table("ubicaciones").select(columnas).execute().data
            break
        except Exception:
            continue
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
        if not hay_actividad or p["categoria"] == "Herramientas":
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
    # Las herramientas tienen su propia pantalla: no entran en conteos ni envíos
    return supabase.table("productos").select("id, codigo, descripcion, categoria, lleva_serie") \
        .eq("activo", True).neq("categoria", "Herramientas").order("codigo").execute().data


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


# ─── Tickets de soporte ─────────────────────────────────────────────

class TicketMovimiento(BaseModel):
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


class TicketConfirmar(BaseModel):
    ticket_numero: str
    distrito: Optional[str] = None
    archivo_nombre: Optional[str] = None
    fila_excel: Optional[Any] = None
    movimientos: List[TicketMovimiento]
    serial_retirado: Optional[str] = None
    retirado_ubicacion_id: Optional[str] = None  # dónde quedó el equipo retirado (camioneta, taller o centro)


@router.get("/tickets/contexto/")
def contexto_de_tickets(usuario: dict = acceso):
    """Lo que necesita la pantalla de importación: tickets ya importados, último conteo por ubicación y estado de los equipos."""
    importados = [i["ticket_numero"] for i in _todos(lambda: supabase.table("tickets_importados").select("ticket_numero"))]
    ultimos = {}
    for c in _todos(lambda: supabase.table("conteos").select("ubicacion_id, fecha, creado_en").order("creado_en", desc=True)):
        ultimos.setdefault(c["ubicacion_id"], c["fecha"])
    equipos = _todos(lambda: supabase.table("equipos_estado").select("serial, estado, ubicacion_id, recibido_en"))
    return {"importados": importados, "ultimos_conteos": ultimos, "equipos": equipos}


@router.post("/tickets/confirmar/")
def confirmar_ticket(data: TicketConfirmar, usuario: dict = acceso):
    """Confirma un ticket de forma atómica (misma función de la base que el módulo actual) y ubica el equipo retirado."""
    try:
        res = supabase.rpc("fn_confirmar_ticket_stock", {
            "p_ticket_numero": data.ticket_numero,
            "p_distrito": data.distrito,
            "p_archivo_nombre": data.archivo_nombre,
            "p_fila_excel": data.fila_excel,
            "p_cargado_por": usuario["nombre"],
            "p_movimientos": [m.model_dump(mode="json") for m in data.movimientos],
        }).execute()
    except Exception as e:
        raise HTTPException(status_code=400, detail=_mensaje_de_error(e))
    resultado = res.data
    if not (resultado or {}).get("duplicado") and data.serial_retirado and data.retirado_ubicacion_id:
        supabase.table("equipos_estado").update({"ubicacion_id": data.retirado_ubicacion_id}) \
            .eq("serial", data.serial_retirado).eq("estado", "RETIRADO_PENDIENTE").execute()
    return resultado


# ─── Retirados ──────────────────────────────────────────────────────

class PiezaRecibida(BaseModel):
    pieza: str
    llego: bool


class RecepcionCreate(BaseModel):
    piezas: List[PiezaRecibida]


class DiasAlerta(BaseModel):
    dias: int


def _dias_alerta() -> int:
    r = supabase.table("configuracion_stock").select("valor").eq("clave", "dias_alerta_retirados").execute().data
    try:
        return int(r[0]["valor"]) if r else 15
    except (ValueError, KeyError):
        return 15


@router.get("/retirados/")
def listar_retirados(usuario: dict = acceso):
    """Equipos retirados que todavía no se recibieron en la Oficina, con el ticket que los retiró."""
    equipos = _todos(lambda: supabase.table("equipos_estado")
                     .select("serial, producto_id, ubicacion_id, productos(codigo, descripcion), ubicaciones(nombre)")
                     .eq("estado", "RETIRADO_PENDIENTE").is_("recibido_en", "null"))
    retiros = {}
    for m in _todos(lambda: supabase.table("movimientos").select("serial, fecha, ticket_id, created_at")
                    .eq("tipo", "RETIRO").order("created_at", desc=True)):
        if m["serial"]:
            retiros.setdefault(m["serial"], m)
    tickets = {t["id"]: t for t in _todos(lambda: supabase.table("tickets_importados").select("id, ticket_numero, distrito, fila_excel"))}
    hoy = date.today()
    salida = []
    for e in equipos:
        m = retiros.get(e["serial"], {})
        t = tickets.get(m.get("ticket_id"), {})
        fila = t.get("fila_excel") or {}
        fecha = m.get("fecha")
        dias = (hoy - date.fromisoformat(fecha)).days if fecha else None
        salida.append({
            "serial": e["serial"],
            "producto_id": e["producto_id"],
            "modelo": (e.get("productos") or {}).get("descripcion"),
            "codigo": ((e.get("productos") or {}).get("codigo") or "").strip(),
            "ubicacion_id": e["ubicacion_id"],
            "ubicacion": (e.get("ubicaciones") or {}).get("nombre"),
            "ticket_numero": t.get("ticket_numero"),
            "cliente": t.get("distrito"),
            "descripcion": fila.get("descripcion") if isinstance(fila, dict) else None,
            "fecha": fecha,
            "dias": dias,
        })
    salida.sort(key=lambda r: -(r["dias"] if r["dias"] is not None else -1))
    return {"dias_alerta": _dias_alerta(), "retirados": salida}


@router.post("/retirados/{serial}/recibir/")
def recibir_retirado(serial: str, data: RecepcionCreate, usuario: dict = acceso):
    oficina = supabase.table("ubicaciones").select("id").eq("tipo", "oficina").limit(1).execute().data
    if not oficina:
        raise HTTPException(status_code=400, detail="No hay una ubicación de tipo oficina")
    eq = supabase.table("equipos_estado").select("serial").eq("serial", serial).execute().data
    if not eq:
        raise HTTPException(status_code=404, detail="Equipo no encontrado")
    ticket = None
    m = supabase.table("movimientos").select("ticket_id").eq("tipo", "RETIRO").eq("serial", serial) \
        .order("created_at", desc=True).limit(1).execute().data
    if m and m[0].get("ticket_id"):
        t = supabase.table("tickets_importados").select("ticket_numero").eq("id", m[0]["ticket_id"]).execute().data
        ticket = t[0]["ticket_numero"] if t else None
    try:
        return supabase.rpc("fn_recibir_retirado", {
            "p_serial": serial, "p_oficina": oficina[0]["id"], "p_recibido_por": usuario["nombre"],
            "p_ticket": ticket, "p_piezas": [p.model_dump() for p in data.piezas],
        }).execute().data
    except Exception as e:
        raise HTTPException(status_code=400, detail=_mensaje_de_error(e))


@router.get("/faltantes/")
def listar_faltantes(usuario: dict = acceso):
    return supabase.table("faltantes").select("id, serial, ticket_numero, pieza, creado_en, ubicaciones(nombre)") \
        .eq("resuelto", False).order("creado_en", desc=True).execute().data


@router.patch("/faltantes/{faltante_id}/resolver/")
def resolver_faltante(faltante_id: str, usuario: dict = acceso):
    r = supabase.table("faltantes").update({"resuelto": True}).eq("id", faltante_id).execute()
    if not r.data:
        raise HTTPException(status_code=404, detail="Faltante no encontrado")
    return r.data


@router.put("/retirados/dias-alerta/")
def guardar_dias_alerta(data: DiasAlerta, usuario: dict = acceso):
    if usuario.get("rol") != "admin":
        raise HTTPException(status_code=403, detail="Solo administración puede cambiar los días de alerta")
    if data.dias < 1 or data.dias > 365:
        raise HTTPException(status_code=400, detail="Los días de alerta tienen que estar entre 1 y 365")
    supabase.table("configuracion_stock").upsert({"clave": "dias_alerta_retirados", "valor": str(data.dias)}).execute()
    return {"dias": data.dias}


# ─── Códigos de La Serenísima ───────────────────────────────────────

@router.get("/mapeo-serenisima/")
def mapeo_serenisima(usuario: dict = acceso):
    """Equivalencia entre los códigos de La Serenísima y nuestros productos (Catálogos → Mapeo La Serenísima)."""
    return supabase.table("mapeo_serenisima").select("*").order("codigo_serenisima").execute().data


@router.get("/centros/stock/")
def stock_de_centros(usuario: dict = acceso):
    """Stock ahora de todos los centros de distribución, por producto, para verlos juntos con los códigos de La Serenísima."""
    try:
        centros = supabase.table("ubicaciones").select("id, nombre, localidad").eq("segmento", "cd").execute().data
    except Exception:
        centros = supabase.table("ubicaciones").select("id, nombre").eq("tipo", "cd").execute().data
    ids = {c["id"] for c in centros}
    stock = defaultdict(dict)
    for s in _todos(lambda: supabase.table("stock_actual").select("ubicacion_id, producto_id, cantidad")):
        if s["ubicacion_id"] in ids:
            stock[s["ubicacion_id"]][s["producto_id"]] = s["cantidad"]
    productos = supabase.table("productos").select("id, codigo, descripcion, categoria").neq("categoria", "Herramientas").execute().data
    return {"centros": sorted(centros, key=lambda c: c["nombre"].strip()), "stock": stock, "productos": productos}
