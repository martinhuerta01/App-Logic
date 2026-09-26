-- Migración 004: de qué ubicación salen los materiales de instalación de los tickets de una ubicación.
-- Ejemplo: los tickets de CD General Rodríguez usan la cámara del centro pero el cable y los soportes de Camioneta 2.
-- PENDIENTE DE APLICAR en Supabase (ejecutar completa, una sola vez).

ALTER TABLE ubicaciones ADD COLUMN IF NOT EXISTS ubicacion_materiales_id uuid NULL
  REFERENCES ubicaciones(id) ON DELETE SET NULL;
