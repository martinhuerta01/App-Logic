-- Migración 005: de qué ubicación salen las cámaras que se instalan en los tickets de una ubicación.
-- Ejemplo: las cámaras instaladas en los centros del interior salen de CD General Rodríguez,
-- porque la oficina las manda ahí y la gente de La Serenísima las reparte.
-- PENDIENTE DE APLICAR en Supabase (ejecutar completa, una sola vez).

ALTER TABLE ubicaciones ADD COLUMN IF NOT EXISTS ubicacion_camaras_id uuid NULL
  REFERENCES ubicaciones(id) ON DELETE SET NULL;
