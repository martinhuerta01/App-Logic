from fastapi import APIRouter
from models.movimientos_camioneta import MovimientoCamionetaCreate, MovimientoCamionetaUpdate
from database import supabase

router = APIRouter()

@router.get("/")
def listar_movimientos(equipo_id: str = None, mes: int = None, anio: int = None):
    query = supabase.table("movimientos_camioneta").select("*, equipos(nombre, patente)")
    if equipo_id:
        query = query.eq("equipo_id", equipo_id)
    if mes and anio:
        desde = f"{anio}-{str(mes).zfill(2)}-01"
        hasta = f"{anio}-{str(mes).zfill(2)}-31"
        query = query.gte("fecha", desde).lte("fecha", hasta)
    result = query.order("fecha", desc=True).execute()
    return result.data

@router.get("/{movimiento_id}/tecnicos")
def listar_tecnicos_jornada(movimiento_id: str):
    result = supabase.table("tecnicos_jornada")\
        .select("*, empleados(nombre)")\
        .eq("movimiento_id", movimiento_id).execute()
    return result.data

@router.post("/")
def crear_movimiento(data: MovimientoCamionetaCreate):
    tecnicos = data.tecnicos or []
    payload = data.model_dump(exclude={"tecnicos"}, mode="json")
    result = supabase.table("movimientos_camioneta").insert(payload).execute()
    movimiento_id = result.data[0]["id"]

    for t in tecnicos:
        supabase.table("tecnicos_jornada").insert({
            "movimiento_id": movimiento_id,
            "tecnico_id": t.tecnico_id,
            "presente": t.presente,
            "motivo_ausencia": t.motivo_ausencia
        }).execute()

    return result.data[0]

@router.put("/{movimiento_id}")
def actualizar_movimiento(movimiento_id: str, data: MovimientoCamionetaUpdate):
    result = supabase.table("movimientos_camioneta")\
        .update(data.model_dump(exclude_none=True, mode="json"))\
        .eq("id", movimiento_id).execute()
    return result.data

@router.delete("/{movimiento_id}")
def eliminar_movimiento(movimiento_id: str):
    supabase.table("tecnicos_jornada").delete().eq("movimiento_id", movimiento_id).execute()
    supabase.table("movimientos_camioneta").delete().eq("id", movimiento_id).execute()
    return {"ok": True}
