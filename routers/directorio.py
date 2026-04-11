from fastapi import APIRouter
from models.directorio import DirectorioCreate, DirectorioUpdate, SubresponsableCreate
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

@router.get("/{entrada_id}/subresponsables")
def listar_subresponsables(entrada_id: str):
    result = supabase.table("subresponsables")\
        .select("*").eq("contacto_id", entrada_id).order("nombre").execute()
    return result.data

@router.post("/")
def crear_entrada(data: DirectorioCreate):
    result = supabase.table("empleados").insert(data.model_dump(exclude_none=True)).execute()
    return result.data

@router.post("/subresponsable")
def crear_subresponsable(data: SubresponsableCreate):
    result = supabase.table("subresponsables").insert(data.model_dump(exclude_none=True)).execute()
    return result.data

@router.put("/{entrada_id}")
def actualizar_entrada(entrada_id: str, data: DirectorioUpdate):
    result = supabase.table("empleados")\
        .update(data.model_dump(exclude_none=True))\
        .eq("id", entrada_id).execute()
    return result.data

@router.delete("/subresponsable/{sub_id}")
def eliminar_subresponsable(sub_id: str):
    supabase.table("subresponsables").delete().eq("id", sub_id).execute()
    return {"ok": True}

@router.delete("/{entrada_id}")
def eliminar_entrada(entrada_id: str):
    supabase.table("empleados").update({"activo": False}).eq("id", entrada_id).execute()
    return {"ok": True}
