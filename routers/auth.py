from fastapi import APIRouter, HTTPException, Request
from models.auth import LoginRequest, TokenResponse
from database import supabase
import jwt
import bcrypt
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from slowapi import Limiter
from slowapi.util import get_remote_address

load_dotenv()

router = APIRouter()
SECRET_KEY = os.getenv("SECRET_KEY")
limiter = Limiter(key_func=get_remote_address)

def crear_token(usuario: str) -> str:
    payload = {
        "sub": usuario,
        "exp": datetime.utcnow() + timedelta(hours=12)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute")
def login(request: Request, data: LoginRequest):
    resultado = supabase.table("usuarios") \
        .select("*") \
        .eq("nombre", data.usuario) \
        .eq("activo", True) \
        .execute()

    if not resultado.data:
        raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos")

    usuario_db = resultado.data[0]
    password_hash = usuario_db.get("password", "")

    if not bcrypt.checkpw(data.password.encode("utf-8"), password_hash.encode("utf-8")):
        raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos")

    token = crear_token(data.usuario)
    return TokenResponse(
        access_token=token,
        usuario=data.usuario,
        rol=usuario_db.get("rol", "usuario"),
        modulos=usuario_db.get("modulos", None),
        submodulos=usuario_db.get("submodulos", None),
    )

