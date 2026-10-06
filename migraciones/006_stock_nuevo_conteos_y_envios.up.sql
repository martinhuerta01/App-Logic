-- Migración 006: módulo Stock nuevo (conteos físicos y envíos entre ubicaciones).
-- PENDIENTE DE APLICAR en Supabase (ejecutar completa, una sola vez).
--
-- Qué agrega:
--   * movimientos.envio_id  : agrupa las líneas de un mismo envío.
--   * movimientos.conteo_id : marca la diferencia que dejó un conteo físico.
--   * productos.lleva_serie : los dispositivos que se siguen por número de serie.
--   * conteos / conteo_lineas : cada conteo físico con lo que decía el sistema, lo contado y el motivo.
--   * fn_registrar_envio    : registra un envío completo de forma atómica (con series).
--   * fn_confirmar_conteo   : deja el stock de una ubicación en lo contado, de forma atómica.
-- No toca nada de lo que ya funciona: el módulo viejo sigue andando con las mismas tablas.

ALTER TABLE movimientos ADD COLUMN IF NOT EXISTS envio_id uuid NULL;
ALTER TABLE movimientos ADD COLUMN IF NOT EXISTS conteo_id uuid NULL;
CREATE INDEX IF NOT EXISTS idx_movimientos_envio_id ON movimientos(envio_id) WHERE envio_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_movimientos_conteo_id ON movimientos(conteo_id) WHERE conteo_id IS NOT NULL;

ALTER TABLE productos ADD COLUMN IF NOT EXISTS lleva_serie boolean NOT NULL DEFAULT false;
UPDATE productos SET lleva_serie = true WHERE upper(trim(codigo)) IN ('D03', 'D13');

CREATE TABLE IF NOT EXISTS conteos (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  ubicacion_id uuid NOT NULL REFERENCES ubicaciones(id),
  fecha date NOT NULL,
  hecho_por text NULL,
  observacion text NULL,
  creado_en timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_conteos_ubicacion ON conteos(ubicacion_id, creado_en DESC);

CREATE TABLE IF NOT EXISTS conteo_lineas (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  conteo_id uuid NOT NULL REFERENCES conteos(id) ON DELETE CASCADE,
  producto_id uuid NOT NULL REFERENCES productos(id),
  esperado int NOT NULL,
  contado int NOT NULL,
  motivo text NULL
);
CREATE INDEX IF NOT EXISTS idx_conteo_lineas_conteo ON conteo_lineas(conteo_id);

-- Suma o resta unidades en el caché de stock (crea la fila si no existe).
CREATE OR REPLACE FUNCTION fn_mover_stock(p_producto uuid, p_ubicacion uuid, p_delta int)
RETURNS void LANGUAGE plpgsql AS $$
DECLARE
  v_id uuid;
BEGIN
  SELECT id INTO v_id FROM stock_actual WHERE producto_id = p_producto AND ubicacion_id = p_ubicacion FOR UPDATE;
  IF v_id IS NULL THEN
    INSERT INTO stock_actual (producto_id, ubicacion_id, cantidad) VALUES (p_producto, p_ubicacion, p_delta);
  ELSE
    UPDATE stock_actual SET cantidad = cantidad + p_delta WHERE id = v_id;
  END IF;
END;
$$;

-- Envío entre ubicaciones. p_lineas: [{producto_id, cantidad, series: ["...", ...]}]
-- Desde una ubicación de tipo oficina no deja sacar más de lo que hay.
-- Desde cualquier otra deja y devuelve un aviso por cada producto que queda en negativo.
CREATE OR REPLACE FUNCTION fn_registrar_envio(
  p_origen uuid, p_destino uuid, p_fecha date, p_cargado_por text, p_lineas jsonb
) RETURNS jsonb LANGUAGE plpgsql AS $$
DECLARE
  v_envio uuid := gen_random_uuid();
  v_origen_tipo text;
  v_origen_nombre text;
  v_linea jsonb;
  v_producto uuid;
  v_cantidad int;
  v_disponible int;
  v_prod_codigo text;
  v_prod_lleva_serie boolean;
  v_series text[];
  v_serie text;
  v_eq record;
  v_ubic_eq text;
  v_negativos jsonb := '[]'::jsonb;
BEGIN
  IF p_origen = p_destino THEN
    RAISE EXCEPTION 'El origen y el destino no pueden ser la misma ubicación';
  END IF;
  SELECT tipo, nombre INTO v_origen_tipo, v_origen_nombre FROM ubicaciones WHERE id = p_origen;
  IF v_origen_nombre IS NULL THEN RAISE EXCEPTION 'No existe la ubicación de origen'; END IF;
  IF NOT EXISTS (SELECT 1 FROM ubicaciones WHERE id = p_destino) THEN RAISE EXCEPTION 'No existe la ubicación de destino'; END IF;
  IF p_lineas IS NULL OR jsonb_array_length(p_lineas) = 0 THEN RAISE EXCEPTION 'El envío no tiene productos'; END IF;

  FOR v_linea IN SELECT * FROM jsonb_array_elements(p_lineas)
  LOOP
    v_producto := (v_linea->>'producto_id')::uuid;
    v_cantidad := (v_linea->>'cantidad')::int;
    IF v_cantidad IS NULL OR v_cantidad <= 0 THEN RAISE EXCEPTION 'La cantidad de cada producto tiene que ser mayor a cero'; END IF;
    SELECT codigo, lleva_serie INTO v_prod_codigo, v_prod_lleva_serie FROM productos WHERE id = v_producto;
    IF v_prod_codigo IS NULL THEN RAISE EXCEPTION 'Producto inexistente'; END IF;

    SELECT coalesce((SELECT cantidad FROM stock_actual WHERE producto_id = v_producto AND ubicacion_id = p_origen), 0) INTO v_disponible;
    IF v_origen_tipo = 'oficina' AND v_disponible < v_cantidad THEN
      RAISE EXCEPTION 'La % no tiene suficiente %: hay % y se quieren enviar %', v_origen_nombre, trim(v_prod_codigo), v_disponible, v_cantidad;
    END IF;

    v_series := ARRAY(SELECT trim(x) FROM jsonb_array_elements_text(coalesce(v_linea->'series', '[]'::jsonb)) AS x WHERE trim(x) <> '');
    IF coalesce(array_length(v_series, 1), 0) > 0 THEN
      IF NOT v_prod_lleva_serie THEN RAISE EXCEPTION 'El producto % no se sigue por número de serie', trim(v_prod_codigo); END IF;
      IF array_length(v_series, 1) <> v_cantidad THEN
        RAISE EXCEPTION 'De % cargaste % números de serie y la cantidad es %', trim(v_prod_codigo), array_length(v_series, 1), v_cantidad;
      END IF;
      IF (SELECT count(DISTINCT s) FROM unnest(v_series) s) <> array_length(v_series, 1) THEN
        RAISE EXCEPTION 'Hay números de serie repetidos en %', trim(v_prod_codigo);
      END IF;

      FOREACH v_serie IN ARRAY v_series
      LOOP
        SELECT e.*, u.nombre AS ubic_nombre INTO v_eq FROM equipos_estado e LEFT JOIN ubicaciones u ON u.id = e.ubicacion_id WHERE e.serial = v_serie;
        IF FOUND THEN
          IF v_eq.producto_id <> v_producto THEN RAISE EXCEPTION 'El número de serie % es de otro producto', v_serie; END IF;
          IF v_eq.estado <> 'EN_STOCK' THEN RAISE EXCEPTION 'El número de serie % está en estado %, no se puede enviar', v_serie, v_eq.estado; END IF;
          IF v_eq.ubicacion_id IS NOT NULL AND v_eq.ubicacion_id <> p_origen THEN
            RAISE EXCEPTION 'El número de serie % figura en %, no en %', v_serie, coalesce(v_eq.ubic_nombre, '?'), v_origen_nombre;
          END IF;
          UPDATE equipos_estado SET ubicacion_id = p_destino, updated_at = now() WHERE id = v_eq.id;
        ELSE
          INSERT INTO equipos_estado (producto_id, serial, estado, ubicacion_id) VALUES (v_producto, v_serie, 'EN_STOCK', p_destino);
        END IF;
        INSERT INTO movimientos (tipo, producto_id, origen_id, destino_id, cantidad, fecha, cargado_por, observacion, serial, envio_id)
        VALUES ('TRANSFERENCIA', v_producto, p_origen, p_destino, 1, p_fecha, p_cargado_por, 'Envío', v_serie, v_envio);
      END LOOP;
    END IF;

    IF v_cantidad - coalesce(array_length(v_series, 1), 0) > 0 THEN
      INSERT INTO movimientos (tipo, producto_id, origen_id, destino_id, cantidad, fecha, cargado_por, observacion, envio_id)
      VALUES ('TRANSFERENCIA', v_producto, p_origen, p_destino, v_cantidad - coalesce(array_length(v_series, 1), 0), p_fecha, p_cargado_por, 'Envío', v_envio);
    END IF;

    PERFORM fn_mover_stock(v_producto, p_origen, -v_cantidad);
    PERFORM fn_mover_stock(v_producto, p_destino, v_cantidad);

    IF v_origen_tipo <> 'oficina' AND v_disponible - v_cantidad < 0 THEN
      v_negativos := v_negativos || jsonb_build_object('producto_id', v_producto, 'codigo', trim(v_prod_codigo), 'queda', v_disponible - v_cantidad);
    END IF;
  END LOOP;

  RETURN jsonb_build_object('envio_id', v_envio, 'lineas', jsonb_array_length(p_lineas), 'negativos', v_negativos);
END;
$$;

-- Conteo físico de una ubicación. p_lineas: [{producto_id, contado, motivo, series: [...]}]
-- Deja el stock de cada producto contado exactamente en lo contado y registra la diferencia.
CREATE OR REPLACE FUNCTION fn_confirmar_conteo(
  p_ubicacion uuid, p_fecha date, p_hecho_por text, p_observacion text, p_lineas jsonb
) RETURNS jsonb LANGUAGE plpgsql AS $$
DECLARE
  v_conteo uuid := gen_random_uuid();
  v_linea jsonb;
  v_producto uuid;
  v_contado int;
  v_esperado int;
  v_delta int;
  v_motivo text;
  v_prod_codigo text;
  v_prod_lleva_serie boolean;
  v_series text[];
  v_serie text;
  v_eq record;
  v_con_diferencia int := 0;
BEGIN
  IF NOT EXISTS (SELECT 1 FROM ubicaciones WHERE id = p_ubicacion) THEN RAISE EXCEPTION 'No existe la ubicación'; END IF;
  IF p_lineas IS NULL OR jsonb_array_length(p_lineas) = 0 THEN RAISE EXCEPTION 'El conteo no tiene productos'; END IF;
  INSERT INTO conteos (id, ubicacion_id, fecha, hecho_por, observacion) VALUES (v_conteo, p_ubicacion, p_fecha, p_hecho_por, p_observacion);

  FOR v_linea IN SELECT * FROM jsonb_array_elements(p_lineas)
  LOOP
    v_producto := (v_linea->>'producto_id')::uuid;
    v_contado := (v_linea->>'contado')::int;
    v_motivo := nullif(trim(coalesce(v_linea->>'motivo', '')), '');
    IF v_contado IS NULL OR v_contado < 0 THEN RAISE EXCEPTION 'Lo contado no puede ser negativo'; END IF;
    SELECT codigo, lleva_serie INTO v_prod_codigo, v_prod_lleva_serie FROM productos WHERE id = v_producto;
    IF v_prod_codigo IS NULL THEN RAISE EXCEPTION 'Producto inexistente'; END IF;

    SELECT coalesce((SELECT cantidad FROM stock_actual WHERE producto_id = v_producto AND ubicacion_id = p_ubicacion), 0) INTO v_esperado;
    v_delta := v_contado - v_esperado;
    INSERT INTO conteo_lineas (conteo_id, producto_id, esperado, contado, motivo) VALUES (v_conteo, v_producto, v_esperado, v_contado, v_motivo);

    IF v_delta <> 0 THEN
      v_con_diferencia := v_con_diferencia + 1;
      INSERT INTO movimientos (tipo, producto_id, origen_id, destino_id, cantidad, fecha, cargado_por, observacion, conteo_id)
      VALUES (
        'AJUSTE', v_producto,
        CASE WHEN v_delta < 0 THEN p_ubicacion END, CASE WHEN v_delta > 0 THEN p_ubicacion END,
        abs(v_delta), p_fecha, p_hecho_por, 'Conteo' || coalesce(': ' || v_motivo, ''), v_conteo
      );
      PERFORM fn_mover_stock(v_producto, p_ubicacion, v_delta);
    END IF;

    v_series := ARRAY(SELECT trim(x) FROM jsonb_array_elements_text(coalesce(v_linea->'series', '[]'::jsonb)) AS x WHERE trim(x) <> '');
    IF coalesce(array_length(v_series, 1), 0) > 0 THEN
      IF NOT v_prod_lleva_serie THEN RAISE EXCEPTION 'El producto % no se sigue por número de serie', trim(v_prod_codigo); END IF;
      IF array_length(v_series, 1) > v_contado THEN
        RAISE EXCEPTION 'De % cargaste % números de serie pero contaste %', trim(v_prod_codigo), array_length(v_series, 1), v_contado;
      END IF;
      IF (SELECT count(DISTINCT s) FROM unnest(v_series) s) <> array_length(v_series, 1) THEN
        RAISE EXCEPTION 'Hay números de serie repetidos en %', trim(v_prod_codigo);
      END IF;
      FOREACH v_serie IN ARRAY v_series
      LOOP
        SELECT * INTO v_eq FROM equipos_estado WHERE serial = v_serie;
        IF FOUND THEN
          IF v_eq.producto_id <> v_producto THEN RAISE EXCEPTION 'El número de serie % es de otro producto', v_serie; END IF;
          IF v_eq.estado = 'INSTALADO' THEN RAISE EXCEPTION 'El número de serie % figura instalado en un vehículo', v_serie; END IF;
          UPDATE equipos_estado SET ubicacion_id = p_ubicacion, updated_at = now() WHERE id = v_eq.id;
        ELSE
          INSERT INTO equipos_estado (producto_id, serial, estado, ubicacion_id) VALUES (v_producto, v_serie, 'EN_STOCK', p_ubicacion);
        END IF;
      END LOOP;
    END IF;
  END LOOP;

  RETURN jsonb_build_object('conteo_id', v_conteo, 'productos', jsonb_array_length(p_lineas), 'con_diferencia', v_con_diferencia);
END;
$$;
