from fastapi import APIRouter
from models.directorio import DirectorioCreate, DirectorioUpdate
from database import supabase

router = APIRouter()

@router.get("/")
def listar_directorio(tipo: str = None):
    query = supabase.table("empleados").select("*, equipos(nombre, patente)")
    if tipo:
        query = query.eq("tipo", tipo)
    result = query.eq("activo", True).order("nombre").execute()
    return result.data

@router.get("/tecnicos")
def listar_tecnicos():
    result = supabase.table("empleados")\
        .select("*, equipos(nombre, patente)")\
        .eq("tipo", "interno").eq("activo", True).order("nombre").execute()
    return result.data

@router.get("/interior")
def listar_interior():
    result = supabase.table("empleados")\
        .select("*")\
        .eq("tipo", "interior").eq("activo", True).order("nombre").execute()
    return result.data

@router.post("/")
def crear_entrada(data: DirectorioCreate):
    result = supabase.table("empleados").insert(data.model_dump(exclude_none=True)).execute()
    return result.data

@router.put("/{entrada_id}")
def actualizar_entrada(entrada_id: str, data: DirectorioUpdate):
    result = supabase.table("empleados")\
        .update(data.model_dump(exclude_none=True))\
        .eq("id", entrada_id).execute()
    return result.data

@router.delete("/{entrada_id}")
def eliminar_entrada(entrada_id: str):
    supabase.table("empleados").update({"activo": False}).eq("id", entrada_id).execute()
    return {"ok": True}
