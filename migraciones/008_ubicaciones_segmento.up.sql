-- Migración 008: segmento de cada ubicación (para agrupar el Stock nuevo).
-- PENDIENTE DE APLICAR en Supabase (ejecutar completa, una sola vez).
--
-- Segmentos: oficina, cd (centros de distribución), taller, tecnico, equipo (camionetas), otras.
-- Se completa con una propuesta según el nombre y el tipo; se corrige después desde Stock → Catálogos → Ubicaciones.
-- Vitaco queda como taller. Los técnicos (sin taller propio) hay que marcarlos a mano: no se puede adivinar por el nombre.

ALTER TABLE ubicaciones ADD COLUMN IF NOT EXISTS segmento text NULL
  CHECK (segmento IS NULL OR segmento IN ('oficina', 'cd', 'taller', 'tecnico', 'equipo', 'otras'));

UPDATE ubicaciones SET segmento = 'oficina' WHERE segmento IS NULL AND tipo = 'oficina';
UPDATE ubicaciones SET segmento = 'equipo'  WHERE segmento IS NULL AND nombre ILIKE 'camioneta%';
UPDATE ubicaciones SET segmento = 'taller'  WHERE segmento IS NULL AND (nombre ILIKE 'taller%' OR nombre ILIKE 'vitaco%');
UPDATE ubicaciones SET segmento = 'cd'      WHERE segmento IS NULL AND tipo = 'cd';
UPDATE ubicaciones SET segmento = 'otras'   WHERE segmento IS NULL;
