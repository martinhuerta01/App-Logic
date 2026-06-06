# App-Logic — Backend API

Sistema de gestión operativa para empresa de GPS/tracking. Permite registrar jornadas, técnicos, equipos, stock, servicios, movimientos de camionetas y tareas.

## Stack

| Capa | Tecnología |
|------|-----------|
| API | FastAPI 0.135.1 + Uvicorn |
| Base de datos | Supabase (PostgreSQL) |
| Auth | JWT (PyJWT) + bcrypt |
| Frontend interno | Reflex 0.8.27 (carpeta `Logic/`) |
| Frontend externo | Next.js 16 (repo separado: `app-logic-web`) |
| Cliente HTTP | httpx |
| Config | python-dotenv (`.env`) |

## Estructura de carpetas

```
App-Logic/
├── main.py          → Entry point FastAPI, registra todos los routers
├── database.py      → Conexión a Supabase (importar desde acá, no instanciar en routers)
├── models/          → Modelos Pydantic (Create, Update por entidad)
├── routers/         → Endpoints FastAPI (un archivo por módulo)
├── Logic/           → Páginas y estado Reflex (frontend interno)
│   ├── Logic.py     → App Reflex principal
│   ├── state.py     → Estado global Reflex
│   └── pages/       → Páginas individuales
├── .claude/
│   └── skills/      → Skills del proyecto para Claude Code
├── .env             → SUPABASE_URL y SUPABASE_KEY (no commitear)
├── requirements.txt → Dependencias Python
└── rxconfig.py      → Config Reflex
```

## Módulos / Routers

| Prefix | Router | Descripción |
|--------|--------|-------------|
| `/auth` | auth.py | Login, JWT |
| `/empleados` | empleados.py | Alta/baja/edición de técnicos |
| `/jornadas` | jornadas.py | Jornadas y ausencias |
| `/stock` | stock.py | Inventario y movimientos |
| `/terceros` | terceros.py | Clientes / terceros |
| `/proveedores` | proveedores.py | Proveedores |
| `/equipos` | equipos.py | Equipos y vehículos |
| `/movimientos-camioneta` | movimientos_camioneta.py | Tracking LogicTracker |
| `/directorio` | directorio.py | Directorio técnicos + precios |
| `/estadisticas` | estadisticas.py | Reportes y métricas |
| `/servicios` | servicios.py | Instalaciones, revisiones, bajas |
| `/opciones-carga` | opciones_carga.py | Opciones configurables |
| `/usuarios` | usuarios.py | Usuarios + sub-módulos (JSONB) |
| `/tareas` | tareas.py | Tickets con tipo, categoría, número |

## Convenciones de código

- **Base de datos**: siempre importar `supabase` desde `database.py`. Nunca instanciar el cliente en otro lado.
- **Modelos**: cada entidad tiene `XxxCreate` y `XxxUpdate` en `models/xxx.py`, usando Pydantic v2 (`BaseModel`).
- **Routers**: un `APIRouter()` por archivo, sin prefijo propio (el prefijo va en `main.py`).
- **IDs**: usar `str` para los IDs de Supabase (UUIDs como string).
- **Serialización**: usar `.model_dump(mode="json")` al insertar/actualizar en Supabase.
- **Errores**: usar `HTTPException` con status codes estándar (400, 404, etc.).
- **Naming**: español para nombres de variables, funciones y rutas (ej: `cargar_jornada`, `/empleados`).
- **Campos opcionales**: `Optional[str] = None` para todos los campos no obligatorios en Update.
- **Sin ORM propio**: Supabase actúa como ORM vía su cliente Python — no usar SQLAlchemy.

## Cómo agregar un nuevo módulo

1. Crear `models/nuevo_modulo.py` con `NuevoModuloCreate` y `NuevoModuloUpdate`
2. Crear `routers/nuevo_modulo.py` con `router = APIRouter()` y los endpoints
3. En `main.py`: importar el router y registrarlo con `app.include_router(..., prefix="/nuevo-modulo")`

## Correr el servidor

```bash
# Activar entorno virtual
venv\Scripts\activate

# Levantar FastAPI
uvicorn main:app --reload

# Levantar Reflex (frontend interno, si aplica)
reflex run
```

## Variables de entorno (.env)

```
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=eyJ...
```

## Skills disponibles

Ver `.claude/skills/` para workflows específicos del proyecto:
- `general.md` — convenciones y patrones principales
- `frontend-design.md` — cómo mejorar el frontend (Reflex + app-logic-web)
- `skill-creator.md` — cómo crear nuevas skills para este proyecto
