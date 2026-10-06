-- Deshace la migración 011. Las correcciones ya hechas quedan como ajustes en Movimientos.

DROP FUNCTION IF EXISTS fn_corregir_stock(uuid, uuid, int, text, text, date);
