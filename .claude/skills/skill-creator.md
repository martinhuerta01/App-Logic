# Skill: Creación de Skills

## Propósito
Workflow para crear nuevas skills de Claude Code adaptadas a este proyecto (App-Logic).
Usar cuando se identifique un patrón de trabajo repetitivo que conviene documentar como skill reutilizable.

---

## Cuándo crear una skill nueva

Crear una skill si se cumple al menos uno de estos:
- El mismo tipo de tarea aparece 3 veces o más en la sesión
- Un proceso tiene más de 5 pasos y requiere recordar el orden
- Hay decisiones de diseño específicas del proyecto que Claude podría olvidar
- Un flujo de trabajo tarda más de 10 minutos y tiene partes mecánicas

**No crear** una skill para cosas que ya están en `CLAUDE.md` o en otra skill existente.

---

## Estructura de una skill

Cada skill vive en `.claude/skills/<nombre>.md` y tiene estas secciones:

```markdown
# Skill: Nombre descriptivo

## Propósito
Una o dos oraciones. Qué hace la skill y cuándo usarla.

## Cuándo usar esta skill
Lista de condiciones concretas que disparan el uso.

## Proceso
Pasos numerados, con ejemplos de código donde aplique.

## Convenciones
Reglas específicas del proyecto para este contexto.

## Red flags
Señales de que algo está saliendo mal.
```

---

## Proceso para crear una skill

### 1. Identificar el patrón
Antes de escribir la skill, hacerse estas preguntas:
- ¿Qué problema resuelve?
- ¿Cuándo se usa exactamente?
- ¿Qué pasos tiene que seguir Claude?
- ¿Qué errores comunes hay que evitar?

### 2. Escribir el archivo

```bash
# Ubicación siempre en:
.claude/skills/<nombre-en-kebab-case>.md
```

Reglas de naming:
- Usar kebab-case: `nuevo-modulo.md`, `refactor-router.md`
- Nombre descriptivo del proceso, no de la entidad
- En español si el proceso es específico del dominio

### 3. Registrar en CLAUDE.md
Agregar la nueva skill al listado en `CLAUDE.md`:

```markdown
## Skills disponibles
- `general.md` — convenciones y patrones principales
- `frontend-design.md` — cómo mejorar el frontend
- `skill-creator.md` — cómo crear nuevas skills
- `nueva-skill.md` — descripción breve
```

### 4. Verificar
- La skill tiene Propósito, Proceso y al menos un ejemplo concreto
- No duplica contenido de `general.md` u otras skills
- Los ejemplos de código son del proyecto real (no genéricos)

---

## Ejemplo: Skill para agregar un módulo nuevo

Si se necesita guía para agregar módulos frecuentemente, la skill podría llamarse `nuevo-modulo.md` y cubrir:
- Crear el modelo Pydantic
- Crear el router
- Registrar en main.py
- Crear la tabla en Supabase (esquema SQL)
- Conectar desde el frontend

---

## Convenciones

- Una skill = un proceso o flujo de trabajo
- No mezclar skills de backend y frontend en un mismo archivo
- Si la skill supera 150 líneas, dividirla en dos
- Revisar skills existentes antes de crear una nueva — puede ser una extensión

---

## Red flags

- Crear una skill que solo dice "hacer X bien" sin pasos concretos — eso es consejo, no skill
- Duplicar las convenciones de `general.md` en cada skill nueva
- Crear una skill para un caso que probablemente no se repita
