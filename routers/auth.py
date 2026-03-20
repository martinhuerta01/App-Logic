from fastapi import APIRouter, HTTPException
from models.auth import LoginRequest, TokenResponse
from database import supabase
import jwt
import bcrypt
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()
SECRET_KEY = os.getenv("SECRET_KEY")

def crear_token(usuario: str) -> str:
    payload = {
        "sub": usuario,
        "exp": datetime.utcnow() + timedelta(hours=12)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest):
    resultado = supabase.table("usuarios") \
        .select("*") \
        .eq("nombre", data.usuario) \
        .execute()

    if not resultado.data:
        raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos")

    usuario_db = resultado.data[0]
    password_hash = usuario_db.get("password", "")

    if not bcrypt.checkpw(data.password.encode("utf-8"), password_hash.encode("utf-8")):
        raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos")

    token = crear_token(data.usuario)
    return TokenResponse(access_token=token, usuario=data.usuario)


@router.post("/hash")
def generar_hash(data: LoginRequest):
    """Endpoint temporal para generar el hash de una password. Eliminarlo después del deploy."""
    hashed = bcrypt.hashpw(data.password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    return {"hash": hashed}