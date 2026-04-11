from fastapi import APIRouter
from database import supabase
from datetime import datetime, timedelta
import calendar

router = APIRouter()

JORNADA_HS = 8  # horas base por día

def rango_fechas(mes, anio):
    anio = int(anio or datetime.now().year)
    mes = int(mes or datetime.now().month)
    desde = f"{anio}-{str(mes).zfill(2)}-01"
    ultimo_dia = calendar.monthrange(anio, mes)[1]
    hasta = f"{anio}-{str(mes).zfill(2)}-{ultimo_dia}"
    return desde, hasta, mes, anio

def calcular_minutos(hora_salida: str, hora_llegada: str) -> int:
    if not hora_salida or not hora_llegada:
        return 0
    try:
        fmt = "%H:%M:%S" if len(hora_salida) > 5 else "%H:%M"
        t1 = datetime.strptime(hora_salida[:8], fmt if len(hora_salida) > 5 else "%H:%M")
        t2 = datetime.strptime(hora_llegada[:8], fmt if len(hora_llegada) > 5 else "%H:%M")
        delta = t2 - t1
        return max(0, int(delta.total_seconds() // 60))
    except:
        return 0

# ─── 1. HORAS TRABAJADAS ──────────────────────────────────────────────

@router.get("/horas")
def horas_trabajadas(mes: int = None, anio: int = None, equipo_id: str = None):
    desde, hasta, mes, anio = rango_fechas(mes, anio)

    query = supabase.table("movimientos_camioneta")\
        .select("*, equipos(nombre, patente), tecnicos_jornada(*, empleados(nombre, equipo_id))")\
        .gte("fecha", desde).lte("fecha", hasta)
    if equipo_id:
        query = query.eq("equipo_id", equipo_id)
    movimientos = query.order("fecha").execute().data

    # Obtener nombres de equipos
    equipos_data = supabase.table("equipos").select("id, nombre").execute().data
    equipos_map = {e["id"]: e["nombre"] for e in equipos_data}

    tecnicos_map = {}
    for mov in movimientos:
        minutos = calcular_minutos(mov.get("hora_salida"), mov.get("hora_llegada"))
        equipo_nombre = (mov.get("equipos") or {}).get("nombre", "")
        for tj in (mov.get("tecnicos_jornada") or []):
            tecnico_id = tj["tecnico_id"]
            emp = tj.get("empleados") or {}
            nombre = emp.get("nombre", "?")
            eq_id = emp.get("equipo_id") or mov.get("equipo_id")
            if tecnico_id not in tecnicos_map:
                tecnicos_map[tecnico_id] = {
                    "nombre": nombre,
                    "equipo": equipos_map.get(eq_id, equipo_nombre),
                    "equipo_id": eq_id,
                    "dias": 0, "minutos": 0, "ausencias": []
                }
            if tj.get("presente", True):
                tecnicos_map[tecnico_id]["dias"] += 1
                tecnicos_map[tecnico_id]["minutos"] += minutos
            else:
                tecnicos_map[tecnico_id]["ausencias"].append({
                    "fecha": mov["fecha"],
                    "motivo": tj.get("motivo_ausencia", "")
                })

    resultado = []
    for tid, d in tecnicos_map.items():
        horas = round(d["minutos"] / 60, 1)
        horas_base = d["dias"] * JORNADA_HS
        balance = round(horas - horas_base, 1)
        resultado.append({
            "tecnico_id": tid,
            "nombre": d["nombre"],
            "equipo": d["equipo"],
            "equipo_id": d["equipo_id"],
            "dias_presentes": d["dias"],
            "horas_trabajadas": horas,
            "horas_base": horas_base,
            "balance": balance,
            "ausencias": d["ausencias"]
        })

    return {"mes": mes, "anio": anio, "tecnicos": resultado}

# ─── 2. SERVICIOS POR RESPONSABLE ─────────────────────────────────────

@router.get("/servicios-responsable")
def servicios_por_responsable(
    responsable: str = None,
    mes: int = None,
    anio: int = None,
    periodo: str = "mes"  # semana | mes | anio
):
    desde, hasta, mes, anio = rango_fechas(mes, anio)

    query = supabase.table("servicios")\
        .select("*")\
        .gte("fecha", desde).lte("fecha", hasta)\
        .eq("estado", "REALIZADO")
    if responsable:
        query = query.eq("responsable", responsable)
    servicios = query.order("fecha").execute().data

    # Agrupar por responsable
    por_responsable = {}
    for s in servicios:
        resp = s.get("responsable") or "Sin asignar"
        if resp not in por_responsable:
            por_responsable[resp] = {"total": 0, "INSTALACION": 0, "REVISION": 0, "DESINSTALACION": 0}
        por_responsable[resp]["total"] += 1
        tipo = s.get("tipo_servicio", "")
        if tipo in por_responsable[resp]:
            por_responsable[resp][tipo] += 1

    # Convertir a lista
    resultado = []
    for resp, datos in sorted(por_responsable.items()):
        resultado.append({
            "responsable": resp,
            "total": datos["total"],
            "instalaciones": datos["INSTALACION"],
            "revisiones": datos["REVISION"],
            "desinstalaciones": datos["DESINSTALACION"],
        })

    total_general = sum(r["total"] for r in resultado)

    return {
        "mes": mes, "anio": anio,
        "total_general": total_general,
        "responsables": resultado,
        "servicios": servicios
    }

# ─── 3. SERVICIOS POR CLIENTE ─────────────────────────────────────────

@router.get("/servicios-cliente")
def servicios_por_cliente(cliente: str = None, mes: int = None, anio: int = None):
    desde, hasta, mes, anio = rango_fechas(mes, anio)

    query = supabase.table("servicios")\
        .select("*")\
        .gte("fecha", desde).lte("fecha", hasta)
    if cliente:
        query = query.ilike("cliente", f"%{cliente}%")
    servicios = query.order("fecha").execute().data

    # Agrupar por cliente
    por_cliente = {}
    for s in servicios:
        cl = s.get("cliente", "Sin cliente")
        if cl not in por_cliente:
            por_cliente[cl] = {"total": 0, "INSTALACION": 0, "REVISION": 0, "DESINSTALACION": 0}
        por_cliente[cl]["total"] += 1
        tipo = s.get("tipo_servicio", "")
        if tipo in por_cliente[cl]:
            por_cliente[cl][tipo] += 1

    clientes_resultado = []
    for cl, datos in sorted(por_cliente.items()):
        clientes_resultado.append({
            "cliente": cl,
            "total": datos["total"],
            "instalaciones": datos["INSTALACION"],
            "revisiones": datos["REVISION"],
            "desinstalaciones": datos["DESINSTALACION"],
        })

    resumen = {
        "total": sum(c["total"] for c in clientes_resultado),
        "instalaciones": sum(c["instalaciones"] for c in clientes_resultado),
        "revisiones": sum(c["revisiones"] for c in clientes_resultado),
        "desinstalaciones": sum(c["desinstalaciones"] for c in clientes_resultado),
    }

    return {
        "mes": mes, "anio": anio,
        "resumen": resumen,
        "clientes": clientes_resultado,
        "servicios": servicios
    }

# ─── 4. REPORTE CRUZADO ───────────────────────────────────────────────

@router.get("/reporte-cruzado")
def reporte_cruzado(mes: int = None, anio: int = None):
    """Productividad: Horas vs Servicios por equipo"""
    desde, hasta, mes, anio = rango_fechas(mes, anio)

    horas = horas_trabajadas(mes=mes, anio=anio)

    servicios_data = supabase.table("servicios")\
        .select("equipo_id, responsable, tipo_servicio, estado")\
        .gte("fecha", desde).lte("fecha", hasta)\
        .eq("estado", "REALIZADO").execute().data

    # Contar servicios por equipo_id
    servicios_por_equipo = {}
    for s in servicios_data:
        eid = s.get("equipo_id")
        if eid:
            servicios_por_equipo[eid] = servicios_por_equipo.get(eid, 0) + 1

    tecnicos = horas.get("tecnicos", [])
    for t in tecnicos:
        eq_id = t.get("equipo_id")
        t["servicios_realizados"] = servicios_por_equipo.get(eq_id, 0)
        dias = t["dias_presentes"]
        t["servicios_por_dia"] = round(t["servicios_realizados"] / dias, 1) if dias > 0 else 0

    return {"mes": mes, "anio": anio, "tecnicos": tecnicos}

@router.get("/cliente-vs-responsable")
def cliente_vs_responsable(mes: int = None, anio: int = None):
    """Cuántos servicios hizo cada cliente con cada responsable"""
    desde, hasta, mes, anio = rango_fechas(mes, anio)

    servicios = supabase.table("servicios")\
        .select("cliente, responsable, tipo_servicio, estado")\
        .gte("fecha", desde).lte("fecha", hasta)\
        .eq("estado", "REALIZADO").execute().data

    cruce = {}
    for s in servicios:
        cl = s.get("cliente", "Sin cliente")
        resp = s.get("responsable") or "Sin asignar"
        key = f"{cl}||{resp}"
        if key not in cruce:
            cruce[key] = {"cliente": cl, "responsable": resp, "total": 0,
                          "INSTALACION": 0, "REVISION": 0, "DESINSTALACION": 0}
        cruce[key]["total"] += 1
        tipo = s.get("tipo_servicio", "")
        if tipo in cruce[key]:
            cruce[key][tipo] += 1

    resultado = sorted(cruce.values(), key=lambda x: (x["cliente"], x["responsable"]))
    return {"mes": mes, "anio": anio, "datos": resultado}
