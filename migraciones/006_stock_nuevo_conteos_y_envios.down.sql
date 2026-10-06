-- Deshace la migración 006.
-- ATENCIÓN: se pierde el historial de conteos y el vínculo de los movimientos con su envío o conteo.
-- Los movimientos y el stock quedan como están (solo se quitan las marcas).

DROP FUNCTION IF EXISTS fn_confirmar_conteo(uuid, date, text, text, jsonb);
DROP FUNCTION IF EXISTS fn_registrar_envio(uuid, uuid, date, text, jsonb);
DROP FUNCTION IF EXISTS fn_mover_stock(uuid, uuid, int);
DROP TABLE IF EXISTS conteo_lineas;
DROP TABLE IF EXISTS conteos;
ALTER TABLE productos DROP COLUMN IF EXISTS lleva_serie;
DROP INDEX IF EXISTS idx_movimientos_conteo_id;
DROP INDEX IF EXISTS idx_movimientos_envio_id;
ALTER TABLE movimientos DROP COLUMN IF EXISTS conteo_id;
ALTER TABLE movimientos DROP COLUMN IF EXISTS envio_id;
