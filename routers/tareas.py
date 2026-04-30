from fastapi import APIRouter
from models.tareas import TareaCreate, TareaUpdate, CompletacionCreate
from database import supabase

router = APIRouter()

@router.get("/")
def listar_tareas(estado: str = None, prioridad: str = None, mes: int = None, anio: int = None):
    query = supabase.table("tareas").select("*")
    if estado:
        query = query.eq("estado", estado)
    if prioridad:
        query = query.eq("prioridad", prioridad)
    if mes and anio:
        import calendar
        ultimo_dia = calendar.monthrange(int(anio), int(mes))[1]
        desde = f"{anio}-{str(mes).zfill(2)}-01"
        hasta = f"{anio}-{str(mes).zfill(2)}-{ultimo_dia}"
        query = query.gte("fecha_vencimiento", desde).lte("fecha_vencimiento", hasta)
    result = query.order("fecha_vencimiento").execute()
    return result.data

@router.post("/")
def crear_tarea(data: TareaCreate):
    result = supabase.table("tareas").insert(data.model_dump(mode="json")).execute()
    return result.data

@router.put("/{tarea_id}")
def actualizar_tarea(tarea_id: str, data: TareaUpdate):
    result = supabase.table("tareas")\
        .update(data.model_dump(exclude_none=True, mode="json"))\
        .eq("id", tarea_id).execute()
    return result.data

@router.delete("/{tarea_id}")
def eliminar_tarea(tarea_id: str):
    supabase.table("tareas").delete().eq("id", tarea_id).execute()
    return {"ok": True}

# ── Completaciones de tareas recurrentes ──

@router.get("/completaciones/")
def listar_completaciones(tarea_id: str = None, fecha: str = None):
    query = supabase.table("tareas_completadas").select("*")
    if tarea_id:
        query = query.eq("tarea_id", tarea_id)
    if fecha:
        query = query.eq("fecha", fecha)
    result = query.execute()
    return result.data

@router.post("/completaciones/")
def crear_completacion(data: CompletacionCreate):
    result = supabase.table("tareas_completadas").insert(data.model_dump(mode="json")).execute()
    return result.data

@router.delete("/completaciones/")
def eliminar_completacion(tarea_id: str, fecha: str):
    supabase.table("tareas_completadas")\
        .delete().eq("tarea_id", tarea_id).eq("fecha", fecha).execute()
    return {"ok": True}
