# Migraciones de la base de datos

Una migración es un cambio de la estructura de la base de datos (tablas, columnas, funciones) guardado como archivo, para poder repetirlo en otro entorno o deshacerlo.

## Convenciones

- Archivos numerados: `NNN_nombre.up.sql` aplica el cambio y `NNN_nombre.down.sql` lo deshace.
- Se ejecutan a mano, en orden, en el editor de instrucciones de Supabase (no hay ejecutor automático).
- Cada migración debe poder deshacerse sin dejar la base inconsistente. Si el deshacer borra datos, el archivo `.down.sql` lo advierte al principio.
- Antes de aplicar una migración nueva en producción, probarla en una copia de la base o en un proyecto de prueba.
- El estado de aplicación se anota en la tabla de abajo.

## Estado

| Migración | Descripción | Aplicada en producción |
|---|---|---|
| 001_stock_tickets_y_seriales | Tickets importados, serial en movimientos, mapeo de talleres, estado de equipos, función de confirmación | Sí |
| 002_stock_talleres_y_configuracion | Doble pool por taller (`aplica_a`), configuración y cliente de equipos, función actualizada | Sí |
| 003_stock_minimos_plazos_y_equipos | Stock mínimo por vista, plazo de entrega por producto y enlace de ubicación con equipo | Sí |
| 004_stock_origen_de_materiales | Ubicación de la que salen los materiales de instalación (cable, cajas, pasacables) de los tickets de cada ubicación | Sí |
| 006_stock_nuevo_conteos_y_envios | Módulo Stock nuevo: conteos físicos, envíos entre ubicaciones con series (funciones atómicas), productos que llevan serie | Sí |
| 007_stock_nuevo_retirados | Retirados: recepción en la Oficina, faltantes y días de alerta (requiere la 006) | Sí |
| 008_ubicaciones_segmento | Segmento de cada ubicación (oficina, centro, taller, técnico, equipo, otras) para agrupar el Stock nuevo | Sí |
| 009_ubicaciones_localidad | Localidad de cada ubicación, para conservarla aunque el nombre sea el de un técnico | Sí |
| 010_serenisima_modo_de_conteo | Cómo se cuenta cada código de La Serenísima (suma o pares completos, como la ficha de enganche) | Sí |
| 011_corregir_stock | Corregir la cantidad de un solo producto en una ubicación, como ajuste con motivo (requiere la 006) | Sí |
| 012_stock_nuevo_entradas | Entradas de compras a la Oficina: agrupación, proveedor y función atómica (requiere la 006) | **Pendiente** |

## Datos iniciales que no son migraciones

Se cargaron por script y no forman parte de estos archivos (son datos, no estructura): las siete ubicaciones de talleres (Taller Bahía Blanca, Río IV, Tucumán, Mar del Plata, Mendoza, Corrientes y Rosario), las 25 palabras clave de `mapeo_talleres` y los kits `GPS_TICKET`, `PORTABLE_TICKET`, `CAMARA_TICKET` y `CORTE_TICKET` en `recetas`. Las migraciones 001 y 002 fueron reconstruidas a partir del plan de la semana del 24 de septiembre de 2026, porque en su momento se ejecutaron directamente en Supabase.
