from fastapi import APIRouter
from models.equipos import EquipoCreate, EquipoUpdate
from database import supabase

router = APIRouter()

@router.get("/")
def listar_equipos():
    result = supabase.table("equipos").select("*").eq("activo", True).order("nombre").execute()
    return result.data

@router.post("/")
def crear_equipo(data: EquipoCreate):
    result = supabase.table("equipos").insert(data.model_dump()).execute()
    return result.data

@router.put("/{equipo_id}")
def actualizar_equipo(equipo_id: str, data: EquipoUpdate):
    result = supabase.table("equipos").update(data.model_dump(exclude_none=True)).eq("id", equipo_id).execute()
    return result.data
