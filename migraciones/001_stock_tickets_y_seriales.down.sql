-- Deshace la migración 001. ATENCIÓN: borra los tickets importados y el estado de equipos por serie.
-- Antes de ejecutar, exportar esas tablas si hay datos que importen.

DROP FUNCTION IF EXISTS fn_confirmar_ticket_stock(text, text, text, jsonb, text, jsonb);
DROP TABLE IF EXISTS equipos_estado;
DROP TABLE IF EXISTS mapeo_talleres;
DROP INDEX IF EXISTS idx_movimientos_ticket_id;
DROP INDEX IF EXISTS idx_movimientos_serial;
ALTER TABLE movimientos DROP COLUMN IF EXISTS ticket_id;
ALTER TABLE movimientos DROP COLUMN IF EXISTS serial;
DROP TABLE IF EXISTS tickets_importados;
