from fastapi import APIRouter, HTTPException, Depends
from models.stock import (
    MapeoTallerCreate, MapeoTallerUpdate,
    RecetaItemCreate, RecetaItemUpdate,
    TicketConfirmarItem,
)
from database import supabase
from auth_middleware import get_current_user

router = APIRouter(dependencies=[Depends(get_current_user)])


# ─── MAPEO DE TALLERES (localidad -> CD, para el import de tickets) ────

@router.get("/mapeo-talleres/")
def listar_mapeo_talleres():
    result = supabase.table("mapeo_talleres").select("*, ubicaciones(nombre)").order("keyword").execute()
    return result.data

@router.post("/mapeo-talleres/")
def crear_mapeo_taller(data: MapeoTallerCreate):
    try:
        result = supabase.table("mapeo_talleres").insert(data.model_dump()).execute()
        return result.data
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/mapeo-talleres/{mapeo_id}")
def actualizar_mapeo_taller(mapeo_id: str, data: MapeoTallerUpdate):
    result = supabase.table("mapeo_talleres").update(data.model_dump(exclude_none=True)).eq("id", mapeo_id).execute()
    return result.data

@router.delete("/mapeo-talleres/{mapeo_id}")
def eliminar_mapeo_taller(mapeo_id: str):
    supabase.table("mapeo_talleres").delete().eq("id", mapeo_id).execute()
    return {"ok": True}


# ─── RECETAS / KITS (composición de insumos por tipo de instalación) ──

@router.get("/recetas/")
def listar_recetas(tipo_instalacion: str = None):
    query = supabase.table("recetas").select("*, productos(codigo, descripcion)")
    if tipo_instalacion:
        query = query.eq("tipo_instalacion", tipo_instalacion)
    result = query.execute()
    return result.data

@router.get("/recetas/tipos/")
def listar_tipos_receta():
    result = supabase.table("recetas").select("tipo_instalacion").execute()
    return sorted({r["tipo_instalacion"] for r in result.data})

@router.post("/recetas/")
def crear_receta(data: RecetaItemCreate):
    try:
        result = supabase.table("recetas").insert(data.model_dump()).execute()
        return result.data
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/recetas/{receta_id}")
def actualizar_receta(receta_id: str, data: RecetaItemUpdate):
    result = supabase.table("recetas").update(data.model_dump(exclude_none=True)).eq("id", receta_id).execute()
    return result.data

@router.delete("/recetas/{receta_id}")
def eliminar_receta(receta_id: str):
    supabase.table("recetas").delete().eq("id", receta_id).execute()
    return {"ok": True}


# ─── IMPORT DE TICKETS DE SOPORTE ──────────────────────────────────────

@router.get("/tickets/importados/")
def listar_tickets_importados(ticket_numero: str = None):
    query = supabase.table("tickets_importados").select("id, ticket_numero, distrito, importado_en")
    if ticket_numero:
        query = query.eq("ticket_numero", ticket_numero)
    result = query.execute()
    return result.data

@router.post("/tickets/confirmar/")
def confirmar_ticket(data: TicketConfirmarItem):
    try:
        result = supabase.rpc("fn_confirmar_ticket_stock", {
            "p_ticket_numero": data.ticket_numero,
            "p_distrito": data.distrito,
            "p_archivo_nombre": data.archivo_nombre,
            "p_fila_excel": data.fila_excel,
            "p_cargado_por": data.cargado_por,
            "p_movimientos": [m.model_dump(mode="json") for m in data.movimientos],
        }).execute()
        return result.data
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
