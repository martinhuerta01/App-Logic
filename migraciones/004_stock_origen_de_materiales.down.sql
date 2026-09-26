-- Deshace la migración 004. Los tickets vuelven a descontar los materiales de la misma ubicación que el resto.

ALTER TABLE ubicaciones DROP COLUMN IF EXISTS ubicacion_materiales_id;
