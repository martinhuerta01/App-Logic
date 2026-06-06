from fastapi import APIRouter, HTTPException, Depends
from database import supabase
from pydantic import BaseModel
from typing import Optional
import bcrypt
from auth_middleware import get_current_user

router = APIRouter(dependencies=[Depends(get_current_user)])

from pydantic import Field

class UsuarioCreate(BaseModel):
    nombre: str = Field(..., max_length=100)
    password: str = Field(..., max_length=200)
    rol: str = "usuario"
    modulos: Optional[list[str]] = None
    submodulos: Optional[dict] = None

class UsuarioUpdate(BaseModel):
    rol:        Optional[str]       = None
    modulos:    Optional[list[str]] = None
    submodulos: Optional[dict]      = None
    activo:     Optional[bool]      = None
    password:   Optional[str]       = Field(None, max_length=200)

@router.get("/")
def listar_usuarios():
    res = supabase.table("usuarios").select("id, nombre, rol, modulos, submodulos, activo").execute()
    return res.data

@router.post("/")
def crear_usuario(data: UsuarioCreate):
    existe = supabase.table("usuarios").select("id").eq("nombre", data.nombre).execute()
    if existe.data:
        raise HTTPException(status_code=400, detail="Ya existe un usuario con ese nombre")
    hashed = bcrypt.hashpw(data.password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    res = supabase.table("usuarios").insert({
        "nombre": data.nombre, "password": hashed,
        "rol": data.rol, "modulos": data.modulos,
        "submodulos": data.submodulos, "activo": True,
    }).execute()
    return res.data[0]

@router.put("/{usuario_id}")
def actualizar_usuario(usuario_id: str, data: UsuarioUpdate):
    updates = {}
    if data.rol        is not None: updates["rol"]        = data.rol
    if data.modulos    is not None: updates["modulos"]    = data.modulos
    if data.submodulos is not None: updates["submodulos"] = data.submodulos
    if data.activo     is not None: updates["activo"]     = data.activo
    if data.password:
        updates["password"] = bcrypt.hashpw(
            data.password.encode("utf-8"), bcrypt.gensalt()
        ).decode("utf-8")
    res = supabase.table("usuarios").update(updates).eq("id", usuario_id).execute()
    return res.data[0]
