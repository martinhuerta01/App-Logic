-- Migración 009: localidad de cada ubicación.
-- PENDIENTE DE APLICAR en Supabase (ejecutar completa, una sola vez).
--
-- Sirve para saber en qué localidad está una ubicación aunque su nombre pase a ser el de un técnico.
-- Se completa con una propuesta: la parte del nombre que sigue a "CD" o "Taller", Vitaco = Córdoba,
-- Camioneta 1 = Longchamps y Camioneta 2 = General Rodríguez. Se corrige desde Stock → Catálogos → Ubicaciones.

ALTER TABLE ubicaciones ADD COLUMN IF NOT EXISTS localidad text NULL;

UPDATE ubicaciones SET localidad = trim(regexp_replace(trim(nombre), '^(CD|Taller)\s+', '', 'i'))
 WHERE localidad IS NULL AND trim(nombre) ~* '^(CD|Taller)\s+';
UPDATE ubicaciones SET localidad = 'Córdoba'           WHERE localidad IS NULL AND nombre ILIKE 'vitaco%';
UPDATE ubicaciones SET localidad = 'Longchamps'        WHERE localidad IS NULL AND trim(nombre) ILIKE 'camioneta 1';
UPDATE ubicaciones SET localidad = 'General Rodríguez' WHERE localidad IS NULL AND trim(nombre) ILIKE 'camioneta 2';
