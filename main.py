from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import auth, empleados, jornadas, stock, terceros, proveedores

app = FastAPI(title="App-Logic API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router,        prefix="/auth",        tags=["Auth"])
app.include_router(empleados.router,   prefix="/empleados",   tags=["Empleados"])
app.include_router(jornadas.router,    prefix="/jornadas",    tags=["Jornadas"])
app.include_router(stock.router,       prefix="/stock",       tags=["Stock"])
app.include_router(terceros.router,    prefix="/terceros",    tags=["Terceros"])
app.include_router(proveedores.router, prefix="/proveedores", tags=["Proveedores"])