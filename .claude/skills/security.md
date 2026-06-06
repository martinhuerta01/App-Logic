---
name: security
description: Checklist de seguridad para el backend FastAPI de App-Logic. Use when adding new endpoints, modifying auth, or reviewing changes before push.
---

# Security Checklist — App-Logic Backend

## Autenticación

- [ ] Todo router nuevo usa `APIRouter(dependencies=[Depends(get_current_user)])`
- [ ] El endpoint `/auth/login` es el ÚNICO sin protección JWT
- [ ] `SECRET_KEY` viene de `.env`, nunca hardcodeado
- [ ] Tokens expiran en 12h (`timedelta(hours=12)`)

## Rate Limiting

- [ ] `/auth/login` tiene `@limiter.limit("5/minute")`
- [ ] `slowapi` registrado en `app.state.limiter` y el handler de `RateLimitExceeded`

## CORS

- [ ] `allow_origins` solo contiene orígenes conocidos (nunca `["*"]` en producción)
- [ ] Orígenes actuales: `["http://localhost:3000"]`

## Endpoints peligrosos

- [ ] No existe `/debug-env` ni `/auth/hash` ni endpoints de diagnóstico expuestos
- [ ] Verificar con `grep -r "debug\|hash\|test" routers/` antes de cada release

## Modelos Pydantic

- [ ] Todos los campos `str` de entrada tienen `max_length`
- [ ] Campos de contraseña: `max_length=200`
- [ ] Campos de texto libre (descripciones): `max_length=2000`
- [ ] Campos de nombre: `max_length=100-150`

## Base de datos

- [ ] RLS deshabilitado solo en tablas internas con acceso controlado por JWT
- [ ] Nunca interpolar strings en queries — usar Supabase client (parametrizado por defecto)

## Dependencias

- [ ] Revisar `requirements.txt` después de cada nueva dependencia: `pip audit` o equivalente
- [ ] No dejar dependencias de desarrollo/prototipado en producción (ej: reflex)

## Variables de entorno

- [ ] `.env` en `.gitignore`
- [ ] `.env.example` documentado con todas las variables requeridas (sin valores reales)
- [ ] Variables requeridas: `SECRET_KEY`, `SUPABASE_URL`, `SUPABASE_KEY`
