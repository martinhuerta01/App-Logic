from fastapi import APIRouter, HTTPException
from models.jornadas import JornadaCreate, AusenciaCreate
from database import supabase

router = APIRouter()

@router.post("/")
def cargar_jornada(data: JornadaCreate):
    # Verificar si ya existe registro para ese empleado en esa fecha
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

# Ausencias
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