# Skill: Frontend Design

## Propósito
Workflow para mejorar, rediseñar o construir interfaces en los dos frontends del proyecto:
- **Reflex** (`Logic/` en este repo) — frontend interno/admin
- **Next.js** (`app-logic-web/`) — frontend principal del cliente

Usar cuando el usuario pida mejorar una pantalla, agregar una vista nueva, o cambiar la UX de algún módulo.

---

## Cuándo usar cada frontend

| Caso | Frontend |
|------|----------|
| Dashboard, estadísticas, gráficos | `app-logic-web` (Next.js) |
| Kanban de tareas | `app-logic-web` (Next.js) |
| Gestión de stock y oficina | `app-logic-web` (Next.js) |
| Login y autenticación | `app-logic-web` (Next.js) |
| Administración de usuarios | `app-logic-web` (Next.js) |
| Panel interno / horarios (Reflex) | `Logic/` (Reflex) |

---

## Stack Frontend — app-logic-web (Next.js)

- **Framework**: Next.js 16 con App Router
- **Estilos**: Tailwind CSS (clases utilitarias, sin CSS custom salvo casos puntuales)
- **Estado global**: React Redux
- **Gráficos**: Recharts
- **Fetch**: fetch nativo o axios hacia `App-Logic` API

### Estructura esperada

```
app-logic-web/
├── app/              → Rutas Next.js (App Router)
│   ├── dashboard/
│   ├── tareas/
│   ├── stock/
│   └── admin/
├── components/       → Componentes reutilizables
├── store/            → Redux slices y configuración
└── public/
```

---

## Stack Frontend — Logic/ (Reflex)

- **Framework**: Reflex 0.8.27 (Python → React)
- **Estado**: `state.py` con `rx.State`
- **Páginas**: una por archivo en `Logic/pages/`
- **Estilos**: props inline de Reflex (`rx.box(padding="1em", ...)`)

---

## Proceso para mejorar una pantalla

### 1. Identificar la pantalla
- ¿En qué frontend vive? ¿Qué archivo?
- ¿Cuál es la funcionalidad actual? ¿Qué datos consume de la API?

### 2. Entender el endpoint relacionado
- Revisar el router en `routers/` correspondiente
- Confirmar qué campos devuelve la API

### 3. Diseñar antes de implementar
Describir brevemente:
- Qué información debe mostrar
- Qué acciones puede hacer el usuario (crear, editar, filtrar, etc.)
- Si hay estados vacíos, de carga o de error que manejar

### 4. Implementar con Tailwind (Next.js)
Principios de diseño a respetar:
- Espaciado consistente: usar escala de Tailwind (`p-4`, `gap-6`, `mt-8`)
- Colores: preferir paleta de grises + un color de acento (ya definido en el proyecto)
- Responsive: pensar mobile-first aunque el uso principal sea desktop
- Componentes reutilizables: si un elemento aparece más de dos veces, extraerlo

### 5. Conectar con la API
```js
// Patrón para fetch en Next.js
const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

const data = await fetch(`${API}/empleados`).then(r => r.json())
```

### 6. Verificar en el navegador
- Abrir la pantalla modificada
- Probar el flujo completo: cargar datos, interactuar, ver errores si los hay
- Revisar en distintos tamaños de pantalla

---

## Convenciones de diseño

- No reinventar componentes básicos si ya existen en el proyecto — buscar primero en `components/`
- Los modales usan el patrón de estado local (`useState`) a menos que afecten estado global
- Los formularios validan en el cliente antes de enviar a la API
- Los mensajes de error van en el idioma del usuario (español)
- Las tablas grandes usan paginación o scroll virtual si superan 50 filas

---

## Red flags

- Agregar librerías de UI (MUI, Chakra, etc.) sin consultar — el proyecto usa Tailwind puro
- Hardcodear la URL de la API en el código — siempre usar variable de entorno
- Ignorar los estados de carga y error — toda llamada async necesita feedback visual
- Mezclar lógica de negocio en los componentes — la lógica va en Redux o en funciones separadas
