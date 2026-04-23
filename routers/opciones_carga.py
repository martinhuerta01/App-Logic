from fastapi import APIRouter
from database import supabase

router = APIRouter()

DEFAULTS = {
    "tipos":        ["INSTALACION", "REVISION", "DESINSTALACION"],
    "dispositivos": ["GPS", "LECTORA", "GPS Y LECTORA", "CAMARA", "TRACTOR", "SEMI", "CHASIS"],
    "estados":      ["PENDIENTE", "CONFIRMADO", "REALIZADO", "SUSPENDIDO"],
}

@router.get("/")
def get_opciones():
    result = {}
    for campo, default in DEFAULTS.items():
        row = supabase.table("configuracion_opciones").select("valor").eq("clave", campo).execute()
        if row.data:
            result[campo] = row.data[0]["valor"]
        else:
            supabase.table("configuracion_opciones").insert({"clave": campo, "valor": default}).execute()
            result[campo] = default
    return result

@router.put("/")
def update_opciones(data: dict):
    for campo in ["tipos", "dispositivos", "estados"]:
        if campo in data:
            supabase.table("configuracion_opciones").upsert({"clave": campo, "valor": data[campo]}).execute()
    return {"ok": True}
