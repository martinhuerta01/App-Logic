from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from database import supabase
from auth_middleware import get_current_user
import fitz  # pymupdf
import re
import logging

logger = logging.getLogger(__name__)

router = APIRouter(dependencies=[Depends(get_current_user)])

BUCKET = "recibos-sueldo"

MESES_MAP = {
    "ENERO":1,"FEBRERO":2,"MARZO":3,"ABRIL":4,"MAYO":5,"JUNIO":6,
    "JULIO":7,"AGOSTO":8,"SEPTIEMBRE":9,"OCTUBRE":10,"NOVIEMBRE":11,"DICIEMBRE":12,
}

def parse_page(text: str):
    """Extrae nombre, legajo, mes y año del texto de una página de recibo."""
    # Log primeras 800 chars para debug
    logger.info(f"[RECIBO] texto extraído (800): {repr(text[:800])}")

    t = " ".join(text.split())  # normalizar espacios/saltos

    # CUIT con o sin guiones: XX-XXXXXXXX-X o XXXXXXXXXXX
    cuit_pat = r"\d{2}-?\d{8}-?\d"

    # Nombre: número de legajo + nombre en mayúsculas + CUIT
    name_m = re.search(
        r"\b(\d{1,4})\s+([A-Z][A-Z\s]+?)\s+(" + cuit_pat + r")\b",
        t,
    )
    nombre = name_m.group(2).strip() if name_m else None
    legajo = name_m.group(1) if name_m else None

    logger.info(f"[RECIBO] nombre={nombre!r} legajo={legajo!r}")

    # Período: mes en español + año de 4 dígitos
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

    logger.info(f"[RECIBO] periodo={periodo_texto!r}")

    return nombre, legajo, mes, anio, periodo_texto


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

        # Crear PDF de página individual
        single = fitz.open()
        single.insert_pdf(doc, from_page=i, to_page=i)
        page_bytes = single.tobytes()
        single.close()

        # Path en Storage: anio/mes/NOMBRE_APELLIDO.pdf
        safe = re.sub(r"[^A-Za-z0-9_]", "_", nombre)
        path = f"{anio}/{mes:02d}/{safe}.pdf"

        # Subir a Supabase Storage (upsert)
        try:
            supabase.storage.from_(BUCKET).upload(
                path, page_bytes,
                file_options={"content-type": "application/pdf", "upsert": "true"},
            )
        except Exception as e:
            # Si el archivo ya existe, intentar con remove + re-upload
            try:
                supabase.storage.from_(BUCKET).remove([path])
                supabase.storage.from_(BUCKET).upload(
                    path, page_bytes,
                    file_options={"content-type": "application/pdf"},
                )
            except Exception as e2:
                errores.append({"pagina": i + 1, "msg": f"Error al guardar archivo: {str(e2)}"})
                continue

        # Guardar metadata en DB
        supabase.table("recibos_sueldo").insert({
            "empleado_nombre": nombre,
            "legajo": legajo,
            "mes": mes,
            "anio": anio,
            "periodo_texto": periodo_texto,
            "archivo_path": path,
            "subido_por": subido_por,
        }).execute()

        procesados.append({"nombre": nombre, "periodo": periodo_texto, "pagina": i + 1})

    doc.close()
    return {"procesados": len(procesados), "errores": len(errores), "detalle": procesados, "detalle_errores": errores}


@router.get("/empleados")
def listar_empleados():
    """Lista empleados con sus períodos disponibles."""
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
    result = supabase.table("recibos_sueldo").select("archivo_path, empleado_nombre, periodo_texto").eq("id", recibo_id).execute()
    if not result.data:
        raise HTTPException(404, "Recibo no encontrado")
    r = result.data[0]
    try:
        signed = supabase.storage.from_(BUCKET).create_signed_url(r["archivo_path"], 3600)
        url = signed.get("signedURL") or signed.get("signed_url") or signed.get("signedUrl", "")
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
        supabase.storage.from_(BUCKET).remove([path])
    except Exception:
        pass
    supabase.table("recibos_sueldo").delete().eq("id", recibo_id).execute()
    return {"ok": True}
