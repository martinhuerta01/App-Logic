-- Deshace la migración 003. ATENCIÓN: se pierden los mínimos de stock, los plazos de entrega y los enlaces de ubicación con equipo.

ALTER TABLE ubicaciones DROP COLUMN IF EXISTS equipo_id;
DROP TABLE IF EXISTS stock_minimo;
ALTER TABLE productos DROP COLUMN IF EXISTS plazo_entrega_dias;
