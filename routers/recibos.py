from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from database import supabase
from auth_middleware import get_current_user
import fitz  # pymupdf
import re
import os
import httpx
import logging

logger = logging.getLogger(__name__)

router = APIRouter(dependencies=[Depends(get_current_user)])

BUCKET = "recibos-sueldo"
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

MESES_MAP = {
    "ENERO":1,"FEBRERO":2,"MARZO":3,"ABRIL":4,"MAYO":5,"JUNIO":6,
    "JULIO":7,"AGOSTO":8,"SEPTIEMBRE":9,"OCTUBRE":10,"NOVIEMBRE":11,"DICIEMBRE":12,
}


def parse_page(text: str):
    t = " ".join(text.split())
    nombre = None
    legajo = None

    # Formato A: etiquetas verticales — "APELLIDO Y NOMBRES <nombre> C.U.I"
    name_m = re.search(r"APELLIDO Y NOMBRES\s+([A-ZÁÉÍÓÚÜÑ][A-ZÁÉÍÓÚÜÑ\s]+?)\s+C\.U\.I", t, re.UNICODE)
    if name_m:
        nombre = name_m.group(1).strip()
        legajo_m = re.search(r"\bLEGAJO\s+(\d+)\b", t)
        legajo = legajo_m.group(1) if legajo_m else None
    else:
        # Formato B: tabla — "Lugar de Pago n<legajo> <NOMBRE> <cuil11> <MES>"
        # Los datos aparecen recién después de todos los encabezados de columna
        b_m = re.search(
            r"Lugar de Pago\s+n(\d+)\s+([A-ZÁÉÍÓÚÜÑ][A-ZÁÉÍÓÚÜÑ\s]+?)\s+\d{10,11}\s+"
            r"(?:ENERO|FEBRERO|MARZO|ABRIL|MAYO|JUNIO|JULIO|AGOSTO|SEPTIEMBRE|OCTUBRE|NOVIEMBRE|DICIEMBRE)",
            t, re.IGNORECASE | re.UNICODE,
        )
        if b_m:
            legajo = b_m.group(1)
            nombre = b_m.group(2).strip()

    # Período: mes en español + año
    period_m = re.search(
        r"\b(ENERO|FEBRERO|MARZO|ABRIL|MAYO|JUNIO|JULIO|AGOSTO|SEPTIEMBRE|OCTUBRE|NOVIEMBRE|DICIEMBRE)\s+(\d{4})\b",
        t, re.IGNORECASE,
    )
    mes = anio = periodo_texto = None
    if period_m:
        mes_str = period_m.group(1).upper()
        anio_str = period_m.group(2)
        mes = MESES_MAP.get(mes_str)
        anio = int(anio_str)
        periodo_texto = f"{mes_str.capitalize()} {anio_str}"

    return nombre, legajo, mes, anio, periodo_texto


def storage_upload(path: str, data: bytes) -> None:
    """Sube un archivo a Supabase Storage via HTTP directo."""
    url = f"{SUPABASE_URL}/storage/v1/object/{BUCKET}/{path}"
    headers = {
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/pdf",
        "x-upsert": "true",
    }
    resp = httpx.post(url, content=data, headers=headers, timeout=30)
    if not resp.is_success:
        raise Exception(f"Storage {resp.status_code}: {resp.text}")


def storage_signed_url(path: str, expires_in: int = 3600) -> str:
    """Genera una URL firmada para descarga."""
    url = f"{SUPABASE_URL}/storage/v1/object/sign/{BUCKET}/{path}"
    headers = {
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
    }
    resp = httpx.post(url, json={"expiresIn": expires_in}, headers=headers, timeout=10)
    if not resp.is_success:
        raise Exception(f"Signed URL {resp.status_code}: {resp.text}")
    data = resp.json()
    signed = data.get("signedURL") or data.get("signedUrl") or data.get("signed_url", "")
    if not signed:
        raise Exception(f"No se obtuvo URL firmada: {data}")
    return f"{SUPABASE_URL}/storage/v1{signed}" if signed.startswith("/object/sign") else signed


@router.post("/upload")
async def subir_pdf(file: UploadFile = File(...), user=Depends(get_current_user)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Solo se aceptan archivos PDF")

    pdf_bytes = await file.read()
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")

    procesados = []
    errores = []
    subido_por = user if isinstance(user, str) else "sistema"

    for i in range(len(doc)):
        page = doc[i]
        text = page.get_text()
        nombre, legajo, mes, anio, periodo_texto = parse_page(text)

        if not nombre or not mes or not anio:
            logger.warning(f"[RECIBO] pág {i+1} sin nombre/período — texto: {repr(text[:600])}")
            errores.append({"pagina": i + 1, "msg": "No se pudo extraer nombre o período"})
            continue

        # Evitar duplicados
        exists = (
            supabase.table("recibos_sueldo")
            .select("id")
            .eq("empleado_nombre", nombre)
            .eq("mes", mes)
            .eq("anio", anio)
            .execute()
        )
        if exists.data:
            errores.append({"pagina": i + 1, "msg": f"Ya existe recibo de {nombre} para {periodo_texto}"})
            continue

        # Crear PDF individual (una sola página)
        single = fitz.open()
        single.insert_pdf(doc, from_page=i, to_page=i)
        page_bytes = single.tobytes()
        single.close()

        # Path en Storage
        safe = re.sub(r"[^A-Za-z0-9_]", "_", nombre)
        path = f"{anio}/{mes:02d}/{safe}.pdf"

        # Subir a Storage via HTTP directo
        try:
            storage_upload(path, page_bytes)
        except Exception as e:
            errores.append({"pagina": i + 1, "msg": f"Error al guardar archivo: {str(e)}"})
            continue

        # Guardar metadata en DB
        try:
            supabase.table("recibos_sueldo").insert({
                "empleado_nombre": nombre,
                "legajo": legajo,
                "mes": mes,
                "anio": anio,
                "periodo_texto": periodo_texto,
                "archivo_path": path,
                "subido_por": subido_por,
            }).execute()
        except Exception as e:
            errores.append({"pagina": i + 1, "msg": f"Error al guardar en DB: {str(e)}"})
            continue

        procesados.append({"nombre": nombre, "periodo": periodo_texto, "pagina": i + 1})

    doc.close()
    return {
        "procesados": len(procesados),
        "errores": len(errores),
        "detalle": procesados,
        "detalle_errores": errores,
    }


@router.get("/empleados")
def listar_empleados():
    result = (
        supabase.table("recibos_sueldo")
        .select("id, empleado_nombre, legajo, mes, anio, periodo_texto")
        .order("empleado_nombre")
        .order("anio", desc=True)
        .order("mes", desc=True)
        .execute()
    )

    empleados: dict = {}
    for r in result.data:
        n = r["empleado_nombre"]
        if n not in empleados:
            empleados[n] = {"nombre": n, "legajo": r.get("legajo"), "periodos": []}
        empleados[n]["periodos"].append({
            "id": r["id"],
            "mes": r["mes"],
            "anio": r["anio"],
            "periodo_texto": r.get("periodo_texto"),
        })

    return list(empleados.values())


@router.get("/{recibo_id}/url")
def get_signed_url(recibo_id: str):
    result = (
        supabase.table("recibos_sueldo")
        .select("archivo_path, empleado_nombre, periodo_texto")
        .eq("id", recibo_id)
        .execute()
    )
    if not result.data:
        raise HTTPException(404, "Recibo no encontrado")
    r = result.data[0]
    try:
        url = storage_signed_url(r["archivo_path"])
    except Exception as e:
        raise HTTPException(500, f"Error al generar URL: {str(e)}")
    return {"url": url, "nombre": r["empleado_nombre"], "periodo": r.get("periodo_texto")}


@router.delete("/{recibo_id}")
def eliminar_recibo(recibo_id: str):
    result = supabase.table("recibos_sueldo").select("archivo_path").eq("id", recibo_id).execute()
    if not result.data:
        raise HTTPException(404, "Recibo no encontrado")
    path = result.data[0]["archivo_path"]
    try:
        url = f"{SUPABASE_URL}/storage/v1/object/{BUCKET}"
        headers = {"Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json"}
        httpx.delete(url, json={"prefixes": [path]}, headers=headers, timeout=10)
    except Exception:
        pass
    supabase.table("recibos_sueldo").delete().eq("id", recibo_id).execute()
    return {"ok": True}
