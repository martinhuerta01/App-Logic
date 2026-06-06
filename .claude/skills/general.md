# Skill: Convenciones generales del proyecto

## Propósito
Guía de referencia rápida para trabajar en App-Logic respetando los patrones establecidos.

---

## Patrón modelo → router → main

Cada entidad del sistema sigue este flujo obligatorio:

```
models/entidad.py          → Define los schemas Pydantic
routers/entidad.py         → Define los endpoints FastAPI
main.py                    → Registra el router con su prefijo
```

**Nunca saltear pasos.** Si se modifica el modelo, revisar si el router necesita ajustes.

---

## Modelos Pydantic

```python
# models/ejemplo.py
from pydantic import BaseModel
from typing import Optional

class EjemploCreate(BaseModel):
    campo_requerido: str
    campo_opcional: Optional[str] = None

class EjemploUpdate(BaseModel):
    campo_opcional: Optional[str] = None
    activo: Optional[bool] = None
```

- Usar `Optional[X] = None` para todos los campos en `Update`
- Usar `str` para IDs (UUIDs de Supabase son strings)
- Usar Pydantic v2 — `.model_dump(mode="json")` para serializar

---

## Routers FastAPI

```python
# routers/ejemplo.py
from fastapi import APIRouter, HTTPException
from models.ejemplo import EjemploCreate, EjemploUpdate
from database import supabase

router = APIRouter()

@router.get("/")
def listar():
    return supabase.table("ejemplos").select("*").execute().data

@router.post("/")
def crear(data: EjemploCreate):
    return supabase.table("ejemplos").insert(data.model_dump(mode="json")).execute().data

@router.get("/{id}")
def obtener(id: str):
    result = supabase.table("ejemplos").select("*").eq("id", id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="No encontrado")
    return result.data[0]

@router.patch("/{id}")
def actualizar(id: str, data: EjemploUpdate):
    payload = {k: v for k, v in data.model_dump(mode="json").items() if v is not None}
    return supabase.table("ejemplos").update(payload).eq("id", id).execute().data

@router.delete("/{id}")
def eliminar(id: str):
    supabase.table("ejemplos").delete().eq("id", id).execute()
    return {"ok": True}
```

- El prefijo (`/ejemplos`) se define en `main.py`, no en el router
- Siempre importar `supabase` desde `database`, nunca instanciar de nuevo
- Retornar `{"ok": True}` en deletes exitosos

---

## Registro en main.py

```python
from routers import ejemplo

app.include_router(ejemplo.router, prefix="/ejemplo", tags=["Ejemplo"])
```

---

## Supabase — operaciones comunes

```python
# Listar con filtro
supabase.table("tabla").select("*").eq("campo", valor).execute().data

# Insertar
supabase.table("tabla").insert(dict).execute().data

# Actualizar
supabase.table("tabla").update(dict).eq("id", id).execute().data

# Eliminar
supabase.table("tabla").delete().eq("id", id).execute()

# Filtros de rango
.gte("fecha", desde).lte("fecha", hasta)

# Ordenar
.order("campo", desc=True)
```

---

## Naming

| Elemento | Convención | Ejemplo |
|----------|-----------|---------|
| Archivos | snake_case | `movimientos_camioneta.py` |
| Clases Pydantic | PascalCase + sufijo | `JornadaCreate`, `EmpleadoUpdate` |
| Funciones de endpoint | snake_case en español | `cargar_jornada`, `listar_ausencias` |
| Prefijos de ruta | kebab-case en español | `/movimientos-camioneta` |
| Tablas Supabase | snake_case plural | `jornadas`, `empleados` |

---

## Qué NO hacer

- No instanciar Supabase fuera de `database.py`
- No usar SQLAlchemy (el cliente Supabase reemplaza al ORM)
- No poner el prefijo de ruta dentro del router (`APIRouter(prefix=...)`)
- No commitear `.env`
- No usar inglés para nombres de dominio (rutas, funciones, variables de negocio)
