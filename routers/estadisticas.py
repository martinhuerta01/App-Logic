from fastapi import APIRouter
from database import supabase
from datetime import datetime, timedelta
import calendar

router = APIRouter()

JORNADA_HS = 8  # horas base por día

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

@router.get("/horas")
def horas_trabajadas(mes: int = None, anio: int = None, equipo_id: str = None):
    anio = anio or datetime.now().year
    mes = mes or datetime.now().month
    desde = f"{anio}-{str(mes).zfill(2)}-01"
    ultimo_dia = calendar.monthrange(int(anio), int(mes))[1]
    hasta = f"{anio}-{str(mes).zfill(2)}-{ultimo_dia}"

    query = supabase.table("movimientos_camioneta")\
        .select("*, equipos(nombre, patente), tecnicos_jornada(*, empleados(nombre))")\
        .gte("fecha", desde).lte("fecha", hasta)
    if equipo_id:
        query = query.eq("equipo_id", equipo_id)
    movimientos = query.order("fecha").execute().data

    tecnicos_map = {}
    for mov in movimientos:
        minutos = calcular_minutos(mov.get("hora_salida"), mov.get("hora_llegada"))
        for tj in (mov.get("tecnicos_jornada") or []):
            tecnico_id = tj["tecnico_id"]
            nombre = tj.get("empleados", {}).get("nombre", "?")
            if tecnico_id not in tecnicos_map:
                tecnicos_map[tecnico_id] = {"nombre": nombre, "dias": 0, "minutos": 0, "ausencias": []}
            if tj.get("presente", True):
                tecnicos_map[tecnico_id]["dias"] += 1
                tecnicos_map[tecnico_id]["minutos"] += minutos
            else:
                tecnicos_map[tecnico_id]["ausencias"].append({
                    "fecha": mov["fecha"],
                    "motivo": tj.get("motivo_ausencia", "")
                })

    resultado = []
    for tid, datos in tecnicos_map.items():
        minutos_base = datos["dias"] * JORNADA_HS * 60
        diferencia = datos["minutos"] - minutos_base
        resultado.append({
            "tecnico_id": tid,
            "nombre": datos["nombre"],
            "dias_presentes": datos["dias"],
            "minutos_trabajados": datos["minutos"],
            "minutos_base": minutos_base,
            "diferencia_minutos": diferencia,
            "ausencias": datos["ausencias"]
        })

    return {"mes": mes, "anio": anio, "tecnicos": resultado, "movimientos": movimientos}

@router.get("/horas/detalle")
def detalle_horas_tecnico(tecnico_id: str, mes: int = None, anio: int = None):
    anio = anio or datetime.now().year
    mes = mes or datetime.now().month
    desde = f"{anio}-{str(mes).zfill(2)}-01"
    ultimo_dia = calendar.monthrange(int(anio), int(mes))[1]
    hasta = f"{anio}-{str(mes).zfill(2)}-{ultimo_dia}"

    jornadas = supabase.table("tecnicos_jornada")\
        .select("*, movimientos_camioneta(fecha, hora_salida, hora_llegada, punto_inicio, punto_fin, equipos(nombre))")\
        .eq("tecnico_id", tecnico_id)\
        .gte("movimientos_camioneta.fecha", desde)\
        .lte("movimientos_camioneta.fecha", hasta)\
        .execute().data

    detalle = []
    for j in jornadas:
        mov = j.get("movimientos_camioneta") or {}
        if not mov or not mov.get("fecha"):
            continue
        minutos = calcular_minutos(mov.get("hora_salida"), mov.get("hora_llegada"))
        detalle.append({
            "fecha": mov["fecha"],
            "equipo": (mov.get("equipos") or {}).get("nombre", ""),
            "hora_salida": mov.get("hora_salida"),
            "hora_llegada": mov.get("hora_llegada"),
            "punto_inicio": mov.get("punto_inicio"),
            "punto_fin": mov.get("punto_fin"),
            "presente": j.get("presente", True),
            "motivo_ausencia": j.get("motivo_ausencia"),
            "minutos_trabajados": minutos if j.get("presente", True) else 0,
            "diferencia_minutos": (minutos - JORNADA_HS * 60) if j.get("presente", True) else -JORNADA_HS * 60
        })

    return sorted(detalle, key=lambda x: x["fecha"])

@router.get("/servicios-cliente")
def servicios_por_cliente(cliente_id: str = None, mes: int = None, anio: int = None):
    anio = anio or datetime.now().year
    mes = mes or datetime.now().month
    desde = f"{anio}-{str(mes).zfill(2)}-01"
    ultimo_dia = calendar.monthrange(int(anio), int(mes))[1]
    hasta = f"{anio}-{str(mes).zfill(2)}-{ultimo_dia}"

    query = supabase.table("servicios")\
        .select("*, equipos(nombre)")\
        .gte("fecha", desde).lte("fecha", hasta)
    if cliente_id:
        query = query.eq("cliente_ref", cliente_id)
    servicios = query.order("fecha").execute().data

    resumen = {"total": 0, "INSTALACION": 0, "REVISION": 0, "DESINSTALACION": 0}
    for s in servicios:
        resumen["total"] += 1
        tipo = s.get("tipo_servicio", "")
        if tipo in resumen:
            resumen[tipo] += 1

    return {"resumen": resumen, "servicios": servicios}

@router.get("/reporte-cruzado")
def reporte_cruzado(mes: int = None, anio: int = None):
    anio = anio or datetime.now().year
    mes = mes or datetime.now().month
    desde = f"{anio}-{str(mes).zfill(2)}-01"
    ultimo_dia = calendar.monthrange(int(anio), int(mes))[1]
    hasta = f"{anio}-{str(mes).zfill(2)}-{ultimo_dia}"

    horas = horas_trabajadas(mes=mes, anio=anio)
    servicios_data = supabase.table("servicios")\
        .select("equipo_id, tipo_servicio, estado")\
        .gte("fecha", desde).lte("fecha", hasta)\
        .eq("estado", "REALIZADO").execute().data

    servicios_por_equipo = {}
    for s in servicios_data:
        eid = s.get("equipo_id")
        if eid:
            servicios_por_equipo[eid] = servicios_por_equipo.get(eid, 0) + 1

    tecnicos = horas.get("tecnicos", [])
    for t in tecnicos:
        t["servicios_realizados"] = servicios_por_equipo.get(t.get("equipo_id"), 0)
        dias = t["dias_presentes"]
        t["servicios_por_dia"] = round(t["servicios_realizados"] / dias, 1) if dias > 0 else 0

    return {"mes": mes, "anio": anio, "tecnicos": tecnicos}
