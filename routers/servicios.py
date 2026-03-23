from fastapi import APIRouter
from models.servicios import ServicioCreate, ServicioUpdate
from database import supabase

router = APIRouter()

@router.get("/")
def listar_servicios(
    cliente_ref: str = None,
    cliente: str = None,
    equipo_id: str = None,
    estado: str = None,
    mes: int = None,
    anio: int = None,
    fecha: str = None
):
    query = supabase.table("servicios").select("*, equipos(nombre, patente)")
    if cliente_ref:
        query = query.eq("cliente_ref", cliente_ref)
    if cliente:
        query = query.ilike("cliente", f"%{cliente}%")
    if equipo_id:
        query = query.eq("equipo_id", equipo_id)
    if estado:
        query = query.eq("estado", estado)
    if fecha:
        query = query.eq("fecha", fecha)
    if mes and anio:
        desde = f"{anio}-{str(mes).zfill(2)}-01"
        hasta = f"{anio}-{str(mes).zfill(2)}-31"
        query = query.gte("fecha", desde).lte("fecha", hasta)
    result = query.order("fecha", desc=True).order("hora_programada").execute()
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
