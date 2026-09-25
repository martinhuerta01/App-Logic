from fastapi import APIRouter, Depends, HTTPException
from models.servicios import ServicioCreate, ServicioUpdate, ServicioLote
from database import supabase
import calendar
import re
from auth_middleware import get_current_user

router = APIRouter(dependencies=[Depends(get_current_user)])

ESTADO_SUSPENDIDO = "SUSPENDIDO"


def normalizar_patente(patente):
    """Sin espacios ni separadores y en mayúsculas. El valor "-" (sin patente) se conserva."""
    if patente is None:
        return None
    limpia = re.sub(r"[\s.\-]", "", str(patente)).upper()
    if limpia:
        return limpia
    return "-" if str(patente).strip() == "-" else None


def _aplica_regla_duplicado(patente, tipo_servicio):
    # Feriados y servicios sin patente ("-" o vacía) no se controlan.
    return bool(patente) and patente != "-" and tipo_servicio not in (None, "", "-")


def _buscar_duplicados(fecha, tipo_servicio, patente, excluir_id=None):
    """Servicios ya cargados con la misma patente normalizada, tipo y fecha, que no estén suspendidos."""
    if not _aplica_regla_duplicado(patente, tipo_servicio):
        return []
    filas = (
        supabase.table("servicios")
        .select("id, fecha, tipo_servicio, patente, estado, responsable, cliente")
        .eq("fecha", str(fecha))
        .eq("tipo_servicio", tipo_servicio)
        .execute()
        .data
    )
    return [
        f for f in filas
        if f["id"] != excluir_id
        and f.get("estado") != ESTADO_SUSPENDIDO
        and normalizar_patente(f.get("patente")) == patente
    ]


def _responder_duplicados(duplicados):
    # 409: el pedido es válido pero choca con algo existente; el frontend pide confirmación.
    raise HTTPException(status_code=409, detail={
        "codigo": "DUPLICADO",
        "mensaje": "Ya existe un servicio con la misma patente, tipo y fecha.",
        "duplicados": duplicados,
    })


def _preparar_para_guardar(data: ServicioCreate):
    fila = data.model_dump(mode="json", exclude={"confirmar_duplicado"})
    fila["patente"] = normalizar_patente(fila.get("patente"))
    return fila


def _marcar_duplicado_confirmado(fila):
    nota = "Duplicado confirmado al cargar"
    fila["observaciones"] = f"{fila['observaciones']} | {nota}" if fila.get("observaciones") else nota


@router.get("/")
def listar_servicios(
    cliente_ref: str = None,
    cliente: str = None,
    equipo_id: str = None,
    responsable: str = None,
    estado: str = None,
    mes: int = None,
    anio: int = None,
    fecha: str = None,
    tipo: str = None,   # "equipos" | "interior"
):
    query = supabase.table("servicios").select("*, equipos(nombre, patente)")
    if cliente_ref:
        query = query.eq("cliente_ref", cliente_ref)
    if cliente:
        query = query.ilike("cliente", f"%{cliente}%")
    if equipo_id:
        query = query.eq("equipo_id", equipo_id)
    if responsable:
        query = query.ilike("responsable", f"%{responsable}%")
    if estado:
        query = query.eq("estado", estado)
    if fecha:
        query = query.eq("fecha", fecha)
    if tipo == "equipos":
        query = query.not_.is_("equipo_id", "null")
    elif tipo == "interior":
        query = query.is_("equipo_id", "null")
    if mes and anio:
        ultimo_dia = calendar.monthrange(int(anio), int(mes))[1]
        desde = f"{anio}-{str(mes).zfill(2)}-01"
        hasta = f"{anio}-{str(mes).zfill(2)}-{ultimo_dia}"
        query = query.gte("fecha", desde).lte("fecha", hasta)
    result = query.order("fecha", desc=True).order("hora_programada").execute()
    return result.data


@router.post("/")
def crear_servicio(data: ServicioCreate):
    fila = _preparar_para_guardar(data)
    duplicados = _buscar_duplicados(fila["fecha"], fila["tipo_servicio"], fila["patente"])
    if duplicados:
        if not data.confirmar_duplicado:
            _responder_duplicados(duplicados)
        _marcar_duplicado_confirmado(fila)
    result = supabase.table("servicios").insert(fila).execute()
    return result.data


@router.post("/lote/")
def crear_servicios_en_lote(lote: ServicioLote):
    """Guarda todas las filas juntas o ninguna. Controla duplicados contra la base y dentro del mismo lote."""
    if not lote.servicios:
        raise HTTPException(status_code=400, detail="El lote no tiene servicios")

    filas = [_preparar_para_guardar(s) for s in lote.servicios]
    con_duplicado = []
    vistos = set()
    for i, fila in enumerate(filas):
        clave = (fila["fecha"], fila["tipo_servicio"], fila["patente"])
        existentes = _buscar_duplicados(fila["fecha"], fila["tipo_servicio"], fila["patente"])
        if _aplica_regla_duplicado(fila["patente"], fila["tipo_servicio"]):
            if clave in vistos:
                existentes = existentes + [{
                    "id": None, "fecha": fila["fecha"], "tipo_servicio": fila["tipo_servicio"],
                    "patente": fila["patente"], "estado": fila["estado"],
                    "responsable": fila.get("responsable"), "cliente": fila.get("cliente"),
                    "en_este_lote": True,
                }]
            vistos.add(clave)
        if existentes:
            con_duplicado.append(i)
            if not lote.confirmar_duplicado:
                _responder_duplicados(existentes)
    for i in con_duplicado:
        _marcar_duplicado_confirmado(filas[i])

    result = supabase.table("servicios").insert(filas).execute()
    return result.data


@router.put("/{servicio_id}")
def actualizar_servicio(servicio_id: str, data: ServicioUpdate):
    cambios = data.model_dump(exclude_none=True, mode="json", exclude={"confirmar_duplicado"})
    if "patente" in cambios:
        cambios["patente"] = normalizar_patente(cambios["patente"])

    # Solo se revisa cuando cambia lo que identifica al servicio (fecha, tipo o patente) o cuando
    # se reactiva uno suspendido; así se puede seguir editando el estado de duplicados históricos.
    if {"fecha", "tipo_servicio", "patente", "estado"} & cambios.keys():
        actual = supabase.table("servicios").select("*").eq("id", servicio_id).execute().data
        if not actual:
            raise HTTPException(status_code=404, detail="Servicio no encontrado")
        antes = actual[0]
        despues = {**antes, **cambios}
        cambio_identidad = (
            str(despues["fecha"]) != str(antes["fecha"])
            or despues["tipo_servicio"] != antes["tipo_servicio"]
            or normalizar_patente(despues.get("patente")) != normalizar_patente(antes.get("patente"))
            or (antes.get("estado") == ESTADO_SUSPENDIDO and despues.get("estado") != ESTADO_SUSPENDIDO)
        )
        if cambio_identidad and despues.get("estado") != ESTADO_SUSPENDIDO:
            duplicados = _buscar_duplicados(
                despues["fecha"], despues["tipo_servicio"],
                normalizar_patente(despues.get("patente")), excluir_id=servicio_id,
            )
            if duplicados and not data.confirmar_duplicado:
                _responder_duplicados(duplicados)

    result = supabase.table("servicios").update(cambios).eq("id", servicio_id).execute()
    return result.data


@router.delete("/{servicio_id}")
def eliminar_servicio(servicio_id: str):
    supabase.table("servicios").delete().eq("id", servicio_id).execute()
    return {"ok": True}
