-- Migración 011: corregir la cantidad de un solo producto en una ubicación (sin hacer un conteo completo).
-- PENDIENTE DE APLICAR en Supabase (ejecutar completa, una sola vez). Requiere la 006 ya aplicada.
--
-- Deja el stock del producto exactamente en la cantidad indicada y registra la diferencia como un ajuste
-- con quién, cuándo y motivo. No cuenta como conteo de la ubicación: no cambia la fecha del último conteo.

CREATE OR REPLACE FUNCTION fn_corregir_stock(
  p_ubicacion uuid, p_producto uuid, p_nuevo int, p_motivo text, p_por text, p_fecha date
) RETURNS jsonb LANGUAGE plpgsql AS $$
DECLARE
  v_actual int;
  v_delta int;
BEGIN
  IF p_nuevo IS NULL OR p_nuevo < 0 THEN RAISE EXCEPTION 'La cantidad no puede ser negativa'; END IF;
  IF NOT EXISTS (SELECT 1 FROM ubicaciones WHERE id = p_ubicacion) THEN RAISE EXCEPTION 'No existe la ubicación'; END IF;
  IF NOT EXISTS (SELECT 1 FROM productos WHERE id = p_producto) THEN RAISE EXCEPTION 'Producto inexistente'; END IF;

  SELECT coalesce((SELECT cantidad FROM stock_actual WHERE producto_id = p_producto AND ubicacion_id = p_ubicacion FOR UPDATE), 0) INTO v_actual;
  v_delta := p_nuevo - v_actual;
  IF v_delta = 0 THEN
    RETURN jsonb_build_object('diferencia', 0, 'anterior', v_actual, 'nuevo', p_nuevo);
  END IF;

  INSERT INTO movimientos (tipo, producto_id, origen_id, destino_id, cantidad, fecha, cargado_por, observacion)
  VALUES (
    'AJUSTE', p_producto,
    CASE WHEN v_delta < 0 THEN p_ubicacion END, CASE WHEN v_delta > 0 THEN p_ubicacion END,
    abs(v_delta), coalesce(p_fecha, CURRENT_DATE), p_por, 'Corrección' || coalesce(': ' || nullif(trim(p_motivo), ''), '')
  );
  PERFORM fn_mover_stock(p_producto, p_ubicacion, v_delta);
  RETURN jsonb_build_object('diferencia', v_delta, 'anterior', v_actual, 'nuevo', p_nuevo);
END;
$$;
