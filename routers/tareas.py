from fastapi import APIRouter
from models.tareas import TareaCreate, TareaUpdate, NotaCreate
from database import supabase

router = APIRouter()

@router.get("/")
def listar_tareas(estado: str = None, tipo: str = None, prioridad: str = None):
    query = supabase.table("tareas").select("*")
    if estado:
        query = query.eq("estado", estado)
    if tipo:
        query = query.eq("tipo", tipo)
    if prioridad:
        query = query.eq("prioridad", prioridad)
    result = query.order("numero", desc=True).execute()
    return result.data

@router.post("/")
def crear_tarea(data: TareaCreate):
    # Auto-número incremental
    max_res = supabase.table("tareas").select("numero").order("numero", desc=True).limit(1).execute()
    ultimo = max_res.data[0]["numero"] if max_res.data and max_res.data[0].get("numero") else 0
    body = data.model_dump(mode="json")
    body["numero"] = (ultimo or 0) + 1
    result = supabase.table("tareas").insert(body).execute()
    return result.data[0]

@router.put("/{tarea_id}")
def actualizar_tarea(tarea_id: str, data: TareaUpdate):
    result = supabase.table("tareas")\
        .update(data.model_dump(exclude_none=True, mode="json"))\
        .eq("id", tarea_id).execute()
    return result.data[0]

@router.delete("/{tarea_id}")
def eliminar_tarea(tarea_id: str):
    supabase.table("tareas").delete().eq("id", tarea_id).execute()
    return {"ok": True}


# ── Notas de ticket ───────────────────────────────────────────────────

@router.get("/{tarea_id}/notas/")
def listar_notas(tarea_id: str):
    result = supabase.table("ticket_notas")\
        .select("*").eq("ticket_id", tarea_id)\
        .order("created_at").execute()
    return result.data

@router.post("/{tarea_id}/notas/")
def crear_nota(tarea_id: str, data: NotaCreate):
    body = data.model_dump(mode="json")
    body["ticket_id"] = tarea_id
    result = supabase.table("ticket_notas").insert(body).execute()
    return result.data[0]

@router.delete("/{tarea_id}/notas/{nota_id}")
def eliminar_nota(tarea_id: str, nota_id: str):
    supabase.table("ticket_notas").delete().eq("id", nota_id).execute()
    return {"ok": True}
