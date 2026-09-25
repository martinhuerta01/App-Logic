import time
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
import os
from dotenv import load_dotenv
from database import supabase

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
_bearer = HTTPBearer()

# Los datos del usuario (rol, módulos, activo) se consultan a la base y se guardan
# unos segundos para no hacer una consulta por cada pedido. Así un cambio de permisos
# o una baja de usuario se aplica en menos de un minuto, sin esperar a que venza la sesión.
_SEGUNDOS_EN_MEMORIA = 60
_usuarios_en_memoria: dict[str, tuple[float, dict | None]] = {}


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
) -> str:
    """
    Valida el Bearer token en cada request protegido.
    Retorna el nombre de usuario extraído del payload.
    Lanza 401 si el token es inválido o expiró.
    """
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user: str = payload.get("sub")
        if user is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expirado")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")


def invalidar_usuario_en_memoria(nombre: str | None = None) -> None:
    """Fuerza a volver a leer los permisos (todos o los de un usuario) en el próximo pedido."""
    if nombre is None:
        _usuarios_en_memoria.clear()
    else:
        _usuarios_en_memoria.pop(nombre, None)


def get_usuario_actual(nombre: str = Depends(get_current_user)) -> dict:
    """Devuelve rol, módulos y estado del usuario de la sesión. 401 si fue dado de baja."""
    ahora = time.time()
    guardado = _usuarios_en_memoria.get(nombre)
    if guardado and ahora - guardado[0] < _SEGUNDOS_EN_MEMORIA:
        usuario = guardado[1]
    else:
        res = supabase.table("usuarios").select("nombre, rol, modulos, activo").eq("nombre", nombre).execute()
        usuario = res.data[0] if res.data else None
        _usuarios_en_memoria[nombre] = (ahora, usuario)

    if not usuario or not usuario.get("activo"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario inactivo o inexistente")
    return usuario


def requiere_admin(usuario: dict = Depends(get_usuario_actual)) -> dict:
    if usuario.get("rol") != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Solo administración puede hacer esto")
    return usuario


def requiere_modulo(*claves: str):
    """
    Deja pasar a administración y a quien tenga alguno de los módulos indicados.
    Un usuario con módulos vacíos (null) no tiene restricción, igual que en el menú.
    """
    def _verificar(usuario: dict = Depends(get_usuario_actual)) -> dict:
        modulos = usuario.get("modulos")
        if usuario.get("rol") == "admin" or modulos is None or any(c in modulos for c in claves):
            return usuario
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tenés permiso para este módulo")
    return _verificar
