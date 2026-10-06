-- Migración 010: cómo se cuenta cada código de La Serenísima.
-- PENDIENTE DE APLICAR en Supabase (ejecutar completa, una sola vez).
--
-- modo = 'suma'  : el código vale la suma de sus productos (por ejemplo insumos de frío).
-- modo = 'pares' : el código es un conjunto completo y vale el mínimo entre sus productos
--                  (ficha de enganche: 5 machos y 5 hembras son 5 fichas completas, no 10).
-- El código 8 (ficha de enganche) queda en 'pares'. Se cambia desde Stock → Catálogos → Mapeo La Serenísima.

ALTER TABLE mapeo_serenisima ADD COLUMN IF NOT EXISTS modo text NOT NULL DEFAULT 'suma'
  CHECK (modo IN ('suma', 'pares'));

UPDATE mapeo_serenisima SET modo = 'pares' WHERE codigo_serenisima = 8;
