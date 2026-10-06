-- Deshace la migración 010: todos los códigos vuelven a sumar sus productos.

ALTER TABLE mapeo_serenisima DROP COLUMN IF EXISTS modo;
