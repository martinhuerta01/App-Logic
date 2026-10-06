-- Deshace la migración 009: se pierde la localidad de cada ubicación.

ALTER TABLE ubicaciones DROP COLUMN IF EXISTS localidad;
