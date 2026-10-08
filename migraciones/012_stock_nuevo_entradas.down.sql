-- Deshace la migración 012. Las entradas ya cargadas quedan como movimientos ENTRADA, sin proveedor ni agrupación.

DROP FUNCTION IF EXISTS fn_registrar_entrada(uuid, date, text, uuid, jsonb);
DROP INDEX IF EXISTS idx_movimientos_entrada_id;
ALTER TABLE movimientos DROP COLUMN IF EXISTS proveedor_id;
ALTER TABLE movimientos DROP COLUMN IF EXISTS entrada_id;
