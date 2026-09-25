-- Migración 002: doble pool por taller (La Serenísima u otros clientes) y configuración/cliente de cada equipo.
-- YA APLICADA en Supabase (reconstruida para dejarla versionada).

-- Distingue el destino según el cliente del ticket
ALTER TABLE mapeo_talleres ADD COLUMN IF NOT EXISTS aplica_a text NOT NULL DEFAULT 'serenisima';

-- Configuración actual del equipo (CHASIS, SEMI, TRACTOR, RFID, BASICO) y cliente actual
ALTER TABLE equipos_estado ADD COLUMN IF NOT EXISTS configuracion text NULL;
ALTER TABLE equipos_estado ADD COLUMN IF NOT EXISTS cliente text NULL;

-- Reemplaza la función anterior: además guarda configuración y cliente
CREATE OR REPLACE FUNCTION fn_confirmar_ticket_stock(
  p_ticket_numero text,
  p_distrito text,
  p_archivo_nombre text,
  p_fila_excel jsonb,
  p_cargado_por text,
  p_movimientos jsonb
) RETURNS jsonb
LANGUAGE plpgsql
AS $$
DECLARE
  v_ticket_id uuid;
  v_mov jsonb;
  v_stock_id uuid;
  v_cantidad_actual int;
BEGIN
  INSERT INTO tickets_importados (ticket_numero, distrito, archivo_nombre, fila_excel, importado_por)
  VALUES (p_ticket_numero, p_distrito, p_archivo_nombre, p_fila_excel, p_cargado_por)
  ON CONFLICT (ticket_numero) DO NOTHING
  RETURNING id INTO v_ticket_id;

  IF v_ticket_id IS NULL THEN
    RETURN jsonb_build_object('duplicado', true, 'ticket_numero', p_ticket_numero);
  END IF;

  FOR v_mov IN SELECT * FROM jsonb_array_elements(p_movimientos)
  LOOP
    INSERT INTO movimientos (tipo, producto_id, origen_id, destino_id, cantidad, fecha, cargado_por, observacion, serial, ticket_id)
    VALUES (
      v_mov->>'tipo', (v_mov->>'producto_id')::uuid,
      NULLIF(v_mov->>'origen_id','')::uuid, NULLIF(v_mov->>'destino_id','')::uuid,
      (v_mov->>'cantidad')::int, (v_mov->>'fecha')::date,
      p_cargado_por, v_mov->>'observacion', NULLIF(v_mov->>'serial',''), v_ticket_id
    );

    IF NULLIF(v_mov->>'origen_id','') IS NOT NULL THEN
      SELECT id, cantidad INTO v_stock_id, v_cantidad_actual FROM stock_actual
        WHERE producto_id = (v_mov->>'producto_id')::uuid AND ubicacion_id = (v_mov->>'origen_id')::uuid;
      IF v_stock_id IS NOT NULL THEN
        UPDATE stock_actual SET cantidad = v_cantidad_actual - (v_mov->>'cantidad')::int WHERE id = v_stock_id;
      ELSE
        INSERT INTO stock_actual (producto_id, ubicacion_id, cantidad)
        VALUES ((v_mov->>'producto_id')::uuid, (v_mov->>'origen_id')::uuid, -(v_mov->>'cantidad')::int);
      END IF;
    END IF;
    IF NULLIF(v_mov->>'destino_id','') IS NOT NULL THEN
      SELECT id, cantidad INTO v_stock_id, v_cantidad_actual FROM stock_actual
        WHERE producto_id = (v_mov->>'producto_id')::uuid AND ubicacion_id = (v_mov->>'destino_id')::uuid;
      IF v_stock_id IS NOT NULL THEN
        UPDATE stock_actual SET cantidad = v_cantidad_actual + (v_mov->>'cantidad')::int WHERE id = v_stock_id;
      ELSE
        INSERT INTO stock_actual (producto_id, ubicacion_id, cantidad)
        VALUES ((v_mov->>'producto_id')::uuid, (v_mov->>'destino_id')::uuid, (v_mov->>'cantidad')::int);
      END IF;
    END IF;

    IF NULLIF(v_mov->>'serial','') IS NOT NULL THEN
      INSERT INTO equipos_estado (producto_id, serial, estado, ubicacion_id, patente, configuracion, cliente)
      VALUES (
        (v_mov->>'producto_id')::uuid, v_mov->>'serial',
        CASE v_mov->>'tipo' WHEN 'RETIRO' THEN 'RETIRADO_PENDIENTE' WHEN 'INSTALACION' THEN 'INSTALADO' ELSE 'EN_STOCK' END,
        CASE WHEN v_mov->>'tipo' = 'INSTALACION' THEN NULL ELSE NULLIF(v_mov->>'destino_id','')::uuid END,
        CASE WHEN v_mov->>'tipo' = 'INSTALACION' THEN v_mov->>'patente' ELSE NULL END,
        NULLIF(v_mov->>'configuracion',''),
        p_distrito
      )
      ON CONFLICT (serial) DO UPDATE SET
        estado = EXCLUDED.estado,
        ubicacion_id = EXCLUDED.ubicacion_id,
        patente = EXCLUDED.patente,
        configuracion = COALESCE(NULLIF(EXCLUDED.configuracion, ''), equipos_estado.configuracion),
        cliente = COALESCE(p_distrito, equipos_estado.cliente),
        updated_at = now();
    END IF;
  END LOOP;

  RETURN jsonb_build_object('duplicado', false, 'ticket_id', v_ticket_id, 'movimientos', jsonb_array_length(p_movimientos));
END;
$$;
