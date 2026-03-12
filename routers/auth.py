from fastapi import APIRouter
router = APIRouter()

from fastapi import APIRouter, HTTPException
from models.auth import LoginRequest, TokenResponse
from database import supabase
import jwt
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
        .eq("password", data.password) \
        .execute()

    if not resultado.data:
        raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos")

    token = crear_token(data.usuario)
    return TokenResponse(access_token=token, usuario=data.usuario)