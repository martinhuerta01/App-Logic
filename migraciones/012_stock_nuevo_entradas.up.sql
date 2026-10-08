-- Migración 012: entradas (compras que llegan a la Oficina) en el módulo Stock nuevo.
-- PENDIENTE DE APLICAR en Supabase (ejecutar completa, una sola vez). Requiere la 006 ya aplicada.
--
--   * movimientos.entrada_id   : agrupa las líneas de una misma entrada.
--   * movimientos.proveedor_id : de qué proveedor vino (opcional).
--   * fn_registrar_entrada     : registra una entrada completa de forma atómica (con números de serie opcionales).

ALTER TABLE movimientos ADD COLUMN IF NOT EXISTS entrada_id uuid NULL;
ALTER TABLE movimientos ADD COLUMN IF NOT EXISTS proveedor_id uuid NULL REFERENCES proveedores(id) ON DELETE SET NULL;
CREATE INDEX IF NOT EXISTS idx_movimientos_entrada_id ON movimientos(entrada_id) WHERE entrada_id IS NOT NULL;

-- p_lineas: [{producto_id, cantidad, series: ["...", ...]}]
CREATE OR REPLACE FUNCTION fn_registrar_entrada(
  p_destino uuid, p_fecha date, p_cargado_por text, p_proveedor uuid, p_lineas jsonb
) RETURNS jsonb LANGUAGE plpgsql AS $$
DECLARE
  v_entrada uuid := gen_random_uuid();
  v_linea jsonb;
  v_producto uuid;
  v_cantidad int;
  v_codigo text;
  v_lleva_serie boolean;
  v_series text[];
  v_serie text;
  v_unidades int := 0;
BEGIN
  IF NOT EXISTS (SELECT 1 FROM ubicaciones WHERE id = p_destino) THEN RAISE EXCEPTION 'No existe la ubicación de destino'; END IF;
  IF p_proveedor IS NOT NULL AND NOT EXISTS (SELECT 1 FROM proveedores WHERE id = p_proveedor) THEN RAISE EXCEPTION 'No existe el proveedor'; END IF;
  IF p_lineas IS NULL OR jsonb_array_length(p_lineas) = 0 THEN RAISE EXCEPTION 'La entrada no tiene productos'; END IF;

  FOR v_linea IN SELECT * FROM jsonb_array_elements(p_lineas)
  LOOP
    v_producto := (v_linea->>'producto_id')::uuid;
    v_cantidad := (v_linea->>'cantidad')::int;
    IF v_cantidad IS NULL OR v_cantidad <= 0 THEN RAISE EXCEPTION 'La cantidad de cada producto tiene que ser mayor a cero'; END IF;
    SELECT codigo, lleva_serie INTO v_codigo, v_lleva_serie FROM productos WHERE id = v_producto;
    IF v_codigo IS NULL THEN RAISE EXCEPTION 'Producto inexistente'; END IF;

    v_series := ARRAY(SELECT trim(x) FROM jsonb_array_elements_text(coalesce(v_linea->'series', '[]'::jsonb)) AS x WHERE trim(x) <> '');
    IF coalesce(array_length(v_series, 1), 0) > 0 THEN
      IF NOT v_lleva_serie THEN RAISE EXCEPTION 'El producto % no se sigue por número de serie', trim(v_codigo); END IF;
      IF array_length(v_series, 1) <> v_cantidad THEN
        RAISE EXCEPTION 'De % cargaste % números de serie y la cantidad es %', trim(v_codigo), array_length(v_series, 1), v_cantidad;
      END IF;
      IF (SELECT count(DISTINCT s) FROM unnest(v_series) s) <> array_length(v_series, 1) THEN
        RAISE EXCEPTION 'Hay números de serie repetidos en %', trim(v_codigo);
      END IF;
      FOREACH v_serie IN ARRAY v_series
      LOOP
        IF EXISTS (SELECT 1 FROM equipos_estado WHERE serial = v_serie) THEN
          RAISE EXCEPTION 'El número de serie % ya está cargado en Equipos por serie', v_serie;
        END IF;
        INSERT INTO equipos_estado (producto_id, serial, estado, ubicacion_id) VALUES (v_producto, v_serie, 'EN_STOCK', p_destino);
        INSERT INTO movimientos (tipo, producto_id, destino_id, cantidad, fecha, cargado_por, observacion, serial, entrada_id, proveedor_id)
        VALUES ('ENTRADA', v_producto, p_destino, 1, p_fecha, p_cargado_por, 'Entrada', v_serie, v_entrada, p_proveedor);
      END LOOP;
    END IF;

    IF v_cantidad - coalesce(array_length(v_series, 1), 0) > 0 THEN
      INSERT INTO movimientos (tipo, producto_id, destino_id, cantidad, fecha, cargado_por, observacion, entrada_id, proveedor_id)
      VALUES ('ENTRADA', v_producto, p_destino, v_cantidad - coalesce(array_length(v_series, 1), 0), p_fecha, p_cargado_por, 'Entrada', v_entrada, p_proveedor);
    END IF;

    PERFORM fn_mover_stock(v_producto, p_destino, v_cantidad);
    v_unidades := v_unidades + v_cantidad;
  END LOOP;

  RETURN jsonb_build_object('entrada_id', v_entrada, 'productos', jsonb_array_length(p_lineas), 'unidades', v_unidades);
END;
$$;
