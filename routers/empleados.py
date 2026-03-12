from fastapi import APIRouter
from models.empleados import EmpleadoCreate, EmpleadoUpdate
from database import supabase

router = APIRouter()

@router.get("/")
def listar_empleados():
    result = supabase.table("empleados").select("*").eq("activo", True).execute()
    return result.data

@router.post("/")
def crear_empleado(data: EmpleadoCreate):
    result = supabase.table("empleados").insert(data.model_dump()).execute()
    return result.data

@router.put("/{empleado_id}")
def actualizar_empleado(empleado_id: str, data: EmpleadoUpdate):
    result = supabase.table("empleados")\
        .update(data.model_dump(exclude_none=True))\
        .eq("id", empleado_id).execute()
    return result.data

@router.delete("/{empleado_id}")
def desactivar_empleado(empleado_id: str):
    result = supabase.table("empleados")\
        .update({"activo": False})\
        .eq("id", empleado_id).execute()
    return {"ok": True}