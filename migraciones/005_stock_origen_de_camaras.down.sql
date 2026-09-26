-- Deshace la migración 005. Las cámaras vuelven a descontarse de la misma ubicación que el resto.

ALTER TABLE ubicaciones DROP COLUMN IF EXISTS ubicacion_camaras_id;
