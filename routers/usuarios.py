from fastapi import APIRouter, HTTPException
from database import supabase
from pydantic import BaseModel
from typing import Optional
import bcrypt

router = APIRouter()

class UsuarioCreate(BaseModel):
    nombre: str
    password: str
    rol: str = "usuario"
    modulos: Optional[list[str]] = None

class UsuarioUpdate(BaseModel):
    rol:      Optional[str]       = None
    modulos:  Optional[list[str]] = None
    activo:   Optional[bool]      = None
    password: Optional[str]       = None

@router.get("/")
def listar_usuarios():
    res = supabase.table("usuarios").select("id, nombre, rol, modulos, activo").execute()
    return res.data

@router.post("/")
def crear_usuario(data: UsuarioCreate):
    existe = supabase.table("usuarios").select("id").eq("nombre", data.nombre).execute()
    if existe.data:
        raise HTTPException(status_code=400, detail="Ya existe un usuario con ese nombre")
    hashed = bcrypt.hashpw(data.password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    res = supabase.table("usuarios").insert({
        "nombre": data.nombre, "password": hashed,
        "rol": data.rol, "modulos": data.modulos, "activo": True,
    }).execute()
    return res.data[0]

@router.put("/{usuario_id}")
def actualizar_usuario(usuario_id: int, data: UsuarioUpdate):
    updates = {}
    if data.rol      is not None: updates["rol"]     = data.rol
    if data.modulos  is not None: updates["modulos"] = data.modulos
    if data.activo   is not None: updates["activo"]  = data.activo
    if data.password:
        updates["password"] = bcrypt.hashpw(
            data.password.encode("utf-8"), bcrypt.gensalt()
        ).decode("utf-8")
    res = supabase.table("usuarios").update(updates).eq("id", usuario_id).execute()
    return res.data[0]
