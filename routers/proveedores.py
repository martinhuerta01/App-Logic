from fastapi import APIRouter, HTTPException
from models.proveedores import ProveedorCreate, ProveedorUpdate
from database import supabase

router = APIRouter()

@router.get("/")
def listar_proveedores():
    result = supabase.table("proveedores").select("*").eq("activo", True).execute()
    return result.data

@router.post("/")
def crear_proveedor(data: ProveedorCreate):
    result = supabase.table("proveedores").insert(data.model_dump()).execute()
    return result.data

@router.put("/{proveedor_id}")
def actualizar_proveedor(proveedor_id: str, data: ProveedorUpdate):
    result = supabase.table("proveedores")\
        .update(data.model_dump(exclude_none=True))\
        .eq("id", proveedor_id).execute()
    return result.data

@router.delete("/{proveedor_id}")
def eliminar_proveedor(proveedor_id: str):
    supabase.table("proveedores")\
        .update({"activo": False})\
        .eq("id", proveedor_id).execute()
    return {"ok": True}