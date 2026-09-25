# App-Logic — Backend API

Sistema de gestión operativa para empresa de GPS/tracking. Permite registrar jornadas, técnicos, equipos, stock, servicios, movimientos de camionetas, recibos de sueldo y tareas. La parte visual está en otro repositorio: `app-logic-web` (Next.js).

## Stack

| Capa | Tecnología |
|------|-----------|
| API | FastAPI 0.135.1 + Uvicorn |
| Base de datos | Supabase (PostgreSQL) |
| Auth | JWT (PyJWT) + bcrypt |
| Cliente HTTP | httpx |
| Config | python-dotenv (`.env`) |

## Estructura de carpetas

```
App-Logic/
├── main.py            → Entry point FastAPI, registra todos los routers
├── database.py        → Conexión a Supabase (importar desde acá, no instanciar en routers)
├── auth_middleware.py → Sesión (JWT) y permisos: get_current_user, requiere_admin, requiere_modulo
├── models/            → Modelos Pydantic (Create, Update por entidad)
├── routers/           → Endpoints FastAPI (un archivo por módulo)
├── migraciones/       → Cambios de la base de datos versionados (.up.sql / .down.sql) — ver LEEME.md
├── .claude/skills/    → Skills del proyecto para Claude Code
├── .env               → SUPABASE_URL, SUPABASE_KEY y SECRET_KEY (no commitear)
└── requirements.txt   → Dependencias Python
```

## Módulos / Routers

| Prefix | Router | Descripción |
|--------|--------|-------------|
| `/auth` | auth.py | Login, JWT |
| `/empleados` | empleados.py | Alta/baja/edición de técnicos |
| `/jornadas` | jornadas.py | Jornadas y ausencias |
| `/stock` | stock.py | Inventario, movimientos, equipos por serial |
| `/stock` | stock_tickets.py | Importación de tickets, mapeo de talleres, kits (recetas) |
| `/terceros` | terceros.py | Terceros (sin llamadas conocidas desde el frontend) |
| `/proveedores` | proveedores.py | Proveedores |
| `/equipos` | equipos.py | Equipos y vehículos |
| `/movimientos-camioneta` | movimientos_camioneta.py | Recorridos de camionetas |
| `/directorio` | directorio.py | Contactos: técnicos, interior, clientes, proveedores |
| `/estadisticas` | estadisticas.py | Reportes y métricas (hoy el frontend no los usa) |
| `/servicios` | servicios.py | Instalaciones, revisiones, bajas |
| `/opciones-carga` | opciones_carga.py | Opciones configurables |
| `/usuarios` | usuarios.py | Usuarios + módulos y submódulos (JSONB) — solo administración |
| `/tareas` | tareas.py | Tareas internas con tipo, categoría, número |
| `/recibos` | recibos.py | Recibos de sueldo — solo con el módulo "recibos" |

## Permisos

- Todo router lleva `dependencies=[Depends(get_current_user)]` como mínimo (solo `/auth/login` es público).
- `requiere_admin` (solo rol `admin`) y `requiere_modulo("clave")` (administración, usuarios con ese módulo o con módulos en `null`) leen el usuario desde la base y lo guardan 60 segundos; una baja o un cambio de permisos se aplica en menos de un minuto.
- Hoy están activos en `/usuarios` (administración) y `/recibos` (módulo recibos). El resto de las rutas se van pasando a `requiere_modulo` de a poco, porque varias se comparten entre módulos (por ejemplo, el Dashboard de inicio usa servicios y tareas). Antes de activar en una ruta, buscar en el frontend quién la llama.

## Convenciones de código

- **Base de datos**: siempre importar `supabase` desde `database.py`. Nunca instanciar el cliente en otro lado.
- **Cambios de estructura**: siempre como archivo en `migraciones/` (aplicar y deshacer). No modificar tablas a mano sin dejar el archivo.
- **Modelos**: cada entidad tiene `XxxCreate` y `XxxUpdate` en `models/xxx.py`, usando Pydantic v2 (`BaseModel`).
- **Routers**: un `APIRouter()` por archivo, sin prefijo propio (el prefijo va en `main.py`).
- **IDs**: usar `str` para los IDs de Supabase (UUIDs como string).
- **Serialización**: usar `.model_dump(mode="json")` al insertar/actualizar en Supabase.
- **Errores**: usar `HTTPException` con status codes estándar (400, 404, etc.).
- **Naming**: español para nombres de variables, funciones y rutas (ej: `cargar_jornada`, `/empleados`).
- **Campos opcionales**: `Optional[str] = None` para todos los campos no obligatorios en Update.
- **Sin ORM propio**: Supabase actúa como ORM vía su cliente Python — no usar SQLAlchemy.
- **Reglas de negocio en el servidor**: las validaciones importantes (duplicados, permisos) van acá; el frontend puede repetirlas solo para avisar antes.

## Cómo agregar un nuevo módulo

1. Crear `models/nuevo_modulo.py` con `NuevoModuloCreate` y `NuevoModuloUpdate`
2. Crear `routers/nuevo_modulo.py` con `router = APIRouter(dependencies=[Depends(requiere_modulo("nuevo-modulo"))])` y los endpoints
3. En `main.py`: importar el router y registrarlo con `app.include_router(..., prefix="/nuevo-modulo")`
4. Si necesita tablas: archivo nuevo en `migraciones/`
5. En el frontend, agregar el módulo en `src/lib/modulos.js` (el menú y los permisos lo toman de ahí)

## Correr el servidor

```bash
# Activar entorno virtual
venv\Scripts\activate

# Levantar FastAPI
uvicorn main:app --reload
```

En Windows, `--reload` a veces queda colgado después de un cambio de archivo: si un cambio no se refleja, detener el proceso y volver a levantarlo.

## Variables de entorno (.env)

```
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=eyJ...
SECRET_KEY=...   # firma de las sesiones; se recomienda de 32 caracteres o más
```

## Skills disponibles

Ver `.claude/skills/` para workflows específicos del proyecto:
- `general.md` — convenciones y patrones principales
- `security.md` — checklist de seguridad
- `testing.md` — pruebas manuales
- `frontend-design.md` — cómo mejorar el frontend (app-logic-web)
