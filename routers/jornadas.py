from fastapi import APIRouter, HTTPException
from models.jornadas import JornadaCreate, AusenciaCreate
from database import supabase

router = APIRouter()

@router.post("/")
def cargar_jornada(data: JornadaCreate):
    existe = supabase.table("jornadas")\
        .select("id")\
        .eq("empleado_id", data.empleado_id)\
        .eq("fecha", str(data.fecha))\
        .execute()
    if existe.data:
        raise HTTPException(status_code=400, detail="Ya existe un registro para ese empleado en esa fecha")
    result = supabase.table("jornadas").insert(data.model_dump(mode="json")).execute()
    return result.data

@router.get("/")
def listar_jornadas(mes: int = None, anio: int = None, empleado_id: str = None):
    query = supabase.table("jornadas").select("*")
    if empleado_id:
        query = query.eq("empleado_id", empleado_id)
    if mes and anio:
        desde = f"{anio}-{str(mes).zfill(2)}-01"
        hasta = f"{anio}-{str(mes).zfill(2)}-31"
        query = query.gte("fecha", desde).lte("fecha", hasta)
    result = query.order("fecha", desc=True).execute()
    return result.data

@router.get("/{jornada_id}")
def obtener_jornada(jornada_id: str):
    result = supabase.table("jornadas").select("*").eq("id", jornada_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Jornada no encontrada")
    return result.data[0]

@router.delete("/{jornada_id}")
def eliminar_jornada(jornada_id: str):
    supabase.table("jornadas").delete().eq("id", jornada_id).execute()
    return {"ok": True}

@router.post("/ausencias/")
def cargar_ausencia(data: AusenciaCreate):
    result = supabase.table("ausencias").insert(data.model_dump(mode="json")).execute()
    return result.data

@router.get("/ausencias/")
def listar_ausencias(empleado_id: str = None):
    query = supabase.table("ausencias").select("*")
    if empleado_id:
        query = query.eq("empleado_id", empleado_id)
    result = query.order("fecha_desde", desc=True).execute()
    return result.data

@router.get("/reporte_cruzado/")
def reporte_cruzado(mes: int = None, anio: int = None):
    jornadas_q = supabase.table("jornadas").select("*")
    servicios_q = supabase.table("servicios").select("*")
    if mes and anio:
        desde = f"{anio}-{str(mes).zfill(2)}-01"
        hasta = f"{anio}-{str(mes).zfill(2)}-31"
        jornadas_q = jornadas_q.gte("fecha", desde).lte("fecha", hasta)
        servicios_q = servicios_q.gte("fecha", desde).lte("fecha", hasta)
    j_data = jornadas_q.execute().data
    s_data = servicios_q.execute().data
    resumen = {}
    for j in j_data:
        nombre = j["nombre"]
        if nombre not in resumen:
            resumen[nombre] = {"nombre": nombre, "dias_trabajados": 0, "horas_total": 0.0, "instalaciones": 0, "desinstalaciones": 0, "revisiones": 0}
        r = resumen[nombre]
        if j["tipo_asistencia"] in ["ACTIVO", "LLEGADA_TARDE"]:
            r["dias_trabajados"] += 1
            r["instalaciones"] += j.get("instalaciones", 0)
            r["desinstalaciones"] += j.get("desinstalaciones", 0)
            r["revisiones"] += j.get("revisiones", 0)
            if j.get("hora_entrada") and j.get("hora_salida"):
                from datetime import datetime
                try:
                    ent = datetime.strptime(j["hora_entrada"], "%H:%M")
                    sal = datetime.strptime(j["hora_salida"], "%H:%M")
                    r["horas_total"] = round(r["horas_total"] + (sal - ent).seconds / 3600, 2)
                except:
                    pass
    por_estado = {}
    por_tipo = {}
    por_cliente = {}
    for s in s_data:
        estado = s.get("estado", "")
        tipo = s.get("tipo_servicio", "")
        cliente = s.get("cliente", "")
        por_estado[estado] = por_estado.get(estado, 0) + 1
        por_tipo[tipo] = por_tipo.get(tipo, 0) + 1
        por_cliente[cliente] = por_cliente.get(cliente, 0) + 1
    return {
        "jornadas": list(resumen.values()),
        "servicios_total": len(s_data),
        "por_estado": [{"estado": k, "cantidad": v} for k, v in por_estado.items()],
        "por_tipo": [{"tipo": k, "cantidad": v} for k, v in por_tipo.items()],
        "por_cliente": [{"cliente": k, "cantidad": v} for k, v in por_cliente.items()],
    }