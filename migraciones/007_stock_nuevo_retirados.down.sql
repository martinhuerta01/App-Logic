-- Deshace la migración 007.
-- ATENCIÓN: se pierde el historial de recepciones y faltantes, y los días de alerta configurados.

DROP FUNCTION IF EXISTS fn_recibir_retirado(text, uuid, text, text, jsonb);
DROP TABLE IF EXISTS faltantes;
DROP TABLE IF EXISTS recepciones;
DROP TABLE IF EXISTS configuracion_stock;
ALTER TABLE equipos_estado DROP COLUMN IF EXISTS recibido_por;
ALTER TABLE equipos_estado DROP COLUMN IF EXISTS recibido_en;
