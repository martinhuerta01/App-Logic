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


class CorreccionStock(BaseModel):
    producto_id: str
    cantidad: int
    motivo: Optional[str] = None
    fecha: Optional[date] = None


@router.post("/ubicaciones/{ubicacion_id}/corregir/")
def corregir_stock(ubicacion_id: str, data: CorreccionStock, usuario: dict = acceso):
    """Corrige la cantidad de un producto en una ubicación y deja la diferencia registrada como ajuste."""
    try:
        res = supabase.rpc("fn_corregir_stock", {
            "p_ubicacion": ubicacion_id, "p_producto": data.producto_id, "p_nuevo": data.cantidad,
            "p_motivo": data.motivo, "p_por": usuario["nombre"], "p_fecha": (data.fecha or date.today()).isoformat(),
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


# ─── Dashboard ──────────────────────────────────────────────────────

VENTANA_CONSUMO_DIAS = 90  # el consumo diario se promedia sobre los últimos 90 días
CLAVES_DE_ALERTA = {"dias_alerta_retirados": 15, "dias_alerta_conteo": 30}


class MinimoOficina(BaseModel):
    producto_id: str
    cantidad_minima: Optional[int] = None  # None quita el mínimo


class AlertaConfig(BaseModel):
    clave: str
    dias: int


def _config_dias(clave: str) -> int:
    try:
        r = supabase.table("configuracion_stock").select("valor").eq("clave", clave).execute().data
        return int(r[0]["valor"]) if r else CLAVES_DE_ALERTA[clave]
    except Exception:
        return CLAVES_DE_ALERTA[clave]


@router.get("/dashboard/")
def dashboard(usuario: dict = acceso):
    hoy = date.today()
    ubicaciones = listar_ubicaciones(usuario)
    oficina = next((u for u in ubicaciones if u["tipo"] == "oficina"), None)

    # Reposición de la Oficina: cuánto hay, el mínimo y cuánto se consume por día (tickets y salidas sin destino)
    desde = (hoy.toordinal() - VENTANA_CONSUMO_DIAS)
    desde_iso = date.fromordinal(desde).isoformat()
    consumo = defaultdict(int)
    for m in _todos(lambda: supabase.table("movimientos").select("producto_id, cantidad")
                    .in_("tipo", ["INSTALACION", "SALIDA"]).is_("destino_id", "null").gte("fecha", desde_iso)):
        consumo[m["producto_id"]] += m["cantidad"]

    stock_oficina = {}
    if oficina:
        stock_oficina = {s["producto_id"]: s["cantidad"] for s in
                         supabase.table("stock_actual").select("producto_id, cantidad").eq("ubicacion_id", oficina["id"]).execute().data}
    try:
        minimos = {m["producto_id"]: m["cantidad_minima"] for m in
                   supabase.table("stock_minimo").select("producto_id, cantidad_minima").eq("ambito", "oficina").execute().data}
    except Exception:
        minimos = {}

    productos = supabase.table("productos").select("id, codigo, descripcion, categoria, plazo_entrega_dias") \
        .eq("activo", True).neq("categoria", "Herramientas").order("codigo").execute().data
    reposicion = []
    for p in productos:
        pid = p["id"]
        stock = stock_oficina.get(pid, 0)
        total = consumo.get(pid, 0)
        if stock == 0 and total == 0 and pid not in minimos:
            continue
        por_dia = round(total / VENTANA_CONSUMO_DIAS, 2)
        dias = int(stock / por_dia) if por_dia > 0 and stock > 0 else (0 if por_dia > 0 else None)
        plazo = p.get("plazo_entrega_dias") if p.get("plazo_entrega_dias") is not None else 3
        pedir_el = date.fromordinal(hoy.toordinal() + max(0, dias - plazo)).isoformat() if dias is not None else None
        reposicion.append({
            "producto_id": pid, "codigo": (p["codigo"] or "").strip(), "descripcion": p["descripcion"], "categoria": p["categoria"],
            "stock": stock, "minimo": minimos.get(pid), "consumo_90_dias": total, "consumo_por_dia": por_dia,
            "dias_de_stock": dias, "plazo_entrega_dias": plazo, "pedir_el": pedir_el,
        })

    # Consumo de los últimos 6 meses por categoría (para el gráfico)
    primer_mes = date(hoy.year, hoy.month, 1)
    meses = []
    y, m = hoy.year, hoy.month
    for _ in range(6):
        meses.append(f"{y}-{m:02d}")
        m -= 1
        if m == 0:
            y, m = y - 1, 12
    meses.reverse()
    desde_6 = f"{meses[0]}-01"
    categoria_de = {p["id"]: p["categoria"] for p in productos}
    por_mes = {mes: defaultdict(int) for mes in meses}
    for mov in _todos(lambda: supabase.table("movimientos").select("producto_id, cantidad, fecha")
                      .in_("tipo", ["INSTALACION", "SALIDA"]).is_("destino_id", "null").gte("fecha", desde_6)):
        cat = categoria_de.get(mov["producto_id"])
        if cat and mov["fecha"][:7] in por_mes:
            por_mes[mov["fecha"][:7]][cat] += mov["cantidad"]
    consumo_mensual = [{"mes": mes, **{c: por_mes[mes].get(c, 0) for c in ("Dispositivos", "Cables", "Accesorios", "Insumos")}} for mes in meses]

    # Retirados y faltantes
    retirados = listar_retirados(usuario)
    dias_retirados = retirados["dias_alerta"]
    atrasados = sum(1 for r in retirados["retirados"] if (r["dias"] or 0) > dias_retirados)
    faltantes = supabase.table("faltantes").select("id").eq("resuelto", False).execute().data
    tramos = [("Hasta 7 días", 0, 7), ("8 a 15 días", 8, 15), ("16 a 30 días", 16, 30), ("31 a 60 días", 31, 60), ("Más de 60 días", 61, 10**6)]
    edades = [{"tramo": nombre, "cantidad": sum(1 for r in retirados["retirados"] if r["dias"] is not None and desde_d <= r["dias"] <= hasta_d)}
              for nombre, desde_d, hasta_d in tramos]
    edades.append({"tramo": "Sin fecha", "cantidad": sum(1 for r in retirados["retirados"] if r["dias"] is None)})

    return {
        "hoy": hoy.isoformat(),
        "ventana_dias": VENTANA_CONSUMO_DIAS,
        "ubicaciones": ubicaciones,
        "reposicion": reposicion,
        "retirados": {"pendientes": len(retirados["retirados"]), "atrasados": atrasados, "dias_alerta": dias_retirados},
        "retirados_por_edad": edades,
        "consumo_mensual": consumo_mensual,
        "faltantes": len(faltantes),
        "dias_alerta_conteo": _config_dias("dias_alerta_conteo"),
    }


@router.put("/minimos/")
def guardar_minimo_oficina(data: MinimoOficina, usuario: dict = acceso):
    if data.cantidad_minima is None:
        supabase.table("stock_minimo").delete().eq("producto_id", data.producto_id).eq("ambito", "oficina").execute()
        return {"ok": True}
    if data.cantidad_minima < 0:
        raise HTTPException(status_code=400, detail="El mínimo no puede ser negativo")
    existente = supabase.table("stock_minimo").select("id").eq("producto_id", data.producto_id).eq("ambito", "oficina").execute().data
    if existente:
        supabase.table("stock_minimo").update({"cantidad_minima": data.cantidad_minima}).eq("id", existente[0]["id"]).execute()
    else:
        supabase.table("stock_minimo").insert({"producto_id": data.producto_id, "ambito": "oficina", "cantidad_minima": data.cantidad_minima}).execute()
    return {"ok": True}


@router.put("/alertas/")
def guardar_alerta(data: AlertaConfig, usuario: dict = acceso):
    if usuario.get("rol") != "admin":
        raise HTTPException(status_code=403, detail="Solo administración puede cambiar los días de alerta")
    if data.clave not in CLAVES_DE_ALERTA:
        raise HTTPException(status_code=400, detail="Alerta desconocida")
    if data.dias < 1 or data.dias > 365:
        raise HTTPException(status_code=400, detail="Los días de alerta tienen que estar entre 1 y 365")
    supabase.table("configuracion_stock").upsert({"clave": data.clave, "valor": str(data.dias)}).execute()
    return {"clave": data.clave, "dias": data.dias}


# ─── Equipos por número de serie: edición completa y borrado ────────

ESTADOS_EQUIPO = {"EN_STOCK", "INSTALADO", "RETIRADO_PENDIENTE", "USADO_OK_CAMPO", "USADO_OK_OFICINA", "FALLA_RMA", "BAJA"}


class EquipoEditar(BaseModel):
    serial: str
    producto_id: str
    estado: str
    ubicacion_id: Optional[str] = None
    patente: Optional[str] = None
    configuracion: Optional[str] = None
    cliente: Optional[str] = None


@router.put("/equipos/{equipo_id}")
def editar_equipo(equipo_id: str, data: EquipoEditar, usuario: dict = acceso):
    """Corrige todos los datos de un equipo (serie, modelo, estado, ubicación, patente, configuración y cliente)."""
    actual = supabase.table("equipos_estado").select("id, serial").eq("id", equipo_id).execute().data
    if not actual:
        raise HTTPException(status_code=404, detail="Equipo no encontrado")
    serial = data.serial.strip()
    if not serial:
        raise HTTPException(status_code=400, detail="El número de serie no puede quedar vacío")
    if data.estado not in ESTADOS_EQUIPO:
        raise HTTPException(status_code=400, detail="Estado inválido")
    producto = supabase.table("productos").select("id, categoria").eq("id", data.producto_id).execute().data
    if not producto or producto[0]["categoria"] != "Dispositivos":
        raise HTTPException(status_code=400, detail="El modelo tiene que ser un producto de la categoría Dispositivos")
    otro = supabase.table("equipos_estado").select("id").eq("serial", serial).neq("id", equipo_id).execute().data
    if otro:
        raise HTTPException(status_code=400, detail=f"Ya existe otro equipo con el número de serie {serial}")
    if data.ubicacion_id and not supabase.table("ubicaciones").select("id").eq("id", data.ubicacion_id).execute().data:
        raise HTTPException(status_code=400, detail="La ubicación no existe")
    limpio = lambda v: (v or "").strip() or None
    cambios = {
        "serial": serial, "producto_id": data.producto_id, "estado": data.estado,
        "ubicacion_id": data.ubicacion_id or None,
        "patente": (limpio(data.patente) or "").upper().replace(" ", "") or None,
        "configuracion": limpio(data.configuracion), "cliente": limpio(data.cliente),
        "updated_at": datetime.now().astimezone().isoformat(),
    }
    return supabase.table("equipos_estado").update(cambios).eq("id", equipo_id).execute().data


@router.delete("/equipos/{equipo_id}")
def eliminar_equipo(equipo_id: str, usuario: dict = acceso):
    """Borra un equipo de la lista. Los movimientos con su número de serie quedan en el historial."""
    if usuario.get("rol") != "admin":
        raise HTTPException(status_code=403, detail="Solo administración puede eliminar equipos")
    r = supabase.table("equipos_estado").delete().eq("id", equipo_id).execute().data
    if not r:
        raise HTTPException(status_code=404, detail="Equipo no encontrado")
    return {"ok": True, "serial": r[0]["serial"]}
