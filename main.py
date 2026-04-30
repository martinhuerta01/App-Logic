from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import auth, empleados, jornadas, stock, terceros, proveedores
from routers import equipos, movimientos_camioneta, directorio, estadisticas, servicios
from routers import opciones_carga
from routers import usuarios, tareas

app = FastAPI(title="App-Logic API", version="2.0.0")

@app.get("/debug-env")
def debug_env():
    import os
    url = os.getenv("SUPABASE_URL", "NOT SET")
    key = os.getenv("SUPABASE_KEY", "NOT SET")
    return {
        "url_length": len(url) if url else 0,
        "url_starts": url[:30] if url else None,
        "url_ends": repr(url[-10:]) if url else None,
        "key_length": len(key) if key else 0,
        "key_starts": key[:10] if key else None,
    }

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
@app.get("/health")
def health():
    return {"status": "ok"}

# Módulos existentes
app.include_router(auth.router,        prefix="/auth",        tags=["Auth"])
app.include_router(empleados.router,   prefix="/empleados",   tags=["Empleados"])
app.include_router(jornadas.router,    prefix="/jornadas",    tags=["Jornadas"])
app.include_router(stock.router,       prefix="/stock",       tags=["Stock"])
app.include_router(terceros.router,    prefix="/terceros",    tags=["Terceros"])
app.include_router(proveedores.router, prefix="/proveedores", tags=["Proveedores"])
app.include_router(opciones_carga.router, prefix="/opciones-carga", tags=["opciones-carga"])

# Nuevos módulos
app.include_router(equipos.router,              prefix="/equipos",              tags=["Equipos"])
app.include_router(movimientos_camioneta.router, prefix="/movimientos-camioneta", tags=["Movimientos"])
app.include_router(directorio.router,           prefix="/directorio",           tags=["Directorio"])
app.include_router(estadisticas.router,         prefix="/estadisticas",         tags=["Estadísticas"])
app.include_router(servicios.router,            prefix="/servicios",            tags=["Servicios"])
app.include_router(usuarios.router, prefix="/usuarios", tags=["Usuarios"])
app.include_router(tareas.router,               prefix="/tareas",               tags=["Tareas"])
