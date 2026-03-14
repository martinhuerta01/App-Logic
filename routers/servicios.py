from fastapi import APIRouter
from models.servicios import ServicioCreate, ServicioUpdate
from database import supabase

router = APIRouter()

@router.get("/")
def listar_servicios(cliente: str = None, estado: str = None, mes: int = None, anio: int = None):
    query = supabase.table("servicios").select("*")
    if cliente:
        query = query.eq("cliente", cliente)
    if estado:
        query = query.eq("estado", estado)
    if mes and anio:
        desde = f"{anio}-{str(mes).zfill(2)}-01"
        hasta = f"{anio}-{str(mes).zfill(2)}-31"
        query = query.gte("fecha", desde).lte("fecha", hasta)
    result = query.order("fecha", desc=True).execute()
    return result.data

@router.post("/")
def crear_servicio(data: ServicioCreate):
    result = supabase.table("servicios").insert(data.model_dump(mode="json")).execute()
    return result.data

@router.put("/{servicio_id}")
def actualizar_servicio(servicio_id: str, data: ServicioUpdate):
    result = supabase.table("servicios")\
        .update(data.model_dump(exclude_none=True, mode="json"))\
        .eq("id", servicio_id).execute()
    return result.data

@router.delete("/{servicio_id}")
def eliminar_servicio(servicio_id: str):
    supabase.table("servicios").delete().eq("id", servicio_id).execute()
    return {"ok": True}