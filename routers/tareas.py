from fastapi import APIRouter
from models.tareas import TareaCreate, TareaUpdate
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
