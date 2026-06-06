---
name: testing
description: Guía de testing para el backend FastAPI de App-Logic. Use when adding new endpoints or fixing bugs to verify behavior manually or con pytest.
---

# Testing Guide — App-Logic Backend

## Verificación manual rápida (antes de push)

### 1. Levantar servidor
```bash
uvicorn main:app --reload --port 8001
```

### 2. Verificar health
```bash
curl http://localhost:8001/health
# Esperado: {"status": "ok"}
```

### 3. Login y obtener token
```bash
curl -X POST http://localhost:8001/auth/login \
  -H "Content-Type: application/json" \
  -d '{"usuario": "tu_usuario", "password": "tu_password"}'
# Esperado: {"access_token": "...", "token_type": "bearer", ...}
```

### 4. Verificar JWT requerido
```bash
curl http://localhost:8001/equipos/
# Esperado: 403 Forbidden o 401 Unauthorized

curl http://localhost:8001/equipos/ \
  -H "Authorization: Bearer TU_TOKEN"
# Esperado: 200 OK con lista de equipos
```

### 5. Verificar rate limiting
```bash
# Ejecutar 6 veces seguidas — la 6ta debe retornar 429
for i in {1..6}; do
  curl -s -o /dev/null -w "%{http_code}\n" \
    -X POST http://localhost:8001/auth/login \
    -H "Content-Type: application/json" \
    -d '{"usuario": "x", "password": "x"}'
done
# Esperado: 401 401 401 401 401 429
```

## Endpoints críticos a testear después de cambios

| Endpoint | Método | Auth | Qué verificar |
|----------|--------|------|----------------|
| `/auth/login` | POST | No | Devuelve token con usuario/rol/modulos/submodulos |
| `/health` | GET | No | Responde 200 |
| `/equipos/` | GET | Sí | 401 sin token, 200 con token |
| `/tareas/` | GET | Sí | Lista tickets correctamente |
| `/tareas/{id}/notas/` | POST | Sí | Crea nota y la devuelve |
| `/usuarios/` | GET | Sí | Solo muestra id/nombre/rol (sin password_hash) |

## Pytest (setup básico)

```bash
pip install pytest httpx
```

```python
# tests/test_auth.py
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health():
    res = client.get("/health")
    assert res.status_code == 200

def test_login_invalido():
    res = client.post("/auth/login", json={"usuario": "x", "password": "x"})
    assert res.status_code == 401

def test_endpoint_sin_token():
    res = client.get("/equipos/")
    assert res.status_code in (401, 403)
```

```bash
pytest tests/ -v
```

## Logs

Los logs de cada request aparecen en la consola con formato:
```
2026-06-06 10:00:00 [INFO] POST /auth/login → 200 (45ms)
```
Útil para diagnosticar latencia o errores en producción.
