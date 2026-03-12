from fastapi import APIRouter, HTTPException
from models.terceros import TerceroCreate, TerceroUpdate
from database import supabase

router = APIRouter()

@router.get("/")
def listar_terceros():
    result = supabase.table("terceros").select("*").eq("activo", True).execute()
    return result.data

@router.post("/")
def crear_tercero(data: TerceroCreate):
    # Crear el tercero
    tercero = supabase.table("terceros").insert(data.model_dump()).execute()
    tercero_id = tercero.data[0]["id"]

    # Crear ubicacion automaticamente para su stock
    ubicacion = supabase.table("ubicaciones").insert({
        "nombre": f"{data.nombre} - {data.ciudad}",
        "tipo": "TERCERO"
    }).execute()

    return {
        "tercero": tercero.data[0],
        "ubicacion": ubicacion.data[0]
    }

@router.put("/{tercero_id}")
def actualizar_tercero(tercero_id: str, data: TerceroUpdate):
    result = supabase.table("terceros")\
        .update(data.model_dump(exclude_none=True))\
        .eq("id", tercero_id).execute()
    return result.data

@router.delete("/{tercero_id}")
def desactivar_tercero(tercero_id: str):
    supabase.table("terceros")\
        .update({"activo": False})\
        .eq("id", tercero_id).execute()
    return {"ok": True}

@router.get("/{tercero_id}/stock")
def stock_tercero(tercero_id: str):
    # Buscar la ubicacion del tercero
    tercero = supabase.table("terceros").select("nombre, ciudad").eq("id", tercero_id).execute()
    if not tercero.data:
        raise HTTPException(status_code=404, detail="Tercero no encontrado")

    t = tercero.data[0]
    ubicacion = supabase.table("ubicaciones")\
        .select("id")\
        .eq("nombre", f"{t['nombre']} - {t['ciudad']}")\
        .eq("tipo", "TERCERO")\
        .execute()

    if not ubicacion.data:
        return []

    ubicacion_id = ubicacion.data[0]["id"]
    result = supabase.table("stock_actual").select(
        "*, productos(codigo, descripcion, categoria)"
    ).eq("ubicacion_id", ubicacion_id).execute()
    return result.data