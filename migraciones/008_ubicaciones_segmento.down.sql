-- Deshace la migración 008: se pierde el segmento de cada ubicación.

ALTER TABLE ubicaciones DROP COLUMN IF EXISTS segmento;
