import logging
import os
import time
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from routers import auth, empleados, jornadas, stock, terceros, proveedores
from routers import equipos, movimientos_camioneta, directorio, estadisticas, servicios
from routers import opciones_carga
from routers import usuarios, tareas, recibos

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="App-Logic API", version="2.0.0")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

_allowed_origins = [
    "http://localhost:3000",
    "https://app-logic-web.vercel.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = round((time.time() - start) * 1000)
    logger.info(f"{request.method} {request.url.path} → {response.status_code} ({duration}ms)")
    return response

@app.get("/health")
def health():
    return {"status": "ok"}

app.include_router(auth.router,                  prefix="/auth",                  tags=["Auth"])
app.include_router(empleados.router,             prefix="/empleados",             tags=["Empleados"])
app.include_router(jornadas.router,              prefix="/jornadas",              tags=["Jornadas"])
app.include_router(stock.router,                 prefix="/stock",                 tags=["Stock"])
app.include_router(terceros.router,              prefix="/terceros",              tags=["Terceros"])
app.include_router(proveedores.router,           prefix="/proveedores",           tags=["Proveedores"])
app.include_router(opciones_carga.router,        prefix="/opciones-carga",        tags=["Opciones"])
app.include_router(equipos.router,               prefix="/equipos",               tags=["Equipos"])
app.include_router(movimientos_camioneta.router, prefix="/movimientos-camioneta", tags=["Movimientos"])
app.include_router(directorio.router,            prefix="/directorio",            tags=["Directorio"])
app.include_router(estadisticas.router,          prefix="/estadisticas",          tags=["Estadísticas"])
app.include_router(servicios.router,             prefix="/servicios",             tags=["Servicios"])
app.include_router(usuarios.router,              prefix="/usuarios",              tags=["Usuarios"])
app.include_router(tareas.router,                prefix="/tareas",                tags=["Tareas"])
app.include_router(recibos.router,               prefix="/recibos",               tags=["Recibos"])
